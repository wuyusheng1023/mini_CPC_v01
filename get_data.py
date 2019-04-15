
import configparser
import pandas as pd
from datetime import datetime
from pymongo import MongoClient


# load configuration
config_file = 'conf.ini'
config = configparser.ConfigParser()
def getConfig(config_file):
	config.read(config_file)
	settings = (config['DEFAULT'])
	db_host = settings['db_host']
	db_port = int(settings['db_port'])
	db_name = settings['db_name']
	col_name = settings['col_name']
	return db_host, db_port, db_name, col_name

db_host, db_port, db_name, col_name = getConfig(config_file)

# initialize database
db = MongoClient(db_host, db_port)[db_name]
collection = db[col_name]

# get query
start = input('input start datetime: ')
end = input('input end datetime: ')
file_name = start + '_' + end
start = datetime.strptime(start, '%Y-%m-%d %H:%M')
end = datetime.strptime(end, '%Y-%m-%d %H:%M')
query = {'date_time': {'$gte': start, '$lte': end}}

# load data
cursor = collection.find(query)
df =  pd.DataFrame(list(cursor))

# Delete the _id
if '_id' in df: del df['_id']

# save to .csv
df.to_csv(file_name+'.csv', index=False)
