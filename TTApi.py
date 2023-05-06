import aiocometd, asyncio, json, requests
from aiocometd import ConnectionType, Client
from TTOrder import *
from DXAuthExtension import AuthExtension
from enum import Enum

CERT_URI = "https://api.cert.tastyworks.com"
PROD_URI = "https://api.tastyworks.com"

CERT_WSS = "wss://streamer.cert.tastyworks.com"
PROD_WSS = "wss://streamer.tastyworks.com"


class DXEvent(Enum):
    GREEKS = "Greeks"
    QUOTE = "Quote"
    TRADE = "Trade"
    PROFILE = "Profile"
    SUMMARY = "Summary"
    THEORETICAL_PRICE = "TheoPrice"


class TTApi:
    username: str = None
    password: str = None
    session_token: str = None
    remember_token: str = None
    streamer_token: str = None
    streamer_uri: str = None
    streamer_websocket_uri: str = None
    streamer_level: str = None
    dxfeed: any = None
    tt_uri: str = None
    wss_uri: str = None
    headers: dict = {}
    user_data: dict = {}

    dxstreamer: any = None

    def __init__(self, username, password) -> None:
        self.headers["Content-Type"] = "application/json"
        self.username = username
        self.password = password

    def __post(self, endpoint, body, headers):
        response = requests.post(
            self.tt_uri + endpoint, data=json.dumps(body), headers=headers
        )
        if response.status_code == 201:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None

    def __get(self, endpoint, body, headers):
        response = requests.get(
            self.tt_uri + endpoint, data=json.dumps(body), headers=headers
        )
        if response.status_code == 200:
            return response.json()
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None

    def __delete(self, endpoint, body, headers):
        response = requests.delete(
            self.tt_uri + endpoint, data=json.dumps(body), headers=headers
        )
        if response.status_code == 204:
            return response
        print(f"Error {response.status_code}")
        print(f"Endpoint: {endpoint}")
        print(f"Body: {body}")
        print(f"Headers: {headers}")
        print(f"Response: {response.text}")
        return None

    def login(self, mfa: str = "") -> bool:
        body = {"login": self.username, "password": self.password, "remember-me": True}

        if mfa != "":
            self.headers["X-Tastyworks-OTP"] = mfa
            self.tt_uri = PROD_URI
            self.wss_uri = PROD_WSS
        else:
            self.tt_uri = CERT_URI
            self.wss_uri = CERT_WSS

        response = self.__post("/sessions", body=body, headers=self.headers)
        if response is None:
            return False

        self.user_data = response["data"]["user"]
        self.session_token = response["data"]["session-token"]
        self.headers["Authorization"] = self.session_token

        if mfa != "":
            del self.headers["X-Tastyworks-OTP"]
        return True

    def fetch_dxfeed_token(self) -> bool:
        response = self.__get("/quote-streamer-tokens", body={}, headers=self.headers)
        if response is None:
            return False
        print(response["data"])
        self.streamer_token = response["data"]["token"]
        self.streamer_uri = response["data"]["streamer-url"]
        self.streamer_websocket_uri = f'{response["data"]["websocket-url"]}/cometd'
        self.streamer_level = response["data"]["level"]
        return True

    async def connect_dxfeed(self) -> bool:
        # !but why!
        aiocometd.client.DEFAULT_CONNECTION_TYPE = ConnectionType.WEBSOCKET
        auth_extension = AuthExtension(self.streamer_token)
        self.dxfeed = Client(
            url=self.streamer_websocket_uri,
            connection_types=ConnectionType.WEBSOCKET,
            auth=auth_extension,
            ssl=False,
        )
        await self.dxfeed.open()
        await self.dxfeed.subscribe("/service/data")
        await self.dxfeed.publish("/service/sub", {"reset": True})
        return True

    async def close_dxfeed(self) -> bool:
        await self.dxfeed.close()

    async def add_dxfeed_sub(
        self, events: list[DXEvent] = [], symbols: list[str] = []
    ) -> bool:
        print("Adding dxfeed subscription")
        print(events, symbols)
        for event in events:
            print(f"Subscribing to {event.value}: {symbols}")
            await self.dxfeed.publish("/service/sub", {"add": {event.value: symbols}})
        return True

    async def del_dxfeed_sub(
        self, events: list[DXEvent] = [], symbols: list[str] = []
    ) -> bool:
        for event in events:
            for symbol in symbols:
                await self.dxfeed.publish(
                    "/service/sub", {"remove": {event.value: symbol}}
                )
        return True

    async def listen_dxfeed(self) -> bool:
        async for msg in self.dxfeed:
            print(f"dxfeed get: {msg}")
        return True

    def logout(self) -> bool:
        response = self.__delete("/sessions", body={}, headers=self.headers)
        return True

    def validate(self) -> bool:
        response = self.__post("/sessions/validate", body={}, headers=self.headers)
        if response is None:
            return False
        self.user_data["external-id"] = response["data"]["external-id"]
        self.user_data["id"] = response["data"]["id"]
        return True

    def fetch_accounts(self) -> bool:
        response = self.__get("/customers/me/accounts", {}, self.headers)
        if response is None:
            return False
        self.user_data["accounts"] = []
        for account in response["data"]["items"]:
            self.user_data["accounts"].append(account)
        return True

    def get_equity_options(self, symbol) -> any:
        response = self.__get(
            f"/option-chains/{symbol}/nested", body={}, headers=self.headers
        )

    def simple_order(self, order: TTOrder = None) -> bool:
        if order is None:
            print(f"You need to supply an order.")
            return False

        response = self.__post(
            f'/accounts/{self.user_data["accounts"][0]["account"]["account-number"]}/orders/dry-run',
            body=order.build_order(),
            headers=self.headers,
        )

        if response is None:
            return False

        print(json.dumps(response))
        return True
