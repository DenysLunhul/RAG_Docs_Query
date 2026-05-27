from app.models.database import Base, engine
from sqlalchemy import text
from app.models.chunks import DocumentChunk


with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()

Base.metadata.create_all(engine)