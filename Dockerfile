FROM python:3.12-slim
WORKDIR /app

# Install dependencies using standard pip
RUN pip install Flask gunicorn

# Copy all files (including the src/ folder) into the container
COPY . .

# Run gunicorn, pointing it to main.py inside the src/ directory
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 src.main:app