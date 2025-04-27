#! /usr/bin/python

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import imutils
import pickle
import time
import argparse
import sys
import cv2
import os
import threading
import queue

import sys
import codecs
import serial
import requests
from time import sleep
    

class ArduinoComs:    
    def __init__(self, port) -> None:
        self.arduino = serial.Serial(port)
        self.ref_val = 100
        print('Coms established')

    def read_and_respond(self, user_id):
        print('Face recognition')
        print('Writing to Arduino: {}'.format(user_id))
        self.arduino.write(bytes(user_id, 'ascii'))
        print('Line read - user_id is {}'.format(user_id))
        meas_val = int(self.arduino.readline())
        print('Line read - meas_val is {}'.format(meas_val))
        # is_drunk = meas_val / ref_val > 0.2 and ref_val - meas_val > 5 and meas_val < 70
        # TODO: maybe rewrite using ?user_id=user_id etc. if possible
        # 'g' if all good, 'r' if drunk, 'b' if already blocked in DB, 'n' if user_id not recognized
        # not tested, server not ready to respond just yet
        response = requests.get('http://localhost:5000/api/add_reading/{}/{}'.format(user_id, meas_val))
        response_msg = response.json()['message']
        print("Response: {}".format(response_msg))
        response_char = ''
        if response_msg == "USER DOESN'T EXIST":
            response_char = 'n'
        elif response_msg == "USER BLOCKED":
            response_char = 'b'
        elif response_msg == "ENTRY BLOCKED":
            response_char = 'r'
        elif response_msg == "ACCEPTED":
            response_char = 'g'
        else:
            response_char = 'n'
        print('Writing to Arduino: {}'.format(response_char))
        self.arduino.write(bytes(response_char, 'ascii'))
        print('Info sent to Arduino')
        sleep(5)  # wait for Arduino to process the response
        
        

ard = ArduinoComs('/dev/ttyUSB0')


#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "Unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())

# parse optional arguments
parser = argparse.ArgumentParser()
parser.add_argument('--pi', action='store_true', help='Use PiCamera instead of USB webcam')
parser.add_argument('--src', type=int, default=0, help='OpenCV video source index')
parser.add_argument('--skip', type=int, default=4, help='Process every Nth frame to increase throughput (higher skip = faster)')
parser.add_argument('--width', type=int, default=640, help='Display frame width (lower width = faster)')
parser.add_argument('--downscale', type=float, default=0.25, help='Downscale factor for detection frame (lower = faster detection)')
parser.add_argument('--model', choices=['hog','cnn'], default='hog', help='Face detection model (hog is faster)')
parser.add_argument('--jitter', type=int, default=0, help='Number of jitters for face encoding (0 for max speed)')
parser.add_argument('--ban-duration', type=int, default=35, help='Duration in seconds to ban printed names temporarily')
args = parser.parse_args()

# initialize banlist to suppress repeated prints
banlist = {}

# initialize Haar cascade
cascade = cv2.CascadeClassifier(os.path.join(os.path.dirname(__file__), 'haarcascade_frontalface_default.xml'))

try:
    MultiTracker = cv2.legacy.MultiTracker_create
    Tracker = cv2.legacy.TrackerKCF_create
except AttributeError:
    MultiTracker = cv2.MultiTracker_create
    Tracker = cv2.TrackerKCF_create
trackers = None

skip_frames = args.skip
frame_count = 0
last_boxes = []
last_names = []

# initialize the video stream (Imutils, Picamera2, or cv2) and allow sensor to warm up
if args.pi:
    print('[INFO] Using Picamera2...')
    try:
        from picamera2 import Picamera2
    except ModuleNotFoundError:
        print("[ERROR] picamera2 module not found. Please install it: pip3 install picamera2")
        sys.exit(1)
    cam = Picamera2()
    # configure for 8-bit RGB output
    config = cam.create_video_configuration(main={'size': (
        640, 480
        ), 'format': 'RGB888'}, controls={'FrameRate': 60})
    cam.configure(config)
    cam.start()
    time.sleep(2.0)
    use_picamera2 = True
    use_cv2 = False
else:
    print(f'[INFO] Attempting VideoStream(src={args.src})...')
    vs = VideoStream(src=args.src, framerate=30).start()
    time.sleep(2.0)
    # verify imutils VideoStream frame; fallback to cv2.VideoCapture on failure
    frame = vs.read()
    if frame is None:
        print('[WARN] VideoStream failed, falling back to cv2.VideoCapture')
        cap = cv2.VideoCapture(args.src)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            print('[ERROR] Cannot open camera, exiting')
            sys.exit(1)
        use_cv2 = True
    else:
        use_cv2 = False
    use_picamera2 = False

# start the FPS counter
fps = FPS().start()

frame_queue = queue.Queue(maxsize=1)
result_lock = threading.Lock()
current_boxes = []
current_names = []
stop_event = threading.Event()

def detection_loop():
    while not stop_event.is_set():
        # wait for next frame, blocking until available
        small = frame_queue.get()
        # detect faces using chosen model
        boxes_s = face_recognition.face_locations(small, model=args.model)
        # compute encodings with jitter for more robust features
        encs = face_recognition.face_encodings(small, boxes_s, num_jitters=args.jitter)
        names = []
        for enc in encs:
            # use stricter tolerance for fewer false positives
            matches = face_recognition.compare_faces(data['encodings'], enc, tolerance=0.5)
            name = 'Unknown'
            if True in matches:
                matchedIdxs = [i for (i,b) in enumerate(matches) if b]
                counts = {}
                for i in matchedIdxs:
                    n = data['names'][i]
                    counts[n] = counts.get(n,0)+1
                name = max(counts, key=counts.get)
            names.append(name)
        with result_lock:
            current_boxes[:] = [(t*4, r*4, b*4, lf*4) for (t,r,b,lf) in boxes_s]
            current_names[:] = names

# start the detection thread
threading.Thread(target=detection_loop, daemon=True).start()

# loop over frames from the video file stream
while True:
    frame_count += 1
    # grab the frame (Picamera2, imutils VideoStream or cv2.VideoCapture) and prepare RGB/BGR copies
    if use_picamera2:
        rgb_frame = cam.capture_array()  # RGB888 array
        frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
    elif use_cv2:
        ret, frame = cap.read()
        if not ret:
            print('[ERROR] cv2.VideoCapture failed, retrying...')
            continue
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        frame = vs.read()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # if the frame was not grabbed correctly, skip processing
    if frame is None:
        print("[ERROR] Failed to grab frame, retrying...")
        continue
    # resize to higher resolution for improved accuracy
    frame = imutils.resize(frame, width=args.width)
    rgb_frame = imutils.resize(rgb_frame, width=args.width)
    # create smaller frame for face recognition (50% size) for balanced speed and accuracy
    small_rgb = cv2.resize(rgb_frame, (0, 0), fx=args.downscale, fy=args.downscale)

    # push small frame for detection only every Nth frame
    if frame_count % skip_frames == 0:
        try:
            frame_queue.put_nowait(small_rgb)
        except queue.Full:
            pass

    # get latest results
    with result_lock:
        boxes = list(current_boxes)
        names = list(current_names)
        if len(names) > 0:
            ard.read_and_respond(names[0])
            names.clear()

    # print recognized names to terminal instead of overlaying on image
    if names:
        now = time.time()
        unique_names = set(names)
        for name in unique_names:
            exp = banlist.get(name, 0)
            if now >= exp:
                print(f"[INFO] Detected: {name}")
                banlist[name] = now + args.ban_duration

    # loop over the recognized faces
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # display only the name for performance
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
            .8, (0, 255, 255), 2)

    # display the image to our screen
    cv2.imshow("Facial Recognition is Running", frame)
    key = cv2.waitKey(1) & 0xFF

    # quit when 'q' key is pressed
    if key == ord("q"):
        break

    # update the FPS counter
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
if use_cv2:
    cap.release()
else:
    vs.stop()
stop_event.set()
