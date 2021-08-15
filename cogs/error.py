import discord
from discord.ext import commands
import math
from os import error
import utils.colors
import utils.utility
import traceback
import sys


class error(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # if command has local error handler, return
        if hasattr(ctx.command, 'on_error'):
            return

        # get the original exception
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.UserInputError):
            await utils.utility.error_message(ctx, "Invalid input.")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await utils.utility.error_message(ctx, f"This command is on cooldown, please retry in `{math.ceil(error.retry_after)} seconds`.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            await utils.utility.error_message(ctx, "This command cannot be used in direct messages.")
            return

        if isinstance(error, commands.DisabledCommand):
            await utils.utility.error_message(ctx, "This command has been disabled.")
            return

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace(
                'guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 1:
                message = "I need the permissions"
            else:
                message = "I need the permission"
            message += f" `{'`, `'.join(missing)}` to run this command."
            await utils.utility.error_message(ctx, message)
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace(
                'guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 1:
                message = "You need the permissions"
            else:
                message = "You need the permission"
            message += f" `{'`, `'.join(missing)}` to use this command."
            await utils.utility.error_message(ctx, message)
            return

        if isinstance(error, commands.CheckFailure):
            await utils.utility.error_message(ctx, "You do not have permission to use this command.")
            return

        if isinstance(error, discord.Forbidden):
            await utils.utility.error_message(ctx, "I do not have permission to run this command.")

        print('Ignoring exception in command {}:'.format(
            ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)


def setup(client):
    client.add_cog(error(client))
