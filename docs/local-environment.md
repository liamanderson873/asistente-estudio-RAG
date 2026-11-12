# Entorno local comprobado

Fecha: 13 de noviembre de 2026.

## Servicios de este equipo

- **PostgreSQL:** contenedor independiente `cuaderno-db-local`, imagen `pgvector/pgvector:0.8.7-pg17-bookworm`, PostgreSQL 17.12 y pgvector. Puerto 55433; bases `study` y `study_test`. Se creó con Docker Desktop porque el acceso a su motor desde la consola de esta sesión estaba denegado. No es un servicio administrado por el Compose del repositorio.
- **Ollama:** instalación nativa para CPU, versión 0.40.16, en `C:/Users/flany/Documents/Codex/Tools/ollama-local/`. Ejecutable de la distribución oficial con firma válida de Ollama Inc. Servicio enlazado a `127.0.0.1:11435`, nube desactivada y una petición/modelo simultáneo.
- **Modelos:** `embeddinggemma` (768 dimensiones) y `qwen2.5:3b` (Q4_K_M). Descargados y verificados por Ollama.
- **API:** FastAPI enlazado a `127.0.0.1:8011`, con configuración desde `.env`.

La contraseña de la base de datos es aleatoria y está en `.env`, excluido de Git. No copiarla a la documentación ni al repositorio público. El contenedor manual usa el almacenamiento persistente que asigna la imagen; no eliminarlo para conservar sus datos. El esquema se inicializó mediante una conexión local, no mediante el montaje SQL de Compose.

El formulario de Docker Desktop publica el puerto con su configuración predeterminada. No se debe asumir que esa publicación manual está restringida a localhost. El Compose del repositorio sí declara explícitamente `127.0.0.1`. Para una entrega final, migrar a ese despliegue conservando los datos. La web y Ollama se mantienen enlazados exclusivamente a localhost.

## Volver a abrir el proyecto

1. Abrir Docker Desktop e iniciar solamente `cuaderno-db-local` si está detenido.
2. Desde PowerShell, en la carpeta del proyecto, ejecutar `./scripts/start-local.ps1`.
3. Abrir http://localhost:8011 y comprobar la conexión.

El script no instala software, no descarga modelos, no cambia otros contenedores y no modifica la política de ejecución de PowerShell. Los registros se guardan en `work/`.

No ejecutar simultáneamente `docker compose up` con todos los servicios y este entorno nativo: comparten los puertos 55433, 11435 y 8011. Compose sigue siendo la alternativa reproducible para un equipo nuevo; no reutiliza automáticamente los datos del contenedor manual.

## Verificación

`/health` comprueba que el proceso de la API responde. `/api/status` comprueba conexión con la biblioteca, presencia del esquema/pgvector y descarga de los modelos. No ejecuta inferencia ni garantiza calidad de respuestas.

Para repetir el recorrido con servicios reales: `uv run python scripts/smoke_test.py`. Usa exclusivamente los dos PDFs originales de `demo/`, comprueba duplicados y enlaces a PDFs, y registra las respuestas sin borrar datos.
