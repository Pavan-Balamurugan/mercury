import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Inventory
from app.schemas import InventoryOut, ReleaseRequest, ReserveRequest, StockSet

router = APIRouter()


@router.put("/inventory/{product_id}", response_model=InventoryOut)
def set_stock(product_id: uuid.UUID, payload: StockSet, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        inv = Inventory(product_id=product_id, available_qty=payload.available_qty, reserved_qty=0)
        db.add(inv)
    else:
        inv.available_qty = payload.available_qty
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/inventory/{product_id}", response_model=InventoryOut)
def get_stock(product_id: uuid.UUID, db: Session = Depends(get_db)):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="No inventory record for product")
    return inv


@router.post("/inventory/reserve", response_model=InventoryOut)
def reserve_stock(payload: ReserveRequest, db: Session = Depends(get_db)):
    inv = (
        db.query(Inventory)
        .filter(Inventory.product_id == payload.product_id)
        .with_for_update()
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="No inventory record for product")

    if inv.available_qty < payload.quantity:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Insufficient stock")

    inv.available_qty -= payload.quantity
    inv.reserved_qty += payload.quantity
    db.commit()
    db.refresh(inv)
    return inv


@router.post("/inventory/release", response_model=InventoryOut)
def release_stock(payload: ReleaseRequest, db: Session = Depends(get_db)):
    inv = (
        db.query(Inventory)
        .filter(Inventory.product_id == payload.product_id)
        .with_for_update()
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="No inventory record for product")

    release_qty = min(payload.quantity, inv.reserved_qty)
    inv.reserved_qty -= release_qty
    inv.available_qty += release_qty
    db.commit()
    db.refresh(inv)
    return inv