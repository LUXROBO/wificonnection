
import cv2
import numpy as np
from PIL import Image
from IPython.display import display, clear_output
from ipywidgets import Video
import time

red = (0, 0, 255)
green = (0, 255, 0)
blue = (255, 0, 0)
white = (255, 255, 255)
yellow = (0, 255, 255)
cyan = (255, 255, 0)
magenta = (255, 0, 255)



font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX  # hand-writing style font
fontScale = 3.5

def tracking():
    cap=cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)
    
    while 1:
        ret, frame = cap.read()


        thickness = 2 
        cv2.putText(frame, 'OpenCV', (120,240), font, fontScale, yellow, thickness)
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if cv2.waitKey(1) & 0xff == ord('q'):
            break
            
        display(pil_img)
        clear_output(wait=True)
        time.sleep(0.01)
