#!/usr/bin/env python
# created by chris@drumminhands.com
# modified by odarriba@gmail.com

import os
import glob
import time
import traceback
from time import sleep
import RPi.GPIO as GPIO
import atexit
import sys
import pygame
from signal import alarm, signal, SIGALRM, SIGKILL
import subprocess as sub

########################
### Variables Config ###
########################
file_path = '/home/pi/photobooth/pics/' # Where to save the photos and videos.

led1_pin = 15 # LED 1
led2_pin = 19 # LED 2
button1_pin = 22 # pin for the big red button (photo)
button2_pin = 18 # pin for the big blue button (video)
shutdown_button_pin = 16 # pin for button to hutdown the pi

instructions_delay = 3 # #delay while showing the instructions
capture_delay = 7 # delay after taking the picture / video
show_delay = 5 # how long to display finished message before beginning a new session

monitor_w = 1184
monitor_h = 624

transform_x = monitor_w # how wide to scale the jpg when replaying
transfrom_y = monitor_h # how high to scale the jpg when replaying

offset_x = 0 # how far off to left corner to display photos
offset_y = 0 # how far off to left corner to display photos

pixel_width = 1920 # width of the photos
pixel_height = monitor_h * pixel_width // monitor_w # Calculate the height

real_path = os.path.dirname(os.path.realpath(__file__))


####################
### Other Config ###
####################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(led1_pin,GPIO.OUT) # LED 1
GPIO.setup(led2_pin,GPIO.OUT) # LED 2
GPIO.setup(button1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 1
GPIO.setup(button2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 2
GPIO.setup(shutdown_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # falling edge detection on button 3

#################
### Functions ###
#################

def cleanup():
  print('Ended abruptly')
  GPIO.cleanup()
atexit.register(cleanup)

def shut_it_down(channel):  
    print "Shutting down..." 
    GPIO.output(led1_pin,True);
    GPIO.output(led2_pin,True);
    time.sleep(3)
    os.system("sudo halt")

def init_pygame():
    pygame.init()
    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
    pygame.display.set_caption('Photo Booth Pics')
    pygame.mouse.set_visible(False) #hide the mouse cursor	
    return pygame.display.set_mode(size, pygame.FULLSCREEN)

def show_image(image_path):
    screen = init_pygame()
    img=pygame.image.load(image_path) 
    img = pygame.transform.scale(img,(transform_x,transfrom_y))
    screen.blit(img,(offset_x,offset_y))
    pygame.display.flip()
				
# define the photo taking function for when the big button is pressed 
def take_photo(): 
	# Turn off the leds
	GPIO.output(led1_pin,False)
	GPIO.output(led2_pin,False)

	show_image(real_path + "/blank.png")
	show_image(real_path + "/instructions.png")
	
	# Blink the button
	state = True
	for i in range(instructions_delay*2):
		GPIO.output(led1_pin,state)
		sleep(0.5)
		state = not state

	show_image(real_path + "/blank.png")


	# Take the pic
	print "Taking the picture" 
	now = time.strftime("%Y-%m-%d-%H:%M:%S") #get the current date and time for the start of the filename

	os.chdir(file_path)
  	sub.Popen("raspistill -t " + capture_delay*1000 + " -o photo_"+now+".jpg", shell=True, stdout=sub.PIPE)
	
	
	########################### Begin Step 4 #################################
	GPIO.output(led1_pin,True) #turn on the LED
	try:
		show_image(file_path + "photo_"+ now + '.jpg')
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)
	
	time.sleep(show_delay)

	GPIO.output(led1_pin,True)
	GPIO.output(led2_pin,True)
	show_image(real_path + "/intro.png");

def take_video():
	# Turn off the leds
	GPIO.output(led1_pin,False)
	GPIO.output(led2_pin,False)

	show_image(real_path + "/blank.png")
	show_image(real_path + "/instructions_video.png")
	
	# Blink the button
	state = True
	for i in range(instructions_delay*2):
		GPIO.output(led2_pin,state)
		sleep(0.5)
		state = not state

	show_image(real_path + "/blank.png")


	# Take the pic
	print "Taking the video" 
	now = time.strftime("%Y-%m-%d-%H:%M:%S") #get the current date and time for the start of the filename

	os.chdir(file_path)
  	sub.Popen("raspivid -t 10000 -o photo_"+now+".h264", shell=True, stdout=sub.PIPE)
	
	
	########################### Begin Step 4 #################################
	GPIO.output(led1_pin,True) #turn on the LED
	try:
		show_image(file_path + "photo_"+ now + '.jpg')
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)
	
	time.sleep(show_delay)

	GPIO.output(led1_pin,True)
	GPIO.output(led2_pin,True)
	show_image(real_path + "/intro.png");


####################
### Main Program ###
####################

# when a falling edge is detected on button2_pin and button3_pin, regardless of whatever   
# else is happening in the program, their function will be run   
GPIO.add_event_detect(shutdown_button_pin, GPIO.FALLING, callback=shut_it_down, bouncetime=300) 

print "Photo booth app running..." 
GPIO.output(led1_pin,True); #light up the lights to show the app is running
GPIO.output(led2_pin,True);
time.sleep(1)
GPIO.output(led1_pin,False); #turn off the lights
GPIO.output(led2_pin,False);
time.sleep(1)
GPIO.output(led1_pin,True); #light up the lights to show the app is running
GPIO.output(led2_pin,True);

show_image(real_path + "/intro.png");

GPIO.add_event_detect(button1_pin, GPIO.FALLING)
GPIO.add_event_detect(button2_pin, GPIO.FALLING)

while True:
	if GPIO.event_detected(button1_pin):
		time.sleep(0.2) #debounce
		take_photo()

	if GPIO.event_detected(button2_pin):
		time.sleep(0.2) #debounce
		take_video()
