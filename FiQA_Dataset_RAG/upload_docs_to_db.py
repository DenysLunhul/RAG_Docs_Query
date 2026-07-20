import json
from itertools import islice
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "fiqa_local"
CORPUS_PATH = "datasets/fiqa/corpus.jsonl"
VECTOR_SIZE = 384
BATCH_SIZE = 512

model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cuda")


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
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        docs = (json.loads(line) for line in f)

        for batch in tqdm(chunked(docs, BATCH_SIZE)):
            texts = []
            valid_docs = []
            for doc in batch:
                title = doc.get("title", "")
                text = doc["text"]
                text_to_embed = f"{title} {text}".strip() if title else text
                if not text_to_embed:
                    continue
                texts.append(text_to_embed)
                valid_docs.append(doc)

            if not texts:
                continue

            vectors = model.encode(texts, batch_size=BATCH_SIZE, device="cuda").tolist()

            points = [
                PointStruct(
                    id=int(doc["_id"]),
                    vector=vector,
                    payload={"doc_id": doc["_id"], "title": doc.get("title", ""), "text": doc["text"]},
                )
                for doc, vector in zip(valid_docs, vectors)
            ]

            qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
