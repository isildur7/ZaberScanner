# -*- coding: utf-8 -*-
"""
Created on Mon Aug 30 21:06:03 2021

@author: amey chaware
"""
import time
from Autofocus import normed_variance, Autofocus
from baslerwrappers import BaslerCamera
from zaber_motion import Units, Library
from zaber_motion.ascii import Connection
from matplotlib import pyplot as plt
import cv2
import numpy as np
import serial

def laplacian(img):
    img_gray = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    img_sobel = cv2.Laplacian(img_gray,cv2.CV_16U)
    return cv2.mean(img_sobel)[0]

def calculation(camera, conv, fom, position, axis):
    axis.move_absolute(position, Units.LENGTH_MILLIMETRES)
    image = camera.take_one_opencv_image(conv)
    actual_postition = axis.get_position(Units.LENGTH_MILLIMETRES)
    fom_here = fom(image)
    return actual_postition, fom_here

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
    
    
def FOM_profile(camera, conv, axis, fom, start, end, stepsize):
    # gather fom profile
    foms = list()
    positions = list()
    p = np.arange(start, end, stepsize)
    for i in p:
        position, fom_here = calculation(camera, conv, fom, i, axis)
        foms.append(fom_here)
        positions.append(position)
    return positions, foms
    

if __name__ == "__main__":
    
    CONFIG_FILE_PATH = "C:/Amey/Code/CYTOLOGY.pfs"
    COM_PORT = 'COM3'
    BAUD_RATE = 115200
    LED_PIN = 2
    STEP_SIZE = 0.05
    START_MM = 17.62
    END_MM = 19.62
    
    # create the camera object
    camera = BaslerCamera(CONFIG_FILE_PATH)
    conv = camera.opencv_converter()
    
    Library.enable_device_db_store()

    connection = Connection.open_serial_port("COM4")
    device_list = connection.detect_devices()
    print("Found {} devices".format(len(device_list)))

    device = device_list[0]
    z_axis = device.get_axis(3)
    
    # initialize the LED comm port and the array
    LEDport = serial.Serial(COM_PORT, BAUD_RATE)
    LEDport.write(("INIT PIN "+str(LED_PIN)+"\r").encode("ascii"))
    time.sleep(0.5)
    LEDport.write(("ALL OFF\n").encode("ascii"))
    
    LEDport.write(("CIRCLE 2 0xFFFFFF\n").encode("ascii"))
    time.sleep(0.5)
    

    x_size = int(3840//3)
    y_size = int(2160//3)
    print(x_size, y_size)
    camera.change_ROI((x_size, y_size), ((3840-x_size)//2, (2160-y_size)//2))
    
    camera.start_imaging()
    
    profile = FOM_profile(camera=camera, conv=conv, axis=z_axis, \
                          fom=normed_variance, start=START_MM, end=END_MM, stepsize=STEP_SIZE)
    
    max_FOM = max(profile[1])
    max_FOM_index = profile[1].index(max_FOM)
    print(max_FOM_index)
    print(len(profile[0]))
    print(len(profile[1]))
    
        
    print ("Max FOM: ", max(profile[1]))
    print ("Max Position: ", profile[0][max_FOM_index])
        
    camera.stop_imaging()
    
    LEDport.write(("ALL OFF\n").encode("ascii"))
    
    plt.figure()
    plt.plot(profile[0], profile[1]/max(profile[1]))