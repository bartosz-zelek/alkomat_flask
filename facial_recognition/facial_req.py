#! /usr/bin/python

# import the necessary packages
from imutils.video import FPS
from picamera2 import Picamera2

import face_recognition
import pickle
import time
import argparse
import cv2
import os
import threading
import queue

import serial
import requests
from time import sleep


class ArduinoComs:
    def __init__(self, port) -> None:
        self.arduino = serial.Serial(port)
        self.ref_val = 100
        print("Coms established")

    def read_and_respond(self, user_id):
        print("Face recognition")
        print("Writing to Arduino: {}".format(user_id))
        self.arduino.write(bytes(user_id, "ascii"))
        print("Line read - user_id is {}".format(user_id))
        meas_val = int(self.arduino.readline())
        print("Line read - meas_val is {}".format(meas_val))
        # is_drunk = meas_val / ref_val > 0.2 and ref_val - meas_val > 5 and meas_val < 70
        # TODO: maybe rewrite using ?user_id=user_id etc. if possible
        # 'g' if all good, 'r' if drunk, 'b' if already blocked in DB, 'n' if user_id not recognized
        # not tested, server not ready to respond just yet
        response = requests.get(
            "http://localhost:5000/api/add_reading/{}/{}".format(
                user_id, meas_val)
        )
        response_msg = response.json()["message"]
        print("Response: {}".format(response_msg))
        response_char = ""
        if response_msg == "USER DOESN'T EXIST":
            response_char = "n"
        elif response_msg == "USER BLOCKED":
            response_char = "b"
        elif response_msg == "ENTRY BLOCKED":
            response_char = "r"
        elif response_msg == "ACCEPTED":
            response_char = "g"
        else:
            response_char = "n"
        print("Writing to Arduino: {}".format(response_char))
        self.arduino.write(bytes(response_char, "ascii"))
        print("Info sent to Arduino")
        sleep(5)  # wait for Arduino to process the response


class FaceRecognition:
    def __init__(self, args):
        encodingsP = "encodings.pickle"
        self.data = pickle.loads(open(encodingsP, "rb").read())
        self.cascade = cv2.CascadeClassifier(
            os.path.join(os.path.dirname(__file__),
                         "haarcascade_frontalface_default.xml")
        )
        self.ard = ArduinoComs("/dev/ttyUSB0")
        self.MultiTracker = cv2.legacy.MultiTracker_create
        self.Tracker = cv2.legacy.TrackerKCF_create

        self.args = args

        self.cam = Picamera2()
        config = self.cam.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"}, controls={"FrameRate": 60}
        )
        self.cam.configure(config)

    def recognize_face_and_return_name(self):
        print("Starting face recognition")
        self.cam.start()
        time.sleep(2.0)  # Allow camera to warm up
        # Repeat until a known face is detected
        name = "Unknown"
        while name == "Unknown":
            # Capture frame and prepare for detection
            frame = self.cam.capture_array()
            rgb = frame

            # Detect face locations and compute encodings
            boxes = face_recognition.face_locations(rgb, model=self.args.model)
            encodings = face_recognition.face_encodings(rgb, boxes, num_jitters=self.args.jitter)

            if not encodings:
                print("No faces detected, retrying...")
                continue

            # Compare first encoding against known encodings
            matches = face_recognition.compare_faces(
                self.data["encodings"], encodings[0], tolerance=0.5
            )
            if True in matches:
                # Find the most frequent matching name
                matched_idxs = [i for i, b in enumerate(matches) if b]
                counts = {}
                for i in matched_idxs:
                    n = self.data["names"][i]
                    counts[n] = counts.get(n, 0) + 1
                name = max(counts, key=counts.get)
            else:
                print("Unknown face detected, retrying...")
        return name


# cam.start()
# time.sleep(2.0)

# fps = FPS().start()

# frame_queue = queue.Queue(maxsize=1)
# result_lock = threading.Lock()
# current_boxes = []
# current_names = []
# stop_event = threading.Event()


# threading.Thread(target=detection_loop, daemon=True).start()

# while True:
#     frame_count += 1
#     rgb_frame = cam.capture_array()
#     frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
#     if frame is None:
#         print("[ERROR] Failed to grab frame, retrying...")
#         continue
#     frame = imutils.resize(frame, width=args.width)
#     rgb_frame = imutils.resize(rgb_frame, width=args.width)
#     small_rgb = cv2.resize(rgb_frame, (0, 0), fx=args.downscale, fy=args.downscale)

#     if frame_count % skip_frames == 0:
#         try:
#             frame_queue.put_nowait(small_rgb)
#         except queue.Full:
#             pass

#     with result_lock:
#         boxes = list(current_boxes)
#         names = list(current_names)

#     for (top, right, bottom, left), name in zip(boxes, names):
#         y = top - 15 if top - 15 > 15 else top + 15
#         cv2.putText(
#             frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2
#         )

#     cv2.imshow("Facial Recognition is Running", frame)
#     key = cv2.waitKey(1) & 0xFF

#     if key == ord("q"):
#         break

#     fps.update()

# fps.stop()
# print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
# print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# cv2.destroyAllWindows()
# stop_event.set()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--width", type=int, default=640, help="width of the frame"
    )
    parser.add_argument(
        "-d",
        "--downscale",
        type=float,
        default=0.25,
        help="factor to downscale the frame",
    )
    parser.add_argument(
        "-s", "--skip", type=int, default=10, help="number of frames to skip"
    )
    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="hog",
        choices=["hog", "cnn"],
        help="face detection model to use",
    )
    parser.add_argument(
        "-j",
        "--jitter",
        type=int,
        default=1,
        help="number of times to jitter the image for encoding",
    )
    fr = FaceRecognition(parser.parse_args())
    name = "Unknown"
    name = fr.recognize_face_and_return_name()
    print("Recognized name: {}".format(name))
