import os, glob, time, configparser
from datetime import datetime
from pymongo import MongoClient

config_file = 'conf.ini'
config = configparser.ConfigParser()
def getConfig(config_file):
	config.read(config_file)
	settings = (config['DEFAULT'])
	working = config['DEFAULT']['working'] == 'T'
	save_data = config['DEFAULT']['save_data'] == 'T'
	sleep_time = float(settings['sleep_time'])
	Ts_ID = settings['Ts_ID']
	Tc_ID = settings['Tc_ID']
	To_ID = settings['To_ID']
	Ts_set = float(settings['Ts_set'])
	Tc_set = float(settings['Tc_set'])
	To_set = float(settings['To_set'])
	P_1 = float(settings['P_1'])
	I_1 = float(settings['I_1'])
	D_1 = float(settings['D_1'])
	scale_1 = float(settings['scale_1'])
	P_2 = float(settings['P_2'])
	I_2 = float(settings['I_2'])
	D_2 = float(settings['D_2'])
	scale_2 = float(settings['scale_2'])
	P_3 = float(settings['P_3'])
	I_3 = float(settings['I_3'])
	D_3 = float(settings['D_3'])
	scale_3 = float(settings['scale_3'])
	P_4 = float(settings['P_4'])
	I_4 = float(settings['I_4'])
	D_4 = float(settings['D_4'])
	scale_4 = float(settings['scale_4'])
	GAIN = float(settings['GAIN'])
	flow_CH = int(settings['flow_CH'])
	flow_coef = float(settings['flow_coef'])
	flow_set = float(settings['flow_set'])
	liquid_pump_installed = settings['liquid_pump_installed'] == 'T'
	liquid_pump_wait = int(settings['liquid_pump_wait'])
	liquid_pump_switch = int(settings['liquid_pump_switch'])
	db_host = settings['db_host']
	db_port = int(settings['db_port'])
	db_name = settings['db_name']
	col_name = settings['col_name']
	return working, save_data, sleep_time, Ts_ID, Tc_ID, To_ID, Ts_set, Tc_set, To_set, P_1, I_1, D_1, scale_1, P_2, I_2, D_2, scale_2, P_3, I_3, D_3, scale_3, P_4, I_4, D_4, scale_4, GAIN, flow_CH, flow_coef, flow_set, liquid_pump_installed, liquid_pump_wait, liquid_pump_switch, db_host, db_port, db_name, col_name

working, save_data, sleep_time, Ts_ID, Tc_ID, To_ID, Ts_set, Tc_set, To_set, P_1, I_1, D_1, scale_1, P_2, I_2, D_2, scale_2, P_3, I_3, D_3, scale_3, P_4, I_4, D_4, scale_4, GAIN, flow_CH, flow_coef, flow_set, liquid_pump_installed, liquid_pump_wait, liquid_pump_switch, db_host, db_port, db_name, col_name = getConfig(config_file)

db = MongoClient(db_host, db_port)[db_name]
collection = db[col_name]

date_time = datetime.utcnow()

dataDict ={
	'date_time': date_time,
	'concentration': -999,
	'counts': -999,
	'Ts': -999,
	'Tc': -999,
	'To': -999,
	'Td': -999,
	'flow': -999,
	'log': 'start'
	}
collection.insert_one(dataDict)