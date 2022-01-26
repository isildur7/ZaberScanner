# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 16:59:55 2021

@author: amey chaware
jerry jiang

"""

import time
from baslerwrappers import BaslerCamera
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection
import cv2
import numpy as np
import serial
import os

# FOMs and calculation of FOM at the given position
def laplacian(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U)
    return cv2.mean(img_sobel)[0]

def energy_laplacian(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    #print(np.shape(img_gray))
    kernel = np.array([[-1, -4, -1],
              [-4, 20, -4],
              [-1, -4, -1]])
    img_sobel = cv2.filter2D(img_gray, cv2.CV_16U, kernel)
    #print(np.shape(img_sobel))
    return np.mean(np.square(img_sobel))

def brenner(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    #print(np.shape(img_gray))
    kernel = np.array([-1, 0, 1])
    img_sobel = cv2.filter2D(img_gray, cv2.CV_16U, kernel)
    #print(np.shape(img_sobel))
    return np.sum(np.square(img_sobel))

def normed_variance(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    #mean, std = cv2.meanStdDev(img_gray)
    #mean, std = np.squeeze(mean), np.squeeze(std)
    return np.var(img_gray)/np.mean(img_gray)
    #return std*std/mean
    
def calculation(camera, conv, fom, position, axis):
    axis.move_absolute(position, Units.LENGTH_MILLIMETRES)
    image = camera.take_one_opencv_image(conv)
    actual_postition = axis.get_position(Units.LENGTH_MILLIMETRES)
    fom_here = fom(image)
    return actual_postition, fom_here

# Helpers for Fibonacci AF
def step_to_absolute(steps):
    # for fibonacci, we need steps 
    return steps*STEP_SIZE + START_MM

def absolute_to_steps(absl):
    return (absl-START_MM)/STEP_SIZE

def get_fibonacci_list(max_index):
    fibo = [1,1]
    for i in range(2,max_index+1):
        fibo.append(fibo[i-1]+fibo[i-2])
    return fibo

# Focusing Algorithms
def Fibonacci(start, end, N, camera, converter, motor, fom):
    # N is the least index of Fibonacci Sequence such that F_N >= end - start
    # requires functions step_to_absolute, absolute_to steps, get_fibonacci_list
    # send axis for motor
    
    fibo = get_fibonacci_list(N)
    picturePos1 = 0
    picturePos2 = 0
    calculate = 0
    for i in range(1, N):
        scale = fibo[N-i-1]/fibo[N-i+1]
        if i == 1:
            picturePos1 = step_to_absolute(start + int(scale*(end-start)))
            picturePos2 = step_to_absolute(end - int(scale*(end-start)))
            picturePos1, fomAt1 = calculation(camera, converter, fom, picturePos1, motor)
            picturePos2, fomAt2 = calculation(camera, converter, fom, picturePos2, motor)
            
        if calculate == 1:
            picturePos1, fomAt1 = calculation(camera, converter, fom, picturePos1, motor)
        elif calculate == 2:
            picturePos2, fomAt2 = calculation(camera, converter, fom, picturePos2, motor)
        
        if fomAt1 < fomAt2:
            start = absolute_to_steps(picturePos1)
            picturePos1 = picturePos2
            picturePos2 = step_to_absolute(end - int(scale*(end - start)))
            fomAt1 = fomAt2
            calculate = 2
        else:
            end = absolute_to_steps(picturePos2)
            picturePos2 = picturePos1
            picturePos1 = step_to_absolute(start + int(scale*(end - start)))
            fomAt2 = fomAt1
            calculate = 1
    picturePos1, fomAt1 = calculation(camera, converter, fom, picturePos1, motor)
    picturePos2, fomAt2 = calculation(camera, converter, fom, picturePos2, motor)
    
    if fomAt1 > fomAt2:
        return picturePos1
    else:
        return picturePos2
    
def Autofocus(start, end, delta, camera, converter, axis, fom):
    # ternary search
    scale = 0.38
    
    while np.abs(start - end) > delta:
        #print(np.abs(start - end))
        picturePos1 = start + (scale*(end-start))
        picturePos2 = end - (scale*(end-start))
        
        picturePos1, fomAt1 = calculation(camera, converter, fom, picturePos1, axis)
        picturePos2, fomAt2 = calculation(camera, converter, fom, picturePos2, axis)
        
        if fomAt1 < fomAt2:
            start = picturePos1
       
        else:
            end = picturePos2
   
    return start/2 + end/2


if __name__ == "__main__":
    
    # Basler camera config file storing all the imaging params
    CONFIG_FILE_PATH = "C:/Amey/Code/a2A3840-45ucBAS_40075263.pfs"
    
    COM_PORT = 'COM3' # COM port for RPI Pico
    
    BAUD_RATE = 115200
    # GPIO pin number on RPI Pico where the array is connected
    LED_PIN = 2
    
    STEP_SIZE = 0.005
    NUM_STEPS = 610
    START_MM = 6.5
    # your end can be calculated by simply START_MM + STEP_SIZE*NUM_STEPS
    
    Library.enable_device_db_store()

    connection = Connection.open_serial_port("COM4")
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))

    device = device_list[0]
    z_axis = device.get_axis(3)
    
    # create the camera object
    camera = BaslerCamera(CONFIG_FILE_PATH)
    conv = camera.opencv_converter()
    
    # after looking at the smaller portion it works
    # Don't know why, and doesn't really work for the
    # full image
    camera.change_ROI((1280,960), ((3840-1280)//2, (2160-960)//2))
    
    # initialize the LED comm port and the array
    LEDport = serial.Serial(COM_PORT, BAUD_RATE)
    LEDport.write(("INIT PIN "+str(LED_PIN)+"\r").encode("ascii"))
    time.sleep(0.5)
    LEDport.write(("ALL OFF\n").encode("ascii"))
    
    LEDport.write(("CIRCLE 1 0xFFFFFF\n").encode("ascii"))
    time.sleep(0.5)
    
    # focusing
    print("Start focusing")
    camera.start_imaging()
    startt = time.time()
    
    #focus_position = Autofocus(start=6.5, end=9.5, delta=0.001, \
     #                        camera=camera, converter=conv, axis=z_axis, fom=normed_variance)
    
    # Fibo is significantly faster and seems more accurate
    focus_position = Fibonacci(start=0, end=NUM_STEPS, N=16, \
                              camera=camera, converter=conv, motor=z_axis, fom=brenner)
        
    z_axis.move_absolute(focus_position, Units.LENGTH_MILLIMETRES)
    endt = time.time()
    camera.stop_imaging()
    
    print(focus_position)
    print(endt-startt)