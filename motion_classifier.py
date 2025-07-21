import numpy as np
import json
import os

DATA_PATH = "data/motions.json"

def load_motions():
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_motion(label, frames):
    motions = load_motions()
    motions[label] = motions.get(label, []) + frames
    with open(DATA_PATH, "w") as f:
        json.dump(motions, f)

def classify(current_pose, motions):
    # Basic L2 distance to known motions
    def avg_pose(samples):
        return np.mean(samples, axis=0)

    best_label, best_score = None, float('inf')
    for label, samples in motions.items():
        samples = [np.array(s).flatten() for s in samples]
        score = np.linalg.norm(avg_pose(samples) - np.array(current_pose).flatten())
        if score < best_score:
            best_label, best_score = label, score
    return best_label if best_score < 0.5 else None
