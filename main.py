import cv2
import json
import mediapipe as mp
from pose_detector import show_pose
from motion_classifier import classify, load_motions
from key_mapper import trigger_key

# Load profile
PROFILE_PATH = "config/selected_profile.json"
with open(PROFILE_PATH, "r") as f:
    profile = json.load(f)

gesture_to_key = {v: profile["key_mapping"][k] for k, v in profile["controls"].items()}

# Init pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Load motion database
motions = load_motions()

# Webcam
cap = cv2.VideoCapture(0)
print("Press Q to quit")

detected_action = ""
cooldown_counter = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    current_pose = []
    if results.pose_landmarks:
        selected = [results.pose_landmarks.landmark[i] for i in range(22)]
        current_pose = [[lm.x, lm.y, lm.z] for lm in selected]

        motion_label = classify(current_pose, motions)
        if motion_label and motion_label in gesture_to_key:
            if motion_label != detected_action or cooldown_counter == 0:
                print(f"🟢 Detected Motion: {motion_label} → Key: {gesture_to_key[motion_label]}")
                detected_action = motion_label
                trigger_key(gesture_to_key[motion_label])
                cooldown_counter = 10  # cooldown in frames
        else:
            detected_action = ""

    if cooldown_counter > 0:
        cooldown_counter -= 1

    # Draw overlay
    frame = show_pose(frame)
    if detected_action:
        cv2.putText(
            frame,
            f"Detected: {detected_action}",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            3,
            cv2.LINE_AA
        )

    cv2.imshow("GameMotion", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
