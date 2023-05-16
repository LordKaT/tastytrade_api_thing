import discord
from discord.ext import commands, tasks

intents = discord.Intents.default()


class LoopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0

    @tasks.loop(seconds=5)
    async def print_loop(self):
        print("loop")

    @print_loop.before_loop
    async def before_printer(self):
        print("Waiting until ready...")
        await self.bot.wait_until_ready()

    def start_tasks(self):
        self.print_loop.start()


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.loop_cog = LoopCog(self)

    async def on_ready(self):
        await self.add_cog(self.loop_cog)
        print(f"We have logged in as {self.user}")
        self.loop_cog.start_tasks()


if __name__ == "__main__":
    bot = MyBot()
    bot.run(
        "MTEwNTk1Nzg4NTY3NjEwMTc3Mw.Glbal0.H1VQ7Ydd04hEzYglCCN7v7jr1EDg5l8NhGuM5w"
    )  # Replace with your Discord bot token
