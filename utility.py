import discord
from decimal import Decimal

# parse time in seconds from string
def parse_time(string):
    string = string.lower()
    total_seconds = Decimal('0')
    prev_num = []
    for character in string:
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

# convert time in seconds to readable string
def time_string(seconds):
    period_seconds = [86400, 3600, 60, 1]
    period_desc = ['days', 'hours', 'minutes', 'seconds']
    s = ''
    remainder = seconds
    for i in range(len(period_seconds)):
        q, remainder = divmod(remainder, period_seconds[i])
        if q > 0:
            if s:
                s += ' '
            s += f'{int(q)} {period_desc[i]}'
    return s

# show message in embed
async def embed_message(ctx, message, color):
    embed = discord.Embed(
        description = message,
        color = color
    )
    await ctx.send(embed = embed)

# show error message in embed
async def error_message(ctx, message):
    embed = discord.Embed(
        description = message,
        color = discord.Color(0xe64545)
    )
    await ctx.send(embed = embed)