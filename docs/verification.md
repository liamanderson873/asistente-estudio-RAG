# Verificación de la primera versión

Estado actualizado el 13 de noviembre de 2026: recorrido completo probado con PostgreSQL y Ollama reales. Los resultados iniciales y limitaciones están en [experiments/README.md](experiments/README.md).

## Verificación con servicios reales (13 de noviembre)

- 64 pruebas correctas, incluidas las tres de PostgreSQL que antes se omitían, la regresión que rechaza la alucinación observada de 1.5B y los límites y citas del contexto reducido; sin pruebas omitidas.
- Comparación real de contexto 5/3 ejecutada con dos preguntas de desarrollo: citas y abstención correctas en los cuatro casos. Resultados y límites en [el informe](experiments/2026-11-13-context-budget.md). `docker compose config --quiet` correcto.
- PostgreSQL 17.12 y pgvector en `cuaderno-db-local`; Ollama 0.40.16 nativo en CPU. Nube desactivada.
- Dos documentos cargados, repetición detectada y enlaces a páginas comprobados.
- 3B respondió correctamente a la pregunta de JOIN y se abstuvo ante la pregunta sobre la fecha de examen. La variante 1.5B falló esta última: no se eligió como modelo predeterminado.
- Comparación léxica/vectorial/híbrida ejecutada con seis preguntas `dev`. `holdout` no se ejecutó.
- Corregida la lectura de `EMBEDDING_DIMENSIONS=768` desde `.env`: antes el tipo Literal rechazaba el texto del entorno. Añadidas pruebas de regresión.
- `/api/status` distingue la disponibilidad de la biblioteca y de los modelos. No comprueba calidad de generación.
- `ruff check .` correcto. La [primera ejecución de GitHub Actions](https://github.com/liamanderson873/asistente-estudio-RAG/actions/runs/43333301568) terminó correctamente tras publicar el commit `50a78fd` en `main`.

## Registro inicial (12 de noviembre)

| Comprobación | Resultado observado |
|---|---|
| `pytest -q` | 44 pruebas correctas, 3 omitidas de PostgreSQL real |
| `ruff check .` | Sin errores |
| `docker compose config --quiet` | Configuración válida |
| Proceso FastAPI y página local | Abre en http://localhost:8011; interfaz en español y aviso real de PostgreSQL no disponible |
| API con dobles controlados | Carga/validación, errores de base de datos, página PDF y validación de preguntas probados |
| PDFs originales | Dos documentos de tres páginas; extracción comprobada y seis páginas renderizadas e inspeccionadas |
| Graphify | Extracción estructural y consulta realizadas; mapa de código en `graphify-out/` |
| Understand Anything | Escaneo y extracción estructural realizados; resultados en `docs/architecture/` |
| Motor Docker | Esta sesión recibe `permission denied` al acceder a `dockerDesktopLinuxEngine` |
| Ollama | No se ha ejecutado un modelo real; no había servicio local disponible |
| Calidad de respuestas y latencia | No medidas; no se publican métricas simuladas |
| CI de GitHub | Workflow preparado localmente; no ejecutado ni publicado |

Las pruebas de PostgreSQL omitidas cubren ingesta idempotente/búsqueda, rollback y duplicados concurrentes. Están preparadas para una base de pruebas aislada. Los tests unitarios no sustituyen esas verificaciones.

Se observa un aviso de deprecación de Starlette relativo a httpx en TestClient. Las pruebas pasan; revisar la migración del cliente de tests en una actualización de dependencias.

## Plan inicial de comprobación (registro histórico)

1. Desde una terminal con acceso a Docker Desktop, ejecutar `docker compose up --build -d` en el repositorio.
2. Esperar a que `models` descargue ambos modelos y termine correctamente.
3. Abrir la web, cargar los dos PDFs y repetir una carga para verificar que no se duplica.
4. Preguntar por INNER JOIN/LEFT JOIN y abrir las citas en sus páginas.
5. Preguntar por la fecha de un examen: comprobar manualmente que se abstiene.
6. Ejecutar la evaluación `dev` y guardar resultados reales. No ajustar con `holdout`.
7. Medir memoria/latencia y ejecutar las pruebas con PostgreSQL real.
