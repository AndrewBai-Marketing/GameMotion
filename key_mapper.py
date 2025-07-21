import keyboard
import time

def trigger_key(action):
    key = action.lower()
    print(f"🔘 Holding: {key}")
    keyboard.press(key)
    time.sleep(0.1)  # hold key for 100ms (adjustable)
    keyboard.release(key)
