from pynput.keyboard import Controller

keyboard = Controller()

ACTION_KEY_MAP = {
    "Jump": "space",
    "Left": "a",
    "Right": "d",
    "Shoot": "j"
}

def trigger_key(action):
    if action in ACTION_KEY_MAP:
        key = ACTION_KEY_MAP[action]
        keyboard.press(key)
        keyboard.release(key)
