"""Mapa estructural; ejecutar con el Python donde esté instalado Graphify."""

import json
from pathlib import Path

from graphify.build import build_from_json
from graphify.cluster import cluster
from graphify.export import to_json
from graphify.extract import extract

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "graphify-out"
    output.mkdir(exist_ok=True)
    files = sorted(
        p
        for folder in ("src", "tests", "scripts")
        for p in (ROOT / folder).rglob("*")
        if p.suffix in {".py", ".js"}
    )
    extracted = extract(files, root=ROOT, cache_root=ROOT)
    graph = build_from_json(extracted, root=ROOT, directed=True)
    if not graph.number_of_nodes():
        raise RuntimeError("Graphify no produjo nodos; no se sobrescribe el mapa.")
    communities = cluster(graph)
    if not to_json(graph, communities, str(output / "graph.json"), force=True):
        raise RuntimeError("Graphify no pudo guardar el mapa.")
    summary = {
        "scope": "structural_code_only",
        "files": len(files),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "communities": len(communities),
    }
    (output / "GRAPH_REPORT.md").write_text(
        "# Mapa estructural de Cuaderno\n\n"
        "Generado con Graphify a partir de Python y JavaScript del proyecto. "
        "No incluye extracción semántica de PDFs ni demuestra corrección del código.\n\n"
        + "\n".join(f"- {key}: {value}" for key, value in summary.items())
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
