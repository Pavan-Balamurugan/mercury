import json

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.db import SessionLocal
from app.inventory_client import release_items
from app.models import Order, OrderItem, OrderStatus
from app.sentinel_logger import log_event


async def consume_payment_events() -> None:
    consumer = AIOKafkaConsumer(
        settings.payment_events_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="order-service",
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode("utf-8"))
            await _handle_payment_event(event)
    finally:
        await consumer.stop()


async def _handle_payment_event(event: dict) -> None:
    order_id = event.get("orderId")
    event_type = event.get("eventType")
    if not order_id or event_type not in ("PaymentCompleted", "PaymentFailed"):
        return

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.PAYMENT_PENDING:
            return

        if event_type == "PaymentCompleted":
            order.status = OrderStatus.CONFIRMED
            db.commit()
            log_event(
                "INFO", "ORDER_CONFIRMED", f"Order {order_id} confirmed",
                user_id=str(order.user_id), metadata={"order_id": str(order_id)},
            )
        else:
            order.status = OrderStatus.PAYMENT_FAILED
            db.commit()
            items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            release_items([{"product_id": i.product_id, "quantity": i.quantity} for i in items])
            log_event(
                "ERROR", "PAYMENT_FAILED", f"Order {order_id} payment failed, stock released",
                user_id=str(order.user_id), metadata={"order_id": str(order_id)},
            )
    finally:
        db.close()