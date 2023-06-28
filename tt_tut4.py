import asyncio
from lib.TTApi import *
from lib.TTConfig import *
from lib.TTOrder import *
from lib.TTWebsocket import *
from lib.DXFeed import *
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

print("Fetch dxFeed token")
if not ttapi.fetch_dxfeed_token():
    exit()

# print("Market Metrics")
# print(ttapi.market_metrics(["SPY", "AAPL", "/MES"]))

# print("Option chains")
# with open("out3.json", "a") as f:
#    f.write(json.dumps(ttapi.option_chains("MSFT")))
# f.write(json.dumps(ttapi.get_instrument_options("MSFT")))

# print(ttapi.option_chains("MSFT"))
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

data_feed = {"MSFT": {}}


data_feed["MSFT"]["option_chains"] = ttapi.option_chains("MSFT")["data"]["items"][0]
expirations = data_feed["MSFT"]["option_chains"]["expirations"]

for ex in expirations:
    if ex["expiration-type"] == "Regular":
        if ex["days-to-expiration"] < 21:
            continue
        data_feed["MSFT"]["current_expiration"] = ex
        break

data_feed["MSFT"]["price"] = None
data_feed["MSFT"]["atm_put"] = None
data_feed["MSFT"]["atm_put_spread"] = None
data_feed["MSFT"]["atm_put_streamer"] = None
data_feed["MSFT"]["atm_call"] = None
data_feed["MSFT"]["atm_call_spread"] = None
data_feed["MSFT"]["atm_call_streamer"] = None
data_feed["MSFT"]["put_oi"] = None
data_feed["MSFT"]["call_oi"] = None
data_feed["MSFT"]["put_vol"] = None
data_feed["MSFT"]["call_vol"] = None


async def main():
    global system_running, task_list
    global data_feed

    await tt_dxfeed.connect()

    await tt_dxfeed.subscribe([DXEvent.SUMMARY, DXEvent.TRADE], ["MSFT"])

    while system_running:
        if len(task_list) > 0:
            for task in task_list:
                if task["action"] == "subscribe":
                    await tt_dxfeed.subscribe(task["events"], task["symbols"])
                elif task["action"] == "disconnect":
                    await tt_dxfeed.disconnect()
                task_list.remove(task)

        dx_data = await tt_dxfeed.listen()
        if dx_data is True: # no data
          continue

        match dx_data[0]:
          case DXEvent.SUMMARY:
            #print(f"Summary Data: {dx_data[1]}")
            pass
          case DXEvent.TRADE:
            #print(f"Trade Data: {dx_data[1]}")
            if dx_data[1][0] not in data_feed:
              data_feed[dx_data[1][0]] = {}
            symbol_data = data_feed[dx_data[1][0]]
            symbol_data["price"] = dx_data[1][6]
            put_streamer = None
            call_streamer = None

            if "current_expiration" not in symbol_data: # tracking an options chain
              continue

            for strike in symbol_data["current_expiration"]["strikes"]:
                if (float(strike["strike-price"]) <= symbol_data["price"]):
                    symbol_data["atm_put"] = float(strike["strike-price"])
                    put_streamer = strike["put-streamer-symbol"]
                elif (float(strike["strike-price"]) > symbol_data["price"]):
                    symbol_data["atm_call"] = float(strike["strike-price"])
                    call_streamer = strike["call-streamer-symbol"]
                    break

            if symbol_data["atm_put_streamer"] is None and put_streamer is not None:
              await tt_dxfeed.data([DXEvent.QUOTE], [put_streamer])
              await tt_dxfeed.subscribe([DXEvent.QUOTE, DXEvent.GREEKS], [put_streamer])
              symbol_data["atm_put_streamer"] = put_streamer

            elif symbol_data["atm_put_streamer"] != put_streamer:
              await tt_dxfeed.unsubscribe([DXEvent.QUOTE, DXEvent.GREEKS], [symbol_data["atm_put_streamer"]])
              await tt_dxfeed.subscribe([DXEvent.QUOTE, DXEvent.GREEKS], [put_streamer])
              symbol_data["atm_put_streamer"] = put_streamer

            if symbol_data["atm_call_streamer"] is None and call_streamer is not None:
              await tt_dxfeed.data([DXEvent.QUOTE, DXEvent.GREEKS], [call_streamer])
              await tt_dxfeed.subscribe([DXEvent.QUOTE, DXEvent.GREEKS], [call_streamer])
              symbol_data["atm_call_streamer"] = call_streamer

            elif symbol_data["atm_call_streamer"] != call_streamer:
              await tt_dxfeed.unsubscribe([DXEvent.QUOTE, DXEvent.GREEKS], [symbol_data["atm_call_streamer"]])
              await tt_dxfeed.subscribe([DXEvent.QUOTE, DXEvent.GREEKS], [call_streamer])
              symbol_data["atm_call_streamer"] = call_streamer
          case DXEvent.QUOTE:
            #print(f"Quote Data: {dx_data[1]}")
            if dx_data[1][0] not in data_feed:
              data_feed[dx_data[1][0]] = {}
            symbol_data = data_feed[dx_data[1][0]]
            symbol_data["bid_price"] = dx_data[1][6]
            symbol_data["ask_price"] = dx_data[1][10]
            symbol_data["spread"] = Decimal(str(dx_data[1][10])) - Decimal(str(dx_data[1][6]))
            print(dx_data[1][0], symbol_data["bid_price"], symbol_data["ask_price"], symbol_data["spread"])
          case DXEvent.GREEKS:
            #print(f"Greeks Data: {dx_data[1]}")
            pass
          case _:
            pass

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
                action="account-subscribe",
                value=[ttapi.user_data["accounts"][0]["account-number"]],
            )
        case "websocket pws":
            tt_websocket.send(action="public-watchlists-subscribe")
        case "spread":
            if "spread" in data_feed["MSFT"]:
              print(f"Spread: {data_feed['MSFT']['spread']}")

print("logout")
if not ttapi.logout():
    exit()
