# SmartStay AI

SmartStay AI is a fully local, CPU-oriented hotel front-desk assistant with real-time text and voice conversations. It combines a quantized Qwen model through Ollama, bounded conversational memory, Moonshine speech recognition, Piper speech synthesis, FastAPI WebSockets, and a React interface.


## Architecture

```text
Text:  React UI <-> /ws/chat  <-> Conversation Manager <-> Local Ollama/Qwen

Voice: Microphone -> /ws/voice -> ffmpeg -> Moonshine ASR
                                      |
                                      v
                              Conversation Manager
                                      |
                                      v
                              Local Ollama/Qwen
                                      |
                                      v
 Browser playback <- ordered WAV <- Piper TTS <- phrase buffer
```

Text and voice use the same client-generated session ID, so a guest can switch modalities without losing context. Different users run concurrently, while a per-session lock protects turn order. ASR, TTS, and the complete voice pipeline each admit up to four active users.

See [Assignment 1's business case](docs/use-case.md) and the detailed [Assignment 2 voice design](docs/assignment-two.md).

## Local models

- **Conversation:** Qwen 2.5 3B Instruct, Q4_K_M, served by Ollama.
- **ASR:** Moonshine English, loaded locally by `moonshine-voice`.
- **TTS:** Piper with a local `.onnx` voice and matching `.onnx.json` configuration.

The included `Modelfile` uses a 2,048-token context and caps output at 160 tokens for predictable CPU use.

```bash
ollama create smartstay-qwen -f Modelfile
```

Download a Piper voice into `models/`. The default Docker configuration expects:

```text
models/en_US-lessac-medium.onnx
models/en_US-lessac-medium.onnx.json
```

Model binaries are intentionally excluded from Git.

## Run locally

Prerequisites: Python 3.11, Node.js 18+, Ollama, and ffmpeg available on `PATH`.

### Backend

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt

# Windows PowerShell
$env:PIPER_MODEL_PATH="models/en_US-lessac-medium.onnx"
$env:PIPER_CONFIG_PATH="models/en_US-lessac-medium.onnx.json"

uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Check `http://localhost:8000/health/voice`. Its `ready` field becomes `true` when ffmpeg, Moonshine, Piper, and the Piper model are available.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`, allow microphone access, press the round microphone button, speak, then press stop. The recognized transcript appears in the shared conversation while the answer streams as text and audio.

### Docker

Keep Ollama running on the host and place the Piper files in `models/`, then run:

```bash
docker compose -f backend/docker-compose.yml up --build
```

## APIs

- `POST /api/chat` — non-streaming text request.
- `WS /ws/chat` — streaming text conversation.
- `WS /ws/voice` — binary recording upload with transcript, text-token, and WAV events.
- `DELETE /api/sessions/{session_id}` — clears volatile session state.
- `GET /health/voice` — checks local voice prerequisites.

The voice recording limit is 8 MB and 30 seconds. Its full event schema is documented in [docs/assignment-two.md](docs/assignment-two.md). A Postman collection is included at `backend/Hotel_AI_Backend.postman_collection.json`.

## Tests and evaluation

Deterministic tests do not load the speech or language models:

```bash
python -m unittest tests.test_assignment_one tests.test_assignment_two
npm run build --prefix frontend
```

Measure the actual voice pipeline against a running server:

```bash
python benchmarks/voice_latency.py sample.webm --runs 5
```

The benchmark reports transcript latency, time to first token, time to first audio, and total turn latency. The `<1 s` goal must be evaluated on the submission laptop after model warm-up; the repository does not fabricate hardware-dependent results.

## Failure handling

- CPU-heavy speech operations run outside the async event loop.
- Recordings, message lengths, conversion duration, and concurrency are bounded.
- Missing ffmpeg, speech packages, or Piper model files produce explicit errors.
- A TTS failure preserves the streamed transcript and text response.
- Browser audio phrases are queued and played in sequence.
- WebSockets are cleaned up on disconnect.

## Known limitations

- Conversation state is in memory and is lost on restart.
- Speech recognition currently uses the English Moonshine model.
- The browser uploads a complete utterance when recording stops; it does not perform partial-word ASR.
- Cold model loading can exceed the sub-second latency target.
- CPU performance varies substantially by hardware and concurrent load.
- The assistant cannot verify availability or complete a real reservation.
