# -*- coding: utf-8 -*-
"""
Created on Wed Oct  6 15:07:05 2021

@author: COLD004
"""

import serial
import time
import os

from Autofocus import brenner, Fibonacci, normed_variance, Autofocus
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection
from baslerwrappers import BaslerCamera

# declaring connection ports
LED_COM_PORT = 'COM3'
MOTOR_COM_PORT = 'COM4'
BAUD_RATE = 115200
GP_pin = 2

# initialize the LED comm port and the array
LEDport = serial.Serial(LED_COM_PORT, BAUD_RATE)
LEDport.write(("INIT PIN "+str(GP_pin)+"\r").encode("ascii"))
time.sleep(0.5)
LEDport.write(("ALL OFF\n").encode("ascii"))

# validating photo saving path
CONFIG_FILE_PATH = "C:/Amey/Code/CYTOLOGY.pfs"
DEFAULT_DIR = "C:/Amey/Data/Cytology/FOV"

print("Start by providing the directory for saving the data.\n")
print("Default directory: {}".format(DEFAULT_DIR))
change = input("Do you want to change it? [y/N]")
if change == "y":
    path = input("Directory: ")
else:
    path = DEFAULT_DIR
    
if not os.path.isdir(path):
    os.mkdir(path)
    print("Directory created")
print("Cunrrent save directory: {}".format(path))

# create the camera object
camera = BaslerCamera(CONFIG_FILE_PATH)
conv = camera.opencv_converter()

BRIGHTFIELD_EXPOSURE = 6500
DARKFIELD_RING_EXPOSURE = 25000
BRIGHTFIELD_RING_EXPOSURE = 8000
RL_HALF_EXPOSURE = 12000
TB_HALF_EXPOSURE = 8500
CYTOLOGY_20X_CIRCLE2_EXPOSURE = 16500
CYTOLOGY_20X_SPIRALKEY0_EXPOSURE = 300000

#STEP_SIZE = 0.005
#NUM_STEPS = 610
START_MM = 17.62
END_MM = 19.62

x_size = int(3840//3)
y_size = int(2160//3)

# configuring the motor
Library.enable_device_db_store()
connection = Connection.open_serial_port(MOTOR_COM_PORT)
device_list = connection.detect_devices()
print("Found {} devices".format(len(device_list)))
    
device = device_list[0]
x_axis = device.get_axis(1)
y_axis = device.get_axis(2)
z_axis = device.get_axis(3)

# automatic moving code parameters, unit in mm
x_step = 0.23
y_step = 0.44
x_detect = 2.29
y_detect = 4.39
# 20X cytology smear 10*10 z-stack scan: x start at 21.2 mm, y start at 29.5 mm


#----------------------------------

total_count = 1
x_loop_count = 1
y_count = 1
reverse = False

# camera start imaging
camera.start_imaging()
time.sleep(2.0)
camera.stop_imaging()

while True:

    print("Now starting: total_count = ", total_count, ", x_loop_count = ", x_loop_count, ", y_count = ", y_count)

    # focusing module
    LEDport.write(("CIRCLE 2 0xFFFFFF\n").encode("ascii"))
    time.sleep(0.5)
    
    print("Start focusing")
    
    z_axis.move_absolute(START_MM, Units.LENGTH_MILLIMETRES)
    camera.set_exposure_time(CYTOLOGY_20X_CIRCLE2_EXPOSURE)
    time.sleep(0.5)
    
    camera.change_ROI((x_size, y_size), ((3840-x_size)//2, (2160-y_size)//2))
    camera.start_imaging()
    
    focus_position = Autofocus(start=START_MM, end=END_MM, delta=0.001, camera=camera, converter=conv, axis=z_axis, fom=normed_variance)
    z_axis.move_absolute(focus_position, Units.LENGTH_MILLIMETRES)
    time.sleep(0.5)
    
    print("focus position: ", focus_position)
    
    camera.stop_imaging()
    LEDport.write(("ALL OFF\r").encode("ascii"))
    
    # print(focus_position)
    
    # capturing module
    max_X = 3840 
    max_Y = 2160
    camera.change_ROI((max_X, max_Y), ((3840-max_X)//2, (2160-max_Y)//2))
    print("Start capturing")
            
    # timestr = time.strftime("%Y%m%d-%H%M%S")
    # savepath = os.path.join(path, timestr)
    # os.mkdir(savepath)
    
    # brightfield
    LEDport.write(("SPIRALKEY 0 0xFFFFFF\r").encode("ascii"))
    camera.set_exposure_time(CYTOLOGY_20X_SPIRALKEY0_EXPOSURE)
    
    # z-stack with FOV change
    z_axis.move_relative(-0.005, Units.LENGTH_MILLIMETRES)
    time.sleep(0.5)
    
    for i in range(11):
        time.sleep(0.5)
        camera.start_imaging()
        time.sleep(0.5)
        camera.capture_and_save_tiff(os.path.join(path, str(total_count) + "_" + str(i) + ".tiff"))
        camera.stop_imaging()
        z_axis.move_relative(0.001, Units.LENGTH_MILLIMETRES)
        time.sleep(0.5)
    
    
    LEDport.write(("ALL OFF\r").encode("ascii"))
    time.sleep(1)
    
    #set it back to bayer
    #camera.set_pixel_format("BayerRG12")
    print("Capturing ended")
    
    # capture of the number (total_count)th block of view has already ended
    total_count = total_count + 1 # total index increase by 1, which is the index of the next block
    if reverse == False: # if the moving direction of x_axis is to the positive
        if x_loop_count * x_step < x_detect:
            x_loop_count = x_loop_count + 1
            x_axis.move_relative(x_step, Units.LENGTH_MILLIMETRES)
        else:
            reverse = True
            if y_count * y_step < y_detect:
                print("y_count = ", y_count, " finished")
                y_count = y_count + 1
                y_axis.move_relative(y_step, Units.LENGTH_MILLIMETRES)
            else:
                print("Entire scan finished.")
                break
    else: # if the x_axis moving direction is backwards
        if x_loop_count > 1:
            x_axis.move_relative(-x_step, Units.LENGTH_MILLIMETRES)
            x_loop_count = x_loop_count - 1
        else:
            reverse = False
            if y_count * y_step < y_detect:
                print("y_count = ", y_count, " finished")
                y_count = y_count + 1
                y_axis.move_relative(y_step, Units.LENGTH_MILLIMETRES)
            else:
                print("Entire scan finished.")
                break
            
        



