import cv2
from picamera2 import Picamera2
import os
import time

name = 'Bartek' # replace with your name
save_dir = f'dataset/{name}'
os.makedirs(save_dir, exist_ok=True)

cam = Picamera2()
cam.preview_configuration.main.size = (512, 304)
cam.preview_configuration.main.format = "RGB888"
cam.preview_configuration.controls.FrameRate = 10
cam.configure("preview")
cam.start()
time.sleep(2)  # Allow camera to warm up

img_counter = 0

while True:
    frame = cam.capture_array()
    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    img_name = f"{save_dir}/image_{img_counter}.jpg"
    cv2.imwrite(img_name, image)
    print(f"{img_name} written!")
    img_counter += 1
    user_input = input("Press Enter to take another photo or 'q' to quit: ")
    if user_input.lower() == 'q':
        print("Exiting...")
        break
