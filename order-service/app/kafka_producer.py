import json
import uuid
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer

from app.config import settings

_producer: AIOKafkaProducer | None = None


async def start_producer() -> None:
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    await _producer.start()


async def stop_producer() -> None:
    if _producer:
        await _producer.stop()


async def publish_order_created(order_id: str, user_id: str) -> None:
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": "OrderCreated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "orderId": order_id,
        "userId": user_id,
    }
    await _producer.send_and_wait(settings.order_events_topic, json.dumps(event).encode("utf-8"))