"""CV olayları (Sözleşme A2): user_arrived, user_left, smile, yawn, drowsy, looking_at_robot_long
+ duygu ifadeleri: sad, angry, surprised (bunlar sözleşmede YOK, takımla eklenmeli)
+ A1 yüz takip akışı (face_track), --track ile.

Kurulum:
    pip install mediapipe opencv-python

Çalıştırma:
    python faz1_olaylar.py            # sadece A2 olayları
    python faz1_olaylar.py --track    # A2 olayları + A1 face_track akışı (~15 mesaj/sn)

Başlangıçta yüzün ilk görününce 2 sn "kalibrasyon" yapılır: nötr (ifadesiz) yüzle kameraya bak.
Duygu skorları bu nötr yüze göre hesaplanır.

Tuşlar:
    c        yeniden kalibre et (kayıtlı ifade şablonlarını da siler)
    s/a/u    üzgün / sinirli / şaşkın ifade ŞABLONU kaydet: tuşa bas, 2 sn o ifadeyi yap ve tut.
             Şablon varsa o duygu, kuralla değil senin kendi yüz ifadene benzerlikle ölçülür.
             Şablonlar sadece bellekte tutulur, program kapanınca silinir.
    q / ESC  çıkış

Süreli olaylar (smile, yawn, drowsy, bakış, duygular) ifade bitince değil, süre şartı dolar
dolmaz ifade hâlâ sürerken, tek kez gönderilir.

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

# AC/KAPAT ham blendshape skoruna göredir. REF: "tam ifade" sayılan ham skor; confidence =
# ham skor / REF. Olayın gönderilebilmesi için confidence >= 0.6 gerekir, yani AC >= 0.6 * REF
# olmalı (aksi halde olay başlar ama hiç gönderilmez).
SMILE_AC, SMILE_KAPAT, SMILE_MIN_SN, SMILE_REF = 0.3, 0.2, 0.1, 0.5   # gülümseme anında gider
YAWN_AC, YAWN_KAPAT, YAWN_MIN_SN, YAWN_REF = 0.4, 0.25, 1.5, 0.65

# drowsy: gözler kısık/kapalı kalma skoru (eyeBlink ortalaması), en az 2 sn sürmeli
# (normal göz kırpma çok kısa sürdüğü için süre şartı onu eler)
DROWSY_AC, DROWSY_KAPAT, DROWSY_MIN_SN, DROWSY_REF = 0.35, 0.25, 2.0, 0.55

# looking_at_robot_long: baş yönü ve bakış kameraya ne kadar yakın (0–1 "merkezlik" skoru)
LOOK_AC, LOOK_KAPAT, LOOK_MIN_SN = 0.2, 0.01, 3.0   # sözleşme: 3 sn'den uzun
YAW_MAX = 30.0     # derece: kafa sağa/sola bu kadar dönünce "bakmıyor"
PITCH_MAX = 30.0   # derece: kafa yukarı/aşağı bu kadar dönünce "bakmıyor"
GAZ_MAX = 0.5      # göz bebeği yönü blendshape'lerinin (0–1) kabul edilen en büyük değeri

GOZ_BAKIS = [
    "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeLookDownLeft",
    "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeLookDownRight",
]

# duygu ifadeleri: nötr yüze göre ham skor, "tam ifade" referansına bölünüp 0–1'e çekilir.
# REF küçüldükçe daha hafif ifadeler de tam sayılır. Hepsi ilk tahmin.
SAD_REF, ANGRY_REF, SURPRISED_REF = 0.2, 0.3, 0.3
EMO_AC, EMO_KAPAT, EMO_MIN_SN = 0.6, 0.4, 0.4

# Şaşkınlık skoru (0–1) bunun üstündeyse ağız açıklığı "esneme" değil "şaşkınlık" sayılır.
YAWN_AYRIM = 0.5

# Kayıtlı ifade şablonu: kaç sn kayıt, şablona en az ne kadar benzemeli (kosinüs benzerliği)
SABLON_SN = 2.0
SABLON_COS_MIN = 0.4
SABLON_TUSLARI = {ord("s"): "sad", ord("a"): "angry", ord("u"): "surprised"}

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
    """Bir skor eşiği aşılınca başlar, düşünce biter. Olayı İFADE SÜRERKEN, TEK KEZ gönderir.

    Gönderme anı: ifade en az min_sure sn sürmüş VE güven (zirve skor / guven_ref, en fazla 1)
    en az MIN_CONFIDENCE olmalı. İkisi de sağlanır sağlanmaz olay gider; ifadenin bitmesi
    beklenmez. guven_ref küçüldükçe hafif ifadeler de yüksek güven alır.
    duration_s, o ana kadar geçen süredir (smile için ~0, yawn/drowsy/bakış için min_sure civarı);
    ifadenin toplam süresi bilinmez. Aynı ifade devam ettiği sürece tekrar gönderilmez.

    Histerezis (ac > kapat) skor eşik civarında titrerken olayın parçalanmasını önler.
    """

    def __init__(self, ad, ac, kapat, min_sure, guven_ref=1.0):
        self.ad, self.ac, self.kapat, self.min_sure = ad, ac, kapat, min_sure
        self.guven_ref = guven_ref
        self.aktif = False
        self.gonderildi = False
        self.baslangic = 0.0
        self.zirve = 0.0

    def guncelle(self, skor, simdi):
        """skor None ise (yüz yok) açık olay kapatılır."""
        if skor is None:
            self.bitir()
            return
        if not self.aktif:
            if skor >= self.ac:
                self.aktif = True
                self.gonderildi = False
                self.baslangic = simdi
                self.zirve = skor
        else:
            self.zirve = max(self.zirve, skor)
            if skor < self.kapat:
                self.bitir()
                return
        self._gonder_dene(simdi)

    def _gonder_dene(self, simdi):
        if not self.aktif or self.gonderildi:
            return
        sure = simdi - self.baslangic
        guven = min(1.0, self.zirve / self.guven_ref)
        if sure >= self.min_sure and guven >= MIN_CONFIDENCE:
            self.gonderildi = True
            olay_gonder(self.ad, self.baslangic, guven, sure)

    def bitir(self):
        self.aktif = False
        self.gonderildi = False


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


def sablon_skoru(b, sablon):
    """b'nin kayıtlı ifade şablonuna benzerliği (0–1).

    Önce yön benzerliğine (kosinüs) bakar: ifade şablonla aynı kas desenine sahip değilse 0.
    Sonra şablonun üzerindeki izdüşümü alır: şablon kadar güçlü ifade = 1.0, yarısı kadar = 0.5.
    """
    dot = sum(b.get(k, 0.0) * v for k, v in sablon.items())
    nn = sum(v * v for v in sablon.values())
    bb = sum(v * v for v in b.values())
    if nn == 0 or bb == 0:
        return 0.0
    if dot / math.sqrt(nn * bb) < SABLON_COS_MIN:
        return 0.0
    return max(0.0, min(1.0, dot / nn))


def ifade_skorlari(b, gulme, cene, sablonlar):
    """Nötr yüze göre düzeltilmiş blendshape'lerden sad / angry / surprised / yawn skorları (0–1).

    b: kalibrasyon farkı uygulanmış blendshape sözlüğü
    gulme, cene: ham gülümseme ve çene açıklığı skorları
    sablonlar: {"sad": {...}, ...} kullanıcının kaydettiği ifade şablonları (boş olabilir)

    Bir duygunun şablonu varsa o duygu şablonla, yoksa kuralla hesaplanır.
    Esneme ile şaşkınlığı ayıran şey ağız değil gözler ve kaşlar: şaşkınlıkta gözler
    iri açılır ve kaşlar kalkar, esnemede gözler kısılır. Bu yüzden şaşkınlık skoru
    yüksekse ağız açıklığı esneme sayılmaz; gözler kısıksa şaşkınlık skoru düşer.
    Mutlu ifadesi zaten `smile` olayı.
    """
    goz_acik = _ort(b, "eyeWideLeft", "eyeWideRight")
    kas_yukari = _ort(b, "browInnerUp", "browOuterUpLeft", "browOuterUpRight")
    goz_kisik = max(_ort(b, "eyeSquintLeft", "eyeSquintRight"),
                    _ort(b, "eyeBlinkLeft", "eyeBlinkRight"))

    agiz_asagi = _ort(b, "mouthFrownLeft", "mouthFrownRight")
    ic_kas = b.get("browInnerUp", 0.0)
    alt_dudak = b.get("mouthShrugLower", 0.0)
    uzgun = 0.4 * agiz_asagi + 0.35 * ic_kas + 0.25 * alt_dudak
    sinirli = (
        0.6 * _ort(b, "browDownLeft", "browDownRight")
        + 0.2 * _ort(b, "noseSneerLeft", "noseSneerRight")
        + 0.2 * _ort(b, "eyeSquintLeft", "eyeSquintRight")
    )
    saskin = max(0.0, 0.6 * goz_acik + 0.4 * kas_yukari - 0.5 * goz_kisik)

    skorlar = {
        "sad": min(1.0, uzgun / SAD_REF),
        "angry": min(1.0, sinirli / ANGRY_REF),
        "surprised": min(1.0, saskin / SURPRISED_REF),
    }
    for ad, sablon in sablonlar.items():
        skorlar[ad] = sablon_skoru(b, sablon)

    saskin_norm = skorlar["surprised"]
    if gulme >= SMILE_KAPAT:
        skorlar["sad"] = skorlar["angry"] = 0.0
    if "sad" not in sablonlar and (cene >= 0.4 or saskin_norm >= YAWN_AYRIM):
        skorlar["sad"] = 0.0   # kural: ağız açıkken ya da gözler iriyken üzgün sayılmaz

    baskin = max(skorlar, key=skorlar.get)
    skorlar = {ad: (v if ad == baskin else 0.0) for ad, v in skorlar.items()}
    skorlar["yawn"] = 0.0 if saskin_norm >= YAWN_AYRIM else cene

    debug = (
        f"uzgun_ham {uzgun:.2f}  agiz asagi {agiz_asagi:.2f}  ic kas {ic_kas:.2f}  "
        f"alt dudak {alt_dudak:.2f}",
        f"goz acik {goz_acik:.2f}  kas yukari {kas_yukari:.2f}  kisik {goz_kisik:.2f}",
    )
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

    smile = SureliOlay("smile", SMILE_AC, SMILE_KAPAT, SMILE_MIN_SN, SMILE_REF)
    yawn = SureliOlay("yawn", YAWN_AC, YAWN_KAPAT, YAWN_MIN_SN, YAWN_REF)
    drowsy = SureliOlay("drowsy", DROWSY_AC, DROWSY_KAPAT, DROWSY_MIN_SN, DROWSY_REF)
    bakis = SureliOlay("looking_at_robot_long", LOOK_AC, LOOK_KAPAT, LOOK_MIN_SN)
    sad = SureliOlay("sad", EMO_AC, EMO_KAPAT, EMO_MIN_SN)
    angry = SureliOlay("angry", EMO_AC, EMO_KAPAT, EMO_MIN_SN)
    surprised = SureliOlay("surprised", EMO_AC, EMO_KAPAT, EMO_MIN_SN)

    kal = Kalibrasyon(KALIB_SN)
    sablonlar = {}          # kullanıcının kaydettiği ifade şablonları (sadece bellekte)
    kayit_ad = None         # şu an hangi ifade kaydediliyor (None = kayıt yok)
    kayit_bitis = 0.0
    kayit_toplam = {}
    kayit_sayi = 0
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
            debug = ("", "")

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
                elif kayit_ad is not None:
                    # şablon kaydı: nötr yüze göre farkın ortalamasını topla
                    for k, v in kal.uygula(b).items():
                        kayit_toplam[k] = kayit_toplam.get(k, 0.0) + v
                    kayit_sayi += 1
                    if simdi >= kayit_bitis:
                        ort = {k: v / kayit_sayi for k, v in kayit_toplam.items()
                               if not k.startswith("_") and v / kayit_sayi > 0.05}
                        sablonlar[kayit_ad] = ort
                        print(f"Sablon kaydedildi: {kayit_ad} ({len(ort)} ozellik)",
                              file=sys.stderr)
                        kayit_ad = None
                else:
                    ifade, debug = ifade_skorlari(kal.uygula(b), gulme, cene, sablonlar)
            else:
                gorunme_basi = None
                kayit_ad = None                 # yüz kaybolursa şablon kaydı iptal
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
                if ifade is not None:
                    satir3 = (f"uzgun: {ifade['sad']:.2f}  sinirli: {ifade['angry']:.2f}  "
                              f"saskin: {ifade['surprised']:.2f}")
                elif kayit_ad is not None:
                    satir3 = f"KAYIT ({kayit_ad}): ifadeyi yap ve tut"
                elif not kal.bitti:
                    satir3 = "KALIBRASYON: notr yuzle bak"
                else:
                    satir3 = ""   # kalibrasyon ya da şablon kaydının bittiği kare
                renk = (0, 255, 255)
            else:
                satir1, satir2, satir3, renk = "yuz yok", "", "", (0, 0, 255)
            cv2.putText(ekran, satir1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir3, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, debug[0], (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 1)
            cv2.putText(ekran, debug[1], (10, 142), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 1)
            yardim = ("[s] uzgun [a] sinirli [u] saskin kaydet  [c] kalibre   sablon: "
                      + (" ".join(sorted(sablonlar)) or "yok"))
            cv2.putText(ekran, yardim, (10, ekran.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow("CV olaylari", ekran)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            if tus == ord("c"):
                kal.sifirla()                   # yeniden kalibre et
                sablonlar.clear()               # taban değişti, eski şablonlar geçersiz
                kayit_ad = None
            elif tus in SABLON_TUSLARI and kal.bitti and yuz_var:
                kayit_ad = SABLON_TUSLARI[tus]
                kayit_bitis = simdi + SABLON_SN
                kayit_toplam = {}
                kayit_sayi = 0

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
