import discord
import os
from discord.ext import commands
import pymongo
import certifi

bot_token = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.presences = True

prefixes = ["%"]
client = commands.Bot(command_prefix=prefixes, intents=intents)
client.remove_command("help")

cluster = pymongo.MongoClient(os.getenv("MONGODB_STRING"), tlsCAFile=certifi.where())
client.db = cluster["discordbot"]

for file in os.listdir("./cogs"):
    if file.endswith(".py"):
        client.load_extension(f"cogs.{file[:-3]}")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="ping for prefix"))
    print("bot has connected to discord")


@client.event
async def on_message(message):
    if client.user in message.mentions:
        await message.channel.send(
            f"The current prefix is `{prefixes[0]}`.\nType `{prefixes[0]}help` for more info."
        )
    await client.process_commands(message)


client.run(bot_token)
