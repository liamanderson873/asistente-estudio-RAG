# Verificación de la primera versión

Fecha: 12 de noviembre de 2026. Estado: base implementada; recorrido completo con modelos y base de datos pendiente.

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

## Siguiente comprobación real

1. Desde una terminal con acceso a Docker Desktop, ejecutar `docker compose up --build -d` en el repositorio.
2. Esperar a que `models` descargue ambos modelos y termine correctamente.
3. Abrir la web, cargar los dos PDFs y repetir una carga para verificar que no se duplica.
4. Preguntar por INNER JOIN/LEFT JOIN y abrir las citas en sus páginas.
5. Preguntar por la fecha de un examen: comprobar manualmente que se abstiene.
6. Ejecutar la evaluación `dev` y guardar resultados reales. No ajustar con `holdout`.
7. Medir memoria/latencia y ejecutar las pruebas con PostgreSQL real.
