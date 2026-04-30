# 🔗 URL Shortener API

A fast, lightweight URL shortener built with **FastAPI** and **Docker**. Supports custom short codes, click tracking, and link expiry.

## Features

- ✅ Shorten any URL
- ✅ Custom short codes
- ✅ Click tracking & stats
- ✅ Link expiry (optional)
- ✅ Delete short URLs
- ✅ SQLite storage (no external DB needed)
- ✅ Auto-generated Swagger docs

## Tech Stack

- **FastAPI** — Modern Python web framework
- **SQLite** — Lightweight persistent storage
- **Docker** — Containerized deployment
- **Pydantic** — Data validation

## Getting Started

### Run with Docker (recommended)

```bash
docker-compose up --build
```

### Run locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/shorten` | Shorten a URL |
| `GET` | `/{short_code}` | Redirect to original URL |
| `GET` | `/stats/{short_code}` | Get click stats |
| `GET` | `/stats/` | List all URLs |
| `DELETE` | `/delete/{short_code}` | Delete a short URL |

## Example Usage

### Shorten a URL
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com/very/long/url"}'
```

### With custom code & expiry
```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com", "custom_code": "gh", "expires_in_days": 7}'
```

### Get stats
```bash
curl http://localhost:8000/stats/gh
```

## Project Structure

```
url-shortener/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image config
├── docker-compose.yml   # Docker Compose setup
└── README.md
```
