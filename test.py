import pymongo

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']

def time(seconds):
    period_seconds = [86400, 3600, 60, 1]
    period_desc = ['days', 'hours', 'mins', 'secs']
    s = ''
    remainder = seconds
    for i in range(len(period_seconds)):
        q, remainder = divmod(remainder, period_seconds[i])
        if q > 0:
            if s:
                s += ' '
            s += f'{q} {period_desc[i]}'
    return s

print(time(10000))