from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

qdrant = QdrantClient(host="qdrant", port=6333)

COLLECTION_NAME = "fiqa_local"

app = FastAPI()


class RetrieveRequest(BaseModel):
    query: str
    top_k: int


model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def get_embedding(text: str) -> list[float]:
    return model.encode(QUERY_PREFIX + text).tolist()


@app.post("/retrieve")
def retrieve_docs(request: RetrieveRequest):
    vector = get_embedding(request.query)

    hits = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=request.top_k,
    ).points

    return {
        "results": [
            {"id": hit.payload["doc_id"], "score": hit.score}
            for hit in hits
        ]
    }