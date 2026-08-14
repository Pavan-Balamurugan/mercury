from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mercury:mercury@postgres:5432/mercury"
    kafka_bootstrap_servers: str = "kafka:9092"
    order_events_topic: str = "order-events"
    payment_events_topic: str = "payment-events"
    failure_rate: float = 0.2

    class Config:
        env_file = ".env"


settings = Settings()