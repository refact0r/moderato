import asyncio
import discord
from discord.ext import commands
import pymongo
from utils import colors, utility, strings
import os


class moderation(commands.Cog):
    """Commands for user moderation."""

    def __init__(self, client):
        self.client = client
        self.words = {
            "mute": ["muted", "muting", "Muted"],
            "unmute": ["unmuted", "unmuting", "Muted"],
            "freeze": ["frozen", "freezing", "Frozen"],
            "unfreeze": ["unfrozen", "unfreezing", "Frozen"],
            "exile": ["exiled", "exiling", "Exiled"],
            "unexile": ["unexiled", "unexiling", "Exiled"],
        }
        self.role_punishments = {"Muted": {}, "Frozen": {}, "Exiled": {}}
        self.bans = {}

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

    async def update_role_timed(self, member, role, add_bool, time):
        await asyncio.sleep(time)
        if add_bool:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

    async def ban_timed(self, guild, member, ban_bool, time):
        await asyncio.sleep(time)
        if ban_bool:
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
    async def parse_args(self, ctx, args, time_bool):
        args_list = args.split(" ")
        unparsed = []
        parsed = False
        everyone = False
        members = set()
        roles = set()
        time = 0

        # check for time
        if len(args_list) > 1 and time_bool:
            time = utility.parse_time(args_list[-1])
            if time > 0:
                args_list = args_list[:-1]
                args = " ".join(args_list)

        # check for "all" and @everyone
        if len(args_list) == 1 and (
            "all" in args_list
            or "everyone" in args_list
            or ctx.message.mention_everyone
        ):
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
    async def role_command(
        self, ctx, args, add_bool, command, role_overwrite, role_color
    ):
        past, present, role_name = self.words[command]

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
            await utility.error_message(
                ctx,
                f"I can't run this command because the <@&{role.id}> role is higher than me.",
            )
            return

        # parsed args
        unparsed, everyone, roles, members, time = await self.parse_args(
            ctx, args, True
        )
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
            if (role in m.roles and add_bool) or (role not in m.roles and not add_bool):
                already.append(m)

        if not time and already:
            for m in already:
                if m in final_members:
                    final_members.remove(m)
                if m in members:
                    members.remove(m)
            await utility.error_message(
                ctx, strings.already_error_string(already, past)
            )
            if not final_members:
                return

        # send before message
        before_string = strings.before_string(everyone, roles, members, time, present)
        embed, msg = await utility.embed_message(ctx, before_string, role_color)

        for m in final_members:
            if m not in already:
                if add_bool:
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
                    self.update_role_timed(m, role, add_bool, time)
                )

        # send after message
        after_string = strings.after_string(everyone, roles, members, time, past)
        await msg.edit(embed=discord.Embed(description=after_string, color=role_color))

    @commands.command(
        aliases=["m"],
        brief="Prevents a user sending messages",
        help="%mute [user(s) or role(s) or all] (time)",
        description="""
            Gives targeted users the Muted role, preventing them from sending messages.
            You can target users by adding their username, nickname, id or mentioning them.
            You can also target users with a certain role.
            You can target everyone in the server by adding "all" or @everyone.
            Add a time at the end of the command to mute users for a certain amount of time.

            **Examples**
            ```%mute user1``````%mute role1 user2 @user3``````%mute role1 user2 @user3 3h``````%mute all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def mute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await self.role_command(ctx, args, True, "mute", overwrite, colors.muted_color)

    @commands.command(
        aliases=["um"],
        brief="Unmutes a user.",
        help="%unmute [user(s) or role(s) or all]",
        description="""
            Same as `%mute` (do `%help mute` for more info), but removes the Muted role instead.
            Unmuting a users with a time will cause them to be muted again when the time has passed.

            **Examples**
            ```%unmute user1``````%unmute role1 user2 @user3``````%unmute role1 user2 @user3 3h``````%unmute all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unmute(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await self.role_command(
            ctx, args, False, "unmute", overwrite, colors.muted_color
        )

    @commands.command(
        aliases=["f"],
        brief="Prevents a user from reacting or sending files.",
        help="%freeze [user(s) or role(s) or all] (time)",
        description="""
            Gives targeted users the Frozen role, preventing them from sending files/embeds, adding reactions, or using external emojis.
            You can target users by adding their username, nickname, id, or mentioning them.
            You can also target users with a certain role.
            You can target everyone in the server by adding "all" or @everyone.
            Add a time at the end of the command to freeze users for a certain amount of time.

            **Examples**
            ```%freeze user1``````%freeze role1 user2 @user3``````%freeze role1 user2 @user3 3h``````%freeze all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def freeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            add_reactions=False,
            attach_files=False,
            embed_links=False,
            external_emojis=False,
        )
        await self.role_command(
            ctx, args, True, "freeze", overwrite, colors.frozen_color
        )

    @commands.command(
        aliases=["uf"],
        brief="Unfreezes a user.",
        help="%unfreeze [user(s) or role(s) or all]",
        description="""
            Same as `%freeze` (do `%help freeze` for more info), but removes the Frozen role instead.
            Unfreezing a users with a time will cause them to be frozen again when the time has passed.

            **Examples**
            ```%unfreeze user1``````%unfreeze role1 user2 @user3``````%unfreeze role1 user2 @user3 3h``````%unfreeze all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unfreeze(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            add_reactions=False,
            attach_files=False,
            embed_links=False,
            external_emojis=False,
        )
        await self.role_command(
            ctx, args, False, "unfreeze", overwrite, colors.frozen_color
        )

    @commands.command(
        aliases=["e"],
        brief="Prevents a user from viewing any channels.",
        help="%exile [user(s) or role(s) or all] (time)",
        description="""
            Gives targeted users the Exiled role, preventing them from viewing normal channels.
            You can target users by adding their username, nickname, id, or mentioning them.
            You can also target users with a certain role.
            You can target everyone in the server by adding "all" or @everyone.
            Add a time at the end of the command to exile users for a certain amount of time.

            **Examples**
            ```%freeze user1``````%freeze role1 user2 @user3``````%freeze role1 user2 @user3 3h``````%freeze all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def exile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            view_channel=False, read_message_history=False
        )
        await self.role_command(
            ctx, args, True, "exile", overwrite, colors.exiled_color
        )

    @commands.command(
        aliases=["ue"],
        brief="Unexiles a user.",
        help="%unexile [user(s) or role(s) or all]",
        description="""
            Same as `%exile` (do `%help exile` for more info), but removes the Exiled role instead.
            Unexiling a users with a time will cause them to be exiled again when the time has passed.

            **Examples**
            ```%unexile user1``````%unexile role1 user2 @user3``````%unexile role1 user2 @user3 3h``````%unexile all```
        """,
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def unexile(self, ctx, *, args):
        overwrite = discord.PermissionOverwrite(
            view_channel=False, read_message_history=False
        )
        await self.role_command(
            ctx, args, False, "unexile", overwrite, colors.exiled_color
        )

    @commands.command(
        aliases=["b"],
        brief="Bans a user.",
        help="%ban [user(s) or role(s) or all] (time)",
        description="""
            Bans targeted users.
            You can target users by typing their username, nickname or mentioning them.
            You can also target users with a certain role.
            Add a time at the end of the command to ban users for a certain amount of time.

            **Examples**
            ```%ban user1``````%ban role1 user2 @user3``````%ban role1 user2 @user3 3h```
        """,
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, ctx, *, args):
        unparsed, everyone, roles, members, time = await self.parse_args(
            ctx, args, True
        )

        roles = list(roles)
        members = list(members)

        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return

        bans = await ctx.guild.bans()
        bans = [ban.user for ban in bans]

        bot_member = ctx.guild.get_member(self.client.user.id)

        already = []
        higher = []
        for m in final_members:
            try:
                banentry = await ctx.guild.fetch_ban(m)
                already.append(m)
            except:
                if m.top_role >= bot_member.top_role:
                    higher.append(m)

        if higher:
            for m in higher:
                if m in final_members:
                    final_members.remove(m)
                if m in members:
                    members.remove(m)
            await utility.error_message(ctx, strings.higher_error_string(higher, "ban"))

        if not time and already:
            for m in already:
                if m in final_members:
                    final_members.remove(m)
                if m in members:
                    members.remove(m)
            await utility.error_message(
                ctx,
                strings.already_error_string(already, "banned"),
            )
            if not final_members:
                return

        # send before message
        before_string = strings.before_string(everyone, roles, members, time, "banning")
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
                    self.ban_timed(ctx.guild, m, True, time)
                )

        # send after message
        after_string = strings.after_string(everyone, roles, members, time, "banned")
        await msg.edit(
            embed=discord.Embed(description=after_string, color=colors.ban_color)
        )

    @commands.command(
        aliases=["ub"],
        brief="Unbans a user.",
        help="%unban [user(s) or role(s) or all] (time)",
        description="""
            Unbans targeted users.
            You can target users by typing their username or id.
            You can unban all banned users by adding "all".
            Unbanning a users with a time will cause them to be banned again when the time has passed.

            **Examples**
            ```%unban user1``````%unban user1 user2 3h``````%unban all```
        """,
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, ctx, *, args):
        users = set()
        time = 0
        args_list = args.split(" ")

        if len(args_list) > 1:
            time = utility.parse_time(args_list[-1])
            if time > 0:
                args_list = args_list[:-1]
                args = " ".join(args_list)

        bans = await ctx.guild.bans()
        ban_ids = [m.user.id for m in bans]

        if len(args_list) == 1 and "all" in args_list:
            for banentry in bans:
                users.add(banentry.user)

        if not users:
            try:
                u = await commands.UserConverter().convert(ctx, args)
                users.add(u)
                parsed = True
            except:
                pass

        if not users:
            for arg in args_list:
                try:
                    u = await commands.UserConverter().convert(ctx, arg)
                    users.add(u)
                except:
                    pass

            for u in ctx.message.mentions:
                users.add(u)

        users = list(users)

        if not users:
            await utility.error_message(ctx, "No users found.")
            return

        already = []
        for u in users:
            if u.id not in ban_ids:
                already.append(u)

        if not time and already:
            for u in already:
                if u in users:
                    users.remove(u)
            await utility.error_message(
                ctx, strings.already_error_string(already, "unbanned")
            )
            if not users:
                return

        # send before message
        before_string = strings.before_string(False, [], users, time, "unbanning")
        embed, msg = await utility.embed_message(ctx, before_string, colors.ban_color)

        for u in users:
            if u not in already:
                await ctx.guild.unban(u)
            # if there is already a timer cancel it
            if u.id in self.bans:
                current = self.bans.pop(u.id)
                current.cancel()
            # add a new timer if time is given
            if time:
                self.bans[u.id] = asyncio.create_task(
                    self.ban_timed(ctx.guild, u, False, time)
                )

        # send after message
        after_string = strings.after_string(False, [], users, time, "unbanned")
        await msg.edit(
            embed=discord.Embed(description=after_string, color=colors.ban_color)
        )

    @commands.command(
        aliases=["k"],
        brief="Kicks a user.",
        help="%kick [user(s) or role(s) or all] (time)",
        description="""
            Kicks targeted users.
            You can target users by typing their username, nickname or mentioning them.
            You can also target users with a certain role.
            Add a time at the end of the command to kick users for a certain amount of time.

            **Examples**
            ```%kick user1``````%kick role1 user2 @user3``````%kick role1 user2 @user3 3h```
        """,
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, ctx, *, args):
        unparsed, everyone, roles, members, time = await self.parse_args(
            ctx, args, False
        )

        roles = list(roles)
        members = list(members)

        final_members = self.get_final_members(ctx, everyone, roles, members)

        if not final_members:
            await utility.error_message(ctx, "No members found.")
            return

        bot_member = ctx.guild.get_member(self.client.user.id)

        higher = []
        for m in final_members:
            if m.top_role >= bot_member.top_role:
                if m in final_members:
                    final_members.remove(m)
                if m in members:
                    members.remove(m)
                higher.append(m)

        if higher:
            await utility.error_message(
                ctx, strings.higher_error_string(higher, "kick")
            )

        # send before message
        before_string = strings.before_string(everyone, roles, members, time, "kicking")
        embed, msg = await utility.embed_message(ctx, before_string, colors.kick_color)

        # ban members
        for m in final_members:
            await ctx.guild.kick(m)

        # send after message
        after_string = strings.after_string(everyone, roles, members, time, "kicked")
        await msg.edit(
            embed=discord.Embed(description=after_string, color=colors.kick_color)
        )

    @commands.command(
        aliases=["p"],
        brief="Purges messages.",
        help="%purge [number]",
        description="""
            Purges a certain number of messages.

            **Examples**
            ```%purge 10```
        """,
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @commands.guild_only()
    async def purge(self, ctx, amount: int):
        deleted = await ctx.channel.purge(limit=amount + 1)


def setup(client):
    client.add_cog(moderation(client))
