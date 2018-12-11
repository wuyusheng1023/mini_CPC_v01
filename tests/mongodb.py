
from pymongo import MongoClient
import datetime

db = MongoClient('localhost', 27017)['mini_CPC']
collection = db.data

post = {"date": datetime.datetime.utcnow(),
		"author": "Yu",
        "text": "My first blog post!",
        "tags": ["mongodb", "python", "pymongo"]}

collection.insert_one(post)