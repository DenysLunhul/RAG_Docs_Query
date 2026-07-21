# Knowledge Base

A collection of RAG (Retrieval-Augmented Generation) projects and experiments.

---

## [Manual-RAG](Manual-RAG/)

A production-deployed RAG-based personal knowledge base — upload PDFs, ask questions in natural language, get answers with citations pointing back to the source document.

**Pipeline:** PDF → S3 → text extraction (pypdf) → chunking (word-based, overlap) → Amazon Titan embeddings (Bedrock) → PostgreSQL + pgvector → cosine similarity search (top 20) → SageMaker cross-encoder reranker (top 5) → Claude Haiku (Bedrock) generates a cited answer.

**Stack:** FastAPI, PostgreSQL + pgvector (RDS), Amazon Titan embeddings, SageMaker reranker (`cross-encoder/ms-marco-MiniLM-L-6-v2`), Claude Haiku via Bedrock, S3, Terraform-provisioned AWS infra (EC2, RDS, S3, ECR, Lambda).

Full details, API endpoints, and deploy instructions: [`Manual-RAG/README.md`](Manual-RAG/README.md).

---

## [FiQA_Dataset_RAG](FiQA_Dataset_RAG/)

A retrieval pipeline benchmarked against **FiQA-2018** (BEIR), a financial-domain Q&A dataset — used to measure and compare different retrieval strategies rather than to serve a product.

**Pipeline:** corpus → token-based chunking with overlap → dense (`BAAI/bge-base-en-v1.5`) + sparse (BM25 via `fastembed`) embeddings → Qdrant (hybrid RRF fusion, grouped by document) → optional cross-encoder reranking (`BAAI/bge-reranker-base`) → top-k results.

**Stack:** FastAPI, Qdrant (dense + sparse vectors, hybrid search), `sentence-transformers`, `fastembed`, `langchain-text-splitters`, Docker Compose with GPU passthrough.

Hybrid search and reranking are implemented and toggleable per-request, but measured (against the full BEIR test set) to underperform plain dense retrieval on this dataset — the default configuration reflects that finding.

Full pipeline details, API, evaluation results, and run instructions: [`FiQA_Dataset_RAG/README.md`](FiQA_Dataset_RAG/README.md).
