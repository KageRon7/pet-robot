"""CV olayları (Sözleşme A2): user_arrived, user_left, smile, yawn, drowsy, looking_at_robot_long
+ duygu ifadeleri: sad, angry, surprised (bunlar sözleşmede YOK, takımla eklenmeli).

Kurulum:
    pip install mediapipe opencv-python

Çalıştırma:
    python faz1_olaylar.py            # sadece A2 olayları
    python faz1_olaylar.py --track    # A2 olayları + A1 face_track akışı (~15 mesaj/sn)

Başlangıçta yüzün ilk görününce 2 sn "kalibrasyon" yapılır: nötr (ifadesiz) yüzle kameraya bak.
Duygu skorları bu nötr yüze göre hesaplanır. Yeniden kalibre etmek için 'c' tuşu.
Çıkış: 'q' veya ESC.

Olaylar konsola (stdout) tek satır JSON olarak düşer:
    {"type": "event", "t": 1728648003.5, "event": "smile", "confidence": 0.87, "duration_s": 2.1}

Gizlilik: kare diske yazılmaz, başka modüle gitmez. Dışarı sadece olay JSON'ları çıkar.
(Pencere sadece senin test etmen için; sonra kaldırılabilir.)
"""

import argparse
import json
import math
import os
import sys
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

# ---- Eşikler (hepsi ilk tahmin, kendi yüzünde test edip ayarla) ----
ARRIVED_SN = 2.0          # sözleşme: yüz en az 2 sn görünsün
LEFT_SN = 10.0            # sözleşme: yüz en az 10 sn yok
MIN_CONFIDENCE = 0.6      # sözleşme: bunun altı gönderilmez

SMILE_AC, SMILE_KAPAT, SMILE_MIN_SN = 0.5, 0.35, 0.3
YAWN_AC, YAWN_KAPAT, YAWN_MIN_SN = 0.5, 0.3, 1.5

# drowsy: gözler kısık/kapalı kalma skoru (eyeBlink ortalaması), en az 2 sn sürmeli
# (normal göz kırpma çok kısa sürdüğü için süre şartı onu eler)
DROWSY_AC, DROWSY_KAPAT, DROWSY_MIN_SN = 0.5, 0.35, 2.0

# looking_at_robot_long: baş yönü ve bakış kameraya ne kadar yakın (0–1 "merkezlik" skoru)
LOOK_AC, LOOK_KAPAT, LOOK_MIN_SN = 0.2, 0.01, 3.0   # sözleşme: 3 sn'den uzun
YAW_MAX = 25.0     # derece: kafa sağa/sola bu kadar dönünce "bakmıyor"
PITCH_MAX = 25.0   # derece: kafa yukarı/aşağı bu kadar dönünce "bakmıyor"
GAZ_MAX = 0.4      # göz bebeği yönü blendshape'lerinin (0–1) kabul edilen en büyük değeri

GOZ_BAKIS = [
    "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeLookDownLeft",
    "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeLookDownRight",
]

# duygu ifadeleri: nötr yüze göre ham skor, "tam ifade" referansına bölünüp 0–1'e çekilir.
# REF küçüldükçe daha hafif ifadeler de tam sayılır. Hepsi ilk tahmin.
SAD_REF, ANGRY_REF, SURPRISED_REF = 0.3, 0.4, 0.4
EMO_AC, EMO_KAPAT, EMO_MIN_SN = 0.6, 0.4, 0.7

# Şaşkınlık skoru (0–1) bunun üstündeyse ağız açıklığı "esneme" değil "şaşkınlık" sayılır.
YAWN_AYRIM = 0.5

KALIB_SN = 2.0     # nötr yüz kalibrasyon süresi

TRACK_HZ = 15      # sözleşme A1: saniyede yaklaşık 15 face_track mesajı


def modeli_indir():
    if not os.path.exists(MODEL_PATH):
        print("Model indiriliyor (tek seferlik)...", file=sys.stderr)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Tamam:", MODEL_PATH, file=sys.stderr)


def olay_gonder(event, t, confidence, duration_s):
    """A2 mesajını üretir. Şimdilik konsola yazar; sonra router'a gönderme buraya gelecek."""
    if confidence < MIN_CONFIDENCE:
        return
    mesaj = {
        "type": "event",
        "t": round(t, 2),
        "event": event,
        "confidence": round(min(confidence, 1.0), 2),
        "duration_s": round(duration_s, 2),
    }
    print(json.dumps(mesaj), flush=True)


class SureliOlay:
    """Bir skor eşiği aşılınca başlar, düşünce biter; süresi yeterliyse olayı gönderir.

    Histerezis (ac > kapat) skor eşik civarında titrerken olayın parçalanmasını önler.
    Olay bittiğinde gönderilir, çünkü duration_s ancak o zaman bilinir.
    """

    def __init__(self, ad, ac, kapat, min_sure):
        self.ad, self.ac, self.kapat, self.min_sure = ad, ac, kapat, min_sure
        self.aktif = False
        self.baslangic = 0.0
        self.zirve = 0.0

    def guncelle(self, skor, simdi):
        """skor None ise (yüz yok) açık olay kapatılır."""
        if skor is None:
            self.bitir(simdi)
            return
        if not self.aktif:
            if skor >= self.ac:
                self.aktif = True
                self.baslangic = simdi
                self.zirve = skor
        else:
            self.zirve = max(self.zirve, skor)
            if skor < self.kapat:
                self.bitir(simdi)

    def bitir(self, simdi):
        if not self.aktif:
            return
        self.aktif = False
        sure = simdi - self.baslangic
        if sure >= self.min_sure:
            olay_gonder(self.ad, self.baslangic, self.zirve, sure)


class Kalibrasyon:
    """Nötr yüzün ortalama blendshape değerlerini çıkarır; duygu skorları bunun farkından hesaplanır.

    Webcam'de herkesin nötr yüzünde bile bazı blendshape'ler sıfır olmaz (örn. hafif kaş
    çatma). Bu taban değer çıkarılınca hafif ifadeler (özellikle üzüntü) görünür olur.
    """

    def __init__(self, sure):
        self.sure = sure
        self.sifirla()

    def sifirla(self):
        self.baslangic = None
        self.toplam = {}
        self.sayi = 0
        self.baz = None

    @property
    def bitti(self):
        return self.baz is not None

    def ekle(self, b, simdi):
        if self.baslangic is None:
            self.baslangic = simdi
        for k, v in b.items():
            self.toplam[k] = self.toplam.get(k, 0.0) + v
        self.sayi += 1
        if simdi - self.baslangic >= self.sure:
            self.baz = {k: v / self.sayi for k, v in self.toplam.items()}
            print("Kalibrasyon bitti.", file=sys.stderr)

    def uygula(self, b):
        return {k: max(0.0, v - self.baz.get(k, 0.0)) for k, v in b.items()}


def blendshape_sozlugu(sonuc):
    return {b.category_name: b.score for b in sonuc.face_blendshapes[0]}


def bas_acisi(sonuc):
    """Yüzün baktığı yönün (yaw, pitch) açısını derece olarak verir.

    Dönüşüm matrisinin üçüncü sütunu yüzün ileri eksenidir. abs(z) kullanıyoruz ki
    eksen yönü (+z / -z) sürümden sürüme değişse de sonuç bozulmasın; biz sadece
    sapmanın büyüklüğüne bakıyoruz.
    """
    m = sonuc.facial_transformation_matrixes[0]
    x, y, z = m[0][2], m[1][2], m[2][2]
    yaw = math.degrees(math.atan2(x, abs(z)))
    pitch = math.degrees(math.atan2(y, math.hypot(x, z)))
    return yaw, pitch


def merkezlik_skoru(yaw, pitch, b):
    """1.0 = tam kameraya bakıyor, 0.0 = sınırda ya da dışında. Baş yönü + göz bebeği."""
    gaz = max(b.get(ad, 0.0) for ad in GOZ_BAKIS)
    sapma = max(abs(yaw) / YAW_MAX, abs(pitch) / PITCH_MAX, gaz / GAZ_MAX)
    return max(0.0, 1.0 - sapma)


def _ort(b, *adlar):
    return sum(b.get(a, 0.0) for a in adlar) / len(adlar)


def ifade_skorlari(b, gulme, cene):
    """Nötr yüze göre düzeltilmiş blendshape'lerden sad / angry / surprised / yawn skorları (0–1).

    b: kalibrasyon farkı uygulanmış blendshape sözlüğü
    gulme, cene: ham gülümseme ve çene açıklığı skorları

    Esneme ile şaşkınlığı ayıran şey ağız değil gözler ve kaşlar: şaşkınlıkta gözler
    iri açılır ve kaşlar kalkar, esnemede gözler kısılır. Bu yüzden şaşkınlık skoru
    yüksekse ağız açıklığı esneme sayılmaz; gözler kısıksa şaşkınlık skoru düşer.
    Mutlu ifadesi zaten `smile` olayı.
    """
    goz_acik = _ort(b, "eyeWideLeft", "eyeWideRight")
    kas_yukari = _ort(b, "browInnerUp", "browOuterUpLeft", "browOuterUpRight")
    goz_kisik = max(_ort(b, "eyeSquintLeft", "eyeSquintRight"),
                    _ort(b, "eyeBlinkLeft", "eyeBlinkRight"))

    uzgun = (
        0.4 * _ort(b, "mouthFrownLeft", "mouthFrownRight")
        + 0.35 * b.get("browInnerUp", 0.0)
        + 0.25 * b.get("mouthShrugLower", 0.0)
    )
    sinirli = (
        0.6 * _ort(b, "browDownLeft", "browDownRight")
        + 0.2 * _ort(b, "noseSneerLeft", "noseSneerRight")
        + 0.2 * _ort(b, "eyeSquintLeft", "eyeSquintRight")
    )
    saskin = max(0.0, 0.6 * goz_acik + 0.4 * kas_yukari - 0.5 * goz_kisik)
    saskin_norm = min(1.0, saskin / SURPRISED_REF)

    skorlar = {
        "sad": min(1.0, uzgun / SAD_REF),
        "angry": min(1.0, sinirli / ANGRY_REF),
        "surprised": saskin_norm,
    }
    if gulme >= SMILE_KAPAT:
        skorlar["sad"] = skorlar["angry"] = 0.0
    if cene >= 0.4 or saskin_norm >= YAWN_AYRIM:
        skorlar["sad"] = 0.0   # ağız açıkken ya da gözler iriyken üzgün sayılmaz

    baskin = max(skorlar, key=skorlar.get)
    skorlar = {ad: (v if ad == baskin else 0.0) for ad, v in skorlar.items()}
    skorlar["yawn"] = 0.0 if saskin_norm >= YAWN_AYRIM else cene

    debug = (f"uzgun_ham {uzgun:.2f}  goz acik {goz_acik:.2f}  "
             f"kas yukari {kas_yukari:.2f}  kisik {goz_kisik:.2f}")
    return skorlar, debug


def yuz_merkezi(noktalar):
    """Yüzün kameradaki merkezi (x, y), 0–1, sol üst köşe (0, 0).

    Tüm yüz noktalarının sınır kutusunun ortası. Kare aynalanmadan işlendiği için
    koordinatlar sözleşmedeki gibi kameranın gördüğü hâle göredir.
    """
    xs = [n.x for n in noktalar]
    ys = [n.y for n in noktalar]
    x = (min(xs) + max(xs)) / 2
    y = (min(ys) + max(ys)) / 2
    return min(1.0, max(0.0, x)), min(1.0, max(0.0, y))


def face_track_gonder(t, present, x, y, looking_at_robot):
    """A1 mesajını üretir. Şimdilik konsola yazar; sonra router'a gönderme buraya gelecek."""
    mesaj = {
        "type": "face_track",
        "t": round(t, 2),
        "present": present,
        "x": None if x is None else round(x, 3),    # present=false ise null
        "y": None if y is None else round(y, 3),
        "looking_at_robot": looking_at_robot,
    }
    print(json.dumps(mesaj), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", action="store_true",
                    help="A1 face_track akışını da stdout'a yaz (~15 mesaj/sn)")
    args = ap.parse_args()
    track_aralik = 1.0 / TRACK_HZ

    modeli_indir()

    secenekler = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,               # gülümseme, çene, göz skorları
        output_facial_transformation_matrixes=True,  # baş yönü
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        raise RuntimeError("Webcam açılamadı (indeks 0). Başka uygulama kullanıyor olabilir.")

    smile = SureliOlay("smile", SMILE_AC, SMILE_KAPAT, SMILE_MIN_SN)
    yawn = SureliOlay("yawn", YAWN_AC, YAWN_KAPAT, YAWN_MIN_SN)
    drowsy = SureliOlay("drowsy", DROWSY_AC, DROWSY_KAPAT, DROWSY_MIN_SN)
    bakis = SureliOlay("looking_at_robot_long", LOOK_AC, LOOK_KAPAT, LOOK_MIN_SN)
    sad = SureliOlay("sad", EMO_AC, EMO_KAPAT, EMO_MIN_SN)
    angry = SureliOlay("angry", EMO_AC, EMO_KAPAT, EMO_MIN_SN)
    surprised = SureliOlay("surprised", EMO_AC, EMO_KAPAT, EMO_MIN_SN)

    kal = Kalibrasyon(KALIB_SN)
    son_track = 0.0         # son face_track mesajının zamanı

    kullanici_var = False   # user_arrived gönderildi, user_left henüz gönderilmedi
    gorunme_basi = None     # yüz kesintisiz görünmeye ne zaman başladı
    kayip_basi = None       # yüz kesintisiz kaybolalı ne zaman oldu

    baslangic = time.monotonic()
    son_ts = -1

    with vision.FaceLandmarker.create_from_options(secenekler) as landmarker:
        while True:
            ok, kare = kamera.read()
            if not ok:
                break

            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            mp_kare = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            ts = int((time.monotonic() - baslangic) * 1000)
            if ts <= son_ts:
                ts = son_ts + 1
            son_ts = ts

            sonuc = landmarker.detect_for_video(mp_kare, ts)
            simdi = time.time()
            yuz_var = bool(sonuc.face_landmarks)

            gulme = cene = goz = merkez = ifade = None
            yuz_x = yuz_y = None
            debug = ""

            if yuz_var:
                kayip_basi = None
                if gorunme_basi is None:
                    gorunme_basi = simdi

                # user_arrived: en az 2 sn kesintisiz yüz
                if not kullanici_var and simdi - gorunme_basi >= ARRIVED_SN:
                    kullanici_var = True
                    olay_gonder("user_arrived", gorunme_basi, 1.0, 0)

                b = blendshape_sozlugu(sonuc)
                gulme = (b.get("mouthSmileLeft", 0.0) + b.get("mouthSmileRight", 0.0)) / 2
                cene = b.get("jawOpen", 0.0)
                goz = (b.get("eyeBlinkLeft", 0.0) + b.get("eyeBlinkRight", 0.0)) / 2
                yaw, pitch = bas_acisi(sonuc)
                merkez = merkezlik_skoru(yaw, pitch, b)
                yuz_x, yuz_y = yuz_merkezi(sonuc.face_landmarks[0])

                if not kal.bitti:
                    kal.ekle(b, simdi)          # kalibrasyon sürerken duygu skoru yok
                else:
                    ifade, debug = ifade_skorlari(kal.uygula(b), gulme, cene)
            else:
                gorunme_basi = None
                if not kal.bitti:
                    kal.sifirla()               # yüz kaybolursa kalibrasyon baştan
                if kayip_basi is None:
                    kayip_basi = simdi

                # user_left: en az 10 sn kesintisiz yüz yok
                if kullanici_var and simdi - kayip_basi >= LEFT_SN:
                    kullanici_var = False
                    olay_gonder("user_left", kayip_basi, 1.0, 0)

            # Esnerken gözler kapanır; bu uyuklama sayılmasın.
            if goz is None:
                drowsy_skoru = None
            else:
                drowsy_skoru = 0.0 if cene >= YAWN_KAPAT else goz
            yawn_skoru = cene if ifade is None else ifade["yawn"]

            smile.guncelle(gulme, simdi)
            yawn.guncelle(yawn_skoru, simdi)
            drowsy.guncelle(drowsy_skoru, simdi)
            bakis.guncelle(merkez, simdi)
            sad.guncelle(None if ifade is None else ifade["sad"], simdi)
            angry.guncelle(None if ifade is None else ifade["angry"], simdi)
            surprised.guncelle(None if ifade is None else ifade["surprised"], simdi)

            # A1: ~15 Hz yüz takip akışı (sadece --track ile). looking_at_robot, bakış
            # olayıyla aynı histerezisi kullanır: bakis.aktif = şu an kameraya bakıyor.
            if args.track and simdi - son_track >= track_aralik:
                son_track = simdi
                face_track_gonder(simdi, yuz_var, yuz_x, yuz_y, bakis.aktif)

            # --- Sadece test için ekran bilgisi ---
            # Önce aynala, sonra yaz; yoksa yazı da aynalanıp ters görünür.
            ekran = cv2.flip(kare, 1)
            if yuz_var:
                satir1 = f"gulme: {gulme:.2f}  cene: {cene:.2f}"
                satir2 = f"goz kapali: {goz:.2f}  bakis: {merkez:.2f}"
                if ifade is None:
                    satir3 = "KALIBRASYON: notr yuzle bak"
                else:
                    satir3 = (f"uzgun: {ifade['sad']:.2f}  sinirli: {ifade['angry']:.2f}  "
                              f"saskin: {ifade['surprised']:.2f}")
                renk = (0, 255, 255)
            else:
                satir1, satir2, satir3, renk = "yuz yok", "", "", (0, 0, 255)
            cv2.putText(ekran, satir1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir3, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, debug, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, renk, 1)
            cv2.imshow("PET ROBOT CAM", ekran)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            if tus == ord("c"):
                kal.sifirla()                   # yeniden kalibre et

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
