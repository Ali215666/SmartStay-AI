"""REST and WebSocket endpoints for SmartStay AI."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from .dependencies import get_session_manager, get_websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    sessions = get_session_manager()
    session_id = sessions.ensure_session(request.session_id, request.user_id)
    response = await sessions.process_message(session_id, request.message)
    return ChatResponse(session_id=session_id, response=response)


@router.delete("/api/sessions/{session_id}")
async def reset_session(session_id: str) -> dict:
    return {"deleted": get_session_manager().delete_session(session_id)}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    connections = get_websocket_manager()
    sessions = get_session_manager()
    connection_id: Optional[str] = None
    await websocket.accept()

    try:
        while True:
            payload = await websocket.receive_json()
            message = str(payload.get("message", "")).strip()
            if not message or len(message) > 2_000:
                await websocket.send_json({"type": "error", "message": "Message must contain 1–2000 characters."})
                continue

            session_id = sessions.ensure_session(payload.get("session_id"), payload.get("user_id"))
            if connection_id != session_id:
                if connection_id:
                    await connections.disconnect(connection_id, close_socket=False)
                await connections.connect(session_id, websocket, accept=False)
                connection_id = session_id

            await websocket.send_json({"type": "start", "session_id": session_id})
            try:
                async for token in sessions.stream_message(session_id, message):
                    await websocket.send_json({"type": "token", "content": token})
                await websocket.send_json({"type": "done", "session_id": session_id})
            except RuntimeError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", connection_id)
    except Exception:
        logger.exception("Unexpected WebSocket failure")
        try:
            await websocket.send_json({"type": "error", "message": "Unexpected server error"})
        except Exception:
            pass
    finally:
        if connection_id:
            await connections.disconnect(connection_id, close_socket=False)

