############################################################
############################################################
# yusheng, 2018-12-11
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694
#
# wiring:
# GPIO04: counter input
# GPIO05: sensor_1 output, MAX31865 select, saturator temperature
# GPIO06: sensor_2 output, MAX31865 select, comdensor temperature
# GPIO13: sensor_3 output, MAX31865 select, optic temperature
# GPIO23: PWM output, cooler
# GPIO24: PWM output, heater

import RPi.GPIO as GPIO
import board
import busio
import digitalio
import adafruit_max31865

import time
from datetime import datetime

from simple_pid import PID

from pymongo import MongoClient

############################################################
############################################################

# sync system time if there is a internet connection

# initialzie GPIO
GPIO.cleanup() # Rrest ports
GPIO.setwarnings(False) # do not show any warnings
GPIO.setmode(GPIO.BCM) # programming the GPIO by BCM pin numbers. (PIN35 as ‘GPIO19’)

# initialize pulse counter
GPIO.setup(4, GPIO.IN) # GPIO8 as counter input
counter = 0

def conterPlus(channel):
	global counter
	if GPIO.input(channel) > 0.5:
		counter = counter + 1

GPIO.add_event_detect(4, GPIO.RISING, callback=conterPlus)

# initialize temperature sensors
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5) # Chip select of the MAX31865 board: saturator temperature
sensor_1 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D6) # Chip select of the MAX31865 board: condensor temperature
sensor_2 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D13) # Chip select of the MAX31865 board: optic temperature
sensor_3 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)

# initialize temerature setpoits
Td_set = 20 # temperature difference setpoint between saturator and condensor

# initialize PID
pid_1 = PID(1, 0.1, 0.05, setpoint=20) # PID for Peltier cooler
pid_2 = PID(10, 0.1, 0.05, setpoint=50) # PID for optic 

# initialize GPIO for PWM
GPIO.setup(23,GPIO.OUT) # initialize GPIO19 as an output
pwm_1 = GPIO.PWM(23,100) # GPIO23 as PWM output, with 100Hz frequency
pwm_1.start(0) # generate PWM signal with 0% duty cycle
GPIO.setup(24,GPIO.OUT) # initialize GPIO20 as an output
pwm_2 = GPIO.PWM(24,100) # GPIO24 as PWM output, with 100Hz frequency
pwm_2.start(0) # generate PWM signal with 0% duty cycle

# initialize flow rate
flow_setpoint = 0.2 # SLPM

# initialaize database
db = MongoClient('localhost', 27017)['mini_CPC'] # database name 'mini_CPC'
collection = db.data # colletction name 'data'

############################################################
############################################################

print('************************')
print('************************')
print('**** mini_CPC start ****')
print('************************')
print('************************')

while True:

	print('************************')

	## OPC counter
	counter  = 0
	time.sleep(1)
	counts = counter
	# print('counts = %d' % counts)

	## get temperatures
	Ts = sensor_1.temperature # saturator temperature
	Tc = sensor_2.temperature # condensor temperature
	To = sensor_3.temperature # optic temperature
	Td = Ts - Tc # temperature difference between saturator and condensor
	print('Ts = %.1f, Tc = %.1f, To = %.1f, Td = %.1f' % (Ts, Tc, To, Td))

	## change PWM
	pid_2.setpoint = Ts + 5 # set OPC temperature 5 degree higher than saturator
	dc_1 = pid_1(Td) # cooler duty cycle
	if dc_1 > 100: # duty cycle should between 0-100
		dc_1 = 100
	elif dc_1 < 0:
		dc_1 = 0
	dc_2 = pid_2(To) # heater duty cycle
	if dc_2 > 100: # duty cycle should between 0-100
		dc_2 = 100
	elif dc_2 < 0:
		dc_2 = 0
	pwm_1.ChangeDutyCycle(dc_1) # change cooler PWM
	pwm_2.ChangeDutyCycle(dc_2) # change heater PWM
	print('cooler PWM = %.1f, heater PWM = %.1f' % (dc_1, dc_2))

	## flow rate
	flow = 0.2 # SLPM
	# print('flow = %.2f' % flow)

	## butonal level and fill

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
	# print(dataDict)
	collection.insert_one(dataDict)

	## watch dog


