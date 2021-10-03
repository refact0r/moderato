import asyncio
import discord
from discord.ext import commands
import time
import pymongo
from utils import colors
from utils import utility
import os


class channels(commands.Cog):
    """Commands for managing channels."""

    def __init__(self, client):
        self.client = client

    @commands.command(
        aliases=["l"],
        brief="Locks a channel",
        help="%lock (channel) (time)",
        description="""
            This command locks the targeted channel, preventing users from speaking in it.
            To lock for a certain time, provide a time at the end of the command.
        """,
    )
    async def lock(self, ctx, *, args=None):
        if not args:
            embed, msg = await utility.embed_message(ctx, "Locking this channel...", colors.lock_color)
            await ctx.channel.set_permissions(
                ctx.guild.default_role, send_messages=False
            )
            embed.description = "Locked this channel."
            await msg.edit(embed = embed)


def setup(client):
    client.add_cog(channels(client))
