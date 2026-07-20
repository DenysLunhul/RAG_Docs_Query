import json
import csv
import requests
from tqdm import tqdm

API_URL = "http://localhost:8000/retrieve"
QUERIES_PATH = "datasets/fiqa/queries.jsonl"
QRELS_TEST_PATH = "datasets/fiqa/qrels/test.tsv"
OUTPUT_PATH = "results.csv"
TOP_K = 10

if __name__ == "__main__":
    needed_query_ids = set()
    with open(QRELS_TEST_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            needed_query_ids.add(row["query-id"])

    with open(QUERIES_PATH, "r", encoding="utf-8") as f, \
         open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as out:

        writer = csv.writer(out)
        writer.writerow(["query_id", "rank", "document_id", "score"])

        for line in tqdm(f):
            query = json.loads(line)
            query_id = query["_id"]
            if query_id not in needed_query_ids:
                continue

            response = requests.post(API_URL, json={"query": query["text"], "top_k": TOP_K})
            response.raise_for_status()
            results = response.json()["results"]

            for rank, result in enumerate(results, start=1):
                writer.writerow([query_id, rank, result["id"], result["score"]])
