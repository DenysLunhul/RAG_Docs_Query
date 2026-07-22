# LangChain-Qdrant-RAG

An agentic RAG over user-uploaded PDFs, built on **LangChain** (`create_agent`) and **LangGraph** — a learning project to practice the current LangChain/LangGraph agent stack, as opposed to the hand-rolled RAG pipelines in `Manual-RAG` and `FiQA_Dataset_RAG`.

---

## What It Does

Upload a PDF → it's chunked, embedded (dense + sparse), and stored in Qdrant. Ask a question → a ReAct agent decides when to call a `retrieve` tool (hybrid dense+sparse search, optional cross-encoder reranking) and answers only from what it finds, with a groundedness check on the final answer.

```
Upload PDF
  → PyPDFLoader (text extraction, per page)
  → RecursiveCharacterTextSplitter (256 tokens, 50 overlap, HF tokenizer-aware)
  → BAAI/bge-base-en-v1.5 (dense) + fastembed BM25 (sparse)
  → Qdrant (named dense + sparse vectors, payload-indexed by doc_id)

Ask a question
  → create_agent (LangChain, ReAct loop over LangGraph)
  → retrieve tool: dense search, or hybrid (Prefetch + RRF fusion) if enabled
      → optional BAAI/bge-reranker-base reranking if enabled
  → middleware: ToolCallLimitMiddleware (caps retrieve calls per run),
      SummarizationMiddleware (compresses long threads),
      GroundingCheckMiddleware (custom — flags answers not backed by retrieved passages)
  → Claude (Haiku) via Bedrock generates the answer
```

`use_hybrid` / `use_reranker` are runtime toggles (LangChain `context`, not tool arguments) passed per request — same pattern as the hybrid/reranker toggles in `FiQA_Dataset_RAG`.

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent | LangChain `create_agent` (ReAct loop, built on LangGraph) |
| Persistence | LangGraph `InMemorySaver` checkpointer (per `thread_id`) |
| Vector DB | Qdrant (dense + sparse named vectors, hybrid RRF fusion) |
| Dense embeddings | `BAAI/bge-base-en-v1.5` (`sentence-transformers`) |
| Sparse embeddings | BM25 via `fastembed` (`Qdrant/bm25`) |
| Reranking | `BAAI/bge-reranker-base` cross-encoder, optional |
| PDF loading / chunking | `langchain-community` `PyPDFLoader`, `langchain-text-splitters` |
| LLM | Claude Haiku via AWS Bedrock (`langchain-aws`) |
| Compute | CUDA-enabled PyTorch (GPU inference), Docker Compose with GPU passthrough |

---

## Project Structure

```
LangChain-Qdrant-RAG/
├── app.py               FastAPI app: upload / chat / list / read / delete endpoints
├── agent.py             retrieve tool, middleware, create_agent, ask()
├── Dockerfile           CUDA-enabled FastAPI service image
├── docker-compose.yaml  qdrant + app services (GPU passthrough, AWS creds mount)
└── requirements.txt
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload a PDF (multipart/form-data, field: `file`) |
| `POST` | `/chat` | Ask a question — `question`, optional `use_hybrid`, `use_reranker` |
| `GET` | `/documents` | List uploaded documents |
| `GET` | `/documents/{doc_id}/read` | Get the original PDF back |
| `DELETE` | `/documents/{doc_id}` | Delete a document's chunks (Qdrant) and file |

---

## Run it

```bash
docker compose up --build
# http://localhost:8000/docs
```

Requires AWS credentials (`~/.aws`) for Bedrock, and an NVIDIA GPU + `nvidia-container-toolkit` on the host for the `app` service's GPU passthrough.
