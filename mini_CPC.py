############################################################
############################################################
# yusheng, 2019-04-11
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694
#
# hardware: 3*DS18B20+, 1*cooler, 2*heater, 1*fan, 1*air_pump, 1*liquild_pump

import os, glob, time, configparser
import numpy as np
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
from datetime import datetime
from simple_pid import PID
from pymongo import MongoClient

############################################################
############################################################

# load configuration
dir_path = os.path.dirname(os.path.realpath(__file__))
print(os.path.realpath(__file__))
print(dir_path)
print('-----')
config_file = dir_path + os.sep + 'conf.ini'
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

# list of GPIO
PIN_3 = 2
PIN_5 = 3
PIN_7  = 4
PIN_11 = 17
PIN_12 = 18
PIN_13 = 27
PIN_15 = 22
PIN_16 = 23
PIN_18 = 24
PIN_19 = 10
PIN_21 = 9
PIN_22 = 25
PIN_23 = 11
PIN_24 = 8
PIN_26 = 7
PIN_27 = 0
PIN_28 = 1
PIN_29 = 5
PIN_31 = 6
PIN_32 = 12
PIN_33 = 13
PIN_35 = 19
PIN_36 = 16
PIN_37 = 26
PIN_38 = 20
PIN_40 = 21

# wiring input:
GPIO_OPC = PIN_11
GPIO_liquid_level = PIN_37

# wiring outut:
GPIO_heater_sat = PIN_12
GPIO_cooler = PIN_16
GPIO_heater_OPC = PIN_18
GPIO_air_pump = PIN_22
GPIO_liquid_pump = PIN_24
GPIO_fan = PIN_26

# initialize GPIO
GPIO.cleanup() # Reset ports
GPIO.setwarnings(False) # do not show any warnings
GPIO.setmode(GPIO.BCM) # programming the GPIO by BCM pin numbers.
GPIO.setup(GPIO_OPC, GPIO.IN) # input, counter
GPIO.setup(GPIO_liquid_level, GPIO.IN) # input
GPIO.setup(GPIO_heater_sat,GPIO.OUT) # output, saturator heater
GPIO.setup(GPIO_cooler,GPIO.OUT) # output, cooler
GPIO.setup(GPIO_heater_OPC,GPIO.OUT) # output, saturator heater
GPIO.setup(GPIO_air_pump,GPIO.OUT) # output
GPIO.setup(GPIO_liquid_pump,GPIO.OUT) # output
GPIO.setup(GPIO_fan,GPIO.OUT) # output

# initialize pulse counter
def conterPlus(channel):
	global counter
	counter = counter + 1

GPIO.add_event_detect(GPIO_OPC, GPIO.RISING, callback=conterPlus)
counter = 0

# initialize temperature sensor
base_dir = '/sys/bus/w1/devices/'
folders = glob.glob(base_dir + '28*')
temp_device_files = [folder + '/w1_slave' for folder in folders]

def get_file(ID, files):
	for file in files:
		if ID in file:
			# print(file)
			device_file = file
	try:
		file_split = device_file.split(ID)
		device_file = file_split[0] + ID + file_split[1]
	except ValueError:
		print('Tempreture sensors have not been well configured!')
	return device_file

Ts_file = get_file(Ts_ID, temp_device_files)
Tc_file = get_file(Tc_ID, temp_device_files)
To_file = get_file(To_ID, temp_device_files)

def read_temp_raw(device_file):
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp(device_file):
	lines = read_temp_raw(device_file)
	count = 0
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
		count = count + 1
		if count > 10:
			raise Exception('cannot temperature from file: ' + device_file)

	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		return temp_c

pid_1 = PID(P_1, I_1, D_1, setpoint=Ts_set) # heater sat
pwm_1 = GPIO.PWM(GPIO_heater_sat,10) # PWM output, with 
pwm_1.start(0) # generate PWM signal with 0% duty cycle
pid_2 = PID(P_2, I_2, D_2, setpoint=Tc_set)
pwm_2 = GPIO.PWM(GPIO_cooler,10)
pwm_2.start(0)
pid_3 = PID(P_3, I_3, D_3, setpoint=To_set)
pwm_3 = GPIO.PWM(GPIO_heater_OPC,10)
pwm_3.start(0)

# initialize flow rate, air pump
flow = 0
adc = Adafruit_ADS1x15.ADS1115() # create the ADC object
pid_4 = PID(P_4, I_4, D_4, setpoint=flow_set) # air pump
pwm_4 = GPIO.PWM(GPIO_air_pump,50)
pwm_4.start(0)

# initialize fan
def fan(on):
	if on == 1:
		GPIO.output(GPIO_fan,GPIO.HIGH)
	elif on == 0:
		GPIO.output(GPIO_fan,GPIO.LOW)

fan(1)

# initialize liquid sensor, liquid pump
def get_liquid_level(level_stat_arr): # record liquid level
	level_stat_arr = np.roll(level_stat_arr, 1)
	liquid_full = GPIO.input(GPIO_liquid_level)
	if liquid_full :
		level_stat_arr[0] = 1
	else:
		level_stat_arr[0] = 0
	return level_stat_arr

def liquid_pump(on): # switch pump
	if on == 1:
		GPIO.output(GPIO_liquid_pump,GPIO.HIGH)
	elif on == 0:
		GPIO.output(GPIO_liquid_pump,GPIO.LOW)

def liquid_pump_act(level_start_arr, pump_stat_arr, switch_cycle):
	stat = pump_stat_arr[0:switch_cycle]
	pump_stat_arr = np.roll(pump_stat_arr, 1)
	if level_start_arr[0] == 1: # if liquid is empty
		print('... liquid pump is working ...')
		if np.unique(stat).size == 1: # if few cycle all the same then switch
			liquid_pump(stat[0])
			pump_stat_arr[0] = not(stat[0])
		else:
			liquid_pump(stat[0])
			pump_stat_arr[0] = stat[0]
	else:
		liquid_pump(0)
		pump_stat_arr[0] = 0
	return pump_stat_arr

liquid_level_stat = np.zeros(liquid_pump_wait)
liquid_pump_stat = np.zeros(liquid_pump_wait)
liquid_pump(0)

# initialize database
db = MongoClient(db_host, db_port)[db_name]
collection = db[col_name]
if save_data:
	date_time = datetime.utcnow() # get system date-time in UTC
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


############################################################
############################################################

print('************************')
print('************************')
print('**** mini_CPC start ****')
print('************************')
print('************************')

while working:

	print('************************************************************************')

	# load settings
	working, save_data, sleep_time, Ts_ID, Tc_ID, To_ID, Ts_set, Tc_set, To_set, P_1, I_1, D_1, scale_1, P_2, I_2, D_2, scale_2, P_3, I_3, D_3, scale_3, P_4, I_4, D_4, scale_4, GAIN, flow_CH, flow_coef, flow_set, liquid_pump_installed, liquid_pump_wait, liquid_pump_switch, db_host, db_port, db_name, col_name = getConfig(config_file)

	# get datettime
	date_time = datetime.utcnow() # get system date-time in UTC
	print(date_time)

	## OPC counter
	counter  = 0
	time.sleep(sleep_time)
	counts = counter
	print(counts)

	## get temperatures
	Ts = read_temp(Ts_file) # saturator temperature
	Tc = read_temp(Tc_file) # condensor temperature
	To = read_temp(To_file) # optics temperature
	print(round(Ts, 2), end = ' ,')
	print(round(Tc, 2), end = ' ,')
	print(round(To, 2))

	## change PWM
	pid_1 = PID(P_1, I_1, D_1, setpoint=Ts_set)
	pid_2 = PID(P_2, I_2, D_2, setpoint=Tc_set)
	pid_3 = PID(P_3, I_3, D_3, setpoint=To_set)
	dc_1 = pid_1(Ts) # heater duty cycle
	dc_2 = pid_2(2*Tc_set - Tc) # cooler duty cycle
	dc_3 = pid_3(To) # heater_2 duty cycle
	print(round(dc_1, 1), end = ' ,')
	print(round(dc_2, 1), end = ' ,')
	print(round(dc_3, 1))
	if dc_1 > 100: # duty cycle should between 0-100
		dc_1 = 100
	elif dc_1 < 0:
		dc_1 = 0
	dc_1 = dc_1*scale_1
	if dc_2 > 100: # duty cycle should between 0-100
		dc_2 = 100
	elif dc_2 < 0:
		dc_2 = 0
	dc_2 = dc_2*scale_2
	if dc_3 > 100: # duty cycle should between 0-100
		dc_3 = 100
	elif dc_3 < 0:
		dc_3 = 0
	dc_3 = dc_3*scale_3
	pwm_1.ChangeDutyCycle(dc_1)
	pwm_2.ChangeDutyCycle(dc_2)
	pwm_3.ChangeDutyCycle(dc_3)

	## flow rate
	flow = 0.9*flow + 0.1*(adc.read_adc(flow_CH, gain=GAIN)/32767)*4.096*flow_coef
	dc_4 = pid_4(flow)
	print(round(flow, 3))
	print(round(dc_4, 1))
	if dc_4 > 100: # duty cycle should between 0-100
		dc_4 = 100
	elif dc_4 < 0:
		dc_4 = 0
	dc_4 = dc_4*scale_4
	pwm_4.ChangeDutyCycle(dc_4)

	## butonal level and fill
	if liquid_pump_installed == 1:
		liquid_level_stat = get_liquid_level(liquid_level_stat)
		liquid_pump_stat = liquid_pump_act(liquid_level_stat, liquid_pump_stat, liquid_pump_switch)
		print(liquid_level_stat)
		print(liquid_pump_stat)

	# log
	if abs(Ts-Ts_set)>2 or abs(Tc-Tc_set)>2 or abs(To-To_set)>2 or abs(flow-flow_set)>0.05:
		log = 'X'
	else:
		log = 'OK'
	print(log)

	# calculate number concentration
	if log == 'OK':
		conc = counts/(flow*1000/60)/sleep_time
	else:
		conc = 0
	print(round(conc))

	# write to database
	# print(save_data)
	if save_data:
		# print(dataDict)
		dataDict ={
			'date_time': date_time,
			'concentration': conc,
			'counts': counts,
			'Ts':Ts,
			'Tc': Tc,
			'To': To,
			'flow': flow,
			'log': log
			}
		collection.insert_one(dataDict)

############################################################
############################################################

# exit
print('************************************************************************')

# ending database
if save_data:
	date_time = datetime.utcnow() # get system date-time in UTC
	dataDict ={
		'date_time': date_time,
		'concentration': -999,
		'counts': -999,
		'Ts': -999,
		'Tc': -999,
		'To': -999,
		'flow': -999,
		'log': 'end'
		}
	collection.insert_one(dataDict)

GPIO.cleanup() # Reset ports

print('************************')
print('************************')
print('*********  bye *********')
print('************************')
print('************************')

