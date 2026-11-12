"""Compara recuperación; la generación y fidelidad de citas se revisan por separado."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import httpx

ROOT = Path(__file__).resolve().parents[1]


def metrics(hits: list[dict], expected: list[list]) -> dict:
    relevant = {tuple(item) for item in expected}
    if not relevant:
        return {"recall_at_5": None, "reciprocal_rank": None}
    retrieved = [(h["name"], h["page"]) for h in hits[:5]]
    first = next((i for i, item in enumerate(retrieved, 1) if item in relevant), None)
    return {
        "recall_at_5": len(set(retrieved) & relevant) / len(relevant),
        "reciprocal_rank": 1 / first if first else 0.0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8011")
    parser.add_argument("--split", choices=["dev", "holdout"], default="dev")
    parser.add_argument("--output", default="evaluation/results-dev.json")
    args = parser.parse_args()
    questions = json.loads((ROOT / "evaluation/questions.json").read_text(encoding="utf-8"))
    rows = []
    with httpx.Client(base_url=args.url, timeout=240) as client:
        for mode in ("lexical", "vector", "hybrid"):
            for question in questions:
                if question["split"] != args.split or not question["expected"]:
                    continue
                start = perf_counter()
                response = client.post(
                    "/api/search",
                    json={
                        "question": question["question"],
                        "mode": mode,
                    },
                )
                response.raise_for_status()
                rows.append(
                    {
                        "id": question["id"],
                        "mode": mode,
                        "seconds": round(perf_counter() - start, 3),
                        **metrics(response.json(), question["expected"]),
                    }
                )
    summary = {}
    for mode in ("lexical", "vector", "hybrid"):
        selected = [row for row in rows if row["mode"] == mode]
        summary[mode] = {
            "questions": len(selected),
            "recall_at_5": sum(r["recall_at_5"] for r in selected) / len(selected),
            "mrr": sum(r["reciprocal_rank"] for r in selected) / len(selected),
        }
    result = {"split": args.split, "scope": "retrieval_only", "summary": summary, "rows": rows}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
