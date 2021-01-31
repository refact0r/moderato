import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import *
import pymongo
from decimal import Decimal

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

class moderation(commands.Cog):
    """Commands for user moderation."""
    
    def __init__(self, client):
        self.client = client

    def duration(self, duration_string):
        duration_string = duration_string.lower()
        total_seconds = Decimal('0')
        prev_num = []
        for character in duration_string:
            if character.isalpha():
                if prev_num:
                    num = Decimal(''.join(prev_num))
                    if character == 'd':
                        total_seconds += num * 60 * 60 * 24
                    elif character == 'h':
                        total_seconds += num * 60 * 60
                    elif character == 'm':
                        total_seconds += num * 60
                    elif character == 's':
                        total_seconds += num
                    prev_num = []
            elif character.isnumeric():
                prev_num.append(character)
        return float(total_seconds)

    def time(self, seconds):
        period_seconds = [86400, 3600, 60, 1]
        period_desc = ['days', 'hours', 'mins', 'secs']
        s = ''
        remainder = seconds
        for i in range(len(period_seconds)):
            q, remainder = divmod(remainder, period_seconds[i])
            if q > 0:
                if s:
                    s += ' '
                s += f'{int(q)} {period_desc[i]}'
        return s

    async def add_role(self, members, role, time, msg, edit):
        for member in members:
            await member.add_roles(role)
        if msg and edit:
            await msg.edit(content = edit)
        if time <= 0:
            return
        await asyncio.sleep(time)
        for member in members:
            await member.remove_roles(role)

    async def filter_members(self, ctx, args):
        members = []
        time = 0

        if args == "all":
            members = ctx.guild.members
        elif len(args) == 2 and args.split(' ')[0] == "all":
            members = ctx.guild.members
            time = self.duration(args.split(' ')[1])

        try:
            m = await MemberConverter().convert(ctx, args)
            members.append(m)
        except:
            pass
            
        if not members:
            try:
                r = await RoleConverter().convert(ctx, args)
                members = r.members
            except:
                pass

        if not members:
            try:
                m = await MemberConverter().convert(ctx, ' '.join(args.split(' ')[:-1]))
                members.append(m)
                time = self.duration(args.split(' ')[-1])
            except:
                pass
        
        if not members:
            try:
                r = await RoleConverter().convert(ctx, ' '.join(args.split(' ')[:-1]))
                members = r.members
                time = self.duration(args.split(' ')[-1])
            except:
                pass

        if not members:
            for i in args.split('"')[1::2]:
                try:
                    m = await MemberConverter().convert(ctx, i)
                    members.append(m)
                except:
                    pass
                try:
                    r = await RoleConverter().convert(ctx, i)
                    members += r.members
                except:
                    pass

            last = args.split(' ')[-1]
                
            for j in args.split('"')[::2]:
                for k in j.split(' '):
                    if k:
                        if k == last:
                            dur = self.duration(last)
                            if dur:
                                time = dur
                                continue
                        try:
                            m = await MemberConverter().convert(ctx, k)
                            members.append(m)
                        except:
                            pass
                        try:
                            r = await RoleConverter().convert(ctx, k)
                            members += r.members
                        except:
                            pass

        return [list(set(members)), time]

    @commands.command(aliases = ["m"], brief = "Prevents a user from sending messages.", help = "%mute [user(s) or role(s)] (time)")
    async def mute(self, ctx, *, args):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You do not have the permissions to use this command.")
            return

        role = None
        for r in ctx.guild.roles:
            if r.name == "Muted" or r.name == "muted":
                role = r
        if not role:
            role = await ctx.guild.create_role(name = "Muted", color = discord.Color(0x505050))
            for channel in ctx.guild.channels:
                overwrite = discord.PermissionOverwrite()
                overwrite.send_messages = False
                await channel.set_permissions(role, overwrite=overwrite)

        result = await self.filter_members(ctx, args)
        members = result[0]
        time = result[1]
        
        if len(members) > 100:
            await ctx.send("You cannot mute more than 100 users at once.")
            return

        msg = None
        edit_string = None
        if not members:
            await ctx.send("No users found.")
            return
        elif len(members) == 1:
            if time == 0:
                await ctx.send(f"`{members[0].display_name}` was muted.")
            else:
                await ctx.send(f"`{members[0].display_name}` was muted for `{self.time(time)}`.")
        else:
            msg = await ctx.send(f"Muting the users {', '.join(['`' + m.display_name + '`' for m in members])}...")
            if time == 0:
                edit_string = f"The users {', '.join(['`' + m.display_name + '`' for m in members])} were muted."
            else:
                edit_string = f"The users {', '.join(['`' + m.display_name + '`' for m in members])} were muted for `{self.time(time)}`."

        await self.add_role(members, role, time, msg, edit_string)

    @commands.command(aliases = ["f"], brief = "Prevents a user from adding reactions, sending files, sending embeds, or using external emojis.", help = "%freeze [user(s) or role(s)] (time)")
    async def freeze(self, ctx, *, args):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You do not have the permissions to use this command.")
            return

        role = None
        for r in ctx.guild.roles:
            if r.name == "Frozen" or r.name == "frozen":
                role = r
        if not role:
            role = await ctx.guild.create_role(name = "Frozen", color = discord.Color.default())
            for channel in ctx.guild.channels:
                overwrite = discord.PermissionOverwrite()
                overwrite.external_emojis = False
                overwrite.attach_files = False
                overwrite.embed_links = False
                overwrite.add_reactions = False
                await channel.set_permissions(role, overwrite=overwrite)

        result = await self.filter_members(ctx, args)
        members = result[0]
        time = result[1]
        
        if len(members) > 100:
            await ctx.send("You cannot freeze more than 100 users at once.")
            return

        msg = None
        edit_string = None
        if not members:
            await ctx.send("No users found.")
            return
        elif len(members) == 1:
            if time == 0:
                await ctx.send(f"`{members[0].display_name}` was frozen.")
            else:
                await ctx.send(f"`{members[0].display_name}` was frozen for `{self.time(time)}`.")
        else:
            msg = await ctx.send(f"Freezing the users {', '.join(['`' + m.display_name + '`' for m in members])}...")
            if time == 0:
                edit_string = f"The users {', '.join(['`' + m.display_name + '`' for m in members])} were frozen."
            else:
                edit_string = f"The users {', '.join(['`' + m.display_name + '`' for m in members])} were frozen for `{aself.time(time)}`."

        await self.add_role(members, role, time, msg, edit_string)

def setup(client):
    client.add_cog(moderation(client))