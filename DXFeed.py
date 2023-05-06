import aiocometd, asyncio, json, requests
from aiocometd import ConnectionType, Client
from TTOrder import *
from DXAuthExtension import AuthExtension
from enum import Enum


class DXEvent(Enum):
    GREEKS = "Greeks"
    QUOTE = "Quote"
    TRADE = "Trade"
    PROFILE = "Profile"
    SUMMARY = "Summary"
    THEORETICAL_PRICE = "TheoPrice"


class DXService(Enum):
    DATA = "/service/data"
    SUB = "/service/sub"


class DXFeed:
    uri: str = None
    auth_token: str = None
    streamer: any = None

    def __init__(self, uri: str = None, auth_token: str = None) -> None:
        self.uri = uri
        self.auth_token = auth_token

    async def connect(self) -> bool:
        aiocometd.client.DEFAULT_CONNECTION_TYPE = ConnectionType.WEBSOCKET
        self.streamer = Client(
            url=self.uri,
            connection_types=ConnectionType.WEBSOCKET,
            auth=AuthExtension(self.auth_token),
        )

        await self.streamer.open()
        await self.streamer.subscribe(DXService.DATA)
        await self.streamer.publish(DXService.SUB, {"reset": True})

    async def disconnect(self) -> bool:
        await self.streamer.close()

    async def subscribe(
        self, events: list[DXEvent] = [], symbols: list[str] = []
    ) -> bool:
        for event in events:
            print(f"Subscribing to {event.value}: {symbols}")
            await self.streamer.publish(DXService.SUB, {"add": {event.value: symbols}})
        return True

    async def unsubscribe(
        self, events: list[DXEvent] = [], symbols: list[str] = []
    ) -> bool:
        for event in events:
            print(f"Ubsubscribing from {event.value}: {symbols}")
            await self.streamer.publish(
                DXService.SUB, {"remove": {event.value: symbols}}
            )
        return True

    async def listen(self) -> bool:
        async for msg in self.streamer:
            print(f"dxfeed get {msg}")
        return True
