FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

COPY . .

EXPOSE 8200
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]
