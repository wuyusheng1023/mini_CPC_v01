############################################################
############################################################
# yusheng, 2019-01-12
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694
#
# hardware: 3*PT1000, 1*cooler, 1*heater, 1*fan, 1*air_flow_sensor, 1*liquid_sensor, 1*liquid_pump


import RPi.GPIO as GPIO
import board
import busio
import digitalio

import adafruit_max31865 # PT1000 temperature module

import adafruit_ads1x15.ads1115 as ADS # ADC module
from adafruit_ads1x15.analog_in import AnalogIn

import numpy as np

import time
from datetime import datetime

from simple_pid import PID

from pymongo import MongoClient

############################################################
############################################################

# sync system time if there is a internet connection

# GPIO.cleanup()

# wiring input:
GPIO_OPC = 4 # GPIO04: counter, input
# GPIO_liquid_level = 27 # liquid sensor, input

# wiring outut:
GPIO_Ts = 5 # GPIO05: sensor_1 output, MAX31865 select, saturator temperature
GPIO_Tc = 6 # GPIO06: sensor_2 output, MAX31865 select, comdensor temperature
GPIO_To = 13 # GPIO13: sensor_3 output, MAX31865 select, optic temperature
GPIO_cooler = 20 # GPIO23: PWM output, cooler
GPIO_heater = 24 # GPIO24: PWM output, heater
GPIO_air_pump = 25 # GPIO25: PWM output, air pump
GPIO_fan = 18 # output, fan
GPIO_liquid_pump = 17 # output, liqiud pump

# configuration
sleep_time = 1 # counter interval
Td_set = 20 # temperature difference setpoint between saturator and condensor
Td_set_2 = 5 # temperature difference setpoint between saturator and optic
P_1 = 1 # PID_1
I_1 = 0.1
D_1 = 0.05 
P_2 = 10 # PID_2
I_2 = 0.1
D_2 = 0.05
P_3 = 0.001 # PID_3
I_3 = 0.01
D_3 = 0.0
flow_set = 500 # SCCM
flow_sensor_zero = 1.25 # volts
flow_sensor_fullscale = 4.1 # volts
liquid_pump_wait = 60 # cycles to wait between fill liquid, avoid work too often.
liquid_pump_switch = 2 # cycles to wait to switch, adjust pump speed
db_host = 'localhost' # MongoDB host name
db_port = 27017 # MongoDB port
db_name = 'mini_CPC' # MongoDB database name
col_name = 'data' # MongoDB collection name
switch_cycle = 1 # solenoid pump cycle

# initialize GPIO
GPIO.cleanup() # Rrest ports
GPIO.setwarnings(False) # do not show any warnings
GPIO.setmode(GPIO.BCM) # programming the GPIO by BCM pin numbers. (PIN35 as ‘GPIO19’)
GPIO.setup(GPIO_OPC, GPIO.IN) # input, counter
# GPIO.setup(GPIO_liquid_level, GPIO.IN) # input, liquid level
GPIO.setup(GPIO_cooler,GPIO.OUT) # output, cooler
GPIO.setup(GPIO_heater,GPIO.OUT) # output, heater
GPIO.setup(GPIO_air_pump,GPIO.OUT) # output, air pump
GPIO.setup(GPIO_fan,GPIO.OUT) # output, fan
GPIO.setup(GPIO_liquid_pump,GPIO.OUT) # output, liquid pump

# initialize SPI temperature board
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5) # Chip select of the MAX31865 board: saturator temperature
sensor_1 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D6) # Chip select of the MAX31865 board: condensor temperature
sensor_2 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D13) # Chip select of the MAX31865 board: optic temperature
sensor_3 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)

# initialize I2C ADC board
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c) # create the ADC object

# initialize pulse counter
def conterPlus(channel):
	global counter
	if GPIO.input(channel) > 0.5:
		counter = counter + 1

GPIO.add_event_detect(GPIO_OPC, GPIO.RISING, callback=conterPlus)
counter = 0

# initialize temperature sensors, PID and PWM
pid_1 = PID(P_1, I_1, D_1, setpoint=Td_set) # PID for Peltier cooler
pwm_1 = GPIO.PWM(GPIO_cooler,100) # PWM output, with 100Hz frequency, cooler
pwm_1.start(0) # generate PWM signal with 0% duty cycle
pid_2 = PID(P_2, I_2, D_2, setpoint=Td_set_2) # optic
pwm_2 = GPIO.PWM(GPIO_heater,100)
pwm_2.start(0)

# initialize flow rate, air pump
pid_3 = PID(P_3, I_3, D_3, setpoint=flow_set) # air pump
pwm_3 = GPIO.PWM(GPIO_air_pump,100)
pwm_3.start(0)

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
	chan = AnalogIn(ads, ADS.P1) # create the analog input channel
	# print('chan.voltage  = %f.2' % chan.voltage)
	if chan.voltage > 0.2 : # liquid empty
		level_stat_arr[0] = 1
	else:
		level_stat_arr[0] = 0
	# print('level_stat(1-empty, 0-full) = %d' % (level_stat_arr[0]))
	return level_stat_arr

def liquid_pump(on): # switch pump
	if on == 1:
		GPIO.output(GPIO_liquid_pump,GPIO.HIGH)
	elif on == 0:
		GPIO.output(GPIO_liquid_pump,GPIO.LOW)

def liquid_pump_act(level_start_arr, pump_stat_arr, switch_cycle): # swith pump if matchs condition
	# print(level_start_arr)
	# print(pump_stat_arr)
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

while True:

	print('************************************************************************')

	## OPC counter
	# counter  = 0
	time.sleep(sleep_time)
	counts = counter
	print('counts = %d' % counts)

	## get temperatures
	Ts = sensor_1.temperature # saturator temperature
	Tc = sensor_2.temperature # condensor temperature
	To = sensor_3.temperature # optic temperature
	Td = Ts - Tc # temperature difference between saturator and condensor
	Td_2 = To - Ts
	print('Ts = %.1f, Tc = %.1f, To = %.1f, Td = %.1f, Td_2 = %.1f' % (Ts, Tc, To, Td, Td_2))

	## flow rate
	chan = AnalogIn(ads, ADS.P0) # create the analog input channel
	flow_voltage = chan.voltage # Volts
	flow = 1000*(flow_voltage-flow_sensor_zero)/(flow_sensor_fullscale-flow_sensor_zero) # SCCM
	print('flow_voltage = %f, flow = %d' % (flow_voltage, flow))

	## change PWM
	pid_2.setpoint = Ts + Td_set_2 # set OPC temperature 5 degree higher than saturator
	dc_1 = pid_1(Td) # cooler duty cycle
	dc_2 = pid_2(To) # heater duty cycle
	dc_3 = pid_3(flow) # air pump duty cycle
	print('cooler PWM = %.1f, heater PWM = %.1f, air pump PWM = %.1f' % (dc_1, dc_2, dc_3))
	if Td_2 < Td_set_2/2: # make sure To higher than Ts
		dc_1 = 0 # if To not higher enough than Ts, cooler shoudn't work
		print('Td_2 < Td_set_2/2')
	elif dc_1 > 100: # duty cycle should between 0-100
		dc_1 = 100
	elif dc_1 < 0:
		dc_1 = 0
	if dc_2 > 100: # duty cycle should between 0-100
		dc_2 = 100
	elif dc_2 < 0:
		dc_2 = 0
	if dc_3 > 100: # duty cycle should between 0-100
		dc_3 = 100
	elif dc_3 < 0:
		dc_3 = 0
	pwm_1.ChangeDutyCycle(dc_1) # change cooler PWM
	pwm_2.ChangeDutyCycle(dc_2) # change heater PWM
	pwm_3.ChangeDutyCycle(dc_3) # change air pump PWM
	# print('cooler PWM = %.1f, heater PWM = %.1f, air pump PWM = %.1f' % (dc_1, dc_2, dc_3))

	## butonal level and fill
	liquid_level_stat = get_liquid_level(liquid_level_stat)
	liquid_pump_stat = liquid_pump_act(liquid_level_stat, liquid_pump_stat, switch_cycle)
	print('liquid levle = %d, liquid pump = %d' % (liquid_level_stat[0], liquid_pump_stat[0]))

	## get system date-time in UTC
	date_time = datetime.utcnow()
	# print('date time = %s' % date_time)

	## get logs
	log = 'OK'
	# print('log = %s' % log)

	## all data into python dictionary then write to mongodb
	concentration = (counts/flow)*1000 # particles/cm^3 in standard condition
	dataDict =	{
		'date_time': date_time,
		'concentration': concentration,
		'counts': counts,
		'Ts': Ts,
		'Tc': Tc,
		'To': To,
		'Td': Td,
		'flow': flow,
		'log': log
	}
	# collection.insert_one(dataDict)
	# print(dataDict)

	## watch dog


