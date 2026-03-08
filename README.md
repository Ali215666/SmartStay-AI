# SmartStay AI

SmartStay AI is a fully local, CPU-friendly conversational assistant for hotel front-desk inquiries. It combines a quantized Qwen model through Ollama, bounded conversational memory, prompt-based hotel policies, a streaming FastAPI API, and a React chat interface.

> Assignment 1 constraint: this version intentionally contains no tools, agents, plugins, external inference APIs, or retrieval-augmented generation (RAG).

## Architecture

```text
React Web UI
     │ JSON over WebSocket
     ▼
FastAPI API ──► WebSocket connection registry
     │
     ▼
Conversation Manager
  ├── session lifecycle
  ├── bounded message history
  ├── per-session turn lock
  └── structured prompt builder
     │ streaming HTTP
     ▼
Local Ollama ──► quantized Qwen 2.5 3B
```

Different sessions can generate concurrently. A lock on each session prevents two overlapping turns from corrupting that conversation's ordering. The backend keeps no database state; restarting it clears active conversations.

## Business case

The assistant answers hotel questions and guides a guest through a reservation request. It remembers details supplied in earlier turns, stays within the hotel domain, and does not pretend to complete actions in another system. See [the use-case and dialogue design](docs/use-case.md).

## Model selection

The default model is Qwen 2.5 3B Instruct in Q4_K_M quantization. It offers a practical balance of instruction following, memory use, and CPU latency on a laptop. The included `Modelfile` uses a 2,048-token context and caps output at 160 tokens to keep response time predictable.

Create the local model after installing Ollama:

```bash
ollama create smartstay-qwen -f Modelfile
```

You may override it with `OLLAMA_MODEL` and `OLLAMA_BASE_URL`.

## Run locally

### Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

API documentation is available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

### Docker

Ollama runs on the host so it can use the laptop CPU directly. Start it first, create the model, then run:

```bash
docker compose -f backend/docker-compose.yml up --build
```

## API

`POST /api/chat` accepts:

```json
{
  "session_id": "optional-client-session-id",
  "message": "What time is check-in?"
}
```

`WS /ws/chat` accepts the same JSON. It emits `start`, multiple `token` events, and a final `done` event. Errors use `{ "type": "error", "message": "..." }`.

The Postman collection is in `backend/Hotel_AI_Backend.postman_collection.json`.

## Evaluation

Run deterministic orchestration tests without loading the LLM:

```bash
python -m unittest tests.test_assignment_one
```

For inference benchmarks, start Ollama and measure at least 20 prompts after one warm-up request. Record median and p95 time-to-first-token, total latency, generated tokens per second, peak RAM, prompt length, and concurrent-user count on the test laptop. Hardware-dependent measurements are intentionally not fabricated in this repository.

Suggested acceptance targets for a 3B Q4 model on a modern laptop CPU:

| Metric | Target |
|---|---:|
| Warm time to first token | under 3 s |
| Median response latency | under 12 s |
| Concurrent active sessions | 5 |
| API error rate in stress run | under 1% |

## Failure handling

- Invalid or oversized messages receive a structured error.
- An unavailable Ollama server produces a clear connection error.
- Each WebSocket is removed from the registry on disconnect.
- Conversation history is bounded to protect the context window and memory footprint.
- The UI reconnects with limited exponential backoff.

## Known limitations

- Conversation state is in memory and is lost on restart.
- The model cannot verify live availability or complete a reservation.
- CPU inference speed depends heavily on hardware and quantization.
- Prompt-only domain enforcement reduces but cannot eliminate hallucinations.
- A single backend process is assumed; horizontal scaling needs shared session storage or sticky sessions.
