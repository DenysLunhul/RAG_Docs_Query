import datetime
from app.models.database import Base
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    chunk_text = Column(String)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.datetime.utcnow())