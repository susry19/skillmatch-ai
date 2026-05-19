from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://skillmatch:password@localhost:5432/skillmatch"

    # Auth
    SECRET_KEY: str = "change-this-secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # AI
    GEMINI_API_KEY: Optional[str] = None

    # Email
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@skillmatch.ai"
    MAIL_FROM_NAME: str = "SkillMatch AI"
    MAIL_SERVER: str = "smtp.sendgrid.net"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # App
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
