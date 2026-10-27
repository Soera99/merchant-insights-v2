# Streamlit dashboard image for Cloud Run (same pattern as anexa-be)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Non-root user. Streamlit writes a few files to ~/.streamlit, so it needs a real home dir.
ARG UID=10001
RUN adduser --disabled-password --gecos "" --uid "${UID}" --home /home/appuser appuser

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser
EXPOSE 8080

# Cloud Run injects $PORT; Streamlit must listen on 0.0.0.0
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0"]
