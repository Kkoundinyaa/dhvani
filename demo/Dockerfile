FROM python:3.11-slim

WORKDIR /app

# Install dhvani and flask
RUN pip install --no-cache-dir dhvani flask gunicorn

# Copy demo files
COPY server.py .
COPY static/ static/
COPY search_index.json data/search_index.json

# HF Spaces uses port 7860
ENV PORT=7860
EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "server:app"]
