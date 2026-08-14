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


async def publish_payment_result(order_id: str, success: bool) -> None:
    event = {
        "eventId": str(uuid.uuid4()),
        "eventType": "PaymentCompleted" if success else "PaymentFailed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "orderId": order_id,
    }
    await _producer.send_and_wait(settings.payment_events_topic, json.dumps(event).encode("utf-8"))