"""Comparación pareada de contexto; conserva recuperación, modelo y parámetros."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from smoke_test import check_answer

from study_rag.config import Settings
from study_rag.ollama import OllamaModel
from study_rag.repository import Repository
from study_rag.service import StudyService, validate_answer


class MeasuredModel(OllamaModel):
    def request(self, path: str, payload: dict) -> dict:
        result = super().request(path, payload)
        if path == "/api/chat":
            self.last_metrics = {
                key: result.get(key)
                for key in (
                    "prompt_eval_count",
                    "eval_count",
                    "total_duration",
                    "load_duration",
                    "prompt_eval_duration",
                    "eval_duration",
                )
            }
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--output", default="work/context-comparison.json")
    args = parser.parse_args()
    settings = Settings(chat_model=args.model)
    model = MeasuredModel(settings)
    service = StudyService(Repository(settings.database_url), model, settings)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results = {
        "model": args.model,
        "scope": "two_development_questions_only",
        "retrieval_limit": 5,
        "rows": [],
    }
    questions = [
        ("¿Qué diferencia hay entre INNER JOIN y LEFT JOIN?", False, [5, 3]),
        ("¿Cuándo es mi próximo examen?", True, [3, 5]),
    ]
    for question, expected_abstained, budgets in questions:
        retrieval_start = perf_counter()
        hits = service.retrieve(question, limit=5)
        retrieval_seconds = perf_counter() - retrieval_start
        if len(hits) != 5:
            raise RuntimeError("La comparación necesita cinco fragmentos recuperados.")
        for budget in budgets:
            context = hits[:budget]
            print("Generando", budget, "fragmentos:", question, flush=True)
            start = perf_counter()
            raw = model.answer(question, context)
            answer = validate_answer(raw, context)
            seconds = perf_counter() - start
            try:
                check_answer(answer, expected_abstained)
                quality_check = "pass"
            except AssertionError as error:
                quality_check = str(error)
            row = {
                "question": question,
                "context_chunks": budget,
                "retrieval_seconds": round(retrieval_seconds, 3),
                "generation_seconds": round(seconds, 3),
                "quality_check": quality_check,
                "model_metrics": model.last_metrics,
                "context": [asdict(hit) for hit in context],
                "raw_answer": raw,
                "validated_answer": answer,
            }
            results["rows"].append(row)
            output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print("Resultado:", quality_check, round(seconds, 2), "s", flush=True)
    print("Comparación guardada en", output, flush=True)


if __name__ == "__main__":
    main()
