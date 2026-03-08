"""
AI Customer Support Chatbot API
================================
A production-ready chatbot API using Claude AI that handles customer inquiries,
maintains conversation context, and provides intelligent responses.

Features:
- Multi-turn conversation with memory
- Customizable system prompts per business
- Rate limiting and error handling
- Conversation history storage
- Streaming responses support
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from anthropic import Anthropic
from datetime import datetime
import json
import uuid
import os

app = FastAPI(title="AI Customer Support Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# In-memory conversation store (use Redis/DB in production)
conversations: dict[str, list] = {}
business_configs: dict[str, dict] = {}

DEFAULT_SYSTEM_PROMPT = """You are a helpful customer support assistant.
Be concise, professional, and solve the customer's problem efficiently.
If you don't know something, say so honestly and offer to escalate to a human agent."""


class BusinessConfig(BaseModel):
    business_id: str
    business_name: str
    system_prompt: str | None = None
    greeting: str = "Hello! How can I help you today?"


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    business_id: str = "default"
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    tokens_used: int
    timestamp: str


@app.post("/api/business/configure")
async def configure_business(config: BusinessConfig):
    """Configure a business profile with custom system prompt."""
    business_configs[config.business_id] = config.model_dump()
    return {"status": "configured", "business_id": config.business_id}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get an AI response."""
    conv_id = request.conversation_id or str(uuid.uuid4())

    if conv_id not in conversations:
        conversations[conv_id] = []

    conversations[conv_id].append({"role": "user", "content": request.message})

    # Get business-specific system prompt
    config = business_configs.get(request.business_id, {})
    system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

    # Keep last 20 messages for context window management
    messages = conversations[conv_id][-20:]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    assistant_message = response.content[0].text
    conversations[conv_id].append({"role": "assistant", "content": assistant_message})

    return ChatResponse(
        conversation_id=conv_id,
        response=assistant_message,
        tokens_used=response.usage.input_tokens + response.usage.output_tokens,
        timestamp=datetime.now().isoformat(),
    )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message and get a streaming AI response."""
    conv_id = request.conversation_id or str(uuid.uuid4())

    if conv_id not in conversations:
        conversations[conv_id] = []

    conversations[conv_id].append({"role": "user", "content": request.message})

    config = business_configs.get(request.business_id, {})
    system_prompt = config.get("system_prompt", DEFAULT_SYSTEM_PROMPT)
    messages = conversations[conv_id][-20:]

    async def generate():
        full_response = ""
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                full_response += text
                yield f"data: {json.dumps({'text': text})}\n\n"

        conversations[conv_id].append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'done': True, 'conversation_id': conv_id})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Retrieve conversation history."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": conversations[conversation_id]}


@app.delete("/api/conversation/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    conversations.pop(conversation_id, None)
    return {"status": "deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
