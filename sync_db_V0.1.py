############################################################
############################################################
# yusheng, 2019-01-13
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694


from pymongo import MongoClient

import time

############################################################
############################################################

db_host_local = 'localhost' # MongoDB local host name
db_port_local = 27017 # MongoDB local port
db_name_local = 'mini_CPC' # MongoDB local database name
col_name_local = 'data' # MongoBD local collection name

db_host_server = 'localhost' # MongoDB server
db_port_server = 27017
db_name_server = 'mini_CPC'
col_name_server = 'mini_CPC_001'

db_local = MongoClient(db_host_local, db_port_local)[db_name_local]
col_local = db_local[col_name_local]
db_server = MongoClient(db_host_server, db_port_server)[db_name_server]
col_server = db_local[col_name_server]


############################################################
############################################################

while True:
	lasest_record_server = col_server.find_one(sort=[('date_time', -1)]) # find updated date_time of server
	lasest_time_server = lasest_record_server['date_time']
	query = {'date_time': {'$gt': lasest_time_server}} # query data haven't upload
	doc = col_local.find(query)
	updates_requests = []

	for x in doc:
		updates_requests.append(UpdateOne(x, {'$set': x}, upsert=True))
		print('Data wait for update: %s' % x['date_time'], flush=True)

    if len(updates_requests) > 0:
        update_result = col_sercer.bulk_write(updates_requests, ordered=False)
        print('Updated - inserted: %d, modified: %d' % (update_result.upserted_count, update_result.modified_count), flush=True)

    # time.sleep(1)
