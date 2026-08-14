from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mercury:mercury@postgres:5432/mercury"
    kafka_bootstrap_servers: str = "kafka:9092"
    inventory_service_url: str = "http://inventory-service:8000"
    order_events_topic: str = "order-events"
    payment_events_topic: str = "payment-events"

    class Config:
        env_file = ".env"


settings = Settings()