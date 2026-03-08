from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import uuid

from .config import get_settings
from .models import get_db, Message
from .schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from .auth import verify_api_key
from .chat import chat, chat_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="AI Chatbot API",
    description="Production-ready conversational AI API powered by Claude",
    version="1.0.0",
    lifespan=lifespan,
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "model": get_settings().model}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    reply, tokens = chat(
        db=db,
        message=request.message,
        conversation_id=conversation_id,
        system_prompt=request.system_prompt,
        max_tokens=request.max_tokens,
    )
    return ChatResponse(
        reply=reply,
        conversation_id=conversation_id,
        tokens_used=tokens,
        model=get_settings().model,
    )


@app.post("/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    conversation_id = request.conversation_id or str(uuid.uuid4())

    async def event_generator():
        async for chunk in chat_stream(
            db=db,
            message=request.message,
            conversation_id=conversation_id,
            system_prompt=request.system_prompt,
            max_tokens=request.max_tokens,
        ):
            yield {"data": chunk}

    return EventSourceResponse(event_generator())


@app.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationOut(
        conversation_id=conversation_id,
        messages=[MessageOut(role=m.role, content=m.content, created_at=m.created_at) for m in messages],
        message_count=len(messages),
    )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    deleted = db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": deleted, "conversation_id": conversation_id}
