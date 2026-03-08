# AI Chatbot API

A production-ready conversational AI API built with FastAPI and Claude. Supports multi-turn conversations, streaming responses, and conversation history management.

## Features

- **Multi-turn Conversations** — Maintains context across messages with session management
- **Streaming Responses** — Real-time token streaming via Server-Sent Events (SSE)
- **Conversation History** — SQLite-backed persistent chat history
- **Rate Limiting** — Configurable per-user rate limits
- **API Key Authentication** — Secure endpoint access
- **Docker Ready** — Containerized deployment with docker-compose

## Tech Stack

- Python 3.11+ / FastAPI
- Anthropic Claude API (claude-sonnet-4-20250514)
- SQLite + SQLAlchemy
- Server-Sent Events (SSE)
- Pydantic for validation

## Quick Start

```bash
git clone https://github.com/cgvl1508/ai-chatbot-api.git
cd ai-chatbot-api
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn app.main:app --reload
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send a message, get AI response |
| POST | `/chat/stream` | Stream AI response via SSE |
| GET | `/conversations/{id}` | Get conversation history |
| DELETE | `/conversations/{id}` | Delete a conversation |
| GET | `/health` | Health check |

## Example

```python
import httpx

response = httpx.post("http://localhost:8000/chat", json={
    "message": "Explain quantum computing in simple terms",
    "conversation_id": "user-123"
}, headers={"X-API-Key": "your-key"})

print(response.json()["reply"])
```

## Architecture

```
app/
├── main.py          # FastAPI app + routes
├── chat.py          # Chat logic + Claude integration
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic schemas
├── auth.py          # API key middleware
├── rate_limit.py    # Rate limiting
└── config.py        # Settings
```

## License

MIT
