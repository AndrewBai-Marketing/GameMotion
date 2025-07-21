import cv2
import json
import os
import time
import mediapipe as mp

# Constants
DATA_FILE = "data/motions.json"
JOINT_COUNT = 22  # First 22 landmarks only

# Setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Load or create motion database
motions = {}
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, "r") as f:
            motions = json.load(f)
    except json.JSONDecodeError:
        print("⚠️ motions.json is corrupted. Starting fresh.")
        motions = {}

# Webcam
cap = cv2.VideoCapture(0)
print("Press 'T' to train a new motion, or 'Q' to quit")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        cv2.imshow("Train Motion", frame)
        key = cv2.waitKey(10)

        if key == ord('q'):
            break

        elif key == ord('t'):
            label = input("Enter motion label (e.g., Jump): ").strip()

            if label not in motions:
                motions[label] = []

            print(f"📸 Get ready! Recording motion '{label}' in 3 seconds...")
            time.sleep(3)

            captured_frames = []
            for i in range(500):
                ret, frame = cap.read()
                if not ret:
                    break

                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(image_rgb)

                if results.pose_landmarks:
                    selected = [results.pose_landmarks.landmark[i] for i in range(JOINT_COUNT)]
                    joints = [[lm.x, lm.y, lm.z] for lm in selected]
                    captured_frames.append(joints)
                    print(f"Captured frame {i+1}")
                else:
                    print("No pose detected")

                cv2.imshow("Capturing...", frame)
                cv2.waitKey(30)

            if captured_frames:
                motions[label].extend(captured_frames)
                with open(DATA_FILE, "w") as f:
                    json.dump(motions, f, indent=2)
                print(f"✅ Saved {len(captured_frames)} frames for '{label}' to {DATA_FILE}")
            else:
                print("❌ No valid frames captured. Try again.")

except KeyboardInterrupt:
    print("\n⛔ KeyboardInterrupt: Exiting gracefully.")

finally:
    cap.release()
    cv2.destroyAllWindows()
