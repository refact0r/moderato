import pymongo

cluster = pymongo.MongoClient("mongodb+srv://test:gSfnRVdfJgDq35fr@cluster0.8ot2g.mongodb.net/discordbot?retryWrites=true&w=majority")
db = cluster['discordbot']
collection = db['ping']

collection.update_many({'_id': 1}, {'$set': {'time': 200}})