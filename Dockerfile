FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runner

WORKDIR /app

# Create non-root user for security best practices
RUN adduser --system --uid 1001 appuser

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/

USER appuser

ENV PORT=8080
CMD ["sh", "-c", "exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]