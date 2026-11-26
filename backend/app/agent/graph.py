from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import MessagesState, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.core.config import settings

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
    llm = ChatGoogleGenerativeAI(
        google_api_key=settings.gemini_api_key,
        model=settings.gemini_chat_model,
        temperature=0.2,
    ).bind_tools(tools)

    async def agent_node(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()
