import json
import uuid
from itertools import islice
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding
from langchain_text_splitters import RecursiveCharacterTextSplitter

COLLECTION_NAME = "fiqa_local"
CORPUS_PATH = "datasets/fiqa/corpus.jsonl"
BATCH_SIZE = 512
CHUNK_SIZE = 256
CHUNK_OVERLAP = 50


model = SentenceTransformer("BAAI/bge-base-en-v1.5", device="cuda")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

VECTOR_SIZE = model.encode("test").shape[0]

splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    model.tokenizer, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

def chunked(iterable, size):
    it = iter(iterable)
    while True:
        chunk = list(islice(it, size))
        if not chunk:
            return
        yield chunk


if __name__ == "__main__":
    qdrant = QdrantClient(host="localhost", port=6333)

    if qdrant.collection_exists(COLLECTION_NAME):
        qdrant.delete_collection(COLLECTION_NAME)

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"dense": models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    qdrant.create_payload_index(collection_name=COLLECTION_NAME, field_name="doc_id", field_schema="keyword")



    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        docs = (json.loads(line) for line in f)

        for batch in tqdm(chunked(docs, BATCH_SIZE)):

            records = []

            for doc in batch:
                title = doc.get("title", "")
                doc_id = doc["_id"]

                for chunk_index, chunk_text in enumerate(splitter.split_text(doc["text"])):
                    text_to_embed = f"{title} {chunk_text}".strip() if title else chunk_text
                    if not text_to_embed:
                        continue
                    records.append({
                        "doc_id": doc_id,
                        "chunk_index": chunk_index,
                        "title": title,
                        "text": chunk_text,
                        "text_to_embed": text_to_embed,
                    })

            if not records:
                continue

            texts = [r["text_to_embed"] for r in records]
            dense_vectors = model.encode(texts, batch_size=BATCH_SIZE, device="cuda").tolist()
            sparse_vectors = list(sparse_model.embed(texts))

            points = [
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        "dense": dense_vector,
                        "sparse": models.SparseVector(
                            indices=sparse_vector.indices.tolist(),
                            values=sparse_vector.values.tolist(),
                        )
                    },
                    payload={
                        "doc_id": r["doc_id"],
                        "chunk_index": r["chunk_index"],
                        "title": r["title"],
                        "text": r["text"],
                    },
                )
                for r, dense_vector, sparse_vector in zip(records, dense_vectors, sparse_vectors)
            ]

            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)