import threading
import uuid
from datetime import datetime, timezone

import httpx

SENTINEL_COLLECTOR_URL = "http://log-collector:8000/logs"
_SERVICE_NAME = "unset-service"


def init_logger(service_name: str) -> None:
    global _SERVICE_NAME
    _SERVICE_NAME = service_name


def _send_sync(event: dict) -> None:
    try:
        httpx.post(SENTINEL_COLLECTOR_URL, json=event, timeout=2.0)
    except Exception:
        # Logging must never break the application. Swallow failures silently.
        pass


def log_event(
    level: str,
    event_type: str,
    message: str,
    user_id: str | None = None,
    request_id: str | None = None,
    trace_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": _SERVICE_NAME,
        "environment": "development",
        "level": level,
        "eventType": event_type,
        "traceId": trace_id or str(uuid.uuid4()),
        "userId": user_id,
        "requestId": request_id,
        "message": message,
        "metadata": metadata or {},
    }
    # Fire-and-forget via a background thread — works whether called from a
    # sync route (no event loop present) or an async route (avoids blocking it).
    threading.Thread(target=_send_sync, args=(event,), daemon=True).start()