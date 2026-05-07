FROM python:3.11-slim

WORKDIR /app

# Install numpy first (binary wheel), then dhvani + flask
RUN pip install --no-cache-dir numpy && \
    pip install --no-cache-dir dhvani==0.2.4 flask gunicorn

COPY server.py .
COPY static/ static/
COPY data/ data/

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "server:app"]
