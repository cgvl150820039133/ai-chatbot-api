from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: str | None = None
    system_prompt: str | None = None
    max_tokens: int | None = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    tokens_used: int
    model: str


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class ConversationOut(BaseModel):
    conversation_id: str
    messages: list[MessageOut]
    message_count: int
