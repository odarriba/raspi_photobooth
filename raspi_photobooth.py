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

led1_pin = 15 # LED 1
led2_pin = 19 # LED 2
button1_pin = 22 # pin for the big red button (photo)
button2_pin = 18 # pin for the big blue button (video)
shutdown_button_pin = 16 # pin for button to hutdown the pi

instructions_delay = 3 # #delay while showing the instructions
capture_delay = 7 # delay after taking the picture
video_length = 10 # seconds to record on the video
show_delay = 5 # how long to display finished message before beginning a new session

monitor_w = 1280
monitor_h = 720

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

def aspect_scale(img,(bx,by)):
    """ Scales 'img' to fit into box bx/by.
     This method will retain the original image's aspect ratio """
    ix,iy = img.get_size()
    if ix > iy:
        # fit to width
        scale_factor = bx/float(ix)
        sy = scale_factor * iy
        if sy > by:
            scale_factor = by/float(iy)
            sx = scale_factor * ix
            sy = by
        else:
            sx = bx
    else:
        # fit to height
        scale_factor = by/float(iy)
        sx = scale_factor * ix
        if sx > bx:
            scale_factor = bx/float(ix)
            sx = bx
            sy = scale_factor * iy
        else:
            sy = by

    sx = int(sx)
    sy = int(sy)

    return pygame.transform.scale(img, (sx,sy))

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

    img = aspect_scale(img, (monitor_w, monitor_h))

    image_x = img.get_rect().w
    image_y = img.get_rect().h

    offset_x = (monitor_w-image_x)/2
    offset_y = 0

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

	os.chdir(real_path + "/pics");
  	sub.Popen("raspistill -t " + str(capture_delay*1000) + " -o photo_"+now+".jpg", shell=True, stdout=sub.PIPE)

  	time.sleep(capture_delay+1)
	
	########################### Begin Step 4 #################################
	GPIO.output(led1_pin,True) #turn on the LED
	try:
		show_image(real_path + "/pics/photo_"+ now + '.jpg')
	except Exception, e:
		tb = sys.exc_info()[2]
		traceback.print_exception(e.__class__, e, tb)

	GPIO.output(led1_pin,True)
	GPIO.output(led2_pin,True)
	show_image(real_path + "/intro.png");

def take_video():
	# Turn off the leds
	GPIO.output(led1_pin,False)
	GPIO.output(led2_pin,False)

	os.chdir(real_path)

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

	os.chdir(real_path+"/video");

	# Remove old hooks
	sub.Popen("rm -f hooks/*", shell=True, stdout=sub.PIPE)

	# Launch picam and wait
	camera = sub.Popen("./picam --preview --opacity 255 --alsadev hw:1,0", shell=True, stdout=sub.PIPE)

	# Start record
	sub.Popen("touch hooks/start_record", shell=True, stdout=sub.PIPE)
	time.sleep(video_length)

	# Stop record
	sub.Popen("touch hooks/stop_record", shell=True, stdout=sub.PIPE)

	# Kill picam
	sub.Popen("pgrep -o -x picam | xargs -I {} kill -9 {}", shell=True, stdout=sub.PIPE)
	time.sleep(1)

	GPIO.output(led1_pin,True)
	GPIO.output(led2_pin,True)
	show_image(real_path + "/intro.png");


####################
### Main Program ###
####################

sub.Popen("xset -dpms", shell=True, stdout=sub.PIPE)
sub.Popen("xset s off", shell=True, stdout=sub.PIPE)
sub.Popen("xset s noblank", shell=True, stdout=sub.PIPE)

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

GPIO.add_event_detect(button1_pin, GPIO.FALLING, bouncetime=300)
GPIO.add_event_detect(button2_pin, GPIO.FALLING, bouncetime=300)

while True:
	if GPIO.event_detected(button1_pin):
		time.sleep(0.2) #debounce
		take_photo()

	if GPIO.event_detected(button2_pin):
		time.sleep(0.2) #debounce
		take_video()
