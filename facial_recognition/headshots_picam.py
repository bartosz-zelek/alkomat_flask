import os
import sys
import time

import cv2
from picamera2 import Picamera2

if len(sys.argv) < 2:
    print("Usage: python headshots_picam.py <name> [number_of_photos]")
    sys.exit(1)


name = sys.argv[1]
number_of_photos = int(sys.argv[2]) if len(sys.argv) > 2 else None

save_dir = f"dataset/{name}"
os.makedirs(save_dir, exist_ok=True)

cam = Picamera2()
cam.preview_configuration.main.size = (512, 304)
cam.preview_configuration.main.format = "RGB888"
cam.preview_configuration.controls.FrameRate = 10
cam.configure("preview")
cam.start()
time.sleep(2)  # Allow camera to warm up

img_counter = 0

if number_of_photos is None:
    while True:
        frame = cam.capture_array()
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        img_name = f"{save_dir}/image_{img_counter}.jpg"
        cv2.imwrite(img_name, image)
        print(f"{img_name} written!")
        img_counter += 1
        user_input = input("Press Enter to take another photo or 'q' to quit: ")
        if user_input.lower() == "q":
            print("Exiting...")
            break
else:
    for i in range(number_of_photos):
        frame = cam.capture_array()
        image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        img_name = f"{save_dir}/image_{img_counter}.jpg"
        cv2.imwrite(img_name, image)
        print(f"{img_name} written!")
        img_counter += 1
