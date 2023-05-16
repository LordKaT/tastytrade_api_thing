import asyncio
from lib.TTApi import *
from lib.TTConfig import *
from lib.TTOrder import *
from lib.TTWebsocket import *
from lib.DXFeed import *
from datetime import datetime, timedelta

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

print("Fetch dxFeed token")
if not ttapi.fetch_dxfeed_token():
    exit()

# print("Market Metrics")
# print(ttapi.market_metrics(["SPY", "AAPL", "/MES"]))

# print(ttapi.get_equity_options("AAPL"))
# print(ttapi.symbol_search("AAPL"))
# print(ttapi.get_instrument_options("AAPL  250620P00195000"))
# print(ttapi.get_public_watchlists())
# print("===")
# print(ttapi.get_instrument_equities("AAPL"))

print("Websocket")
tt_websocket = TTWebsocket(uri=ttapi.tt_wss, auth_token=ttapi.session_token)
tt_websocket.connect()

print("DXFeed")
tt_dxfeed = DXFeed(uri=ttapi.streamer_websocket_uri, auth_token=ttapi.streamer_token)

system_running = True
task_list = []


async def main():
    global system_running
    global task_list
    await tt_dxfeed.connect()

    # this isn't working as expected and need to investigate why
    from_time = datetime.utcnow() - timedelta(days=6)
    to_time = datetime.utcnow()
    # await tt_dxfeed.subscribe([DXEvent.CANDLE], ["AAPL{=1d}"], "10d", "1682917200000")
    # await tt_dxfeed.subscribe([DXEvent.QUOTE], ["SPY"])
    await tt_dxfeed.subscribe_time_series(
        "TSLA", from_time=1677628800000, to_time=1683331200000
    )
    while system_running:
        await tt_dxfeed.listen()
        if len(task_list) > 0:
            for task in task_list:
                if task["action"] == "subscribe":
                    await tt_dxfeed.subscribe(task["events"], task["symbols"])
                elif task["action"] == "disconnect":
                    await tt_dxfeed.disconnect()
                task_list.remove(task)


async_loop_main = asyncio.new_event_loop()


def start_loop(loop, routine):
    asyncio.run(routine())


async_thread_main = threading.Thread(target=start_loop, args=(async_loop_main, main))
async_thread_main.start()


while system_running:
    command = input("?").lower()
    match command:
        case "quit":
            tt_websocket.disconnect()
            task_list.append({"action": "disconnect"})
            system_running = False
        case "dxfeed subscribe test":
            task_list.append(
                {
                    "action": "subscribe",
                    "events": [DXEvent.SUMMARY],
                    "symbols": ["MPW"],
                }
            )
            task_list.append(
                {
                    "action": "subscribe",
                    "events": [DXEvent.QUOTE],
                    "symbols": ["DAL"],
                }
            )
        case "websocket connect":
            tt_websocket.send(
                action="connect",
                value=[ttapi.user_data["accounts"][0]["account"]["account-number"]],
            )
        case "websocket pws":
            tt_websocket.send(action="public-watchlists-subscribe")

print("logout")
if not ttapi.logout():
    exit()
