# FiQA Dataset RAG

A retrieval pipeline benchmarked against **FiQA-2018** (BEIR), a financial-domain Q&A dataset (~57.6k forum-style answer passages, 648 test queries) — used to measure and compare different retrieval strategies rather than to serve a product.

---

## Pipeline

```
Corpus (corpus.jsonl)
  → token-based chunking with overlap (LangChain RecursiveCharacterTextSplitter,
    sized against the embedding model's own tokenizer — chunk_size=256, overlap=50 tokens)
  → dense embeddings (BAAI/bge-base-en-v1.5) + sparse BM25 embeddings (fastembed, Qdrant/bm25)
  → Qdrant collection (named dense + sparse vectors, payload-indexed by doc_id)

Query → /retrieve (FastAPI)
  → dense search, optionally fused with BM25 (Qdrant hybrid query: prefetch + Reciprocal Rank Fusion)
  → grouped by doc_id (best chunk per document) to deduplicate chunks of the same source doc
  → optionally reranked with a cross-encoder (BAAI/bge-reranker-base)
  → top-k document ids returned
```

Hybrid search and reranking are both implemented and can be toggled per-request (`use_hybrid`, `use_reranker` on `POST /retrieve`), with no rebuild required — they default to off.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Vector DB | Qdrant (dense + sparse named vectors, hybrid RRF fusion, grouped search) |
| Dense embeddings | `BAAI/bge-base-en-v1.5` (`sentence-transformers`) |
| Sparse embeddings | BM25 via `fastembed` (`Qdrant/bm25`), IDF applied server-side by Qdrant |
| Chunking | `langchain-text-splitters` (`RecursiveCharacterTextSplitter`, token-aware) |
| Reranking | `BAAI/bge-reranker-base` cross-encoder (`sentence-transformers`) |
| Compute | CUDA-enabled PyTorch (GPU inference), Docker Compose with GPU passthrough |

---

## API

| Method | Endpoint | Body |
|---|---|---|
| `POST` | `/retrieve` | `{"query": "...", "top_k": 10, "use_hybrid": false, "use_reranker": false}` |

`use_hybrid` and `use_reranker` default to `false` (dense-only) — the empirically best-performing configuration on this dataset (see below).

---

## Evaluation

`evaluate.py` runs all 648 test queries through `/retrieve` and reports Recall@5 / Recall@10 against the official BEIR qrels (`test_client.py` drives the requests and writes `results.csv`).

### Findings

Measured on the full 648-query test set, dense-only retrieval outperformed every combination that added BM25 and/or reranking:

| Configuration | Recall@5 | Recall@10 |
|---|---|---|
| **Dense-only (chunked)** | **0.3947** | **0.4745** |
| Hybrid (dense + BM25) + reranker | 0.3457 | 0.4363 |

BM25/hybrid and the cross-encoder reranker are implemented correctly (verified via direct Qdrant queries, reranker sign-check, and ablation testing) but both measurably hurt recall on this dataset — FiQA's informal, high-lexical-overlap forum text gives BM25 little useful signal, and `bge-reranker-base` is not well calibrated to this domain style. This matches published BEIR numbers, where BM25 alone scores well below dense retrieval on FiQA (nDCG@10 0.24 vs ~0.40 for a comparable dense model), and even 7B-parameter SOTA embedding models top out around nDCG@10 ≈ 0.62–0.63 — well short of very high recall targets on this particular dataset. The default configuration (`use_hybrid=False`, `use_reranker=False`) reflects the empirically best setup; hybrid/reranking code is kept in place (and toggle-able) as a documented, measured experiment rather than removed.

---

## Project structure

```
FiQA_Dataset_RAG/
├── app.py                 FastAPI /retrieve endpoint (dense / hybrid / reranker, all toggleable)
├── upload_docs_to_db.py   chunking + dense/sparse embedding + Qdrant indexing
├── load_data.py           one-time BEIR FiQA dataset download
├── test_client.py         drives /retrieve for every query in the test qrels, writes results.csv
├── evaluate.py            runs test_client.py, computes Recall@5 / Recall@10
├── Dockerfile             CUDA-enabled FastAPI service image
├── docker-compose.yaml    qdrant + fastapi services (GPU passthrough on fastapi)
└── datasets/fiqa/         corpus.jsonl, queries.jsonl, qrels/
```

---

## Run it

```bash
docker compose up -d qdrant
python upload_docs_to_db.py      # chunk, embed, index into Qdrant (one-time, GPU recommended)
docker compose build fastapi && docker compose up -d fastapi
python evaluate.py               # Recall@5 / Recall@10 against the test set
```
