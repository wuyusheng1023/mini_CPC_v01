############################################################
############################################################
# yusheng, 2019-03-26
# email: yusheng.wu@helsinki.fi
# tel: +358 41 4722 694
#
# hardware: 2*PT1000, 2*cooler, 1*heater, 1*fan


import RPi.GPIO as GPIO
import board
import busio
import digitalio

import adafruit_max31865 # PT1000 temperature module

import numpy as np

import time

from simple_pid import PID

############################################################
############################################################

# wiring input:
GPIO_OPC = 4 # GPIO04: counter, input

# wiring outut:
GPIO_heater_1 = 17 # GPIO, PWM output, heater
GPIO_heater_2 = 18 # GPIO, PWM output, heater
GPIO_cooler_1 = 27 # GPIO, PWM output, cooler
GPIO_cooler_2 = 22 # GPIO, PWM output, cooler
GPIO_fan = 23 # output, fan

# configuration
sleep_time = 1 # counter interval
Ts_set = 40 # temperature set point of saturator
Tc_set = 15 # temperature set point of condensor
To_set = 42
P_1 = 10 # PID_1, heater
I_1 = 0.1
D_1 = 0.05 
P_2 = 10 # PID_2, cooler
I_2 = 0.1
D_2 = 0.05
P_3 = 10 # PID_3, heater
I_3 = 0.1
D_3 = 0.05

# initialize GPIO
GPIO.cleanup() # Rrest ports
GPIO.setwarnings(False) # do not show any warnings
GPIO.setmode(GPIO.BCM) # programming the GPIO by BCM pin numbers. (PIN35 as ‘GPIO19’)
GPIO.setup(GPIO_OPC, GPIO.IN) # input, counter
GPIO.setup(GPIO_heater_1,GPIO.OUT) # output, heater
GPIO.setup(GPIO_heater_2,GPIO.OUT) # output, heater
GPIO.setup(GPIO_cooler_1,GPIO.OUT) # output, cooler
GPIO.setup(GPIO_cooler_2,GPIO.OUT) # output, cooler
GPIO.setup(GPIO_fan,GPIO.OUT) # output, fan

# initialize SPI temperature board
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5) # Chip select of the MAX31865 board: saturator temperature
sensor_1 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D6) # Chip select of the MAX31865 board: condensor temperature
sensor_2 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)
cs = digitalio.DigitalInOut(board.D13) # Chip select of the MAX31865 board: optic temperature
sensor_3 = adafruit_max31865.MAX31865(spi, cs, rtd_nominal=1000.0, ref_resistor=4300.0)

# initialize pulse counter
def conterPlus(channel):
	global counter
	counter = counter + 1

GPIO.add_event_detect(GPIO_OPC, GPIO.RISING, callback=conterPlus)
counter = 0

# initialize temperature sensors, PID and PWM
pid_1 = PID(P_1, I_1, D_1, setpoint=Ts_set) # heater
pwm_1 = GPIO.PWM(GPIO_heater_1,100) # PWM output, with 100Hz frequency
pwm_1.start(0) # generate PWM signal with 0% duty cycle
pid_2 = PID(P_2, I_2, D_2, setpoint=Tc_set) # cooler
pwm_2 = GPIO.PWM(GPIO_cooler_1,100)
pwm_2.start(0)
pid_3 = PID(P_2, I_2, D_2, setpoint=Tc_set) # cooler
pwm_3 = GPIO.PWM(GPIO_cooler_2,100) # PWM output, with 100Hz frequency
pwm_3.start(0) 
pid_4 = PID(P_3, I_3, D_3, setpoint=To_set) # heater
pwm_4 = GPIO.PWM(GPIO_heater_2,100) # PWM output, with 100Hz frequency
pwm_4.start(0) # generate PWM signal with 0% duty cycle

# initialize fan
def fan(on):
	if on == 1:
		GPIO.output(GPIO_fan,GPIO.HIGH)
	elif on == 0:
		GPIO.output(GPIO_fan,GPIO.LOW)

fan(1)

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
	print('counts = %d' % counts)

	## get temperatures
	Ts = sensor_1.temperature # saturator temperature
	Tc = sensor_2.temperature # condensor temperature
	To = sensor_3.temperature # optics temperature

	## change PWM
	dc_1 = pid_1(Ts) # heater duty cycle
	dc_2 = pid_2(2*Tc_set - Tc) # cooler duty cycle
	dc_3 = pid_4(To) # heater_2 duty cycle

	print('Ts = %.1f, Tc = %.1f, To = %.1f' % (Ts, Tc, To))
	print('dc_1 = %.1f, dc_2 = %.1f, dc_3 = %.1f' % (dc_1, dc_2, dc_3))

	if dc_1 > 100: # duty cycle should between 0-100
		dc_1 = 100
	elif dc_1 < 0:
		dc_1 = 0
	if dc_2 > 100: # duty cycle should between 0-100
		dc_2 = 100
	elif dc_2 < 0:
		dc_2 = 0
	# dc_2 = 0.5*dc_2
	if dc_3 > 100: # duty cycle should between 0-100
		dc_3 = 100
	elif dc_3 < 0:
		dc_3 = 0
	pwm_1.ChangeDutyCycle(dc_1) # heater PWM
	pwm_2.ChangeDutyCycle(dc_2) # cooler PWM
	pwm_3.ChangeDutyCycle(dc_2) # cooler PWM
	pwm_4.ChangeDutyCycle(dc_3) # cooler PWM
