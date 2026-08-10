from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mercury:mercury@postgres:5432/mercury"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()