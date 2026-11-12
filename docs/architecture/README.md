# Análisis del repositorio

Se utilizan las dos herramientas solicitadas por el usuario con alcance estructural:

- **Graphify:** `graphify-out/graph.json` contiene entidades y relaciones extraídas del código Python/JavaScript; `GRAPH_REPORT.md` informa del alcance y las cantidades. Consulta validada: `graphify query "StudyService Repository OllamaModel"`. Para regenerar, ejecutar `scripts/map_architecture.py` con el intérprete que tenga instalado Graphify.
- **Understand Anything:** `understand-scan.json` es el inventario generado por su scanner; `understand-structure.json` contiene definiciones y relaciones estructurales extraídas por sus parsers. Se usaron los scripts originales del plugin, con sus dependencias resueltas desde la instalación compartida.

No se ha ejecutado la cadena completa de análisis semántico, revisión y tours de Understand Anything ni se ha validado su dashboard. Estos resultados no deben presentarse como un knowledge graph semántico completo. HTML/CSS pueden figurar entre los archivos sin parser disponible. Ninguna herramienta demuestra corrección del código ni de las respuestas del RAG.

Los corpus PDF, entornos virtuales, cachés y los propios resultados de análisis quedan fuera del escaneo. Los grafos se deben regenerar después de cambios del código; no son una fuente de verdad que sustituya los archivos.
