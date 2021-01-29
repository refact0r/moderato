import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import *
import time
import pymongo

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

class moderation(commands.Cog):
    """Commands for user moderation."""
    
    def __init__(self, client):
        self.client = client

    @commands.command(brief = "Prevents a user from sending messages.", help = "%mute [user] (time)")
    async def mute(self, ctx, *, args):
        print(args)
        if args == "all":
            await ctx.send("mute all")
            return
        if len(ctx.message.mentions) > 0:
            for m in ctx.message.mentions:
                await ctx.send(f"mute {m.name}")
            return
        try:
            m = await MemberConverter().convert(ctx, args)
            await ctx.send(f"mute {m.name}")
        except Exception:
            print(Exception)
        try:
            r = await RoleConverter().convert(ctx, args)
            await ctx.send(f"mute {r.name}")
        except Exception:
            print(Exception)

def setup(client):
    client.add_cog(moderation(client))