import asyncio
import discord
from discord.ext import commands
import pymongo
from utils import colors
from utils import utility
import os


class moderation(commands.Cog):
    """Commands for user moderation."""

    def __init__(self, client):
        self.client = client
        self.role_punishments = {
            "Muted": {},
            "Frozen": {},
            "Exiled": {}
        }

    # generate already error string
    def already_error(self, members, action):
        if len(members) == 1:
            return f"The member <@{members[0].id}> is already {action}."
        else:
            return f"The members {', '.join([f'<@{m.id}>' for m in members])} are already {action}."

    # generate member string
    def member_string(self, everyone, roles, members):
        string = ""

        if everyone:
            string += "everyone"
        else:
            if roles:
                if len(roles) == 1:
                    string += f"the role <@&{roles[0].id}>"
                else:
                    string += f"the roles {', '.join([f'<@&{r.id}>' for r in roles])}"
                if members:
                    string += " and "
            if members:
                if len(members) == 1:
                    string += f"the member <@{members[0].id}>"
                else:
                    string += f"the members {', '.join([f'<@{m.id}>' for m in members])}"

        return string

    # generate before message string
    def before_string(self, everyone, roles, members, time, action):
        string = f"{action} ".capitalize()
        string += self.member_string(everyone, roles, members)

        if time:
            string += f" for `{utility.time_string(time)}`..."
        else:
            string += "..."

        return string

    # generate before message string for updating
    def before_update_string(self, everyone, roles, members, time, action):
        if len(roles) > 1 or len(members) > 1 or (len(roles) == 1 and len(members) == 1):
            string = f"Updating the {action} timers for "
        else:
            string = f"Updating the {action} timer for "

        string += self.member_string(everyone, roles, members)

        if time:
            string += f" to `{utility.time_string(time)}`..."
        else:
            string += "..."

        return string

    # generate after message string
    def after_string(self, everyone, roles, members, time, action):
        string = self.member_string(everyone, roles, members)
        string = string[0].upper() + string[1:]

        if len(roles) > 1 or len(members) > 1 or (len(roles) == 1 and len(members) == 1):
            string += f" were {action}"
        else:
            string += f" was {action}"

        if time:
            string += f" for `{utility.time_string(time)}`."
        else:
            string += "."

        return string

    # generate after message string
    def after_update_string(self, everyone, roles, members, time, action):
        if len(roles) > 1 or len(members) > 1 or (len(roles) == 1 and len(members) == 1):
            string = f"Update the {action} timers for "
        else:
            string = f"Update the {action} timer for "

        string += self.member_string(everyone, roles, members)

        if time:
            string += f" to `{utility.time_string(time)}`."
        else:
            string += "."

        return string

    def get_final_members(self, ctx, everyone, roles, members):
        final_members = set()

        if everyone:
            for m in ctx.guild.members:
                final_members.add(m)
        else:
            for m in members:
                final_members.add(m)
            for r in roles:
                for m in r.members:
                    final_members.add(m)

        return list(final_members)

    async def update_roles(self, members, role, add_role):
        if add_role:
            for m in members:
                await m.add_roles(role)
        else:
            for m in members:
                await m.remove_roles(role)

    async def update_role_timed(self, member, role, add_role, time):
        await asyncio.sleep(time)
        if add_role:
            print(f"remove from {member.name}")
            await member.remove_roles(role)
            print(f"add to {member.name}")
        else:
            await member.add_roles(role)

    # parses members from args
    async def parse_args(self, ctx, args):
        args_list = args.split(' ')
        parsed = False
        everyone = False
        members = set()
        roles = set()
        time = 0

        # check for time
        if len(args_list) > 1:
            time = utility.parse_time(args_list[-1])
            if time > 0:
                args_list = args_list[:-1]
                args = ' '.join(args_list)

        # check for "all" and @everyone
        if len(args_list) == 1 and ("all" in args_list or "everyone" in args_list or ctx.message.mention_everyone):
            everyone = True
            parsed = True

        # check for member
        if not parsed:
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

        if not parsed:

            # check for individual members and role names
            for arg in args_list:
                try:
                    m = await commands.MemberConverter().convert(ctx, arg)
                    members.add(m)
                except:
                    try:
                        r = await commands.RoleConverter().convert(ctx, arg)
                        roles.add(r)
                    except:
                        pass

            # check for mentions
            for m in ctx.message.mentions:
                members.add(m)
            for r in ctx.message.role_mentions:
                r.add(r)

        return everyone, list(roles), list(members), time

    # basic role moderation command
    async def role_command(self, ctx, args, add_role, verb, past, present, role_name, role_overwrite, role_color):

        # find role or create if it doesnt exist
        role = None
        for r in ctx.guild.roles:
            if r.name == role_name or r.name == role_name:
                role = r
        if not role:
            role = await ctx.guild.create_role(name=role_name, color=role_color)
            for c in ctx.guild.channels:
                await c.set_permissions(role, overwrite=role_overwrite)

        # check if role is higher than bot
        if role > ctx.guild.get_member(self.client.user.id).top_role:
            await utility.error_message(ctx, f"I can't run this command because the <@&{role.id}> role is higher than me.")
            return

        # parsed args
        everyone, roles, members, time = await self.parse_args(ctx, args)

        # get final list of members
        final_members = self.get_final_members(ctx, everyone, roles, members)

        # check for no members
        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return
        
        # if len(final_members) > 100:
        #     await ctx.send(f"You cannot use this command on more than 100 users at once.")
        #     return

        # set has_role to members that already have/don't have the role and remove them from final_members
        has_role = []
        temp = []
        for m in final_members:
            if (role in m.roles and add_role) or not (role in m.roles or add_role):
                has_role.append(m)
            else:
                temp.append(m)
        final_members = temp

        if has_role:
            # if some members already have the role don't use roles/everyone in the message
            everyone = False
            roles = []
            members = final_members

            if time:
                # send before updating message
                before_string = self.before_update_string(
                    everyone, roles, has_role, time, verb)
                embed, msg_update = await utility.embed_message(ctx, before_string, role_color)
            else:
                # error message if no time
                await utility.error_message(ctx, self.already_error(has_role, past))

        # if there are still members remaining send normal before message
        if everyone or roles or members or final_members:
            before_string = self.before_string(
                everyone, roles, members, time, present)
            embed, msg = await utility.embed_message(ctx, before_string, role_color)

        # update roles
        await self.update_roles(members, role, add_role)

        for m in final_members:
            # if there is already a timer cancel it
            if m.id in self.role_punishments[role_name]:
                current = self.role_punishments[role_name].pop(m.id)
                current.cancel()
            # add a new timer if time is given
            if time:
                self.role_punishments[role_name][m.id] = asyncio.create_task(
                    self.update_role_timed(m, role, add_role, time))

        # send after updated message
        if has_role and time:
            after_string = self.after_update_string(
                everyone, roles, has_role, time, past)
            await msg_update.edit(embed=discord.Embed(description=after_string))

        # send normal after message
        if everyone or roles or members or final_members:
            after_string = self.after_string(
                everyone, roles, members, time, past)
            await msg.edit(embed=discord.Embed(description=after_string))

    @commands.command(aliases=["m"], brief="Prevents a user sending messages", help="%mute [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def mute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await self.role_command(ctx, args, True, "mute", "muted", "muting", "Muted", overwrite, colors.muted_color)
        print(self.role_punishments)

    @commands.command(aliases=["um"], brief="Unmutes a user.", help="%unmute [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unmute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await self.role_command(ctx, args, False, "unmute", "unmuted", "unmuting", "Muted", overwrite, colors.muted_color)
        print(self.role_punishments)

    @commands.command(aliases=["f"], brief="Prevents a user from adding reactions, sending files, sending embeds, or using external emojis.", help="%freeze [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def freeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            add_reactions=False, attach_files=False, embed_links=False, external_emojis=False)
        await self.role_command(ctx, args, True, "freeze", "frozen", "freezing", "Frozen", overwrite, colors.frozen_color)

    @commands.command(aliases=["uf"], brief="Unfreezes a user.", help="%unfreeze [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unfreeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            add_reactions=False, attach_files=False, embed_links=False, external_emojis=False)
        await self.role_command(ctx, args, False, "unfreeze", "unfrozen", "unfreezing", "Frozen", overwrite, colors.frozen_color)

    @commands.command(aliases=["e"], brief="Prevents a user from viewing any channels.", help="%exile [user(s) or role(s) or all] (time)")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def exile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            view_channel=False, read_message_history=False)
        await self.role_command(ctx, args, True, "exile", "exiled", "exiling", "Exiled", overwrite, colors.exiled_color)

    @commands.command(aliases=["ue"], brief="Unexiles a user.", help="%unexile [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unexile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            view_channel=False, read_message_history=False)
        await self.role_command(ctx, args, False, "unexile", "unexiled", "unexiling", "Exiled", overwrite, colors.exiled_color)

    @commands.command(aliases=["b"], brief="Bans a user.", help="%ban [user(s) or role(s) or all] (time)")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, *, args):
        everyone, roles, members, time = await self.parse_args(ctx, args)
        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return

        msg_string = self.generate_message(
            everyone, roles, members, time, "banned")
        await utility.embed_message(ctx, msg_string, colors.ban_color)

        for m in final_members:
            await m.ban()
        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in members:
            await m.unban()

    @commands.command(aliases=["ub"], brief="Unbans a user.", help="%unban [user(s) or role(s) or all] (time)")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, *, args):
        everyone, roles, members, time = await self.parse_args(ctx, args)
        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await ctx.send(embed=discord.Embed(description="No members found.", color=colors.error_color))
            return

        msg_string = self.generate_message(
            everyone, roles, members, time, "unbanned")
        msg = await ctx.send(embed=discord.Embed(description=msg_string, color=colors.ban_color))

        for m in final_members:
            try:
                await m.unban()
            except:
                await msg.edit(embed=discord.Embed(description="No members found.", color=colors.error_color))

        if time <= 0:
            return
        await asyncio.sleep(time)
        for m in members:
            await m.ban()


def setup(client):
    client.add_cog(moderation(client))
