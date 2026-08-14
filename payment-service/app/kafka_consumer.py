import json
import random

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.db import SessionLocal
from app.kafka_producer import publish_payment_result
from app.models import Payment, PaymentStatus


async def consume_order_events() -> None:
    consumer = AIOKafkaConsumer(
        settings.order_events_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="payment-service",
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            await _handle_order_event(event)
    finally:
        await consumer.stop()


async def _handle_order_event(event: dict) -> None:
    if event.get("eventType") != "OrderCreated":
        return

    order_id = event.get("orderId")
    if not order_id:
        return

    db = SessionLocal()
    try:
        existing = db.query(Payment).filter(Payment.order_id == order_id).first()
        if existing:
            return

        success = random.random() > settings.failure_rate
        status = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED

        payment = Payment(order_id=order_id, status=status)
        db.add(payment)
        db.commit()
    finally:
        db.close()

    await publish_payment_result(order_id, success)