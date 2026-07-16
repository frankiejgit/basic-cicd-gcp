FROM python:3.12-slim
WORKDIR /app

# Install dependencies using standard pip
RUN pip install fastapi uvicorn

# Copy all files (including the src/ folder) into the container
COPY . .

# Run uvicorn, pointing it to main:app inside the src/ directory
CMD exec uvicorn src.main:app --host 0.0.0.0 --port $PORT