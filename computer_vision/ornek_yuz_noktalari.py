"""Faz 0 başlangıç örneği: webcam'i aç, yüz noktalarını çiz, ağız açıklığını ve gülümsemeyi yazdır.

Çalıştırmak için repo kök klasöründen:
    python -m computer_vision.ornek_yuz_noktalari

Çıkmak için görüntü penceresindeyken q tuşuna bas.

DİKKAT: İnternetteki örneklerin çoğu `mp.solutions.face_mesh` kullanır. MediaPipe'ın
yeni sürümlerinde `mp.solutions` yok; o kod "AttributeError" verir. Burada yeni yol olan
"Face Landmarker" kullanılıyor. Model dosyası (~4 MB) ilk çalıştırmada otomatik indirilir.

Bu bir öğrenme alıştırması; bilerek basit, sırayla çalışan bir döngü. Gerçek modül Faz 1'de
asyncio ile yazılacak ve sözleşme A1/A2 mesajları üretecek.

Gizlilik: kamera görüntüsü sadece ekranda gösterilir, hiçbir yere kaydedilmez.
"""

import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python import vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
MODEL_YOLU = Path(__file__).parent / "modeller" / "face_landmarker.task"

# Yüz noktalarının numaraları (468 noktalık yüz haritasında).
UST_DUDAK = 13
ALT_DUDAK = 14
ALIN = 10
CENE = 152


# Model dosyası yoksa internetten indirir, varsa hiçbir şey yapmaz.
def modeli_hazirla() -> Path:
    if not MODEL_YOLU.exists():
        MODEL_YOLU.parent.mkdir(parents=True, exist_ok=True)
        print("Model indiriliyor (bir kereye mahsus)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_YOLU)
    return MODEL_YOLU


# Video modunda çalışan bir Face Landmarker oluşturur. Blendshape'ler açık:
# MediaPipe bize "çene ne kadar açık", "ne kadar gülümsüyor" gibi 0–1 arası hazır skorlar verir.
def landmarker_olustur(model_yolu: Path) -> vision.FaceLandmarker:
    ayarlar = vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_yolu)),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
    )
    return vision.FaceLandmarker.create_from_options(ayarlar)


# Ağız açıklığını yüz boyuna bölerek verir. Böylece kameraya yakın ya da uzak
# olman sonucu değiştirmez. Ağız kapalıyken ~0.00, esnerken ~0.15 ve üstü.
def agiz_acikligi(noktalar) -> float:
    agiz = abs(noktalar[ALT_DUDAK].y - noktalar[UST_DUDAK].y)
    yuz_boyu = abs(noktalar[CENE].y - noktalar[ALIN].y)
    return agiz / yuz_boyu if yuz_boyu > 0 else 0.0


# Blendshape listesinden istenen skoru adıyla bulur; yoksa 0 döner.
def skor(blendshapeler, ad: str) -> float:
    for b in blendshapeler:
        if b.category_name == ad:
            return b.score
    return 0.0


# Bir kare üzerinde yüzü bulur, noktaları kareye çizer ve ölçümleri döndürür.
# Yüz yoksa None döner.
def kareyi_isle(landmarker: vision.FaceLandmarker, kare, zaman_ms: int) -> dict | None:
    rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)  # OpenCV BGR verir, MediaPipe RGB ister
    goruntu = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    sonuc = landmarker.detect_for_video(goruntu, zaman_ms)

    if not sonuc.face_landmarks:
        return None

    noktalar = sonuc.face_landmarks[0]
    yukseklik, genislik = kare.shape[:2]
    for n in noktalar:
        # Noktalar 0–1 arası oranlarla gelir; piksele çevirip küçük bir daire çiziyoruz.
        cv2.circle(kare, (int(n.x * genislik), int(n.y * yukseklik)), 1, (0, 255, 0), -1)

    blend = sonuc.face_blendshapes[0]
    return {
        "agiz": agiz_acikligi(noktalar),
        "cene_acik": skor(blend, "jawOpen"),
        "gulumseme": (skor(blend, "mouthSmileLeft") + skor(blend, "mouthSmileRight")) / 2,
    }


# Kamerayı açar, her kareyi işler ve sonucu hem pencereye hem terminale yazar.
def main() -> None:
    landmarker = landmarker_olustur(modeli_hazirla())
    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        print("Kamera açılamadı. Başka bir program (Zoom, Teams) kamerayı kullanıyor olabilir.")
        return

    baslangic = time.monotonic()
    son_yazdirma = 0.0
    try:
        while True:
            okundu, kare = kamera.read()
            if not okundu:
                print("Kameradan görüntü gelmedi.")
                break
            kare = cv2.flip(kare, 1)  # ayna görüntüsü, daha doğal görünür

            # Video modunda her karenin zamanı bir öncekinden büyük olmalı.
            zaman_ms = int((time.monotonic() - baslangic) * 1000)
            olcum = kareyi_isle(landmarker, kare, zaman_ms)

            if olcum is None:
                yazi = "Yuz yok"
            else:
                yazi = (
                    f"agiz {olcum['agiz']:.2f}  cene {olcum['cene_acik']:.2f}"
                    f"  gulumseme {olcum['gulumseme']:.2f}"
                )
            cv2.putText(kare, yazi, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Terminali boğmamak için saniyede bir kez yazdır.
            if time.monotonic() - son_yazdirma > 1:
                print(yazi)
                son_yazdirma = time.monotonic()

            cv2.imshow("Yuz noktalari (q: cikis)", kare)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        kamera.release()
        cv2.destroyAllWindows()
        landmarker.close()


if __name__ == "__main__":
    main()
