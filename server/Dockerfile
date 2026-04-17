# Python + LibreOffice headless image for the CV Engine web service.
FROM python:3.12-slim

# LibreOffice is required for DOCX→PDF normalization. libreoffice-core + writer
# keeps the image lean (~400MB with deps) versus the full libreoffice meta.
# fonts-liberation avoids "Could not find font" warnings during headless conversion.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libreoffice-core \
        libreoffice-writer \
        fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e . 2>/dev/null || true

# Now copy source and install editably so our code is picked up.
COPY cv_engine /app/cv_engine
COPY prompts /app/prompts
COPY rubrics /app/rubrics
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -e .

# Default DB path points at the mounted persistent disk on Render.
# Override locally via `-e CV_ENGINE_DB_PATH=/tmp/dev.db`.
ENV CV_ENGINE_DB_PATH=/data/cv_engine.db
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Render provides $PORT; default to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn cv_engine.web:app --host 0.0.0.0 --port ${PORT:-8000}"]
