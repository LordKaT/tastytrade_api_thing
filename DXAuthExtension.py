from typing import Optional
import aiocometd
from aiocometd.constants import MetaChannel
from aiocometd.typing import Payload, Headers


class AuthExtension(aiocometd.AuthExtension):
    def __init__(self, token: str = "") -> None:
        self.token = token

    async def outgoing(self, payload: Payload = None, headers: Headers = None):
        for load in payload:
            if load["channel"] == MetaChannel.CONNECT:
                print("metachannel connect")
                print(load)
            if load["channel"] == MetaChannel.HANDSHAKE:
                print("metachannel handshake")
                load.update({"ext": {"com.devexperts.auth.AuthToken": self.token}})
                print(load)

    async def incoming(self, payload: Payload = None, headers: Headers | None = None):
        pass
        # return await super().incoming(payload, headers)

    async def authenticate(self) -> None:
        pass
        # return super().authenticate()
