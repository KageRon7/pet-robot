# Sahte beyin (Faz 0)


import random  


EMOTIONS = ("idle", "happy", "curious", "sleepy", "sad", "playful", "startled")


def decide(b1=None) -> dict:
    return {
        "emotion": random.choice(EMOTIONS),
        "intensity": round(random.uniform(0.3, 1.0), 2),
        "duration_s": random.randint(3, 8),
        
        "memory_note": None, # hafıza vize sonrası, şimdilik hep boş (None, JSON'da null olur)
        "reason": "Sahte beyin: rastgele seçildi",
    }


if __name__ == "__main__":
    for _ in range(5):
        print(decide())