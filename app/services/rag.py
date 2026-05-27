from sqlalchemy.orm import Session
from app.services.embeddings import get_embedding
from app.models.chunks import DocumentChunk
from app.config import settings
import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def retrieve_chunks(question: str, db: Session) -> list:
    question_vector = get_embedding(question)
    chunks = db.query(DocumentChunk).order_by(
        DocumentChunk.embedding.cosine_distance(question_vector)
    ).limit(5).all()
    return chunks


def generate_answer(question: str, chunks: list) -> str:
    context = ""
    for chunk in chunks:
        context += f"{chunk.chunk_text} (source: {chunk.filename})\n\n"

    response = bedrock.converse(
        modelId=settings.bedrock_model_id,
        system=[{"text": "You are a helpful assistant. Answer using only provided context. Always cite sources."}],
        messages=[
            {"role": "user", "content": [{"text": f"Context:\n{context}\n\nQuestion: {question}"}]}
        ],
        inferenceConfig={"maxTokens": 1000}
    )

    answer = response['output']['message']['content'][0]['text']
    return answer