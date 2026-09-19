import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.inventory_client import InsufficientStockError, reserve_items
from app.kafka_producer import publish_order_created
from app.models import Order, OrderItem, OrderStatus
from app.schemas import OrderCreate, OrderOut
from app.sentinel_logger import log_event

router = APIRouter()


@router.post("/orders", response_model=OrderOut)
async def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    order = Order(user_id=payload.user_id, status=OrderStatus.PENDING)
    db.add(order)
    db.flush()

    for item in payload.items:
        db.add(OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity))
    db.commit()
    db.refresh(order)
    log_event(
        "INFO", "ORDER_CREATED", f"Order {order.id} created",
        user_id=str(order.user_id), metadata={"order_id": str(order.id)},
    )

    try:
        reserve_items([{"product_id": i.product_id, "quantity": i.quantity} for i in payload.items])
    except InsufficientStockError:
        order.status = OrderStatus.FAILED
        db.commit()
        db.refresh(order)
        log_event(
            "ERROR", "ORDER_FAILURE", f"Order {order.id} failed — inventory conflict",
            user_id=str(order.user_id), metadata={"order_id": str(order.id)},
        )
        return order

    order.status = OrderStatus.PAYMENT_PENDING
    db.commit()
    db.refresh(order)

    await publish_order_created(str(order.id), str(order.user_id))
    log_event(
        "INFO", "ORDER_PAYMENT_PENDING", f"Order {order.id} reserved, awaiting payment",
        user_id=str(order.user_id), metadata={"order_id": str(order.id)},
    )

    return order


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order