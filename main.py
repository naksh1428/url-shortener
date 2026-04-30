import string
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
import sqlite3
import os

app = FastAPI(
    title="URL Shortener API",
    description="A simple URL shortener with click tracking and expiry support",
    version="1.0.0"
)

DB_PATH = os.getenv("DB_PATH", "urls.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            expires_at TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None
    expires_in_days: Optional[int] = None


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    expires_at: Optional[str]


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: str
    expires_at: Optional[str]


@app.post("/shorten", response_model=ShortenResponse, tags=["URL"])
def shorten_url(request: Request, body: ShortenRequest):
    """Shorten a URL with optional custom code and expiry."""
    conn = get_db()

    short_code = body.custom_code or generate_short_code()

    # Check if custom code already exists
    existing = conn.execute(
        "SELECT id FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=409, detail="Short code already in use")

    created_at = datetime.utcnow().isoformat()
    expires_at = None
    if body.expires_in_days:
        expires_at = (datetime.utcnow() + timedelta(days=body.expires_in_days)).isoformat()

    conn.execute(
        "INSERT INTO urls (original_url, short_code, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (str(body.url), short_code, created_at, expires_at)
    )
    conn.commit()
    conn.close()

    base_url = str(request.base_url).rstrip("/")
    return ShortenResponse(
        short_code=short_code,
        short_url=f"{base_url}/{short_code}",
        original_url=str(body.url),
        expires_at=expires_at
    )


@app.get("/{short_code}", tags=["URL"])
def redirect_url(short_code: str):
    """Redirect to the original URL."""
    conn = get_db()
    row = conn.execute(
        "SELECT original_url, expires_at FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")

    if row["expires_at"] and datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        conn.close()
        raise HTTPException(status_code=410, detail="This URL has expired")

    conn.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = ?", (short_code,))
    conn.commit()
    conn.close()

    return RedirectResponse(url=row["original_url"])


@app.get("/stats/{short_code}", response_model=StatsResponse, tags=["Stats"])
def get_stats(short_code: str):
    """Get click statistics for a short URL."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM urls WHERE short_code = ?", (short_code,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return StatsResponse(
        short_code=row["short_code"],
        original_url=row["original_url"],
        clicks=row["clicks"],
        created_at=row["created_at"],
        expires_at=row["expires_at"]
    )


@app.get("/stats/", tags=["Stats"])
def list_all_urls():
    """List all shortened URLs with stats."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM urls ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.delete("/delete/{short_code}", tags=["URL"])
def delete_url(short_code: str):
    """Delete a short URL."""
    conn = get_db()
    result = conn.execute("DELETE FROM urls WHERE short_code = ?", (short_code,))
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Short URL not found")

    return {"message": f"Short URL '{short_code}' deleted successfully"}


@app.get("/", tags=["Health"])
def root():
    return {"message": "URL Shortener API is running!", "docs": "/docs"}
