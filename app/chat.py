import anthropic
from sqlalchemy.orm import Session

from .config import get_settings
from .models import Message


def get_conversation_history(db: Session, conversation_id: str, limit: int = 50) -> list[dict]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def chat(
    db: Session,
    message: str,
    conversation_id: str,
    system_prompt: str | None = None,
    max_tokens: int | None = None,
) -> tuple[str, int]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    history = get_conversation_history(db, conversation_id)
    history.append({"role": "user", "content": message})

    kwargs = {
        "model": settings.model,
        "max_tokens": max_tokens or settings.max_tokens,
        "messages": history,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    response = client.messages.create(**kwargs)
    reply = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens

    # Save both messages
    db.add(Message(conversation_id=conversation_id, role="user", content=message, token_count=0))
    db.add(Message(conversation_id=conversation_id, role="assistant", content=reply, token_count=tokens))
    db.commit()

    return reply, tokens


async def chat_stream(
    db: Session,
    message: str,
    conversation_id: str,
    system_prompt: str | None = None,
    max_tokens: int | None = None,
):
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    history = get_conversation_history(db, conversation_id)
    history.append({"role": "user", "content": message})

    kwargs = {
        "model": settings.model,
        "max_tokens": max_tokens or settings.max_tokens,
        "messages": history,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    full_reply = []
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            full_reply.append(text)
            yield text

    reply = "".join(full_reply)
    db.add(Message(conversation_id=conversation_id, role="user", content=message, token_count=0))
    db.add(Message(conversation_id=conversation_id, role="assistant", content=reply, token_count=0))
    db.commit()
