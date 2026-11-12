FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev
RUN useradd --create-home student
USER student
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "study_rag.app:app", "--host", "0.0.0.0", "--port", "8000"]
