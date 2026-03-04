"""Application service construction."""

from functools import lru_cache

from conversation.memory_manager import MemoryManager
from conversation.prompt_builder import PromptBuilder
from conversation.session_manager import SessionManager
from llm.ollama_client import OllamaClient

from .websocket_manager import WebSocketManager


@lru_cache
def get_websocket_manager() -> WebSocketManager:
    return WebSocketManager()


@lru_cache
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


@lru_cache
def get_memory_manager() -> MemoryManager:
    return MemoryManager(max_messages=12)


@lru_cache
def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


@lru_cache
def get_session_manager() -> SessionManager:
    return SessionManager(get_ollama_client(), get_memory_manager(), get_prompt_builder())

