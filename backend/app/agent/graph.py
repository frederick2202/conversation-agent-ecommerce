"""
Definição do agente conversacional "Lumen AI" com LangGraph + Google Gemini.

O grafo implementa o padrão ReAct (raciocinar -> agir com ferramentas -> observar):

    START -> agent --(LLM pediu ferramenta?)--> tools -> agent -> ... -> fim
                   \\--(resposta final, sem tool call)--> END

- Nó "agent": chama o Gemini com o prompt de sistema + histórico de mensagens.
- Nó "tools": executa as ferramentas solicitadas (definidas em `app/agent/tools.py`)
  e devolve o resultado ao LLM, que decide o próximo passo.
"""

from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings

# Instruções fixas de comportamento do agente. Os nomes entre crases devem
# corresponder exatamente aos nomes das funções-ferramenta em `tools.py`.
SYSTEM_PROMPT = """
Você é a Lumen AI, assistente virtual oficial do e-commerce de eletrônicos Lumen.
Regras estritas:
1. Nunca invente preços, especificações, SKUs ou disponibilidade. Sempre consulte as ferramentas em tempo real.
2. Quando o cliente perguntar sobre um produto (nome ou SKU), use `buscar_produto`. Se não existir, use `sugerir_similares` e apresente sugestões de forma amigável.
3. Antes de adicionar um item ao carrinho, garanta que as variações obrigatórias (cor, voltagem, armazenamento, switch) foram escolhidas. Se faltar variação, peça para o cliente escolher uma das opções exibidas nos botões abaixo.
4. Após adicionar ao carrinho, confirme claramente os itens, quantidades e subtotal atualizado, informando que o botão de Checkout está pronto abaixo.
5. Para dúvidas de troca, devolução, frete, pagamento ou garantia, use `consultar_faq`.
6. Responda em português do Brasil de forma concisa, cordial e objetiva (baixa carga cognitiva).
"""


def build_lumen_graph(tools: list):
    """Monta e compila o grafo do agente com as ferramentas informadas.

    O grafo é recriado a cada mensagem (veja `ChatService.stream_reply`) porque as
    ferramentas são closures vinculadas à sessão/carrinho do cliente atual.
    """
    llm = ChatGoogleGenerativeAI(
        google_api_key=settings.gemini_api_key,
        model=settings.gemini_chat_model,
        temperature=0.2,  # Baixa criatividade: respostas mais previsíveis e fiéis aos dados.
    ).bind_tools(tools)  # Informa ao LLM quais ferramentas ele pode chamar (e seus parâmetros).

    async def agent_node(state: MessagesState):
        # O prompt de sistema é injetado a cada chamada e não fica salvo no estado.
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = await llm.ainvoke(messages)
        # MessagesState acumula mensagens: o retorno é anexado ao histórico do grafo.
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    # `tools_condition` direciona para "tools" se a resposta do LLM contém tool calls; senão encerra (END).
    builder.add_conditional_edges("agent", tools_condition)
    # Após executar ferramentas, volta ao agente para ele interpretar os resultados.
    builder.add_edge("tools", "agent")
    return builder.compile()
