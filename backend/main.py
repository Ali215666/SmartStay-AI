"""FastAPI entry point for SmartStay AI."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .app.dependencies import get_ollama_client
from .app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="SmartStay AI",
        description="Local hotel front-desk conversational API",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/")
    async def root() -> dict:
        return {"service": "SmartStay AI", "status": "online"}

    @app.get("/health")
    async def health() -> dict:
        return {"status": "healthy", "inference": "local-ollama"}

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await get_ollama_client().close()

    return app


app = create_app()

