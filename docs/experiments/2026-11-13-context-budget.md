# Contexto de tres frente a cinco fragmentos

13 de noviembre de 2026. Qwen 2.5 3B en Ollama CPU, mismo equipo y biblioteca de demostración que en la evaluación inicial.

Se recuperaron cinco fragmentos una sola vez por pregunta. Se enviaron al modelo los cinco o los tres primeros, conservando su orden y los parámetros del generador. Orden de ejecución: JOIN 5→3, examen 3→5. Una ejecución por caso; no se utilizó holdout.

| Pregunta | 5 fragmentos | 3 fragmentos | Reducción observada | Tokens de entrada 5→3 |
|---|---:|---:|---:|---:|
| INNER JOIN / LEFT JOIN | 76,526 s | 55,378 s | 27,6 % | 1255→765 |
| Fecha del examen, ausente en los documentos | 71,654 s | 46,742 s | 34,8 % | 1220→756 |

Los tiempos incluyen generación, carga del modelo y validación; excluyen recuperación (3,615 s para JOIN y 4,136 s para examen). Las cargas variaron entre ejecuciones. La respuesta de JOIN con tres fragmentos fue más breve: 88 tokens de salida frente a 162. Por tanto, la diferencia de tiempo no se atribuye exclusivamente a la longitud de entrada ni constituye una estimación estable de rendimiento.

Los cuatro controles automáticos pasaron. En la revisión manual, ambas respuestas de JOIN explican correctamente que INNER JOIN conserva coincidencias y LEFT JOIN conserva todas las filas izquierdas con NULL cuando no hay correspondencia, respaldadas por SQL, página 2. Ambas variantes se abstuvieron ante la fecha del examen y no devolvieron citas.

Se adopta `ANSWER_CONTEXT_CHUNKS=3`, configurable entre 1 y 5. La búsqueda y las métricas de recuperación siguen usando cinco resultados. El validador solo acepta citas del contexto enviado. Reducir el contexto puede perder información necesaria para otras preguntas; estos dos ejemplos de desarrollo no demuestran calidad general. Ampliar la evaluación antes de extraer conclusiones sobre otros documentos o preguntas con varias fuentes.

Reproducción: `python scripts/benchmark_context.py`, con PostgreSQL, los dos PDFs de demostración y los modelos disponibles. Respuestas, contexto y métricas sin transformar en [el JSON adjunto](2026-11-13-context-budget.json).
