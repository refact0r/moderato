import discord
import os
from discord.ext import commands

bot_token = ""

intents = discord.Intents.default()
intents.members = True
intents.presences = True

client = commands.Bot(command_prefix = ['%'], intents = intents)

client.remove_command('help')

for file in os.listdir('./cogs'):
	if file.endswith('.py'):
		client.load_extension(f'cogs.{file[:-3]}')

@client.event
async def on_ready():
	print("bot has connected to discord")

client.run(bot_token)
