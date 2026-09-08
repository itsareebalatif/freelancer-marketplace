FROM python:3.11-slim

# Install uv from official binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Set environment variables for clean python execution
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH"
# Copy dependency definition files
COPY pyproject.toml uv.lock* ./

# Install dependencies into /app/.venv using uv
RUN uv sync --no-install-project --no-dev
# Copy the rest of the application code
COPY . .

# Expose default API port
EXPOSE 8000

# Run Alembic migrations and start FastAPI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]