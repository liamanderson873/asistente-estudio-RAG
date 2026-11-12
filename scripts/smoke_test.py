"""Recorrido real con los documentos originales de demo; no borra datos."""

import argparse
import json
from pathlib import Path
from time import perf_counter

import httpx

ROOT = Path(__file__).resolve().parents[1]


def check_answer(answer: dict, expected_abstained: bool) -> None:
    if answer.get("abstained") is not expected_abstained:
        raise AssertionError("La respuesta no cumple la expectativa de abstención de la demo.")
    if not expected_abstained and not any(
        citation.get("document") == "sql-fundamentos.pdf" and citation.get("page") == 2
        for citation in answer.get("citations", [])
    ):
        raise AssertionError("La respuesta de JOIN debe citar la página 2 del documento SQL.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8011")
    parser.add_argument("--output", default="work/smoke-results.json")
    args = parser.parse_args()
    results = {"scope": "real_services_smoke_test", "uploads": [], "answers": []}
    with httpx.Client(base_url=args.url, timeout=240) as client:
        response = client.get("/api/status")
        response.raise_for_status()
        results["services"] = response.json()
        if not results["services"]["ready"]:
            raise RuntimeError("Los servicios locales todavía no están listos.")
        for filename in ["sql-fundamentos.pdf", "python-fundamentos.pdf"]:
            data = (ROOT / "demo" / filename).read_bytes()
            start = perf_counter()
            response = client.post("/api/documents", files={"file": (filename, data)})
            response.raise_for_status()
            uploaded = {
                "name": filename,
                **response.json(),
                "seconds": round(perf_counter() - start, 2),
            }
            results["uploads"].append(uploaded)
            print("Documento preparado:", filename, uploaded["seconds"], "s", flush=True)
        response = client.post(
            "/api/documents",
            files={
                "file": ("sql-fundamentos.pdf", (ROOT / "demo/sql-fundamentos.pdf").read_bytes())
            },
        )
        response.raise_for_status()
        results["duplicate_detected"] = response.json()["duplicate"]
        if not results["duplicate_detected"]:
            raise RuntimeError("No se ha detectado el documento repetido.")
        # Preguntas de desarrollo. No utilizar el conjunto holdout para ajustes.
        for question, expected_abstained in [
            ("¿Qué diferencia hay entre INNER JOIN y LEFT JOIN?", False),
            ("¿Cuándo es mi próximo examen?", True),
        ]:
            start = perf_counter()
            response = client.post("/api/ask", json={"question": question, "mode": "hybrid"})
            response.raise_for_status()
            answer = {
                "question": question,
                "seconds": round(perf_counter() - start, 2),
                **response.json(),
            }
            results["answers"].append(answer)
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            check_answer(answer, expected_abstained)
            print(
                "Pregunta:",
                question,
                "Abstención:",
                answer["abstained"],
                "Tiempo:",
                answer["seconds"],
                flush=True,
            )
            for citation in answer["citations"]:
                source = client.get(citation["url"].split("#")[0])
                source.raise_for_status()
                if not source.content.startswith(b"%PDF-"):
                    raise RuntimeError("Una cita no enlaza al PDF original.")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Resultados reales guardados en", output, flush=True)


if __name__ == "__main__":
    main()
