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
        self.bans = {}

    # generate already error string
    def already_error(self, members, action):
        if len(members) == 1:
            return f"The member <@{members[0].id}> is already {action}."
        else:
            return f"The members {', '.join([f'<@{m.id}>' for m in members])} are already {action}."

    # generate already error string
    def higher_error(self, members, action):
        if len(members) == 1:
            return f"I do not have the permissions to {action} the member <@{members[0].id}>."
        else:
            return f"I do not have the permissions to {action} the members {', '.join([f'<@{m.id}>' for m in members])}."

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

    async def update_role_timed(self, member, role, add_role, time):
        await asyncio.sleep(time)
        if add_role:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

    async def ban_timed(self, guild, member, ban, time):
        await asyncio.sleep(time)
        if ban:
            await guild.unban(member)
        else:
            await guild.ban(member)

    async def parse_outside(self, ctx, unparsed):
        members = set()
        for arg in unparsed:
            try:
                m = await commands.UserConverter().convert(ctx, arg)
                members.add(m)
            except:
                pass
        return members

    # parses members from args
    async def parse_args(self, ctx, args):
        args_list = args.split(' ')
        unparsed = []
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
                        unparsed.append(arg)

            # check for mentions
            for m in ctx.message.mentions:
                members.add(m)
            for r in ctx.message.role_mentions:
                r.add(r)

        return unparsed, everyone, roles, members, time

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
        unparsed, everyone, roles, members, time = await self.parse_args(ctx, args)
        roles = list(roles)
        members = list(members)

        # get final list of members
        final_members = self.get_final_members(ctx, everyone, roles, members)

        # check for no members
        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return

        # if len(final_members) > 100:
        #     await ctx.send(f"You cannot use this command on more than 100 users at once.")
        #     return

        # set already to members that already have/don't have the role and remove them from final_members
        already = []
        for m in final_members:
            if (role in m.roles and add_role) or (role not in m.roles and not add_role):
                already.append(m)

        if not time:
            # remove members in already from final_members and members
            for m in already:
                if m in final_members:
                    final_members.remove(m)
                if m in members:
                    members.remove(m)
            
            # send already error
            if already:
                await utility.error_message(ctx, self.already_error(already, past))
                if not final_members:
                    return

        # send before message
        before_string = self.before_string(
            everyone, roles, members, time, present)
        embed, msg = await utility.embed_message(ctx, before_string, role_color)

        for m in final_members:
            if m not in already:
                if add_role:
                    await m.add_roles(role)
                else:
                    await m.remove_roles(role)
            # if there is already a timer cancel it
            if m.id in self.role_punishments[role_name]:
                current = self.role_punishments[role_name].pop(m.id)
                current.cancel()
            # add a new timer if time is given
            if time:
                self.role_punishments[role_name][m.id] = asyncio.create_task(
                    self.update_role_timed(m, role, add_role, time))

        # send after message
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

    @commands.command(aliases=["um"], brief="Unmutes a user.", help="%unmute [user(s) or role(s) or all]")
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unmute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await self.role_command(ctx, args, False, "unmute", "unmuted", "unmuting", "Muted", overwrite, colors.muted_color)

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
        unparsed, everyone, roles, members, time = await self.parse_args(ctx, args)

        if unparsed:
            outside_members = await self.parse_outside(ctx, unparsed)
            members |= outside_members

        roles = list(roles)
        members = list(members)

        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return

        bot_member = ctx.guild.get_member(self.client.user.id)

        # set already to members that already are banned
        already = []
        temp = []
        higher = []
        for m in final_members:
            try:
                banentry = await ctx.guild.fetch_ban(m)
                already.append(m)
            except:
                if m.top_role > bot_member.top_role:
                    higher.append(m)
                else:
                    temp.append(m)
        final_members = temp

        if higher:
            everyone = False
            roles = []
            members = final_members
            await utility.error_message(ctx, self.higher_error(higher, "ban"))

        if already:
            # if some members already have the role don't use roles/everyone in the message
            everyone = False
            roles = []
            members = final_members

            if time:
                # send before updating message
                before_string = self.before_update_string(
                    everyone, roles, already, time, "ban")
                embed, msg_update = await utility.embed_message(ctx, before_string, colors.ban_color)
            else:
                # error message if no time
                await utility.error_message(ctx, self.already_error(already, "banned"))

        # if there are still members remaining send normal before message
        if everyone or roles or members or final_members:
            before_string = self.before_string(
                everyone, roles, members, time, "banning")
            embed, msg = await utility.embed_message(ctx, before_string, colors.ban_color)

        # ban members
        for m in final_members:
            await ctx.guild.ban(m)
            # if there is already a timer cancel it
            if m.id in self.bans:
                current = self.bans.pop(m.id)
                current.cancel()
            # add a new timer if time is given
            if time:
                self.bans[m.id] = asyncio.create_task(
                    self.ban_timed(ctx.guild, m, True, time))

        # send after updated message
        if already and time:
            after_string = self.after_update_string(
                everyone, roles, already, time, "ban")
            await msg_update.edit(embed=discord.Embed(description=after_string))

        # send normal after message
        if everyone or roles or members or final_members:
            after_string = self.after_string(
                everyone, roles, members, time, "banned")
            await msg.edit(embed=discord.Embed(description=after_string))

    @commands.command(aliases=["ub"], brief="Unbans a user.", help="%unban [user(s) or role(s) or all] (time)")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, *, args):
        unparsed, everyone, roles, members, time = await self.parse_args(ctx, args)

        if unparsed:
            outside_members = await self.parse_outside(ctx, unparsed)
            members |= outside_members

        roles = list(roles)
        members = list(members)

        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await ctx.send(embed=discord.Embed(description="No members found.", color=colors.error_color))
            return

        bans = await ctx.guild.bans()
        bans = [ban.user for ban in bans]

        bot_member = ctx.guild.get_member(self.client.user.id)

        already = []
        temp = []
        higher = []
        for m in final_members:
            try:
                banentry = await ctx.guild.fetch_ban(m)
                temp.append(m)
            except:
                if isinstance(m, discord.Member) and m.top_role > bot_member.top_role:
                    higher.append(m)
                else:
                    already.append(m)
        final_members = temp

        print(already)
        print(final_members)
        print(higher)

        if already:
            # if some members already have the role don't use roles/everyone in the message
            everyone = False
            roles = []
            members = final_members

            if time:
                if higher:
                    await utility.error_message(ctx, self.higher_error(higher, "unban"))
                # send before updating message
                before_string = self.before_update_string(
                    everyone, roles, already, time, "unban")
                embed, msg_update = await utility.embed_message(ctx, before_string, colors.ban_color)
            else:
                # error message if no time
                await utility.error_message(ctx, self.already_error(already, "unbanned"))

        # if there are still members remaining send normal before message
        if everyone or roles or members or final_members:
            before_string = self.before_string(
                everyone, roles, members, time, "unbanning")
            embed, msg = await utility.embed_message(ctx, before_string, colors.ban_color)

        # ban members
        for m in final_members:
            await ctx.guild.unban(m)
            # if there is already a timer cancel it
            if m.id in self.bans:
                current = self.bans.pop(m.id)
                current.cancel()
            # add a new timer if time is given
            if time:
                self.bans[m.id] = asyncio.create_task(
                    self.ban_timed(ctx.guild, m, False, time))

        # send after updated message
        if already and time:
            after_string = self.after_update_string(
                everyone, roles, already, time, "unban")
            await msg_update.edit(embed=discord.Embed(description=after_string))

        # send normal after message
        if everyone or roles or members or final_members:
            after_string = self.after_string(
                everyone, roles, members, time, "unbanned")
            await msg.edit(embed=discord.Embed(description=after_string))


def setup(client):
    client.add_cog(moderation(client))
