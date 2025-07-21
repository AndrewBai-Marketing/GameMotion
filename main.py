import cv2
from pose_detector import get_keypoints, show_pose
from motion_classifier import classify, load_motions
from key_mapper import trigger_key

motions = load_motions()

cap = cv2.VideoCapture(0)
print("Press Q to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    keypoints = get_keypoints(frame)
    if keypoints:
        current_pose = list(keypoints.values())
        action = classify(current_pose, motions)
        if action:
            print("Detected:", action)
            trigger_key(action)

    frame = show_pose(frame)
    cv2.imshow("GameMotion", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
