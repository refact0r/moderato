import discord
from discord.ext import commands
import time
import pymongo

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

class utility(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command(aliases = ['h'])
    async def help(self, ctx, command = None):
        print("test")

    @commands.command(description = "Says hello back.", brief = "says hello back", help = "%hi")
    async def hi(self, ctx):
        await ctx.send(f"Hello, {ctx.author.display_name}")

    @commands.command(aliases = ['p'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        collection = db['ping']
        before = time.monotonic()
        message = await ctx.send("Pong!")
        ping = int((time.monotonic() - before) * 1000)
        await message.edit(content = f"Pong! `{ping}ms`")
        if ping < collection.find_one({'_id': 0})['time']:
            collection.update_one({'_id': 0}, {'$set': {'time': ping, 'name': ctx.author.name}})
        if ping > collection.find_one({'_id': 1})['time']:
            collection.update_one({'_id': 1}, {'$set': {'time': ping, 'name': ctx.author.name}})

    @commands.command(aliases = ['pl'])
    async def pingleaderboard(self, ctx):
        collection = db['ping']
        fastest = collection.find_one({'_id': 0})
        slowest = collection.find_one({'_id': 1})
        embed = discord.Embed(
            title = f"Ping Leaderboard",
            description = f"Fastest: `{fastest['time']}` ms by {fastest['name']}\nSlowest: `{slowest['time']}` ms by {slowest['name']}",
            color = ctx.author.color
        )
        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(utility(client))