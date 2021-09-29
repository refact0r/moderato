import asyncio
import discord
from discord.ext import commands
import time
import pymongo
from utils import colors
from utils import utility
import os

cog_order = ["general", "moderation"]


class general(commands.Cog):
    """General commands."""

    def __init__(self, client):
        self.client = client

    @commands.command(
        aliases=["h"],
        brief="Shows all commands, commands in a category, or information about a command",
        help="%help (category or command)",
        description="When used without arguments, this command will send a list of all commands. Use arrow reactions to navigate categories. You can also provide the name of a command to get more specific information.",
    )
    async def help(self, ctx, command=None):
        if not command or command in [str(i + 1) for i in range(len(cog_order))]:
            embeds = []
            embeds.append(
                discord.Embed(
                    title="Help",
                    description="""
                    Click the reactions to go to categories, or use `%help [category]`.
                """,
                    color=colors.help_color,
                )
            )

            count = 1
            for cog_name in cog_order:
                cog = self.client.cogs[cog_name]

                if cog:
                    embed = discord.Embed(
                        title="Help",
                        description="""
                            Click the reactions to go to categories, or use `%help [category]`.
                            For more info about a command, use `%help [command]`.
                            `()` means optional, `[]` means required.
                        """,
                        color=colors.help_color,
                    )
                    embed.set_footer(text=f"Page {count}/{len(cog_order)}")
                    embeds.append(embed)

                    commands_string = ""
                    for c in cog.get_commands():
                        if c.help and c.brief:
                            commands_string += f"```{c.help}```{c.brief}"

                    embed.add_field(
                        name=cog_name.capitalize(), value=commands_string, inline=False
                    )
                    embeds[0].add_field(
                        name=f"Page {count} - {cog_name.capitalize()}",
                        value=cog.description,
                        inline=False,
                    )

                    count += 1

            current = 0
            if command:
                current = int(command)

            msg = await ctx.send(embed=embeds[current])
            await msg.add_reaction("◀️")
            await msg.add_reaction("▶️")

            def check(reaction, user):
                return reaction.message.id == msg.id and user != self.client.user

            while True:
                try:
                    reaction, user = await self.client.wait_for(
                        "reaction_add", timeout=300.0, check=check
                    )
                except asyncio.TimeoutError:
                    await msg.edit(
                        embed=discord.Embed(
                            description="Command timed out.", color=colors.help_color
                        )
                    )
                    await msg.clear_reactions()
                    return

                try:
                    await reaction.remove(user)
                except:
                    pass

                if reaction.emoji == "◀️":
                    if current == 0:
                        current = len(embeds) - 1
                    else:
                        current -= 1
                elif reaction.emoji == "▶️":
                    if current == len(embeds) - 1:
                        current = 0
                    else:
                        current += 1

                await msg.edit(embed=embeds[current])

    @commands.command(brief="Says hello back.", help="%hi")
    async def hi(self, ctx):
        await ctx.send(f"Hello, {ctx.author.display_name}")

    @commands.command(aliases=[], brief="Checks the bot's latency.", help="%ping")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping(self, ctx):
        collection = self.client.db["ping"]

        before = time.monotonic()
        embed, message = await utility.embed_message(ctx, "Pong!", colors.ping_color)
        ping = int((time.monotonic() - before) * 1000)
        embed.description = f"Pong! `{ping}ms`"
        await message.edit(embed=embed)

        if ping < collection.find_one({"_id": 0})["time"]:
            collection.update_one(
                {"_id": 0}, {"$set": {"time": ping, "name": ctx.author.name}}
            )
        if ping > collection.find_one({"_id": 1})["time"]:
            collection.update_one(
                {"_id": 1}, {"$set": {"time": ping, "name": ctx.author.name}}
            )

    @commands.command(
        aliases=["pl", "plb"],
        brief="Gets the fastest and slowest pings achieved.",
        help="%pingleaderboard",
    )
    async def pingleaderboard(self, ctx):
        collection = self.client.db["ping"]
        fastest = collection.find_one({"_id": 0})
        slowest = collection.find_one({"_id": 1})

        embed = discord.Embed(
            title="Ping Leaderboard",
            description=f"Fastest: `{fastest['time']}` ms by {fastest['name']}\nSlowest: `{slowest['time']}` ms by {slowest['name']}",
            color=colors.ping_color,
        )
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(general(client))
