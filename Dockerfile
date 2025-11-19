# Stage 1: Build uv
FROM python:3.11-slim as builder

# Install uv
RUN pip install uv

# Stage 2: Application
FROM python:3.11-slim

WORKDIR /app

# Copy uv from the builder stage
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy the dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync
RUN uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# Copy the rest of the application's code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
