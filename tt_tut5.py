import asyncio
from lib.TTApi import *
from lib.TTConfig import *
from lib.TTOrder import *
from lib.TTWebsocket import *
from lib.DXFeed import *
from lib.DXLink import *
from datetime import datetime, timedelta
from decimal import Decimal

ttapi = TTApi()

print("Login")
if not ttapi.login():
    exit()

print("Validate")
if not ttapi.validate():
    exit()

print("Fetch accounts")
if not ttapi.fetch_accounts():
    exit()

print("Get quote tokens")
if not ttapi.get_quote_tokens():
    exit()

# print("Get Options Chain")
# print(ttapi.option_chains("PYPL"))
# exit()

print("Websocket")
tt_websocket = TTWebsocket(uri=ttapi.tt_wss, auth_token=ttapi.session_token)
tt_websocket.connect()

print("DXLink")
tt_dxlink = DXLink(uri=ttapi.streamer_websocket_uri, auth_token=ttapi.streamer_token)

system_running = True

while system_running:
    command = input("?").lower()
    match command:
        case "quit":
            tt_websocket.disconnect()
            tt_dxlink.disconnect()
            system_running = False
        case "dxlink test":
            tt_dxlink.send(
                {
                    "type": "FEED_SUBSCRIPTION",
                    "channel": 1,
                    "add": [
                        {
                            "symbol": "PYPL",  # ".PYPL230915P70",
                            "type": "Quote",
                        }
                    ],
                }
            )
        case "websocket connect":
            tt_websocket.send(
                action="account-subscribe",
                value=[ttapi.user_data["accounts"][0]["account-number"]],
            )
        case "websocket pws":
            tt_websocket.send(action="public-watchlists-subscribe")

print("logout")
if not ttapi.logout():
    exit()
