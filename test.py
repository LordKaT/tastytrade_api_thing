import asyncio, configparser, threading, time, websocket
from TTApi import DXEvent, TTApi
from TTOrder import *

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

system_running = True


async def dxfeed_client():
    global system_running
    print("Connect dxfeed websocket")
    await ttapi.connect_dxfeed()
    print("Add dxfeed subscriptions")
    await ttapi.add_dxfeed_sub(
        [
            DXEvent.GREEKS,
            DXEvent.QUOTE,
            DXEvent.TRADE,
            DXEvent.PROFILE,
            DXEvent.SUMMARY,
            DXEvent.THEORETICAL_PRICE,
        ],
        ["SPY", ".SPY230508P412"],
    )

    while system_running:
        await ttapi.listen_dxfeed()
        time.sleep(0.05)


async def dxfeed_close():
    await ttapi.close_dxfeed()


# order = TTOrder(TTTimeInForce.GTC, 0.25, TTPriceEffect.CREDIT, TTOrderType.LIMIT)
# option = TTOption('MPW', '230721', TTOptionSide.PUT, 6.00)
# order.add_leg(TTInstrumentType.EQUITY_OPTION, option.symbol, 1, TTLegAction.STO)
# option = TTOption('MPW', '230721', TTOptionSide.CALL, 5.00)
# order.add_leg(TTInstrumentType.EQUITY_OPTION, option.symbol, 1, TTLegAction.BTO)

# ttapi.simple_order(order)

print("Websocket stuff")
ws_url = "wss://streamer.cert.tastyworks.com"
# ws_url = 'wss://streamer.tastyworks.com'

body = {"auth-token": ttapi.session_token, "action": "", "value": ""}


def on_message(ws, message):
    print(f"wss get {message}")


def on_error(ws, error):
    print(f"wss error: {error}")


def on_close(ws, status_code, message):
    print(f"wss close: {status_code} {message}")


def on_open(ws):
    print(f"wss open")

    body["action"] = "heartbeat"
    body["value"] = ""
    ws.send(json.dumps(body))

    body["action"] = "public-watchlists-subscribe"
    body["value"] = ""
    ws.send(json.dumps(body))

    body["action"] = "connect"
    body["value"] = [f'{ttapi.user_data["accounts"][0]["account"]["account-number"]}']
    ws.send(json.dumps(body))


thread_stop = False
ws = websocket.WebSocketApp(
    ws_url,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
    on_open=on_open,
)


def tt_client():
    ws.run_forever()


def dx_client():
    asyncio.run(dxfeed_client())


def kill_dx_client():
    asyncio.run(dxfeed_close())


websocket_thread = threading.Thread(target=tt_client)
dxfeed_thread = threading.Thread(target=dx_client)

websocket_thread.start()
dxfeed_thread.start()

while system_running:
    command = input("?").lower()
    if command == "quit":
        system_running = False
        ws.close()
        kill_dx_client()

# websocket_thread.join()
# dxfeed_thread.join()

# asyncio.run(dxfeed_client())

print("logout")
if not ttapi.logout():
    exit()
