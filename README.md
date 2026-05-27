# Personal Knowledge Base

A system that lets users upload multiple documents (PDFs) and chat with them as a unified knowledge base. Ask any question, get answers with citations showing exactly which document and chunk the answer came from.

**Example:**
```
Upload: lecture_week3.pdf, research_paper.pdf, book_notes.pdf

Ask: "what is the CAP theorem?"
→ "According to lecture_week3.pdf: CAP theorem states that..."
```

---

## Architecture

```
User uploads PDF
→ S3 stores raw file
→ pypdf extracts text
→ text split into chunks
→ SageMaker embedding endpoint generates vectors
→ chunks + vectors stored in RDS pgvector

User asks question
→ SageMaker embeds question
→ pgvector finds top K similar chunks
→ chunks + question sent to Claude via Bedrock
→ answer returned with source citations
```

---

## Stack

**Local development:**
```
FastAPI          → REST API
PostgreSQL       → metadata + chunk storage
pgvector         → vector similarity search
pypdf            → PDF text extraction
Docker Compose   → local orchestration
```

**AWS:**
```
S3               → raw PDF storage
RDS              → PostgreSQL + pgvector
EC2              → FastAPI container
ECR              → Docker image registry
SageMaker        → embedding model endpoint
Bedrock (Claude) → LLM answers
Terraform        → infrastructure as code
```

**Python libraries:**
```
fastapi          → API framework
sqlalchemy       → PostgreSQL ORM
pgvector         → vector client
pypdf            → PDF parsing
boto3            → AWS SDK
pydantic         → data validation
```

---

## Project Structure

```
knowledge-base/
├── app/
│   ├── main.py           → FastAPI app
│   ├── routes/
│   │   ├── documents.py  → upload endpoints
│   │   └── query.py      → question endpoints
│   ├── services/
│   │   ├── parser.py     → PDF parsing + chunking
│   │   ├── embeddings.py → SageMaker calls
│   │   ├── storage.py    → S3 operations
│   │   └── rag.py        → retrieval + Bedrock
│   ├── models/
│   │   └── database.py   → SQLAlchemy models
│   └── config.py         → settings + env vars
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 3 Week Plan

```
Week 1
├── Day 1-2: PDF parsing + chunking working
├── Day 3-4: pgvector setup + storing chunks
└── Day 5-7: embeddings + similarity search working

Week 2
├── Day 1-2: Claude via API answering with citations
├── Day 3-4: FastAPI routes + Docker Compose
└── Day 5-7: full pipeline working end to end locally

Week 3
├── Day 1-2: Terraform configs for all AWS resources
├── Day 3-4: deploy on AWS, test everything
├── Day 5:   record demo
├── Day 6:   terraform destroy + write README
└── Day 7:   buffer for things breaking
```

---

## Local vs AWS Mapping

```
Local (dev)          AWS (demo deploy)
─────────────────────────────────────
local files      →   S3
PostgreSQL       →   RDS
Claude API       →   Bedrock
manual embed     →   SageMaker endpoint
docker-compose   →   EC2 + ECR
```

---

## CV Description

> Built a personal knowledge base — upload any PDFs and chat with them using RAG. FastAPI backend, PostgreSQL/pgvector for vector search, Claude via AWS Bedrock for answers, SageMaker for embeddings. Fully containerized with Docker, infrastructure provisioned on AWS (S3, EC2, RDS, ECR) via Terraform.
