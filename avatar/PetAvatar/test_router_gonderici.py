import socket
import json
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
hedef = ("127.0.0.1", 5555)

# Kaan'ın MediaPipe modülünden gelecek örnek senaryolar:
# (Duygu, Yatay Bakış [-1 sol, +1 sağ], Dikey Bakış [-1 yukarı, +1 aşağı])
senaryolar = [
    {"emotion": "curious", "look_x": -0.8, "look_y": -0.5},  # Sol üst köşeye merakla bak
    {"emotion": "happy",   "look_x": 0.8,  "look_y": -0.3},  # Sağ üste gülümseyerek bak
    {"emotion": "tsundere","look_x": -0.6, "look_y": 0.4},   # Sol alta tripli bak
    {"emotion": "startled","look_x": 0.0,  "look_y": -0.9},  # Tam yukarı şaşkın bak
    {"emotion": "idle",    "look_x": 0.0,  "look_y": 0.0},   # Merkeze dön ve normalleş
]

print("MediaPipe simülasyonu başlıyor...")

for veri in senaryolar:
    paket = json.dumps(veri).encode("utf-8")
    sock.sendto(paket, hedef)
    print(f"Gönderildi -> Duygu: {veri['emotion']} | Bakış: ({veri['look_x']}, {veri['look_y']})")
    time.sleep(2.5)

print("Simülasyon tamamlandı. 3 saniye sonra kedi tekrar fare imlecini takip etmeye dönecek.")