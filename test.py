import face_recognition
import os
import cv2
from datetime import datetime

def collect_face_images_from_rpi_camera(save_dir="dataset/photo", num_images=10):
    """
    Collect face images from the Raspberry Pi camera and save them to a directory.
    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Initialize camera (use 0 for default camera, or use PiCamera if on Raspberry Pi)
    cap = cv2.VideoCapture(0)
    count = 0
    print("Press 'q' to quit early.")
    while count < num_images:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Failed to grab frame")
            break
        # Convert grayscale to BGR if needed
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        # Convert to RGB for face_recognition
        rgb_frame = frame[:, :, ::-1]
        face_locations = face_recognition.face_locations(rgb_frame)
        for (top, right, bottom, left) in face_locations:
            # Draw rectangle around face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        # Save image if at least one face detected
        if face_locations:
            img_name = os.path.join(save_dir, f"face_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg")
            cv2.imwrite(img_name, frame)
            print(f"Saved {img_name}")
            count += 1
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    
def just_save_photo():
    """
    Just save a photo from the camera without face detection.
    """
    save_dir = "dataset/photo"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera")
        return
    ret, frame = cap.read()
    print(f"ret: {ret}")
    print(f"frame is None: {frame is None}")
    if ret and frame is not None:
        img_name = os.path.join(save_dir, f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg")
        res = cv2.imwrite(img_name, frame)
        print(f"cv2.imwrite result: {res}")
        if res:
            print(f"Saved {img_name}")
        else:
            print(f"Failed to save photo at {img_name}")
    else:
        print("Failed to capture frame from camera.")
    cap.release()
    
just_save_photo()
