from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .consumers import HOSPITAL_GROUP


def broadcast(event_type, data):
    """Send a live update to every open MedTwin screen."""
    async_to_sync(get_channel_layer().group_send)(
        HOSPITAL_GROUP,
        {"type": "hospital.event", "message": {"type": event_type, "data": data}},
    )
