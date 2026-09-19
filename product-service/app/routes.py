import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.cache import redis_client
from app.config import settings
from app.db import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductOut
from app.sentinel_logger import log_event

router = APIRouter()


def _cache_key(product_id: str) -> str:
    return f"product:{product_id}"


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    log_event("INFO", "PRODUCT_CREATED", f"Product created: {product.name}", metadata={"product_id": str(product.id)})
    return product


@router.get("/products/search", response_model=list[ProductOut])
def search_products(q: str = "", category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Product)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(Product.category == category)
    return query.all()


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    key = _cache_key(str(product_id))
    cached = redis_client.get(key)
    if cached:
        log_event("INFO", "CACHE_HIT", f"Product cache hit: {product_id}", metadata={"product_id": str(product_id)})
        return json.loads(cached)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    out = ProductOut.model_validate(product)
    redis_client.setex(key, settings.cache_ttl_seconds, out.model_dump_json())
    log_event("INFO", "CACHE_MISS", f"Product cache miss: {product_id}", metadata={"product_id": str(product_id)})
    return out


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: uuid.UUID, payload: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)

    redis_client.delete(_cache_key(str(product_id)))
    log_event("INFO", "PRODUCT_UPDATED", f"Product updated: {product.name}", metadata={"product_id": str(product_id)})
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    redis_client.delete(_cache_key(str(product_id)))
    log_event("INFO", "PRODUCT_DELETED", f"Product deleted: {product_id}", metadata={"product_id": str(product_id)})
