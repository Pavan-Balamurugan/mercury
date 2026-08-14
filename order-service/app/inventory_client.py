import httpx

from app.config import settings


class InsufficientStockError(Exception):
    pass


def reserve_items(items: list[dict]) -> None:
    """Reserve stock for each item synchronously. Rolls back any already-reserved
    items if one fails, then raises InsufficientStockError."""
    reserved_so_far: list[dict] = []

    with httpx.Client(base_url=settings.inventory_service_url, timeout=5.0) as client:
        for item in items:
            resp = client.post(
                "/inventory/reserve",
                json={"product_id": str(item["product_id"]), "quantity": item["quantity"]},
            )
            if resp.status_code == 409:
                _release(client, reserved_so_far)
                raise InsufficientStockError(f"Insufficient stock for {item['product_id']}")
            resp.raise_for_status()
            reserved_so_far.append(item)


def _release(client: httpx.Client, items: list[dict]) -> None:
    for item in items:
        client.post(
            "/inventory/release",
            json={"product_id": str(item["product_id"]), "quantity": item["quantity"]},
        )


def release_items(items: list[dict]) -> None:
    with httpx.Client(base_url=settings.inventory_service_url, timeout=5.0) as client:
        _release(client, items)