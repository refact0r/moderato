import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import *
import pymongo
from utility import parse_time, time_string

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster["discordbot"]

class moderation(commands.Cog):
    """Commands for user moderation."""
    
    def __init__(self, client):
        self.client = client

    # add role to members
    async def add_role(self, members, role, time):
        for member in members:
            await member.add_roles(role)
        if time <= 0:
            return
        await asyncio.sleep(time)
        for member in members:
            await member.remove_roles(role)

    # remove role from members
    async def remove_role(self, members, role, time):
        for member in members:
            await member.remove_roles(role)
        if time <= 0:
            return
        await asyncio.sleep(time)
        for member in members:
            await member.add_roles(role)

    # parses members from args
    async def parse_members(self, ctx, args):
        args_list = args.split(' ')
        parsed = False
        everyone = False
        members = set([])
        roles = set([])
        time = 0

        # check for "all" and @everyone
        if "all" in args_list or "everyone" in args_list or ctx.message.mention_everyone:
            everyone = True
            parsed = True
            if len(args_list) > 1:
                time = parse_time(args_list[-1])

        # check for role
        try:
            r = await RoleConverter().convert(ctx, args)
            roles.add(r)
            parsed = True
        except:
            pass

        # check for member
        if not parsed:
            try:
                m = await MemberConverter().convert(ctx, args)
                members.add(m)
                parsed = True
            except:
                pass

        # check for role with time
        if not parsed:
            try:
                r = await RoleConverter().convert(ctx, ' '.join(args_list[:-1]))
                roles.add(r)
                time = parse_time(args_list[-1])
                parsed = True
            except:
                pass

        # check for member with time
        if not parsed:
            try:
                m = await MemberConverter().convert(ctx, ' '.join(args_list[:-1]))
                members.add(m)
                time = parse_time(args_list[-1])
                parsed = True
            except:
                pass

        if not parsed:

            # check for individual members and role names
            for i in args_list:
                if i == args_list[-1]:
                    time = parse_time(i)
                    if time > 0:
                        continue

                try:
                    r = await RoleConverter().convert(ctx, i)
                    roles.add(r)
                except:
                    pass

                try:
                    m = await MemberConverter().convert(ctx, i)
                    members.add(m)
                except:
                    pass
            
            # check for mentions
            for r in ctx.message.role_mentions:
                r.add(r)
            for m in ctx.message.mentions:
                members.add(m)

        return everyone, list(roles), list(members), time

    # basic role moderation command
    async def role_command(self, ctx, args, add_role, name, role_name, role_overwrite, role_color):

        # find role or create if it doesnt exist
        role = None
        for r in ctx.guild.roles:
            if r.name == role_name.capitalize() or r.name == role_name:
                role = r
        if not role:
            role = await ctx.guild.create_role(name = role_name.capitalize(), color = role_color)
            for c in ctx.guild.channels:
                await c.set_permissions(role, overwrite = role_overwrite)

        # get final list of members
        everyone, roles, members, time = await self.parse_members(ctx, args)
        final_members = set([])

        if everyone:
            final_members.add(ctx.guild.members)
        else:
            for r in roles:
                final_members.add(r.members)
            for m in members:
                final_members.add(m)

        final_members = list(final_members)
        
        # checks
        if not final_members:
            await ctx.send("No users found.")
            return
        '''
        if len(final_members) > 100:
            await ctx.send(f"You cannot use this command on more than 100 users at once.")
            return
        '''

        # generate and send message
        msg_string = ""
        if len(final_members) == 1:
            if time != 0:
                msg_string += f"`{members[0].name}` was {name} for `{time_string(time)}`."
            else:
                msg_string += f"`{members[0].name}` was {name}."
        else:
            if everyone:
                msg_string += f"Everyone"
            else:
                if len(roles) > 0:
                    if len(roles) == 1:
                        msg_string += f"the role `{roles[0].name}`"
                    else:
                        msg_string += f"the roles `{', '.join([r.name for r in roles])}`"
                    if members:
                        msg_string += " and "
                if len(members) > 0:
                    if len(members) == 1:
                        msg_string += f"the member `{members[0].name}`"
                    else:
                        msg_string += f"the members `{', '.join([m.name for m in members])}`"
                msg_string.capitalize()
            if time != 0:
                msg_string += f" were {name} for `{time_string(time)}`."
            else:
                msg_string += f" were {name}."
        
        await ctx.send(msg_string)

        # add or remove role
        if add_role:
            await self.add_role(final_members, role, time)
        else:
            await self.remove_role(final_members, role, time)

    @commands.command(aliases = ["m"], brief = "Prevents a user sending messages", help = "%mute [user(s) or role(s)] (time)")
    async def mute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages = False)
        await self.role_command(ctx, args, True, "muted", "Muted", overwrite, discord.Color(0x505050))

    @commands.command(aliases = ["um"], brief = "Unmutes a user.", help = "%unmute [user(s) or role(s)]")
    async def unmute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages = False)
        await self.role_command(ctx, args, False, "unmuted", "Muted", overwrite, discord.Color(0x505050))

    @commands.command(aliases = ["f"], brief = "Prevents a user from adding reactions, sending files, sending embeds, or using external emojis.", help = "%freeze [user(s) or role(s)] (time)")
    async def freeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(add_reactions = False, attach_files = False, embed_links = False, external_emojis = False)
        await self.role_command(ctx, args, True, "frozen", "Frozen", overwrite, discord.Color(0xb0b0b0))

    @commands.command(aliases = ["uf"], brief = "Unfreezes a user.", help = "%unfreeze [user(s) or role(s)]")
    async def unfreeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(add_reactions = False, attach_files = False, embed_links = False, external_emojis = False)
        await self.role_command(ctx, args, False, "unfrozen", "Frozen", overwrite, discord.Color(0xb0b0b0))

    @commands.command(aliases = ["e"], brief = "Prevents a user from viewing any channels.", help = "%exile [user(s) or role(s)] (time)")
    async def exile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(view_channel = False, read_message_history = False)
        await self.role_command(ctx, args, True, "exiled", "Exiled", overwrite, discord.Color(0x202020))

    @commands.command(aliases = ["ue"], brief = "Unexiles a user.", help = "%unexile [user(s) or role(s)]")
    async def unexile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(view_channel = False, read_message_history = False)
        await self.role_command(ctx, args, False, "unexiled", "Exiled", overwrite, discord.Color(0x202020))

def setup(client):
    client.add_cog(moderation(client))