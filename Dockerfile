FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    BALANCE_DATA_DIR=/data

WORKDIR /app

# En HuggingFace Spaces, /data es el volumen persistente (si está habilitado).
# Aun así, la fuente de verdad es el HF Dataset privado vía persistence.py.
RUN mkdir -p /data && chmod 777 /data

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

# Render (y otros PaaS) asignan el puerto por la variable $PORT.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
