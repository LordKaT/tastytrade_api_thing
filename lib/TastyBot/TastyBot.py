import discord, time
from datetime import datetime, timedelta
from discord.ext import commands
from lib.TTApi import *
from lib.TTConfig import *
from lib.TastyBot.TBConfig import *
from lib.TastyBot.TastyCommands import *


class TastyBot(commands.Bot):
    tbconfig: TBConfig = TBConfig()
    ttapi: TTApi = None

    watchlist: any = None
    metrics: list = []
    fetch_symbols: dict = {}
    symbols: dict = {}
    alertlist: dict = {}
    alert_message: str = ""
    alert_message_header: str = ""
    alert_message_footer: str = ""
    last_alert: any = None

    def __init__(self, ttapi: TTApi = None) -> None:
        self.ttapi = ttapi
        self.alert_message_header = "```ansi\n\u001b[1;30mIVR Alert List\u001b[0m\n"
        self.alert_message_header += "  Status    Symbol  IVR Change  Liquidity\n"
        self.alert_message_footer = "```"

        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="!", intents=intents)
        self.run(self.tbconfig.discord_token)

    async def send(self, msg: str = "") -> None:
        await self.get_channel(self.tbconfig.discord_channel).send(msg)

    async def debug(self, msg: str = "") -> None:
        await self.get_channel(self.tbconfig.discord_debug_channel).send(msg)

    async def on_ready(self):
        print(f"{self.user.name} connected.")
        self.tasty_cog = TastyCommands(self)
        await self.add_cog(self.tasty_cog)
        self.tasty_cog.start_tasks()

    async def on_error(self, event, *args, **kwargs):
        print(f"Unhandled error")
        print(args[0])

    async def fetch_watchlist(self):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Fetching watchlist {now}... ", end="", flush=True)
        self.watchlist = self.ttapi.get_watchlists(self.tbconfig.watchlist)
        self.metrics = {"data": {"items": []}}
        metrics_list = []
        for entry in self.watchlist["data"]["watchlist-entries"]:
            self.fetch_symbols[entry["symbol"]] = entry
            metrics_list.append(entry["symbol"])
        for i in range(0, len(metrics_list), 10):
            metric = []
            for j in range(i, i + 10):
                if j < len(metrics_list):
                    metric.append(metrics_list[j])
            mm = self.ttapi.market_metrics(metric)["data"]["items"]
            self.metrics["data"]["items"].extend(mm)
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Fetch complete {now}", flush=True)

    async def update_watchlist(self):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Updating watchlist {now}... ", end="", flush=True)
        for item in self.metrics["data"]["items"]:
            symbol = item["symbol"]

            if symbol == "VIX" or symbol == "/VX" or symbol == "VIX1D":
                continue

            data = self.fetch_symbols[symbol]

            instrument_type = (
                data["instrument-type"] if "instrument-type" in data else "None"
            )

            ivr = (
                round(float(item["implied-volatility-index-rank"]) * 100.00, 2)
                if "implied-volatility-index-rank" in item
                else 0.00
            )
            ivr_5day = (
                round(float(item["implied-volatility-index-5-day-change"]) * 100.00, 2)
                if "implied-volatility-index-5-day-change" in item
                else 0.00
            )
            ivr_index = (
                round(float(item["implied-volatility-index"]) * 100.00, 2)
                if "implied-volatility-index" in item
                else 0.00
            )
            liquidity = (
                round(float(item["liquidity-rank"]), 2)
                if "liquidity-rank" in item
                else 0.00
            )

            now = datetime.now().time()
            target = datetime.strptime("09:30", "%H:%M").time()

            prev_ivr_open = (
                self.symbols[symbol]["ivr_open"] if symbol in self.symbols else ivr
            )

            self.symbols[symbol] = {
                "type": instrument_type,
                "ivr": ivr,
                "ivr_index": ivr_index,
                "ivr_5day": ivr_5day,
                "ivr_open": ivr if now <= target else prev_ivr_open,
                "liquidity": liquidity,
            }
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Update complete {now}", flush=True)

    async def update_alertlist(self):
        for symbol, data in self.symbols.items():
            status = ""
            if data["ivr"] >= self.tbconfig.ivr_extreme:
                status = "Extreme"
            elif data["ivr"] >= self.tbconfig.ivr_tasty:
                status = "Tasty"
            elif data["ivr"] >= self.tbconfig.ivr_elevated:
                status = "Elevated"
            else:
                if symbol in self.alertlist:
                    del self.alertlist[symbol]
                continue
            new = False if symbol in self.alertlist else True
            self.alertlist[symbol] = {
                "prev_ivr": (
                    self.alertlist[symbol]["ivr"] if symbol in self.alertlist else None
                ),
                "ivr": data["ivr"],
                "ivr_open": data["ivr_open"],
                "liquidity": data["liquidity"],
                "prev_status": (
                    self.alertlist[symbol]["status"] if symbol in self.alertlist else ""
                ),
                "status": status,
                "new": new,
            }

    async def update_alerts(self, only_new: bool = False):
        self.alert_messages = []
        keys = list(self.alertlist.keys())
        for i in range(0, len(keys), 5):
            ivr_symbol = "•"
            status_symbol = "•"
            has_updates = False
            self.alert_message = self.alert_message_header
            for j in range(i, i + 5):
                if j >= len(keys):
                    break
                position_symbol = " "
                data = self.alertlist[keys[j]]
                if data["prev_ivr"] is None:
                    ivr_symbol = "¤"
                elif data["prev_ivr"] == data["ivr"] and only_new:
                    continue
                elif data["prev_ivr"] == data["ivr"]:
                    ivr_symbol = "•"
                elif data["prev_ivr"] < data["ivr"]:
                    ivr_symbol = "↑"
                elif data["prev_ivr"] > data["ivr"]:
                    ivr_symbol = "↓"
                    continue  # TODO: remove if wanting all alerts
                if (
                    data["prev_status"] != data["status"]
                    and data["prev_ivr"] is not None
                ):
                    status_symbol = ivr_symbol
                if keys[j] in self.ttapi.user_data["account_positions"]:
                    position_symbol = "\u001b[1;33m►\u001b[0m"
                has_updates = True
                status = ""
                if data["status"] == "Extreme":
                    status = "\u001b[1;37m\u001b[0;41mExtreme\u001b[0m "
                elif data["status"] == "Tasty":
                    status = "\u001b[1;35mTasty\u001b[0m   "
                elif data["status"] == "Elevated":
                    status = "\u001b[1;34mElevated\u001b[0m"
                symbol_padded = keys[j].ljust(7)
                ivr_diff = round(
                    (data["ivr"] - data["ivr_open"]) / data["ivr_open"] * 100,
                    2,
                )
                ivr_color = "30"
                if ivr_diff < 0:
                    ivr_color = "31"
                elif ivr_diff > 0:
                    ivr_color = "32"
                ivr_diff = f"{str(ivr_diff)}% {ivr_symbol}".ljust(11, " ")
                self.alert_message += (
                    f"{position_symbol}{status_symbol}{status}  {symbol_padded} "
                    f"\u001b[0;{ivr_color}m{ivr_diff}\u001b[0m "
                    f"{data['liquidity']}\n"
                )
            self.alert_message += self.alert_message_footer
            if has_updates:
                self.alert_messages.append(self.alert_message)
