"use client";

/**
 * Widget flutuante de chat com a "Lumen AI" (agente LangGraph + Gemini no backend).
 *
 * Montado globalmente em app/layout.tsx (canto inferior direito). Fluxo:
 * 1. Ao obter o `sessionId` (StoreContext), carrega o histórico persistido da
 *    conversa via `GET /api/v1/chat/sessions/{session_id}`; se vazio, mostra uma
 *    mensagem de boas-vindas apenas local. "Reiniciar conversa" chama
 *    `DELETE /api/v1/chat/sessions/{session_id}`.
 * 2. Ao enviar uma mensagem, faz `POST /api/v1/chat/stream` com o corpo
 *    `{ session_id, message }`. O backend responde em Server-Sent Events
 *    (`text/event-stream`), lidos manualmente via `ReadableStream` (a API
 *    `EventSource` do navegador não suporta POST). Eventos emitidos pelo backend:
 *    - `token`      → `data: {"token": "..."}` — pedaço do texto da resposta,
 *                     concatenado à última mensagem do assistente;
 *    - `ui_actions` → `data: {"actions": [...]}` — ações de interface (ver
 *                     ChatUiAction), enviadas uma vez ao final, só se houver;
 *    - `done`       → `data: {}` — fim do stream (sem tratamento explícito: o
 *                     loop termina quando o servidor fecha a conexão).
 *    O widget também aceita um evento `status` (`data: {"status": "..."}`), mas o
 *    backend atual não o emite; o rótulo "Pensando..." é definido localmente e
 *    some no primeiro `token`.
 * 3. As `ui_actions` são renderizadas abaixo da resposta:
 *    - `SELECT_VARIANT`: botões de variação; o clique envia `opt.prompt` como nova
 *      mensagem, pedindo ao agente para adicionar aquela variação ao carrinho;
 *    - `CART_UPDATED`: card com total e link para o checkout. Quando recebido, o
 *      carrinho global é recarregado (`refreshCart`), pois o agente alterou o
 *      carrinho diretamente no backend.
 */

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bot, MessageCircle, RotateCcw, Send, ShoppingBag, X } from "lucide-react";
import { API_URL, api, formatBRL } from "@/lib/api";
import { useStore } from "@/context/StoreContext";
import { ChatMessageItem, ChatUiAction } from "@/types";

/** Sugestões exibidas como atalhos enquanto a conversa só tem a saudação inicial. */
const QUICK_PROMPTS = [
  "Qual o estoque do LMN-NB-001?",
  "Quero comprar o Headset Sony",
  "Qual a política de troca e frete?",
];

/** Chat flutuante com streaming de respostas e ações interativas do agente de IA. */
export function LumenChatWidget() {
  const { sessionId, refreshCart, showToast } = useStore();
  /** Painel do chat aberto/fechado (o botão redondo sempre aparece). */
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [input, setInput] = useState("");
  /** `true` enquanto uma resposta está sendo recebida; bloqueia novos envios. */
  const [isStreaming, setIsStreaming] = useState(false);
  /** Rótulo de progresso ("Pensando..." local ou evento `status`, se houver); vazio = oculto. */
  const [statusLabel, setStatusLabel] = useState("");
  /** Elemento sentinela no fim da lista, usado para rolar até a última mensagem. */
  const bottomRef = useRef<HTMLDivElement>(null);

  // Carrega o histórico da conversa desta sessão assim que o sessionId existe.
  // A mensagem de boas-vindas é apenas local (não é salva no backend).
  useEffect(() => {
    if (!sessionId) return;
    api
      .getChatHistory(sessionId)
      .then((hist) => {
        if (hist.length > 0) {
          setMessages(hist);
        } else {
          setMessages([
            {
              role: "assistant",
              content:
                "Olá! Eu sou a Lumen AI, assistente virtual da loja. Posso consultar especificações e estoque em tempo real, adicionar produtos ao carrinho ou tirar dúvidas sobre frete e trocas. Como posso ajudar?",
            },
          ]);
        }
      })
      .catch(() => {});
  }, [sessionId]);

  // Auto-scroll para o final a cada nova mensagem/token, mudança de status ou abertura do painel.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, statusLabel, isOpen]);

  /**
   * Envia uma mensagem ao agente e consome a resposta em streaming (SSE).
   * Usada pelo formulário, pelos atalhos QUICK_PROMPTS e pelos botões de variação.
   */
  const sendMessage = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed || !sessionId || isStreaming) return;

    setInput("");
    setIsStreaming(true);
    setStatusLabel("Pensando...");
    // Adiciona a mensagem do usuário e um "placeholder" vazio do assistente,
    // que será preenchido token a token conforme o stream chega.
    setMessages((prev) => [...prev, { role: "user", content: trimmed }, { role: "assistant", content: "" }]);

    try {
      const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: trimmed }),
      });

      if (!response.body) throw new Error("Stream indisponível.");

      // Leitura incremental do corpo. Cada evento SSE tem o formato
      // "event: <nome>\ndata: <json>\n\n"; como um chunk de rede pode cortar
      // um evento ao meio, o trecho incompleto fica no `buffer` até o próximo chunk.
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        // O último pedaço pode ser um evento ainda incompleto: guarda para a próxima iteração.
        buffer = events.pop() || "";

        for (const rawEvent of events) {
          const eventMatch = rawEvent.match(/event:\s*(.+)/);
          const dataMatch = rawEvent.match(/data:\s*(.+)/);
          if (!eventMatch || !dataMatch) continue;

          const eventName = eventMatch[1].trim();
          const payload = JSON.parse(dataMatch[1]);

          if (eventName === "status") {
            setStatusLabel(payload.status);
          } else if (eventName === "token") {
            // Primeiro token esconde o status e o texto vai sendo anexado à última mensagem (do assistente).
            setStatusLabel("");
            setMessages((prev) => {
              const copy = [...prev];
              const last = copy[copy.length - 1];
              copy[copy.length - 1] = { ...last, content: last.content + payload.token };
              return copy;
            });
          } else if (eventName === "ui_actions") {
            // Anexa as ações à resposta atual para serem renderizadas abaixo dela.
            const actions: ChatUiAction[] = payload.actions;
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { ...copy[copy.length - 1], ui_actions: actions };
              return copy;
            });
            // O agente alterou o carrinho no backend: sincroniza o estado global (contador, drawer).
            if (actions.some((a) => a.type === "CART_UPDATED")) {
              refreshCart();
              showToast("Carrinho atualizado pela Lumen AI!", "success");
            }
          }
        }
      }
    } catch {
      showToast("Não foi possível obter resposta do agente.", "error");
    } finally {
      setIsStreaming(false);
      setStatusLabel("");
    }
  };

  /** Apaga o histórico no backend e reinicia a conversa localmente. */
  const handleResetChat = async () => {
    if (!sessionId) return;
    await api.clearChatHistory(sessionId);
    setMessages([
      { role: "assistant", content: "Conversa reiniciada! Como posso ajudar na sua compra hoje?" },
    ]);
    showToast("Histórico de conversa limpo.", "info");
  };

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end">
      {/* Painel do chat (visível apenas quando aberto) */}
      {isOpen && (
        <div className="mb-3 flex h-[540px] w-[360px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl border border-slate-200">
          {/* Cabeçalho: identidade do assistente + botão de reiniciar conversa */}
          <div className="flex items-center justify-between bg-[#0099D6] px-4 py-3 text-white">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-bold leading-tight">Lumen AI • Assistente Virtual</p>
                <p className="text-[11px] text-cyan-100">Responde em tempo real</p>
              </div>
            </div>
            <button
              onClick={handleResetChat}
              title="Reiniciar conversa"
              className="rounded-lg p-1.5 hover:bg-white/20 transition"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          </div>

          {/* Área de mensagens (rolável) */}
          <div className="flex-1 overflow-y-auto bg-slate-50 p-3.5 space-y-3 text-sm">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}>
                {/* Balão da mensagem; mostra "..." na resposta vazia enquanto o stream não envia tokens */}
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 leading-relaxed whitespace-pre-wrap shadow-sm ${
                    msg.role === "user"
                      ? "bg-[#0099D6] text-white rounded-br-sm"
                      : "bg-white text-slate-800 border border-slate-200 rounded-bl-sm"
                  }`}
                >
                  {msg.content || (isStreaming && idx === messages.length - 1 ? "..." : "")}
                </div>

                {/* Ações de UI geradas pelo agente para esta mensagem */}
                {msg.ui_actions?.map((action, aIdx) => (
                  <div key={aIdx} className="mt-2 w-[90%] space-y-1.5">
                    {/* SELECT_VARIANT: cada opção vira um botão que envia `opt.prompt` de volta ao agente */}
                    {action.type === "SELECT_VARIANT" && action.options && (
                      <div className="rounded-xl border border-cyan-200 bg-cyan-50/70 p-2.5 space-y-1.5">
                        <p className="text-[11px] font-bold text-[#0F2B5B]">
                          Escolha a variação ({action.product_sku}):
                        </p>
                        {action.options.map((opt) => (
                          <button
                            key={opt.variant_id}
                            disabled={isStreaming}
                            onClick={() => sendMessage(opt.prompt)}
                            className="flex w-full items-center justify-between rounded-lg bg-[#0099D6] px-3 py-2 text-left text-xs font-semibold text-white hover:bg-[#0082B8] transition"
                          >
                            <span>{opt.label}</span>
                            <span className="font-bold">{formatBRL(opt.price)}</span>
                          </button>
                        ))}
                      </div>
                    )}

                    {/* CART_UPDATED: resumo do carrinho + atalho para o checkout (padrão "/checkout") */}
                    {action.type === "CART_UPDATED" && (
                      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 space-y-2">
                        <div className="flex items-center justify-between text-xs font-bold text-emerald-900">
                          <span>Carrinho ({action.total_items} itens)</span>
                          <span>{formatBRL(action.subtotal || 0)}</span>
                        </div>
                        <Link
                          href={action.checkout_url || "/checkout"}
                          className="flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition"
                        >
                          <ShoppingBag className="h-3.5 w-3.5" />
                          Ir para o Checkout
                        </Link>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ))}

            {/* Indicador de progresso (exibido até chegar o primeiro token) */}
            {statusLabel && (
              <div className="flex items-center gap-2 text-xs text-slate-500 animate-pulse">
                <span className="h-2 w-2 rounded-full bg-[#0099D6]" />
                {statusLabel}
              </div>
            )}

            {/* Atalhos de perguntas: só aparecem enquanto há no máximo a mensagem de boas-vindas */}
            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {QUICK_PROMPTS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="rounded-full bg-[#0099D6] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#0082B8] transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Campo de entrada; desabilitado durante o streaming */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage(input);
            }}
            className="flex items-center gap-2 border-t border-slate-200 bg-white p-3"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Digite sua mensagem..."
              disabled={isStreaming}
              className="flex-1 rounded-full bg-slate-100 px-4 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-[#0099D6]"
            />
            <button
              type="submit"
              disabled={isStreaming || !input.trim()}
              aria-label="Enviar mensagem"
              className="flex h-9 w-9 items-center justify-center rounded-full bg-[#0099D6] text-white hover:bg-[#0082B8] disabled:opacity-40 transition"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      )}

      {/* Botão flutuante que abre/fecha o painel */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        aria-label={isOpen ? "Fechar assistente virtual" : "Abrir assistente virtual Lumen AI"}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[#0099D6] text-white shadow-2xl hover:scale-105 hover:bg-[#0082B8] transition"
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </div>
  );
}
