import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

motions_path = "data/motions.json"
config_path = "config/selected_profile.json"

motions = list(json.load(open(motions_path)).keys()) if os.path.exists(motions_path) else []
actions = ["Jump", "Left", "Right"]

profile = {
    "profile_name": "TestProfile",
    "controls": {},
    "key_mapping": {
        "Jump": "space",
        "Left": "a",
        "Right": "d",
    }
}

def save_profile():
    for action in actions:
        motion = motion_vars[action].get()
        profile["controls"][action] = motion
    with open(config_path, "w") as f:
        json.dump(profile, f, indent=2)
    messagebox.showinfo("Saved", f"Profile saved to {config_path}")

root = tk.Tk()
root.title("GameMotion - Simple Profile Selector")

motion_vars = {}
for i, action in enumerate(actions):
    ttk.Label(root, text=action).grid(row=i, column=0, padx=10, pady=5)
    motion_vars[action] = tk.StringVar(value=motions[0] if motions else "")
    ttk.Combobox(root, textvariable=motion_vars[action], values=motions, width=30).grid(row=i, column=1, padx=10, pady=5)

ttk.Button(root, text="Save Profile", command=save_profile).grid(row=len(actions), column=0, columnspan=2, pady=20)

root.mainloop()
