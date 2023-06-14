import discord
import time
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional
from discord.ext import commands, tasks
from discord.ext.commands.cog import Cog
from discord.ext.commands.core import Command
from lib.TTApi import *
from lib.TTConfig import *
from lib.TastyBot.TBConfig import *


class TastyCommands(commands.Cog):
    bot = None
    last_alert = None
    open_warning = False
    open_alerted = False
    close_warning = False
    close_alerted = False
    first_run = True

    def __init__(self, bot) -> None:
        self.bot = bot

    async def send_alerts(self):
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Sending alerts {now} ... ", end="", flush=True)
        for message in self.bot.alert_messages:
            await self.bot.send(message)
            time.sleep(0.25)
        now = datetime.now().strftime("%H:%M:%S")
        print(f"Finished alerts {now}", flush=True)

    @commands.command(brief="Read this to understand the watchlist posts.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def README(self, ctx):
        msg = (
            f"```ansi\n\u001b[1;30mTastyBot README\u001b[0m\n"
            f"\u001b[4;44;37mUpdate Markers\u001b[0m\n"
            f"• - unchanged since last update.\n"
            f"↓ - down since last update.\n"
            f"↑ - up since last update.\n"
            f"\n"
            f"\u001b[4;44;37mDefinitions\u001b[0m\n"
            f"IVR Change - Relative change in IVR since market open.\n"
            f"Liquidity - \u001b[0;41;37m(experimental)\u001b[0m Liquidity rank.\n"
            f"```"
        )
        await self.bot.send(msg)

    @commands.command(administrator=True, hidden=True)
    async def alert(self, ctx, *params):
        await self.bot.fetch_watchlist()
        await self.bot.update_watchlist()
        await self.bot.update_alertlist()
        alert_all = True
        if len(params) >= 1:
            alert_param, *extra_params = params
            if alert_param.lower() == "all":
                alert_all = True
            elif alert_param.lower() == "new":
                alert_all = False
        if alert_all:
            await self.bot.update_alerts(only_new=False)
        else:
            await self.bot.update_alerts(only_new=True)
        await self.send_alerts()

    @commands.command(administrator=True, hidden=True)
    async def chain(self, ctx, *params):
        if len(params) < 1:
            return
        symbol, *extra_params = params
        print(self.bot.ttapi.option_chains(symbol))

    @commands.command(brief="Displays the current TastyBot watchlist.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def watchlist(self, ctx):
        watchlist_message = "```ansi\n\u001b[1;30mRise of the Machines\u001b[0m\n"
        for entry in self.bot.watchlist["data"]["watchlist-entries"]:
            watchlist_message += f"{entry['symbol']}, "
        watchlist_message = watchlist_message[:-2]
        watchlist_message += "```"
        await self.bot.send(watchlist_message)

    @tasks.loop(seconds=1.00)
    async def fetch_loop(self):
        if datetime.today().weekday() in [5, 6]:  # It's the weekend, ignore
            return

        # only run every 2 minutes-ish
        now = datetime.now()
        if now.minute % 2 != 0 or now.second != 0:
            return

        if now.hour >= 9 and now.hour <= 19:
            if now.hour == 9 and now.minute < 30:
                return
            elif now.hour == 19 and now.minute > 0:
                return

            now = datetime.now().strftime("%H:%M:%S")
            print(f"Entering fetch_loop {now}", flush=True)

            await self.bot.fetch_watchlist()
            await self.bot.update_watchlist()
            await self.bot.update_alertlist()

            if self.first_run:
                self.first_run = False
                await self.bot.update_alerts(only_new=False)
            else:
                now = datetime.now()
                # if now.minute % 30 == 0:
                #    await self.bot.update_alerts(only_new=False)
                # else:
                await self.bot.update_alerts(only_new=True)
            await self.send_alerts()

            now = datetime.now().strftime("%H:%M:%S")
            print(f"Exiting fetch_loop {now}", flush=True)

    @fetch_loop.before_loop
    async def before_fetch_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=1.00)
    async def market_warning_loop(self):
        if datetime.today().weekday() in [5, 6]:  # It's the weekend, ignore
            return
        now = datetime.now()
        if now.hour == 9 and now.minute == 28 and not self.open_warning:
            self.open_warning = True
            self.close_alerted = False
            await self.bot.send(
                f"```ansi\n\u001b[1;31m2 Minute Open Warning!\u001b[0m\n```"
            )
        if now.hour == 9 and now.minute == 30 and not self.open_alerted:
            self.open_alerted = True
            await self.bot.send(f"```ansi\n\u001b[1;31mMarkets are Open!\u001b[0m\n```")
        if now.hour == 15 and now.minute == 58 and not self.close_warning:
            self.close_warning = True
            await self.bot.send(
                f"```ansi\n\u001b[1;31m2 Minute Close Warning!\u001b[0m\n```"
            )
        if now.hour == 16 and not self.close_alerted:
            self.close_alerted = True
            self.open_warning = False
            self.open_alerted = False
            self.close_warning = False
            await self.bot.send(f"```ansi\n\u001b[1;31mMarket Closed!\u001b[0m\n```")

    @market_warning_loop.before_loop
    async def before_market_warning_loop(self):
        await self.bot.wait_until_ready()

    def start_tasks(self):
        self.fetch_loop.start()
        self.market_warning_loop.start()
