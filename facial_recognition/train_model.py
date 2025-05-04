#! /usr/bin/python

# import the necessary packages
import os

# import argparse
import pickle

import cv2
import face_recognition
from imutils import paths

# our images are located in the dataset folder
print("[INFO] start processing faces...")
imagePaths = list(paths.list_images("/home/bartox7777/alkomat_flask/dataset"))

# initialize/load known encodings and names
encodingsPath = "/home/bartox7777/alkomat_flask/encodings.pickle"
knownEncodingsBeforeTraining = []
knownNamesBeforeTraining = []

knownNames = []
knownEncodings = []

if os.path.exists(encodingsPath):
    print("[INFO] loading existing encodings...")
    with open(encodingsPath, "rb") as f:
        data = pickle.load(f)
        print(data)
    knownEncodingsBeforeTraining = data["encodings"]
    knownNamesBeforeTraining = data["names"]

print(knownNamesBeforeTraining)


# loop over the image paths
for i, imagePath in enumerate(imagePaths):
    # extract the person name from the image path
    name = imagePath.split(os.path.sep)[-2]

    if name in knownNamesBeforeTraining:
        print(f"[INFO] skipping {name} as it already exists in encodings")
        continue

    print(f"[INFO] processing image {i+1}/{len(imagePaths)}")
    # load the input image and convert it from RGB (OpenCV ordering)
    # to dlib ordering (RGB)
    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # detect the (x, y)-coordinates of the bounding boxes
    # corresponding to each face in the input image
    boxes = face_recognition.face_locations(rgb, model="hog")

    # compute the facial embedding for the face
    encodings = face_recognition.face_encodings(rgb, boxes)

    # loop over the encodings
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)

for i, name in enumerate(knownNamesBeforeTraining):
    knownEncodings.append(knownEncodingsBeforeTraining[i])
    knownNames.append(name)

print(knownNames)

# dump the facial encodings + names to disk
print("[INFO] serializing encodings...")
with open(encodingsPath, "wb") as f:
    f.write(pickle.dumps({"encodings": knownEncodings, "names": knownNames}))
