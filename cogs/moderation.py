import asyncio
import discord
from discord.ext import commands
import pymongo
import utils.colors
import utils.utility
import os

cluster = pymongo.MongoClient(os.getenv('MONGODB_STRING'))
db = cluster["discordbot"]

class moderation(commands.Cog):
    """Commands for user moderation."""
    
    def __init__(self, client):
        self.client = client
    
    # generate message string
    def generate_message(self, everyone, roles, members, time, name):
        msg_string = ""
        plural = False
        if everyone:
            msg_string += f"Everyone"
        else:
            if len(roles) > 0:
                if len(roles) == 1:
                    msg_string += f"the role `{roles[0].name}`"
                else:
                    msg_string += f"the roles `{'`, `'.join([r.name for r in roles])}`"
                    plural = True
                if members:
                    msg_string += " and "
                    plural = True
            if len(members) > 0:
                if len(members) == 1:
                    msg_string += f"the member `{members[0].name}`"
                else:
                    msg_string += f"the members `{'`, `'.join([m.name for m in members])}`"
                    plural = True
            msg_string = msg_string[0].upper() + msg_string[1:]

        if plural:
            msg_string += f" were {name}"
        else:
            msg_string += f" was {name}"

        if time != 0:
            msg_string += f" for `{utils.utility.time_string(time)}`."
        else:
            msg_string += "."

        return msg_string

    # add role to members
    async def add_role(self, members, role, time):
        for m in members:
            await m.add_roles(role)
        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in role.members:
            await m.remove_roles(role)

    # remove role from members
    async def remove_role(self, members, role, time):
        for m in members:
            await m.remove_roles(role)
        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in members:
            await m.add_roles(role)

    # parses members from args
    async def parse_args(self, ctx, args):
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
                time = utils.utility.parse_time(args_list[-1])
            pass

        # check for member
        try:
            m = await commands.MemberConverter().convert(ctx, args)
            members.add(m)
            parsed = True
        except:
            pass

        # check for role
        if not parsed:
            try:
                r = await commands.RoleConverter().convert(ctx, args)
                roles.add(r)
                parsed = True
            except:
                pass

        if len(args_list) > 1 and utils.utility.parse_time(args_list[-1]) > 0:

            # check for member with time
            if not parsed:
                try:
                    m = await commands.MemberConverter().convert(ctx, ' '.join(args_list[:-1]))
                    members.add(m)
                    time = utils.utility.parse_time(args_list[-1])
                    parsed = True
                except:
                    pass

            # check for role with time
            if not parsed:
                try:
                    r = await commands.RoleConverter().convert(ctx, ' '.join(args_list[:-1]))
                    roles.add(r)
                    time = utils.utility.parse_time(args_list[-1])
                    parsed = True
                except:
                    pass

        if not parsed:

            # check for individual members and role names
            for i in args_list:
                if i == args_list[-1]:
                    time = utils.utility.parse_time(i)
                    if time > 0:
                        continue

                try:
                    m = await commands.MemberConverter().convert(ctx, i)
                    members.add(m)
                except:
                    pass

                try:
                    r = await commands.RoleConverter().convert(ctx, i)
                    roles.add(r)
                except:
                    pass
            
            # check for mentions
            for m in ctx.message.mentions:
                members.add(m)
            for r in ctx.message.role_mentions:
                r.add(r)
            
        final_members = set([])
        roles, members = list(roles), list(members)

        if everyone:
            for m in ctx.guild.members:
                final_members.add(m)
        else:
            for m in members:
                final_members.add(m)
            for r in roles:
                for m in r.members:
                    final_members.add(m)

        return everyone, roles, members, final_members, time

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
        everyone, roles, members, final_members, time = await self.parse_args(ctx, args)
        
        # checks
        if not final_members:
            await utils.utility.error_message(ctx, "No members found.")
            return
        '''
        if len(final_members) > 100:
            await ctx.send(f"You cannot use this command on more than 100 users at once.")
            return
        '''

        # generate and send message
        msg_string = self.generate_message(everyone, roles, members, time, name)
        await utils.utility.embed_message(ctx, msg_string, role_color)

        # add or remove role
        if add_role:
            await self.add_role(final_members, role, time)
        else:
            await self.remove_role(final_members, role, time)

    @commands.command(aliases = ["m"], brief = "Prevents a user sending messages", help = "%mute [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def mute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages = False)
        await self.role_command(ctx, args, True, "muted", "Muted", overwrite, utils.colors.muted_color)

    @commands.command(aliases = ["um"], brief = "Unmutes a user.", help = "%unmute [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def unmute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages = False)
        await self.role_command(ctx, args, False, "unmuted", "Muted", overwrite, utils.colors.muted_color)

    @commands.command(aliases = ["f"], brief = "Prevents a user from adding reactions, sending files, sending embeds, or using external emojis.", help = "%freeze [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def freeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(add_reactions = False, attach_files = False, embed_links = False, external_emojis = False)
        await self.role_command(ctx, args, True, "frozen", "Frozen", overwrite, utils.colors.frozen_color)

    @commands.command(aliases = ["uf"], brief = "Unfreezes a user.", help = "%unfreeze [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def unfreeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(add_reactions = False, attach_files = False, embed_links = False, external_emojis = False)
        await self.role_command(ctx, args, False, "unfrozen", "Frozen", overwrite, utils.colors.frozen_color)

    @commands.command(aliases = ["e"], brief = "Prevents a user from viewing any channels.", help = "%exile [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def exile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(view_channel = False, read_message_history = False)
        await self.role_command(ctx, args, True, "exiled", "Exiled", overwrite, utils.colors.exiled_color)

    @commands.command(aliases = ["ue"], brief = "Unexiles a user.", help = "%unexile [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles = True)
    @commands.bot_has_permissions(manage_roles = True)
    @commands.guild_only()
    async def unexile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(view_channel = False, read_message_history = False)
        await self.role_command(ctx, args, False, "unexiled", "Exiled", overwrite, utils.colors.exiled_color)

    @commands.command(aliases = ["b"], brief = "Bans a user.", help = "%ban [user(s) or role(s) or all] (time)")
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def ban(self, ctx, *, args):
        everyone, roles, members, final_members, time = await self.parse_args(ctx, args)

        if not final_members:
            await utils.utility.error_message(ctx, "No members found.")
            return

        msg_string = self.generate_message(everyone, roles, members, time, "banned")
        await utils.utility.embed_message(ctx, msg_string, utils.colors.ban_color)

        for m in final_members:
            await m.ban()
        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in members:
            await m.unban()

    @commands.command(aliases = ["ub"], brief = "Unbans a user.", help = "%unban [user(s) or role(s) or all] (time)")
    @commands.has_permissions(ban_members = True)
    @commands.bot_has_permissions(ban_members = True)
    @commands.guild_only()
    async def unban(self, ctx, *, args):
        everyone, roles, members, final_members, time = await self.parse_args(ctx, args)

        if not final_members:
            await ctx.send(embed = discord.Embed(description = "No members found.", color = utils.colors.error_color)) 
            return

        msg_string = self.generate_message(everyone, roles, members, time, "unbanned")
        msg = await ctx.send(embed = discord.Embed(description = msg_string, color = utils.colors.ban_color)) 

        for m in final_members:
            try:
                await m.unban()
            except discord.Forbidden:
                await msg.edit(embed = discord.Embed(description = "No members found.", color = utils.colors.error_color)) 
            except discord.NotFound:
                await msg.edit(embed = discord.Embed(description = "No members found.", color = utils.colors.error_color)) 
                
        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in members:
            await m.ban()

def setup(client):
    client.add_cog(moderation(client))