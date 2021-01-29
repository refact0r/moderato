import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import *
import pymongo
from decimal import Decimal
from datetime import timedelta

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

class moderation(commands.Cog):
    """Commands for user moderation."""
    
    def __init__(self, client):
        self.client = client

    def duration(self, duration_string): #example: '5d3h2m1s'
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
            elif character.isnumeric() or character == '.':
                prev_num.append(character)
        return float(total_seconds)

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

    @commands.command(brief = "Prevents a user from sending messages.", help = "%mute [user] (time)")
    async def mute(self, ctx, *, args):
        print(args)

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

        members = []
        time = 0

        if args == "all":
            if len(ctx.guild.members) > 100:
                await ctx.send("You cannot mute more than 100 users at once.")
                return
            members = ctx.guild.members
        elif len(args) == 2 and args.split[' '][0] == "all":
            if len(ctx.guild.members) > 100:
                await ctx.send("You cannot mute more than 100 users at once.")
                return
            members = ctx.guild.members
            time = self.duration(args.split[' '][1])

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
                m = await MemberConverter().convert(ctx, args.split(' ')[:-1].join(' '))
                members.append(m)
                time = self.duration(args.split[' '][-1])
            except:
                pass
        
        if not members:
            try:
                r = await RoleConverter().convert(ctx, args.split(' ')[:-1].join(' '))
                members = r.members
                time = self.duration(args.split[' '][-1])
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

        members = list(set(members)) 
        
        if len(members) > 100:
            await ctx.send("You cannot mute more than 100 users at once.")
            return

        msg = None
        edit_string = None
        if not members:
            await ctx.send("No users found.")
            return
        elif len(members) == 1:
            await ctx.send(f"{members[0].display_name} was muted.")
        else:
            msg = await ctx.send(f"Muting the users {', '.join(['`' + m.display_name + '`' for m in members])}...")
            edit_string = f"The users {', '.join(['`' + m.display_name + '`' for m in members])} were muted."

        await self.add_role(members, role, time, msg, edit_string)

def setup(client):
    client.add_cog(moderation(client))