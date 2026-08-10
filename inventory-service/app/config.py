from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mercury:mercury@postgres:5432/mercury"

    class Config:
        env_file = ".env"


settings = Settings()