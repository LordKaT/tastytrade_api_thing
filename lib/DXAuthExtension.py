import aiocometd
from aiocometd.constants import MetaChannel
from aiocometd.typing import Payload, Headers


class DXAuthExtension(aiocometd.AuthExtension):
    def __init__(self, token: str = "") -> None:
        self.token = token

    async def outgoing(self, payload: Payload = None, headers: Headers = None):
        for load in payload:
            if load["channel"] == MetaChannel.CONNECT:
                continue
            if load["channel"] == MetaChannel.HANDSHAKE:
                load.update({"ext": {"com.devexperts.auth.AuthToken": self.token}})

    async def incoming(self, payload: Payload = None, headers: Headers = None):
        pass

    async def authenticate(self) -> None:
        pass
