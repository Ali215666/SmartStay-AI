"""Session lifecycle and conversation orchestration."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Optional


class SessionManager:
    def __init__(self, ollama_client, memory_manager, prompt_builder):
        self.ollama_client = ollama_client
        self.memory_manager = memory_manager
        self.prompt_builder = prompt_builder
        self.sessions: Dict[str, dict] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def create_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        session_id = session_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        self.sessions.setdefault(
            session_id,
            {"user_id": user_id, "created_at": now, "last_active": now},
        )
        self.memory_manager.create_session(session_id)
        self._locks.setdefault(session_id, asyncio.Lock())
        return session_id

    def ensure_session(self, session_id: Optional[str], user_id: Optional[str] = None) -> str:
        if session_id and session_id in self.sessions:
            return session_id
        return self.create_session(user_id=user_id, session_id=session_id)

    async def stream_message(self, session_id: str, user_message: str) -> AsyncGenerator[str, None]:
        if session_id not in self.sessions:
            raise ValueError("Unknown session")

        async with self._locks[session_id]:
            history = self.memory_manager.get_active_context(session_id)
            prompt = self.prompt_builder.build_prompt(history, user_message)
            chunks = []
            async for token in self.ollama_client.generate_stream(prompt):
                chunks.append(token)
                yield token

            response = "".join(chunks).strip()
            if response:
                self.memory_manager.add_message(session_id, "user", user_message)
                self.memory_manager.add_message(session_id, "assistant", response)
            self.sessions[session_id]["last_active"] = datetime.now(timezone.utc).isoformat()

    async def process_message(self, session_id: str, user_message: str) -> str:
        return "".join([token async for token in self.stream_message(session_id, user_message)])

    def delete_session(self, session_id: str) -> bool:
        existed = self.sessions.pop(session_id, None) is not None
        self._locks.pop(session_id, None)
        self.memory_manager.delete_session(session_id)
        return existed

