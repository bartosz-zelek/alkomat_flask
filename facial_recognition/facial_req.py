#! /usr/bin/python

# import the necessary packages
import argparse
import base64
import json
import os
import pickle

import cv2
import face_recognition
import requests
import serial
from picamera2 import Picamera2

ip = "150.254.45.26:5000"


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
        try:
            response = requests.get(
                "http://localhost:5000/api/add_reading/{}/{}".format(user_id, meas_val)
            )
            response_msg = response.json()["message"]
        except requests.exceptions.RequestException as e:
            response_msg = "CONNECTION ERROR"
        print("Response: {}".format(response_msg))
        response_char = ""
        if response_msg == "USER DOESN'T EXIST":
            response_char = "USER DOESN'T EXIST"
        elif response_msg == "USER BLOCKED":
            response_char = "USER BLOCKED"
        elif response_msg == "ENTRY BLOCKED":
            response_char = "ENTRY BLOCKED"
        elif response_msg == "ACCEPTED":
            response_char = "ACCEPTED"
        elif response_msg == "CONNECTION ERROR":
            response_char = "CONNECTION ERROR"
        else:
            response_char = "UNKNOWN"
        print("Writing to Arduino: {}".format(response_char))
        self.arduino.write(bytes(response_char, "ascii"))
        print("Info sent to Arduino")


class FaceRecognition:
    def __init__(self, args):
        # path to the encodings file and dynamic reload on change
        self.encodingsP = "/home/bartox7777/alkomat_flask/encodings.pickle"
        self.data = {}
        self._encodings_mtime = None

        def _reload_encodings():
            try:
                mtime = os.path.getmtime(self.encodingsP)
                if self._encodings_mtime != mtime:
                    with open(self.encodingsP, "rb") as f:
                        self.data = pickle.load(f)
                        self._encodings_mtime = mtime
                    print("Encodings reloaded:", self._encodings_mtime)
            except Exception as e:
                print("Failed to reload encodings:", e)

        self._reload_encodings = _reload_encodings
        # initial load
        self._reload_encodings()
        self.cascade = cv2.CascadeClassifier(
            os.path.join(
                os.path.dirname(__file__), "haarcascade_frontalface_default.xml"
            )
        )
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
        # Repeat until a known face is detected
        name = "Unknown"
        while name == "Unknown":
            self._reload_encodings()
            # Capture frame and prepare for detection
            frame = self.cam.capture_array()
            rgb = frame

            # Detect face locations and compute encodings
            boxes = face_recognition.face_locations(rgb, model=self.args.model)
            encodings = face_recognition.face_encodings(
                rgb, boxes, num_jitters=self.args.jitter
            )

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
        return name, frame


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--uuid", type=str, help="UUID of the user", required=True
    )
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

    while True:
        name = "Unknown"
        name, picture = fr.recognize_face_and_return_name()
        uuid = fr.args.uuid
        # encode frame to JPEG and base64 so Flask can parse JSON
        _, img_buf = cv2.imencode(".jpg", picture)
        img_b64 = base64.b64encode(img_buf).decode("ascii")
        payload = {"photo": img_b64, "user_id": name}
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"http://{ip}/api/uuid/{uuid}", data=json.dumps(payload), headers=headers
        )
        if response.status_code == 200:
            print("UUID sent successfully")
        else:
            print(f"Failed to send UUID: {response.status_code} {response.text}")
        print("Recognized name: {}".format(name))
