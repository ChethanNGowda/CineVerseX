import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _resolve_database_uri():
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if database_url and database_url != "postgresql://:@localhost:5432/cineversex":
        return database_url

    return f"sqlite:///{(BASE_DIR / 'cineversex.db').as_posix()}"

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cineversex_secret_2026")
    IMDB_DB_PATH = os.environ.get("IMDB_DB_PATH", "")

    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()

    SQLALCHEMY_TRACK_MODIFICATIONS = False
