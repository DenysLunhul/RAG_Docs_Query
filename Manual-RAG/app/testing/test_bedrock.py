from app.models.database import SessionLocal
from app.models.chunks import DocumentChunk
from app.services.embeddings import get_embedding
from app.services.rag import retrieve_chunks, generate_answer

db = SessionLocal()

print("Generating embedding...")
embedding = get_embedding("The CAP theorem states that a distributed system cannot simultaneously guarantee consistency, availability and partition tolerance.")

print("Storing chunk...")
chunk = DocumentChunk(
    filename="test.pdf",
    chunk_text="The CAP theorem states that a distributed system cannot simultaneously guarantee consistency, availability and partition tolerance.",
    embedding=embedding
)
db.add(chunk)
db.commit()
print("Chunk stored.")

print("Querying...")
question = "what is CAP theorem?"
chunks = retrieve_chunks(question, db)
print(f"Found {len(chunks)} chunks")

print("Generating answer...")
answer = generate_answer(question, chunks)
print(answer)

db.close()