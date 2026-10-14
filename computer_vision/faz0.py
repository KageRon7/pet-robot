"""Faz 0: Webcam + MediaPipe Tasks FaceLandmarker ile yüz noktalarını çiz,
ağız açıklığını ekrana sayı olarak yaz.

Kurulum
Çıkış: pencere açıkken 'q' veya ESC.

Not: mp.solutions KULLANILMIYOR. Yeni yol: mediapipe.tasks.python.vision.FaceLandmarker.
Gizlilik: kare hiçbir yere kaydedilmez veya gönderilmez, sadece ekranda gösterilir.
"""

import math
import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
MODEL_PATH = "face_landmarker.task"

# Ağız açıklığı için iç dudak noktaları
UST_DUDAK, ALT_DUDAK = 13, 14
SOL_KOSE, SAG_KOSE = 78, 308


def modeli_indir():
    if not os.path.exists(MODEL_PATH):
        print("Model indiriliyor (tek seferlik)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Tamam:", MODEL_PATH)


def agiz_orani(landmarks, w, h):
    """Dudak aralığı / ağız genişliği. Yüzün kameraya uzaklığından bağımsızdır."""

    def pt(i):
        return landmarks[i].x * w, landmarks[i].y * h

    return math.dist(pt(UST_DUDAK), pt(ALT_DUDAK)) / math.dist(pt(SOL_KOSE), pt(SAG_KOSE))


def main():
    modeli_indir()

    secenekler = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        raise RuntimeError("Webcam açılamadı (indeks 0). Başka uygulama kullanıyor olabilir.")

    baslangic = time.monotonic()
    son_ts = -1

    with vision.FaceLandmarker.create_from_options(secenekler) as landmarker:
        while True:
            ok, kare = kamera.read()
            if not ok:
                break

            kare = cv2.flip(kare, 1)  # ayna görünümü
            h, w = kare.shape[:2]

            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            mp_kare = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # VIDEO modunda zaman damgası (ms) kesinlikle artan olmalı
            ts = int((time.monotonic() - baslangic) * 1000)
            if ts <= son_ts:
                ts = son_ts + 1
            son_ts = ts

            sonuc = landmarker.detect_for_video(mp_kare, ts)

            if sonuc.face_landmarks:
                noktalar = sonuc.face_landmarks[0]

                for n in noktalar:
                    cv2.circle(kare, (int(n.x * w), int(n.y * h)), 1, (0, 255, 0), -1)

                oran = agiz_orani(noktalar, w, h)
                cv2.putText(kare, f"agiz: {oran:.2f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            else:
                cv2.putText(kare, "yuz yok", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            cv2.imshow("Faz 0 - Yuz noktalari", kare)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
