from pathlib import Path
from urllib.parse import quote_plus

from dotenv import dotenv_values
from pydantic_settings import BaseSettings


ROOT_DIR = Path(__file__).resolve().parents[2]

env = dotenv_values(ROOT_DIR / ".env")


class Settings(BaseSettings):

    postgres_host: str = (
        env.get("POSTGRES_HOST")
        or "localhost"
    )

    postgres_port: int = int(
        env.get("POSTGRES_PORT")
        or 5432
    )

    postgres_db: str = (
        env.get("POSTGRES_DB")
        or "employee_assistant"
    )

    postgres_user: str = (
        env.get("POSTGRES_USER")
        or "employee_assistant"
    )

    postgres_password: str = (
        env.get("POSTGRES_PASSWORD")
        or ""
    )

    database_url: str | None = (
        env.get("DATABASE_URL")
        or None
    )

    api_host: str = (
        env.get("API_HOST")
        or "0.0.0.0"
    )

    api_port: int = int(
        env.get("API_PORT")
        or 8000
    )

    admin_initial_password: str | None = env.get("ADMIN_INITIAL_PASSWORD") or None
    admin_session_hours: int = int(env.get("ADMIN_SESSION_HOURS") or 12)
    auth_cookie_secure: bool = (env.get("AUTH_COOKIE_SECURE") or "false").lower() in {"1", "true", "yes"}

    @property
    def sqlalchemy_url(self) -> str:

        if self.database_url:
            return self.database_url

        encoded_user = quote_plus(self.postgres_user)
        encoded_password = quote_plus(self.postgres_password)

        return (
            f"postgresql+psycopg://"
            f"{encoded_user}:{encoded_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )


settings = Settings()
