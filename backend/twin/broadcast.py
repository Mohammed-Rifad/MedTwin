import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from contextlib import contextmanager
from .consumers import HOSPITAL_GROUP


def _send(message):
    async_to_sync(get_channel_layer().group_send)(
        HOSPITAL_GROUP, {"type": "hospital.event", "message": message}
    )



_muted = False


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


def broadcast(event_type, data):
    """Send a live update to every open MedTwin screen, once the current save has succeeded."""
    if _muted:
        return
    message = {"type": event_type, "data": json.loads(json.dumps(data, cls=DjangoJSONEncoder))}
    transaction.on_commit(lambda: _send(message), robust=True)
