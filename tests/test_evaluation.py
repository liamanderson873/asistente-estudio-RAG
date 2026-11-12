import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "evaluate", Path(__file__).parents[1] / "scripts/evaluate.py"
)
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)


def test_metrics_deduplicate_pages_and_keep_first_relevant_rank():
    result = evaluate.metrics(
        [
            {"name": "other.pdf", "page": 1},
            {"name": "sql.pdf", "page": 2},
            {"name": "sql.pdf", "page": 2},
        ],
        [["sql.pdf", 2], ["sql.pdf", 3]],
    )
    assert result == {"recall_at_5": 0.5, "reciprocal_rank": 0.5}


def test_unanswerable_questions_are_not_scored_as_retrieval_successes():
    assert evaluate.metrics([], []) == {"recall_at_5": None, "reciprocal_rank": None}
