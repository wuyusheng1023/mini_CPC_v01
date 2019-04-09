############################################################
############################################################
# yusheng, 2019-03-26
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694

import time

import RPi.GPIO as GPIO
import Adafruit_ADS1x15

############################################################
############################################################

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
GPIO_OPC = PIN_11 # GPIO04: counter, input
GPIO_liquid_level = PIN_37 # liquid sensor, input

# wiring outut:
GPIO_heater_SAT = PIN_12 # GPIO, PWM output, heater
GPIO_cooler = PIN_16 # GPIO, PWM output, cooler
GPIO_heater_OPC = PIN_18 # GPIO, PWM output, condensor heater
GPIO_air_pump = PIN_22
GPIO_liquid_pump = PIN_24
GPIO_fan = PIN_26 # output, fan

# initialize GPIO
GPIO.cleanup() # Reset ports
GPIO.setwarnings(False) # do not show any warnings
GPIO.setmode(GPIO.BCM) # programming the GPIO by BCM pin numbers. (PIN35 as ‘GPIO19’)
GPIO.setup(GPIO_OPC, GPIO.IN) # input, counter
GPIO.setup(GPIO_liquid_level, GPIO.IN) # input
GPIO.setup(GPIO_heater_SAT,GPIO.OUT) # output, saturator heater
GPIO.setup(GPIO_cooler,GPIO.OUT) # output, cooler
GPIO.setup(GPIO_heater_OPC,GPIO.OUT) # output, saturator heater
GPIO.setup(GPIO_air_pump,GPIO.OUT) # output
GPIO.setup(GPIO_liquid_pump,GPIO.OUT) # output
GPIO.setup(GPIO_fan,GPIO.OUT) # output

# initialize I2C ADC board
adc = Adafruit_ADS1x15.ADS1115() # create the ADC object

############################################################
############################################################

# test
sleep_time = 1 # interval
GPIO.output(GPIO_heater_SAT, GPIO.HIGH)
GPIO.output(GPIO_cooler, GPIO.HIGH)
GPIO.output(GPIO_heater_OPC, GPIO.HIGH)
GPIO.output(GPIO_air_pump, GPIO.HIGH)
GPIO.output(GPIO_liquid_pump, GPIO.HIGH)
GPIO.output(GPIO_fan, GPIO.HIGH)

############################################################
############################################################

print('************************')
print('************************')
print('* mini_CPC test start  *')
print('************************')
print('************************')

while True:

	print('************************************************************************')
	
	## OPC counter
	counter_state = GPIO.input(GPIO_OPC)
	print('counter_state')
	print(counter_state)

	## liquid level
	liquid_state = GPIO.input(GPIO_liquid_level)
	print('liquid_state')
	print(liquid_state)

	## ADC
	GAIN = 1
	values = [0]*4
	for i in range(4):
		values[i] = adc.read_adc(i, gain=GAIN)
	print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))

