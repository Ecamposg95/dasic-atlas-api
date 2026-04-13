import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and not url.startswith("postgresql+psycopg://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    token_cookie_name: str
    cookie_secure: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL no está configurada.")

    secret_key = os.getenv("SECRET_KEY", "").strip()
    if not secret_key:
        raise RuntimeError("SECRET_KEY no está configurada.")

    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    token_cookie_name = os.getenv("TOKEN_COOKIE_NAME", "access_token").strip() or "access_token"
    cookie_secure = _as_bool(os.getenv("COOKIE_SECURE", "false"), default=False)

    return Settings(
        database_url=normalize_database_url(database_url),
        secret_key=secret_key,
        access_token_expire_minutes=access_token_expire_minutes,
        token_cookie_name=token_cookie_name,
        cookie_secure=cookie_secure,
    )
