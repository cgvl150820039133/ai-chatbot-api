from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid

from .config import get_settings

engine = create_engine(get_settings().database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    token_count = Column(Integer, default=0)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
