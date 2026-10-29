FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir . graphifyy==0.9.95 \
    && useradd --create-home --uid 10001 reaper

USER reaper

ENTRYPOINT ["reaper"]
