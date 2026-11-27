"""
Orquestra a conversa com o agente de IA e transmite a resposta via Server-Sent Events (SSE).

Formato do stream produzido por `stream_reply` (consumido pelo widget de chat do frontend):
    event: token       data: {"token": "<pedaço de texto>"}    -> repetido várias vezes (efeito "digitando")
    event: ui_actions  data: {"actions": [...]}                -> opcional, enviado uma vez ao final
    event: done        data: {}                                -> fim da resposta
"""

from collections.abc import AsyncGenerator
import json
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.graph import build_lumen_graph
from app.agent.tools import build_agent_tools
from app.core.config import settings
from app.models.entities import ChatMessage
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatHistoryItem
from app.services.cart_service import CartService
from app.services.faq_service import FaqService
from app.services.product_service import ProductService


class ChatService:
    def __init__(
        self,
        chat_repo: ChatRepository,
        product_service: ProductService,
        cart_service: CartService,
        faq_service: FaqService,
    ):
        self.chat_repo = chat_repo
        self.product_service = product_service
        self.cart_service = cart_service
        self.faq_service = faq_service

    async def get_history(self, session_id: str) -> list[ChatHistoryItem]:
        """Retorna o histórico salvo da sessão (usado pelo frontend ao reabrir o chat)."""
        rows = await self.chat_repo.get_history(session_id)
        return [
            ChatHistoryItem(
                role=r.role,
                content=r.content,
                ui_actions=r.ui_actions,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def clear_session(self, session_id: str) -> None:
        """Apaga todo o histórico de mensagens da sessão (o carrinho não é afetado)."""
        await self.chat_repo.clear_session(session_id)

    async def stream_reply(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        """Processa a mensagem do usuário e gera a resposta do agente em formato SSE.

        Passos:
        1. Carrega o histórico recente (contexto) e salva a mensagem do usuário.
        2. Se não houver chave do Gemini configurada, responde com uma mensagem de orientação.
        3. Monta as ferramentas + grafo LangGraph e executa, repassando os tokens do LLM conforme chegam.
        4. Ao final, envia as ações de UI coletadas pelas ferramentas e salva a resposta completa.
        """
        # Histórico é lido ANTES de salvar a nova mensagem, para não duplicá-la no contexto.
        # Atenção: o repositório ordena do mais antigo para o mais novo, então `limit=16`
        # retorna as 16 PRIMEIRAS mensagens da sessão.
        history_rows = await self.chat_repo.get_history(session_id, limit=16)
        await self.chat_repo.add_message(
            ChatMessage(session_id=session_id, role="user", content=user_message)
        )

        # Valores começando com "cole-sua-chave" são tratados como placeholder (chave não configurada).
        if not settings.gemini_api_key or settings.gemini_api_key.startswith("cole-sua-chave"):
            fallback_msg = (
                "Configure a variável `GEMINI_API_KEY` no arquivo `backend/.env` e reinicie o container "
                "para ativar o agente LangGraph com Gemini."
            )
            yield f"event: token\ndata: {json.dumps({'token': fallback_msg}, ensure_ascii=False)}\n\n"
            await self.chat_repo.add_message(
                ChatMessage(session_id=session_id, role="assistant", content=fallback_msg)
            )
            yield "event: done\ndata: {}\n\n"
            return

        # Converte o histórico do banco para o formato de mensagens do LangChain.
        lc_messages = [
            HumanMessage(content=r.content) if r.role == "user" else AIMessage(content=r.content)
            for r in history_rows
        ]
        lc_messages.append(HumanMessage(content=user_message))

        # Lista preenchida pelas ferramentas durante a execução do grafo (ver app/agent/tools.py).
        ui_actions: list[dict] = []
        tools = build_agent_tools(
            session_id=session_id,
            product_service=self.product_service,
            cart_service=self.cart_service,
            faq_service=self.faq_service,
            collected_ui_actions=ui_actions,
        )
        graph = build_lumen_graph(tools)

        full_response = ""
        # `astream_events` emite eventos internos do grafo; aqui só interessam os pedaços (chunks)
        # de texto gerados pelo LLM ("on_chat_model_stream").
        async for event in graph.astream_events({"messages": lc_messages}, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                # O Gemini pode devolver o conteúdo como string ou como lista de partes
                # (ex.: [{"type": "text", "text": "..."}]); normalizamos para texto puro.
                if isinstance(content, list):
                    token = "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    )
                else:
                    token = str(content) if content else ""

                if token:
                    full_response += token
                    yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

        if ui_actions:
            yield f"event: ui_actions\ndata: {json.dumps({'actions': ui_actions}, ensure_ascii=False)}\n\n"

        # Persiste a resposta completa (e as ações de UI) para reconstruir o histórico depois.
        await self.chat_repo.add_message(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_response,
                ui_actions=ui_actions or None,
            )
        )
        yield "event: done\ndata: {}\n\n"
