import asyncio
import discord
from discord.ext import commands
import time
import pymongo

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

descriptions = {
    'utility': "General utility commands."
}
cog_blacklist = ['error']

class utility(commands.Cog):
    """General utility commands."""
    
    def __init__(self, client):
        self.client = client

    @commands.command(aliases = ['h'])
    async def help(self, ctx, command = None):
        embeds = []
        embeds.append(discord.Embed(
            title = "Help",
            description = """
                Click the reactions to go to specific categories, or use `%help [category]`.
                To get information about a specific command, use `%help [command]`.
            """,
            color = 0x4f85f6
        ))
        embeds[0].set_footer(text = f"Page 1/{len(self.client.cogs) - len(cog_blacklist) + 1}")

        count = 2
        for cog_name in self.client.cogs:
            if cog_name not in cog_blacklist:
                cog = self.client.cogs[cog_name]

                embed = discord.Embed(
                    title = "Help",
                    description = """
                        Click the reactions to go to specific categories, or use `%help [category]`.
                        To get information about a specific command, use `%help [command]`.
                    """,
                    color = 0x4f85f6
                )
                embed.set_footer(text = f"Page {count}/{len(self.client.cogs) - len(cog_blacklist) + 1}")
                embeds.append(embed)

                commands_string = ""
                for command in cog.get_commands():
                    commands_string += f"```{command.help}```{command.brief}"
                
                embed.add_field(name = cog_name.capitalize(), value = commands_string, inline = False)
                embeds[0].add_field(name = f"Page {count} - {cog_name.capitalize()}", value = cog.description, inline = False)

                count += 1

        msg = await ctx.send(embed = embeds[0])
        await msg.add_reaction('◀️')
        await msg.add_reaction('▶️')

        def check(reaction, user):
            return reaction.message.id == msg.id and user != self.client.user

        current = 1
        while True:
            try:
                reaction, user = await self.client.wait_for('reaction_add', timeout = 300.0, check = check)
            except asyncio.TimeoutError:
                return

            try:
                await reaction.remove(user)
            except:
                pass

            if reaction.emoji == '◀️':
                if current == 1:
                    current = len(embeds)
                else:
                    current -= 1
            elif reaction.emoji == '▶️':
                if current == len(embeds):
                    current = 1
                else:
                    current += 1

            await msg.edit(embed = embeds[current])


    @commands.command(brief = "says hello back", help = "%hi")
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
            title = "Ping Leaderboard",
            description = f"Fastest: `{fastest['time']}` ms by {fastest['name']}\nSlowest: `{slowest['time']}` ms by {slowest['name']}",
            color = ctx.author.color
        )
        await ctx.send(embed = embed)

def setup(client):
    client.add_cog(utility(client))