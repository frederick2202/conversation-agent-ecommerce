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
        await self.chat_repo.clear_session(session_id)

    async def stream_reply(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        history_rows = await self.chat_repo.get_history(session_id, limit=16)
        await self.chat_repo.add_message(
            ChatMessage(session_id=session_id, role="user", content=user_message)
        )

        if not settings.openai_api_key or settings.openai_api_key.startswith("sk-proj-substitua"):
            fallback_msg = (
                "Configure a variável `OPENAI_API_KEY` no arquivo `backend/.env` e reinicie o container "
                "para ativar o agente LangGraph completo."
            )
            yield f"event: token\ndata: {json.dumps({'token': fallback_msg}, ensure_ascii=False)}\n\n"
            await self.chat_repo.add_message(
                ChatMessage(session_id=session_id, role="assistant", content=fallback_msg)
            )
            yield "event: done\ndata: {}\n\n"
            return

        lc_messages = [
            HumanMessage(content=r.content) if r.role == "user" else AIMessage(content=r.content)
            for r in history_rows
        ]
        lc_messages.append(HumanMessage(content=user_message))

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
        async for event in graph.astream_events({"messages": lc_messages}, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    token = str(chunk.content)
                    full_response += token
                    yield f"event: token\ndata: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
            elif kind == "on_tool_start":
                tool_name = event.get("name", "ferramenta")
                yield f"event: status\ndata: {json.dumps({'status': f'Consultando {tool_name}...'}, ensure_ascii=False)}\n\n"

        if ui_actions:
            yield f"event: ui_actions\ndata: {json.dumps({'actions': ui_actions}, ensure_ascii=False)}\n\n"

        await self.chat_repo.add_message(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_response,
                ui_actions=ui_actions or None,
            )
        )
        yield "event: done\ndata: {}\n\n"
