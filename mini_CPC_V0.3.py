############################################################
############################################################
# yusheng, 2019-04-11
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694
#
# hardware: 3*DS18B20+, 1*cooler, 2*heater, 1*fan, 1*air_pump, 1*liquild_pump

import os, glob, time
import numpy as np
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
from simple_pid import PID

############################################################
############################################################

# configuration
sleep_time = 1 # counter interval
Ts_ID = '28-00000afd43ff'
Tc_ID = '28-00000afcb345'
To_ID = '28-00000afd4235'
Ts_set = 40 # temperature set point of saturator
Tc_set = 20 # temperature set point of condensor
To_set = 42 # temperature set point of OPC
P_1 = 10 # PID_1, heater_sat
I_1 = 0.1
D_1 = 0.05 
scale_1 = 0.25
P_2 = 10 # PID_2, cooler
I_2 = 0.1
D_2 = 0.05
scale_2 = 0.5
P_3 = 10 # PID_3, heater_OPC
I_3 = 0.1
D_3 = 0.05
scale_3 = 0.5
P_4 = 1000 # PID_4, air_pump
I_4 = 10
D_4 = 0.05
scale_4 = 0.8
GAIN = 1 # ADC gain
flow_CH = 0 # flow sensor to ADC channel
flow_coef = 15 # flow meter calibartion coefficient
flow_set = 0.2 # L/min
liquid_pump_installed = 1 # 0: no liquid_pump, 1: installed
liquid_pump_wait = 60 # cycles to wait between fill liquid, avoid work too often.
liquid_pump_switch = 2 # cycles to wait to switch, adjust pump speed

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
			print(file)
			device_file = file
	file_split = device_file.split(ID)
	device_file = file_split[0] + ID + file_split[1]
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
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
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
	counter  = 0
	time.sleep(sleep_time)
	counts = counter
	print(f'counts = {counts}')

	## get temperatures
	Ts = read_temp(Ts_file) # saturator temperature
	Tc = read_temp(Tc_file) # condensor temperature
	To = read_temp(To_file) # optics temperature
	print(f'Ts = {Ts}, Tc = {Tc}, To = {To}')

	## change PWM
	dc_1 = pid_1(Ts) # heater duty cycle
	dc_2 = pid_2(2*Tc_set - Tc) # cooler duty cycle
	dc_3 = pid_3(To) # heater_2 duty cycle
	print(f'dc_1 = {dc_1}, dc_2 = {dc_2}, dc_3 = {dc_3}')

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
	flow = flow*0.95 + adc.read_adc(flow_CH, gain=GAIN)/32767*4.096*0.05/flow_coef
	dc_4 = pid_4(flow)
	print(f'flow = {flow}')
	print(f'dc_4 {dc_4}')
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
		print(f'liquid_level_stat: {liquid_level_stat}')
		print(f'liquid_pump_stat: {liquid_pump_stat}')




















