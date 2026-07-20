import csv
import subprocess
import sys
from collections import defaultdict

RESULTS_PATH = "results.csv"
QRELS_TEST_PATH = "datasets/fiqa/qrels/test.tsv"


def load_qrels(path):
    relevant = defaultdict(set)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            relevant[row["query-id"]].add(row["corpus-id"])
    return relevant


def load_results(path):
    ranked = defaultdict(list)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ranked[row["query_id"]].append((int(row["rank"]), row["document_id"]))
    return ranked


def recall_at_k(ranked, relevant, k):
    scores = []
    for query_id, relevant_ids in relevant.items():
        retrieved_ids = {doc_id for rank, doc_id in ranked.get(query_id, []) if rank <= k}
        scores.append(len(retrieved_ids & relevant_ids) / len(relevant_ids))
    return sum(scores) / len(scores)


if __name__ == "__main__":
    subprocess.run([sys.executable, "test_client.py"], check=True)

    qrels = load_qrels(QRELS_TEST_PATH)
    ranked = load_results(RESULTS_PATH)

    print(f"Recall@5: {recall_at_k(ranked, qrels, 5):.4f}")
    print(f"Recall@10: {recall_at_k(ranked, qrels, 10):.4f}")
