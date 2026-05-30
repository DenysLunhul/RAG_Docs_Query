# Knowledge Base

A RAG-based personal knowledge base — upload PDFs and ask questions in natural language. Answers include citations pointing back to the source document.

**Live demo:** `http://54.172.178.21:8000`

---

## What It Does

Upload any PDF → the system extracts text, splits it into chunks, embeds them using Amazon Titan, and stores them in PostgreSQL with pgvector. Ask a question → the system finds the most relevant chunks using vector similarity search, reranks them using a SageMaker cross-encoder, and passes the top results to Claude (Bedrock) which returns an answer with source citations.

```
Upload PDF
  → S3 (raw file storage)
  → pypdf (text extraction)
  → chunking (500 words, 50 word overlap)
  → Amazon Titan via Bedrock (embeddings)
  → RDS PostgreSQL + pgvector (vector storage)

Ask a question
  → Amazon Titan (embed question)
  → pgvector cosine similarity (top 20 chunks)
  → SageMaker reranker (cross-encoder, top 5)
  → Claude Haiku via Bedrock (answer + citations)
```

---

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Database | PostgreSQL + pgvector (RDS) |
| Vector search | pgvector cosine similarity |
| Embeddings | Amazon Titan (`amazon.titan-embed-text-v1`) |
| Reranking | SageMaker (`cross-encoder/ms-marco-MiniLM-L-6-v2`) |
| LLM | Claude Haiku via AWS Bedrock |
| File storage | AWS S3 |
| Compute | AWS EC2 (t3.micro) |
| Container registry | AWS ECR |
| Infrastructure | Terraform |
| Local dev | Docker Compose |

---

## Project Structure

```
knowledge_base/
├── app/
│   ├── main.py               FastAPI app + static file serving
│   ├── routes/
│   │   ├── documents.py      upload, list, read, delete endpoints
│   │   └── query.py          question answering endpoint
│   ├── services/
│   │   ├── parser.py         PDF text extraction + chunking
│   │   ├── embeddings.py     Amazon Titan embeddings via Bedrock
│   │   ├── reranker.py       SageMaker cross-encoder reranking
│   │   ├── storage.py        S3 operations
│   │   └── rag.py            retrieval pipeline + Claude answer generation
│   ├── models/
│   │   ├── chunks.py         DocumentChunk SQLAlchemy model
│   │   ├── database.py       DB engine + session
│   │   ├── init_db.py        table creation
│   │   └── schemas.py        Pydantic request schemas
│   ├── static/
│   │   ├── index.html        frontend
│   │   ├── style.css
│   │   └── app.js
│   └── config.py             settings from env vars
├── lambda/
│   └── delete_chunks.py      auto-delete DB chunks on S3 file removal
├── terraform/
│   ├── ec2.tf                EC2 + Elastic IP
│   ├── rds.tf                PostgreSQL RDS
│   ├── s3.tf                 S3 bucket + lifecycle rule (30 day expiry)
│   ├── lambda.tf             Lambda + S3 trigger + IAM
│   ├── iam.tf                EC2 IAM role + policies
│   ├── ecr.tf                ECR repository
│   ├── security_groups.tf    security group references
│   └── vpc.tf                VPC reference
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/document/upload` | Upload a PDF (multipart/form-data, field: `file`) |
| `GET` | `/document/list` | List all uploaded files |
| `GET` | `/document/read?filename=` | Stream a PDF file |
| `DELETE` | `/document/delete?filename=` | Delete file from S3 (triggers Lambda to clean DB) |
| `POST` | `/query` | Ask a question `{"query": "..."}` |

---

## AWS Infrastructure

- **EC2** — `t3.micro`, Ubuntu 24.04, runs Docker container, has Elastic IP
- **RDS** — PostgreSQL 16, `db.t3.micro`, pgvector extension
- **S3** — PDF storage, 30-day lifecycle expiry
- **ECR** — Docker image registry
- **Lambda** — triggered on S3 object delete, removes chunks from DB
- **SageMaker** — real-time inference endpoint for reranking (`ml.m4.xlarge`)
- **Bedrock** — Amazon Titan embeddings + Claude Haiku for answers
- **IAM** — EC2 role with S3, Bedrock, ECR, SageMaker permissions

---

## Deploy from Scratch

```bash
# 1. Build and push Docker image
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 287528889753.dkr.ecr.us-east-1.amazonaws.com
docker build -t knowledge-base .
docker tag knowledge-base:latest 287528889753.dkr.ecr.us-east-1.amazonaws.com/knowledge-base:latest
docker push 287528889753.dkr.ecr.us-east-1.amazonaws.com/knowledge-base:latest

# 2. Provision infrastructure
cd terraform
terraform init
terraform apply
# wait ~10 min for EC2 user_data to complete

# 3. Open the app
# http://<ec2_public_ip>:8000
```

## Local Development

```bash
docker compose up --build
# http://localhost:8000
```

---

## Tear Down

```bash
terraform destroy
# S3, ECR, and RDS are protected with prevent_destroy = true
# SageMaker endpoint must be deleted manually from AWS console
```
