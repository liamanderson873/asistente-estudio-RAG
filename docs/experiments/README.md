# Primera evaluación con servicios reales

13 de noviembre de 2026. Equipo observado en los registros de inferencia: Intel Core i5-1335U, aproximadamente 15,7 GiB de RAM total y ejecución en CPU. Durante una carga del modelo había unos 753 MiB libres; otras aplicaciones estaban abiertas. Estos tiempos no son un benchmark aislado.

## Recorrido completo

PostgreSQL 17.12 con pgvector y Ollama 0.40.16. Los dos PDFs originales se cargaron en 10,96 y 10,21 segundos. Repetir el PDF de SQL devolvió el mismo documento y `duplicate=true`. Los enlaces de las citas respondieron con los PDFs originales.

| Prueba de desarrollo | Qwen 2.5 3B | Qwen 2.5 1.5B |
|---|---|---|
| Diferencia INNER JOIN / LEFT JOIN | Respuesta respaldada por la página 2; 120,31 s | Respuesta respaldada por la página 2; 63,46 s |
| Fecha de mi próximo examen | Abstención correcta; 96,36 s | Respuesta inventada con citas irrelevantes; 56,69 s |

La revisión de las respuestas fue manual contra los fragmentos citados. **Se mantiene 3B como predeterminado.** El caso de 1.5B demuestra por qué verificar que un ID de cita existe no basta para garantizar una respuesta fundamentada. Dos preguntas no permiten concluir que 3B sea fiable en general ni que 1.5B falle siempre.

## Recuperación

Seis preguntas contestables del conjunto `dev`, seis páginas en total y evaluación por página física. Las preguntas sin respuesta no entran en estas métricas.

| Método | Recall@5 | MRR |
|---|---:|---:|
| Léxico (`plainto_tsquery`, términos combinados con AND) | 0,333 | 0,333 |
| Vectorial | 1,000 | 1,000 |
| Híbrido (RRF) | 1,000 | 1,000 |

No se utilizó `holdout` para realizar estos ajustes. Los documentos se crearon para la demo y las preguntas están relacionadas con ellos: no extrapolar los resultados a PDFs arbitrarios. Algunas mediciones de latencia de recuperación coincidieron con otras pruebas de generación; no sirven para comparar velocidad entre métodos.

Los JSON adjuntos conservan respuestas, referencias y medidas reales. No contienen contraseñas ni documentos personales. El siguiente trabajo es ampliar las preguntas, mejorar la abstención y reducir el contexto/latencia manteniendo controles de calidad.
