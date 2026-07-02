FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

EXPOSE 8000

# Production entrypoint: migrate, then serve on $PORT (Render) or 8000 (plain Docker).
# docker-compose.yml overrides this command for local dev (uvicorn --reload).
CMD ["sh", "/app/start.sh"]
