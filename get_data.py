
import os, configparser
import pandas as pd
from datetime import datetime
from pymongo import MongoClient


data_folder = 'data'

dir_path = os.path.dirname(os.path.realpath(__file__))

# load configuration
config_file = dir_path + os.sep + 'conf.ini'
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

data_dir = dir_path + os.sep + data_folder
try:
    # Create target Directory
    os.mkdir(data_dir)
    print("Directory " , data_dir ,  " Created ") 
except FileExistsError:
    print("Directory " , data_dir ,  " already exists")

file_name = data_dir + os.sep + start + '_' + end + '.csv'
print(file_name)
start = datetime.strptime(start, '%Y-%m-%d %H:%M')
end = datetime.strptime(end, '%Y-%m-%d %H:%M')
query = {'date_time': {'$gte': start, '$lte': end}}

# load data
cursor = collection.find(query)
df =  pd.DataFrame(list(cursor))

# Delete the _id
if '_id' in df: del df['_id']

# save to .csv
df.to_csv(file_name, index=False)
