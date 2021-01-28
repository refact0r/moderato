import discord
import os
from discord.ext import commands
from datetime import datetime
import pymongo

#bot_token = os.getenv('BOT_TOKEN')
bot_token = "ODA0MTA0NjI3ODI5MjExMTQ2.YBHeyg.fAQc8l5Ph3-cGiMz5cS91FJOn00"

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
