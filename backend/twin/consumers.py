from channels.generic.websocket import AsyncJsonWebsocketConsumer

HOSPITAL_GROUP = "hospital"


class HospitalConsumer(AsyncJsonWebsocketConsumer):
    """One open MedTwin screen. Receives every live hospital update."""

    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        await self.channel_layer.group_add(HOSPITAL_GROUP, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(HOSPITAL_GROUP, self.channel_name)

    async def hospital_event(self, event):
        await self.send_json(event["message"])
