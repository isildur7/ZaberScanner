# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 15:06:19 2021

@author: COLD004
"""

import time
from baslerwrappers import BaslerCamera
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection
import cv2
import numpy as np
import serial
import os

def laplacian(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U)
    return cv2.mean(img_sobel)[0]

def calculation(camera, conv, fom, position, motor):
    motor.goToPosition(position, 850)
    image = camera.take_one_opencv_image(conv)
    return fom(image)

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

if __name__ == "__main__":
    
    CONFIG_FILE_PATH = "C:/Amey/Code/a2A3840-45ucBAS_40075263.pfs"
    COM_PORT = 'COM3'
    BAUD_RATE = 115200
    LED_PIN = 2
    STEP_SIZE = 0.001
    NUM_STEPS = 3000
    
    Library.enable_device_db_store()

    connection = Connection.open_serial_port("COM4")
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))

    device = device_list[0]
    z_axis = device.get_axis(3)
    
    # create the camera object
    camera = BaslerCamera(CONFIG_FILE_PATH)
    conv = camera.opencv_converter()
    
    # initialize the LED comm port and the array
    LEDport = serial.Serial(COM_PORT, BAUD_RATE)
    LEDport.write(("INIT PIN "+str(LED_PIN)+"\r").encode("ascii"))
    time.sleep(0.5)
    LEDport.write(("ALL OFF\n").encode("ascii"))
    
    LEDport.write(("CIRCLE 1 0xFFFFFF\n").encode("ascii"))
    camera.start_imaging()
    time.sleep(0.5)
    
    position = np.array([0.,0.,0.])
    fom = np.array([0.,0.,0.])
    
    z_axis.move_relative(-2, Units.LENGTH_MILLIMETRES)
    
    position[0] = z_axis.get_position(Units.LENGTH_MILLIMETRES)
    image = camera.take_one_opencv_image(conv)
    fom[0] = np.double(10e+6/brenner(image))
    z_axis.move_relative(1.5, Units.LENGTH_MILLIMETRES)
    
    position[1] = z_axis.get_position(Units.LENGTH_MILLIMETRES)
    image = camera.take_one_opencv_image(conv)
    fom[1] = np.double(10e+6/brenner(image))
    z_axis.move_relative(1.5, Units.LENGTH_MILLIMETRES)
    
    position[2] = z_axis.get_position(Units.LENGTH_MILLIMETRES)
    image = camera.take_one_opencv_image(conv)
    fom[2] = np.double(10e+6/brenner(image))
    
    camera.stop_imaging()
    
    denom = (position[0] - position[1])*(position[0] - position[2])*\
        (position[1] - position[2])
    A = (position[2] * (fom[1] - fom[0]) + position[1] * (fom[0] - fom[2])\
         + position[0] * (fom[2] - fom[1])) / denom
    B = (position[2]**2 * (fom[0] - fom[1]) + position[1]**2 * \
         (fom[2] - fom[0]) + position[0]**2 * (fom[1] - fom[2])) / denom
        
    z_axis.move_absolute(-B/2/A, Units.LENGTH_MILLIMETRES)
    LEDport.write(("ALL OFF\n").encode("ascii"))