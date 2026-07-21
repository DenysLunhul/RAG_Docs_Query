import sentence_transformers
from fastapi import FastAPI
from fastembed import SparseTextEmbedding
from pydantic import BaseModel
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

qdrant = QdrantClient(host="qdrant", port=6333)

COLLECTION_NAME = "fiqa_local"
PREFETCH_LIMIT=50
RERANK_CANDIDATES = 30
app = FastAPI()


class RetrieveRequest(BaseModel):
    query: str
    top_k: int
    use_hybrid: bool = False
    use_reranker: bool = False


embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5", device="cuda")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

reranker = sentence_transformers.CrossEncoder("BAAI/bge-reranker-base", device="cuda")

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def get_embedding(text: str) -> list[float]:
    return embedding_model.encode(QUERY_PREFIX + text).tolist()

def get_sparse_vector(text: str) -> models.SparseVector:
    embedding = next(sparse_model.embed([text]))
    return models.SparseVector(indices=embedding.indices.tolist(), values=embedding.values.tolist())


@app.post("/retrieve")
def retrieve_docs(request: RetrieveRequest):
    candidate_limit = RERANK_CANDIDATES if request.use_reranker else request.top_k

    if request.use_hybrid:
        groups = qdrant.query_points_groups(
            collection_name=COLLECTION_NAME,
            prefetch=[
                models.Prefetch(query=get_embedding(request.query), using="dense", limit=PREFETCH_LIMIT),
                models.Prefetch(query=get_sparse_vector(request.query), using="sparse", limit=PREFETCH_LIMIT)
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            group_by="doc_id",
            limit=candidate_limit,
            group_size=1,
        ).groups
    else:
        groups = qdrant.query_points_groups(
            collection_name=COLLECTION_NAME,
            query=get_embedding(request.query),
            using="dense",
            group_by="doc_id",
            limit=candidate_limit,
            group_size=1,
        ).groups

    if request.use_reranker:
        pairs = [(request.query, g.hits[0].payload["text"]) for g in groups]
        scores = reranker.predict(pairs)
        ranked = sorted(zip(groups, scores), key=lambda x: x[1], reverse=True)[:request.top_k]
        return {
            "results": [{"id": g.id, "score": float(score)} for g, score in ranked]
        }

    return {
        "results": [{"id": g.id, "score": g.hits[0].score} for g in groups]
    }