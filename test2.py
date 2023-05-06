import asyncio, configparser, threading, time, websocket
from TTApi import *
from TTOrder import *
from TTWebsocket import *

config = configparser.ConfigParser()
config.read("tt.config")

tt_username = config.get("Credentials", "username")
tt_password = config.get("Credentials", "password")

ttapi = TTApi(tt_username, tt_password)

print("Login")
mfa = input("MFA: ")
if not ttapi.login(mfa):
    exit()

print("Validate")
if not ttapi.validate():
    exit()

print("Fetch accounts")
if not ttapi.fetch_accounts():
    exit()

print("Fetch dxFeed token")
if not ttapi.fetch_dxfeed_token():
    exit()

# print(ttapi.get_equity_options("AAPL"))
print(ttapi.symbol_search("AAPL"))
print(ttapi.get_instrument_options("AAPL  250620P00195000"))
print(ttapi.get_public_watchlists())
print("===")
print(ttapi.get_instrument_equities("AAPL"))

system_running = True

print("Websocket")
tt_websocket = TTWebsocket(ttapi.is_prod, ttapi.session_token)
tt_websocket.connect()

while system_running:
    command = input("?").lower()
    match command:
        case "quit":
            tt_websocket.disconnect()
            system_running = False
        case "websocket connect":
            tt_websocket.send(
                action="connect",
                value=ttapi.user_data["accounts"][0]["account"]["account-number"],
            )
        case "websocket pws":
            tt_websocket.send(action="public-watchlists-subscribe")


print("logout")
if not ttapi.logout():
    exit()
