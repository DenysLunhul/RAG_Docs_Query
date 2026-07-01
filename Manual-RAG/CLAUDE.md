# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A RAG-based personal knowledge base. Users upload PDFs; the system chunks, embeds, and stores them in PostgreSQL with pgvector. Users ask questions; the system retrieves relevant chunks via cosine similarity, reranks them with a SageMaker cross-encoder, then passes the top results to Claude Haiku (Bedrock) to generate a cited answer.

## Commands

**Local development:**
```bash
docker compose up --build   # starts app (port 8000) + pgvector postgres (port 5433)
```

**Initialize the database** (run once after first `docker compose up`):
```bash
docker compose exec app python -m app.models.init_db
```

**Manual integration test** (requires live AWS credentials + running DB):
```bash
python -m app.testing.test_bedrock
```

**Deploy to AWS:**
```bash
# Build and push image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ecr-url>
docker build -t knowledge-base .
docker tag knowledge-base:latest <ecr-url>/knowledge-base:latest
docker push <ecr-url>/knowledge-base:latest

# Provision infrastructure
cd terraform
terraform init
terraform apply   # prompts for db_password
```

**Tear down:**
```bash
terraform destroy   # S3, ECR, RDS have prevent_destroy = true; delete SageMaker endpoint manually first
```

## Architecture

### Request Flow

**Upload:** `POST /document/upload` → `storage.py` (S3) + `parser.py` (pypdf chunking) + `embeddings.py` (Amazon Titan via Bedrock) → `document_chunks` table (pgvector)

**Query:** `POST /query` → `rag.retrieve_chunks()` embeds question via Titan → pgvector cosine distance top 20 → `reranker.py` (SageMaker cross-encoder, endpoint name hardcoded as `"knowledge-base-reranker"`) top 5 → `rag.generate_answer()` (Claude Haiku via Bedrock Converse API)

**Delete:** `DELETE /document/delete` → S3 delete → S3 event triggers Lambda (`lambda/delete_chunks.py`) → Lambda deletes matching rows from `document_chunks` by filename

### Key Constraints

- All boto3 clients are hardcoded to `us-east-1`.
- Embedding vector dimension is **1536** (Amazon Titan `amazon.titan-embed-text-v1`) — the `Vector(1536)` column type in `chunks.py` must match.
- Chunking is word-count based (default 500 words, 50-word overlap), configured in `.env` as `CHUNK_SIZE` / `CHUNK_OVERLAP`.
- The Lambda uses `pg8000` (not psycopg2) to connect to RDS; its dependencies are bundled in `lambda/delete_chunks.zip`.
- Database schema is created by running `app/models/init_db.py` as a script — there is no migration framework.

### Environment Variables (`.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy connection string — use `postgres:5432` for docker-compose, RDS URL in production |
| `S3_BUCKET_NAME` | S3 bucket for raw PDFs |
| `BEDROCK_MODEL_ID` | ARN of the Claude inference profile |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Chunking parameters (words) |

### Infrastructure

Terraform manages: VPC (reference only), EC2 (`t3.micro` with Elastic IP, runs Docker container), RDS PostgreSQL 16 with pgvector (`db.t3.micro`), S3 (30-day lifecycle), ECR, Lambda (S3 delete trigger), IAM role for EC2. The SageMaker reranker endpoint (`ml.m4.xlarge`, model `cross-encoder/ms-marco-MiniLM-L-6-v2`) is provisioned separately and must be deleted manually before `terraform destroy`.
