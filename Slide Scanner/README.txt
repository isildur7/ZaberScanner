Applications to Download:
- Pylon viewer (for the camera) https://www.baslerweb.com/en/downloads/software-downloads/
- Zaber console (for the platform motors) https://www.zaber.com/software
- Arduino (for LED control)

Python Packages Necessary:
- serial
- time
- os
- numpy
- cv2 https://pypi.org/project/opencv-python/
- pypylon (pylon, genicam) https://github.com/basler/pypylon
- zaber_motion (Units, Library) https://www.zaber.com/software/docs/motion-library/ascii/tutorials/install/py/
- zaber_motion.ascii (Connection)

Files Required:
- FOV change.py
- Autofocus.py
- baslerwrappers.py
- camera configuration file (saved via pylon viewer)

General Instructions:
- Determine the serial ports for the camera HDMI cable and LED control, input into the code
- Obtain the proper configuration file (.pfs) through the pylon viewer application, save and input the corresponding directory into the code
- Determine the proper exposure for the sample, input into the code
- Determine the approximate focus region on the z-axis and calculate the vertical movement limit for motors. Input into the code to keep sample slides and lens safe.

Multiple Field of View (FOV) Instructions:
- Input the interested x and y scan region as "x_detect" and "y_detect" in "FOV change.py".
- Input the x and y step size that represents one FOV as "x_step" and "y_step", recorded manually by looking through the pylon viewer.
- Check that camera exposure is set to the right value.
- If the task includes taking z-stacks, set the vertical step size and step number (in the for loop range function) to the right value.

LED Array Setup:
- https://github.com/isildur7/neopixel-matrix-on-RPi-Pico