import discord
from discord.ext import commands
import math
from os import error
import utility

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

        if isinstance(error, commands.NoPrivateMessage):
            await utility.error_message(ctx, "This command cannot be used in direct messages.")
            return

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 1:
                message = "I need the permissions"
            else:
                message = "I need the permission"
            message += f" `{'`, `'.join(missing)}` to run this command."
            await utility.error_message(ctx, message)
            return

        if isinstance(error, commands.DisabledCommand):
            await utility.error_message(ctx, "This command has been disabled.")
            return

        if isinstance(error, commands.CommandOnCooldown):
            await utility.error_message(ctx, f"This command is on cooldown, please retry in `{math.ceil(error.retry_after)} seconds`.")
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
            if len(missing) > 1:
                message = "You need the permissions"
            else:
                message = "You need the permission"
            message += f" `{'`, `'.join(missing)}` to use this command."
            await utility.error_message(ctx, message)
            return

        if isinstance(error, commands.UserInputError):
            await utility.error_message(ctx, "Invalid input.")
            return

        if isinstance(error, commands.CheckFailure):
            await utility.error_message(ctx, "You do not have permission to use this command.")
            return
        
        print(error)
    
def setup(client):
    client.add_cog(error(client))
