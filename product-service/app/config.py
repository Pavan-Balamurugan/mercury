from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mercury:mercury@postgres:5432/mercury"
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()