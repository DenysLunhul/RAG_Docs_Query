import json
import boto3



def rerank(question: str, chunks: list) -> list:
    sagemaker = boto3.client("sagemaker-runtime", region_name = "us-east-1")

    payload = {"inputs": [{"text": question, "text_pair": chunk.chunk_text[:1000]} for chunk in chunks]}

    response = sagemaker.invoke_endpoint(
        EndpointName = "knowledge-base-reranker",
        ContentType = "application/json",
        Body = json.dumps(payload)
    )

    results = json.loads(response["Body"].read())

    scored = sorted(zip(results, chunks), key=lambda x: x[0]["score"], reverse=True)
    top_5 = scored[:5]
    top_chunks = []
    for _, chunk in top_5:
        top_chunks.append(chunk)
    return top_chunks