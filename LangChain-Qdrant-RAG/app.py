import os
import uuid
from itertools import islice

import sentence_transformers
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

COLLECTION_NAME = "user_docs"
BATCH_SIZE = 512
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50
PREFETCH_LIMIT=50
RERANK_CANDIDATES = 30
TOP_K = 5
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("qdrant_PORT", 6333))
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
dense_model = SentenceTransformer("BAAI/bge-base-en-v1.5", device="cuda")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
reranker = sentence_transformers.CrossEncoder("BAAI/bge-reranker-base", device="cuda")

VECTOR_SIZE = dense_model.get_embedding_dimension()

splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    dense_model.tokenizer, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)


def chunked(iterable, size):
    it = iter(iterable)
    while True:
        batch = list(islice(it, size))
        if not batch:
            return
        yield batch


def ensure_collection():
    if not qdrant.collection_exists(COLLECTION_NAME):
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config={"dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)},
            sparse_vectors_config={"sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        qdrant.create_payload_index(collection_name=COLLECTION_NAME, field_name="doc_id", field_schema="keyword")


from agent import ask
@app.post("/chat")
async def chat(question: str, use_hybrid: bool = False, use_reranker: bool = False):
    return {"answer": ask(question, use_hybrid, use_reranker)}


@app.post("/documents/upload")
async def upload_document(file: UploadFile):
    ensure_collection()

    file_bytes = await file.read()
    doc_id = file.filename
    file_path = os.path.join(UPLOAD_DIR, doc_id)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    pages = PyPDFLoader(file_path).load()

    records = []
    for page in pages:
        for chunk_index, chunk_text in enumerate(splitter.split_text(page.page_content)):
            if not chunk_text.strip():
                continue
            records.append({
                "doc_id": doc_id,
                "page": page.metadata.get("page", 0),
                "chunk_index": chunk_index,
                "text": chunk_text,
            })

    if not records:
        return {"message": "no extractable text", "doc_id": doc_id, "chunks": 0}

    total = 0
    for batch in chunked(records, BATCH_SIZE):
        texts = [r["text"] for r in batch]
        dense_vectors = dense_model.encode(texts, batch_size=BATCH_SIZE).tolist()
        sparse_vectors = list(sparse_model.embed(texts))

        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector={
                    "dense": dense_vector,
                    "sparse": models.SparseVector(
                        indices=sparse_vector.indices.tolist(),
                        values=sparse_vector.values.tolist(),
                    ),
                },
                payload=record,
            )
            for record, dense_vector, sparse_vector in zip(batch, dense_vectors, sparse_vectors)
        ]
        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        total += len(points)

    return {"message": "uploaded", "doc_id": doc_id, "chunks": total}


@app.get("/documents")
async def list_documents():
    return {"documents": os.listdir(UPLOAD_DIR)}


@app.get("/documents/{doc_id}/read")
async def read_document(doc_id: str):
    file_path = os.path.join(UPLOAD_DIR, doc_id)
    return FileResponse(file_path, media_type="application/pdf", filename=doc_id)


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    qdrant.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.Filter(
            must=[models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
        ),
    )

    file_path = os.path.join(UPLOAD_DIR, doc_id)
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": "deleted", "doc_id": doc_id}