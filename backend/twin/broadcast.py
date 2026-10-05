import asyncio
import json
import threading
from contextlib import contextmanager

from asgiref.sync import async_to_sync
from channels.layers import InMemoryChannelLayer, get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from .consumers import HOSPITAL_GROUP

_muted = False
_loop = None
_loop_lock = threading.Lock()


@contextmanager
def muted():
    """Inside a `with muted():` block, nothing is broadcast. Used when generating history."""
    global _muted
    previous = _muted
    _muted = True
    try:
        yield
    finally:
        _muted = previous


def _background_loop():
    """One long-lived event loop per program, so the Redis connection is opened once and reused."""
    global _loop
    with _loop_lock:
        if _loop is None:
            _loop = asyncio.new_event_loop()
            threading.Thread(target=_loop.run_forever, daemon=True, name="broadcast").start()
    return _loop


def _send(message):
    layer = get_channel_layer()
    event = {"type": "hospital.event", "message": message}
    if isinstance(layer, InMemoryChannelLayer):
        # Tests: the in-memory post office lives inside the test itself.
        async_to_sync(layer.group_send)(HOSPITAL_GROUP, event)
    else:
        future = asyncio.run_coroutine_threadsafe(layer.group_send(HOSPITAL_GROUP, event), _background_loop())
        future.result(timeout=5)


def broadcast(event_type, data):
    """Send a live update to every open MedTwin screen, once the current save has succeeded."""
    if _muted:
        return
    message = {"type": event_type, "data": json.loads(json.dumps(data, cls=DjangoJSONEncoder))}
    transaction.on_commit(lambda: _send(message), robust=True)
