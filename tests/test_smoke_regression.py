import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("smoke", ROOT / "scripts/smoke_test.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def test_observed_small_model_hallucination_cannot_pass_smoke_test():
    results = json.loads(
        (ROOT / "docs/experiments/2026-11-13-smoke-1.5b.json").read_text(encoding="utf-8")
    )
    invented_exam_answer = results["answers"][1]
    with pytest.raises(AssertionError, match="abstención"):
        smoke.check_answer(invented_exam_answer, expected_abstained=True)
