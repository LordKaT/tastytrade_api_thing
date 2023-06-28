import aiocometd, asyncio
from aiocometd import ConnectionType, Client
from lib.TTOrder import *
from lib.DXAuthExtension import DXAuthExtension
from enum import Enum


class DXAction(str, Enum):
    ADD = "add"
    ADD_TIME_SERIES = "addTimeSeries"


class DXEvent(str, Enum):
    TRADE = "Trade"
    QUOTE = "Quote"
    SUMMARY = "Summary"
    PROFILE = "Profile"
    ORDER = "Order"
    TIME_AND_SALE = "TimeAndSale"
    CANDLE = "Candle"
    TRADE_ETH = "TradETH"
    SPREAD_ORDER = "SpreadOrder"
    GREEKS = "Greeks"
    THEORETICAL_PRICE = "TheoPrice"
    UNDERLYING = "Underlying"
    SERIES = "Series"
    CONFIGURATION = "Configuration"


class DXService(str, Enum):
    DATA = "/service/data"
    SUBSCRIBE = "/service/sub"


class DXFeed:
    uri: str = None
    auth_token: str = None
    streamer: any = None
    active: bool = False

    def __init__(self, uri: str = None, auth_token: str = None) -> None:
        self.uri = uri
        self.auth_token = auth_token

    async def connect(self) -> bool:
        aiocometd.client.DEFAULT_CONNECTION_TYPE = ConnectionType.WEBSOCKET
        self.streamer = Client(
            url=self.uri,
            connection_types=ConnectionType.WEBSOCKET,
            auth=DXAuthExtension(self.auth_token),
        )

        await self.streamer.open()
        await self.streamer.subscribe(DXService.DATA.value)
        await self.streamer.publish(DXService.SUBSCRIBE.value, {"reset": True})

        self.active = True

    async def disconnect(self) -> bool:
        self.active = False
        await self.streamer.close()

    async def data(
        self,
        events: list[DXEvent] = [],
        symbols: list[str] = [],
    ) -> bool:
        for event in events:
            print(f"Data for {event.value}: {symbols}")
            body = {}
            body[event.value] = symbols
            await self.streamer.publish(
                DXService.DATA.value,
                {DXAction.ADD: {event.value: symbols}},
            )
        return True

    async def subscribe(
        self,
        events: list[DXEvent] = [],
        symbols: list[str] = [],
    ) -> bool:
        for event in events:
            print(f"Subscribing to {event.value}: {symbols}")
            body = {}
            body[event.value] = symbols
            await self.streamer.publish(
                DXService.SUBSCRIBE.value,
                {DXAction.ADD: {event.value: symbols}},
            )
        return True

    async def subscribe_time_series(
        self, symbol: str = None, from_time: int = None, to_time: int = None
    ) -> bool:
        body = {}
        body[DXEvent.CANDLE.value] = [
            {
                "eventSymbol": symbol,
                "fromTime": from_time,
                "toTime": to_time,
            }
        ]
        print({DXAction.ADD_TIME_SERIES.value: body})
        await self.streamer.publish(
            DXService.SUBSCRIBE.value, {DXAction.ADD_TIME_SERIES.value: body}
        )
        return True

    async def unsubscribe(
        self, events: list[DXEvent] = [], symbols: list[str] = []
    ) -> bool:
        for event in events:
            print(f"Unsubscribing from {event.value}: {symbols}")
            await self.streamer.publish(
                DXService.SUBSCRIBE, {"remove": {event.value: symbols}}
            )
        return True

    async def listen(self) -> bool:
        try:
            async with asyncio.timeout(0.1):
                async for msg in self.streamer:
                    if msg["channel"] != DXService.DATA:
                        print(f"dxfeed other {msg}")
                        continue
                    return msg["data"]
                    # print(f"dxfeed get {msg}")
                return True
        except asyncio.TimeoutError:
            return True
