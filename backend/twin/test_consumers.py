from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from config.asgi import application

from .broadcast import broadcast

ORIGIN = [(b"origin", b"http://localhost")]


class HospitalChannelTests(TransactionTestCase):
    def setUp(self):
        nurse = User.objects.create_user(username="nurse1", password="x", role=User.Role.NURSE)
        self.token = str(AccessToken.for_user(nurse))

    def connect_to(self, token=None):
        path = "/ws/hospital/" + (f"?token={token}" if token else "")
        return WebsocketCommunicator(application, path, headers=ORIGIN)

    async def test_logged_in_user_receives_broadcasts(self):
        communicator = self.connect_to(self.token)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await sync_to_async(broadcast)("test", {"message": "hello"})
        self.assertEqual(
            await communicator.receive_json_from(),
            {"type": "test", "data": {"message": "hello"}},
        )
        await communicator.disconnect()

    async def test_connection_without_token_is_refused(self):
        connected, _ = await self.connect_to().connect()
        self.assertFalse(connected)

    async def test_connection_with_bad_token_is_refused(self):
        connected, _ = await self.connect_to("not-a-real-token").connect()
        self.assertFalse(connected)
