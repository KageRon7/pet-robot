"""CV olayları (Sözleşme A2) + A1 yüz takip akışı (face_track).

Faz 1 olayları: user_arrived, user_left, smile, yawn, drowsy, looking_at_robot_long, sad, angry, surprised
Faz 2 (YENİ) olayları:
    hand_near              el kameraya yaklaştı
    face_covered           el yüzü kapattı
    face_uncovered         el çekildi, yüz geri geldi (duration_s = kaç sn kapalı kaldı)
    head_down_long         baş uzun süre öne eğik (telefona bakıyor)
    room_dark              oda birden karardı
    room_bright            oda birden aydınlandı
    second_face_appeared   görüntüde ikinci bir yüz var
    second_face_gone       ikinci yüz gitti
    hand_wave              el sallama (selam)
    thumbs_up              baş parmak yukarı (okey)
    middle_finger          orta parmak çekme
    stop                   dik açık avuç, kıpırdamadan (dur işareti)
    shush                  işaret parmağı ağzın önünde (şşş)
    salute                 el alında, yatay (selam verme)
    answer_yes             kafa sallama, evet (yukarı-aşağı)
    answer_no              kafa sallama, hayır (sağa-sola)
    object_appeared        listedeki bir nesne görüntüye girdi   (olayda ekstra "label" alanı)
    object_gone            o nesne görüntüden çıktı              (label)
    object_shown           nesne elle kameraya doğru tutuluyor   (label)
A1 face_track mesajına YENİ alanlar: head_dir (left/right/up/down/center), head_yaw, head_pitch.

Kurulum:
    pip install mediapipe opencv-python

Çalıştırma:
    python faz2_olaylar.py            # sadece A2 olayları
    python faz2_olaylar.py --track    # A2 olayları + A1 face_track akışı (~15 mesaj/sn)

Başlangıçta yüz ilk görününce 2 sn "kalibrasyon" yapılır: nötr (ifadesiz), kameraya/kediye normal
bakan yüzle dur. Duygu skorları ve baş açıları bu nötr duruşa göre hesaplanır.

Tuşlar:
    c        yeniden kalibre et (kayıtlı ifade şablonlarını da siler)
    s/a/u    üzgün / sinirli / şaşkın ifade ŞABLONU kaydet: tuşa bas, 2 sn o ifadeyi yap ve tut.
    q / ESC  çıkış

Süreli olaylar, süre şartı dolar dolmaz ifade hâlâ sürerken, tek kez gönderilir.

Olaylar konsola (stdout) tek satır JSON olarak düşer:
    {"type": "event", "t": 1728648003.5, "event": "smile", "confidence": 0.87, "duration_s": 2.1}
    {"type": "face_track", "t": ..., "present": true, "x": 0.5, "y": 0.4,
     "looking_at_robot": true, "head_yaw": -12.4, "head_pitch": 3.1}

BAŞ YÖNÜ KURALI: KULLANICININ KENDİ YÖNÜ (pencerede aynalı görüntüde ne görüyorsan o):
    head_dir   "right" = kullanıcı kendi SAĞINA döndü, "left" = kendi soluna,
               "up" / "down" = yukarı / aşağı, "center" = nötr. Yüz yoksa null.
    head_yaw   > 0 sağa, < 0 sola (derece)      head_pitch > 0 yukarı, < 0 aşağı (derece)
    0 = kalibrasyondaki nötr duruş. Yüz yoksa ya da el yüzü kapatıyorsa null.
NOT: x/y hâlâ kameranın gördüğü aynalanmamış görüntüye göre (sözleşme). Baş yönü ise
kullanıcının perspektifinde. İşaretler gerçek yüzle test edilmeli; ters çıkarsa
YAW_ISARET / PITCH_ISARET'i çevir.

Gizlilik: kare diske yazılmaz, başka modüle gitmez. Dışarı sadece olay JSON'ları ve sayısal
face_track değerleri çıkar. Işık için sadece tek bir parlaklık sayısı hesaplanır.
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
EL_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)
OBJ_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/object_detector/"
    "efficientdet_lite0/float16/1/efficientdet_lite0.tflite"
)
OBJ_MODEL_PATH = "efficientdet_lite0.tflite"
EL_MODEL_PATH = "gesture_recognizer.task"   # el landmark'ları + hazır hareketler (Thumb_Up, Open_Palm...)

# ---- Eşikler (hepsi ilk tahmin, kendi yüzünde test edip ayarla) ----
ARRIVED_SN = 2.0          # sözleşme: yüz en az 2 sn görünsün
LEFT_SN = 10.0            # sözleşme: yüz en az 10 sn yok
MIN_CONFIDENCE = 0.6      # sözleşme: bunun altı gönderilmez

# AC/KAPAT ham skora göredir. REF: "tam ifade" sayılan ham skor; confidence = ham skor / REF.
# Olayın gönderilebilmesi için confidence >= 0.6 gerekir, yani AC >= 0.6 * REF olmalı.
SMILE_AC, SMILE_KAPAT, SMILE_MIN_SN, SMILE_REF = 0.3, 0.2, 0.1, 0.5
YAWN_AC, YAWN_KAPAT, YAWN_MIN_SN, YAWN_REF = 0.4, 0.25, 1.5, 0.65
DROWSY_AC, DROWSY_KAPAT, DROWSY_MIN_SN, DROWSY_REF = 0.35, 0.25, 2.0, 0.55

LOOK_AC, LOOK_KAPAT, LOOK_MIN_SN = 0.2, 0.01, 3.0   # sözleşme: 3 sn'den uzun
YAW_MAX = 30.0
PITCH_MAX = 30.0
GAZ_MAX = 0.5

GOZ_BAKIS = [
    "eyeLookInLeft", "eyeLookOutLeft", "eyeLookUpLeft", "eyeLookDownLeft",
    "eyeLookInRight", "eyeLookOutRight", "eyeLookUpRight", "eyeLookDownRight",
]

SAD_REF, ANGRY_REF, SURPRISED_REF = 0.2, 0.3, 0.3
EMO_AC, EMO_KAPAT, EMO_MIN_SN = 0.6, 0.4, 0.4
YAWN_AYRIM = 0.5

SABLON_SN = 2.0
SABLON_COS_MIN = 0.4
SABLON_TUSLARI = {ord("s"): "sad", ord("a"): "angry", ord("u"): "surprised"}

KALIB_SN = 2.0
# Yüz kısa süre kaybolunca (el kapatınca) kalibrasyon bozulmasın: ancak bu kadar sn yüz yoksa sıfırla.
KALIB_SIFIRLA_SN = 5.0

TRACK_HZ = 15

# ---- Faz 2 eşikleri ----

# hand_near: el boyutu = (bilek → orta parmak kökü mesafesi) / kare yüksekliği.
# Kol boyu uzaklıkta ~0.15, yüze yakın ~0.3+. AC >= 0.6 * REF olmalı.
HAND_AC, HAND_KAPAT, HAND_MIN_SN, HAND_REF = 0.25, 0.18, 0.3, 0.35

# face_covered: elin sınır kutusu, yüz kutusunun ne kadarını örtüyor (0–1).
COVER_AC, COVER_KAPAT, COVER_MIN_SN, COVER_REF = 0.5, 0.25, 0.3, 0.8
ACILMA_BEKLE_SN = 8.0     # el çekildikten sonra yüz bu kadar sn içinde geri gelmezse face_uncovered iptal
REF_GECERLI_SN = 4.0      # yüz kayboldu: son yüz kutusu bu kadar sn boyunca "yüz yeri" sayılır
REF_KAPALI_SN = 10.0      # yüz örtülüyken kutu daha uzun süre geçerli (uzun ce-ee bozulmasın)
EL_KAYBOLMA_TUT_SN = 0.6  # el yüze yaklaşırken yüz kayboldu ve el görünmüyorsa örtme sürüyor say

# head_down_long: nötr duruşa göre aşağı eğim (derece). AC >= 0.6 * REF olmalı.
HEAD_DOWN_AC, HEAD_DOWN_KAPAT, HEAD_DOWN_MIN_SN, HEAD_DOWN_REF = 20.0, 12.0, 5.0, 30.0
ASAGI_TOLERANS_SN = 1.0   # çok eğilince yüz 1 sn kadar kaybolabilir, olay bozulmasın

# Baş yönü akışı
YAW_ISARET = -1           # + = kullanıcının kendi sağı. Test et, ters çıkarsa 1 yap
PITCH_ISARET = 1          # test et, ters çıkarsa -1
POSE_OLU_BOLGE = 8.0      # derece: bunun altı 0 sayılır (titreme olmasın)
POSE_ALFA = 0.4           # yumuşatma (0–1, küçüldükçe daha yumuşak)
DIR_AC = 15.0             # derece: bu kadar dönünce yön etiketi (left/right/up/down) başlar
DIR_KAPAT = 9.0           # derece: bunun altına inince tekrar center (titreme olmasın)

# Oda ışığı: parlaklık 0–1. hızlı ortalama / yavaş taban oranı eşikleri.
ISIK_HIZLI_SN = 0.3
ISIK_YAVAS_SN = 5.0
ISIK_KARARDI_ORAN = 0.55      # hızlı <= yavaş * 0.55 → room_dark
ISIK_AYDINLANDI_ORAN = 1.8    # hızlı >= yavaş * 1.8 → room_bright
ISIK_ISINMA_SN = 5.0          # program başlarken taban oturana kadar olay yok
ISIK_BEKLEME_SN = 3.0         # iki ışık olayı arası en az bu kadar
EL_YAKIN_BEKLE_SN = 1.5       # el kamerayı kapatınca "karardı" sayma

# İkinci yüz: yüz kutusu alanı (kare alanına oranı) en az bu kadar olmalı (uzaktaki/poster elenir)
IKINCI_MIN_ALAN = 0.01
IKINCI_GELDI_SN = 1.5
IKINCI_GITTI_SN = 3.0

# thumbs_up: GestureRecognizer "Thumb_Up" skoru (0–1)
THUMB_AC, THUMB_KAPAT, THUMB_MIN_SN = 0.6, 0.4, 0.5

# middle_finger: orta parmak uzanık, işaret/yüzük/serçe kıvrık (landmark geometrisi, hazır hareket yok)
ORTA_AC, ORTA_KAPAT, ORTA_MIN_SN = 0.6, 0.4, 0.5
ORTA_UZANMA = 1.15        # orta parmak ucu, PIP'e göre bilekten en az bu kadar uzakta olmalı
ORTA_FARK = 1.25          # orta parmak ucu, diğer parmak uçlarının en uzağından en az bu kadar uzak

# stop: dik duran açık avuç, kıpırdamadan (sallama değil). Avuç merkezi pencerede en fazla bu kadar oynar.
STOP_AC, STOP_KAPAT, STOP_MIN_SN = 0.6, 0.4, 0.4
STOP_PENCERE_SN = 0.6
STOP_HAREKET_MAX = 0.25   # el boyu biriminde

# shush (şşş): işaret parmağı uzanık, diğerleri kıvrık, parmak ucu ağza yakın
SUS_AC, SUS_KAPAT, SUS_MIN_SN = 0.6, 0.4, 0.5
SUS_MESAFE = 0.25         # parmak ucu - ağız mesafesi, yüz yüksekliğinin katı olarak en fazla

# salute (selam verme): yatay duran açık el, parmak ucu alın/şakak bölgesinde
SELAM_AC, SELAM_KAPAT, SELAM_MIN_SN = 0.6, 0.4, 0.6
SELAM_X_PAY = 0.4         # yüz kutusunun yanlarına bu oranda pay
SELAM_Y_YUKARI = 0.3      # yüz kutusunun üstünden bu kadar yukarı (yüz yüksekliği katı)
SELAM_Y_ASAGI = 0.4       # yüz kutusunun üstünden bu kadar aşağı (alın + kaş hizası)

# hand_wave: açık avuç merkezinin yatay salınımı (el boyu biriminde)
WAVE_PENCERE_SN = 1.5
WAVE_GENLIK = 0.4         # bir salınımın en az büyüklüğü (el boyunun katı)
WAVE_DONUS = 3            # pencerede en az bu kadar yön değişimi
WAVE_BEKLEME_SN = 2.0

# answer_yes / answer_no: baş açısının salınımı (derece)
SALLAMA_PENCERE_SN = 2.0
NOD_GENLIK = 5.0          # yukarı-aşağı salınım en az bu kadar derece
SHAKE_GENLIK = 7.0        # sağa-sola salınım en az bu kadar derece
SALLAMA_DONUS = 3         # pencerede en az bu kadar yön değişimi
SALLAMA_BEKLEME_SN = 2.0

# Nesne algılama (COCO sınıfları). Sadece bu listedekiler olay üretir.
OBJ_LISTE = {
    "cup", "bottle", "cell phone", "sports ball", "teddy bear", "bear", "laptop", "book",
    "remote", "game controller", "scissors", "backpack", "umbrella", "apple", "banana",
    "orange", "bowl",
}
# COCO'da oyun kolu sınıfı yok: telefon, oyun kolu ve kumanda hep "remote"/"cell phone" çıkıyor.
# "remote" diyen tespiti kutunun en/boy oranına göre ayırıyoruz (uzun kenar / kısa kenar):
#   >= OBJ_KUMANDA_ORAN  ince uzun  -> remote (TV kumandası)
#   >= OBJ_TELEFON_ORAN  orta       -> cell phone
#   daha küçük           kısa kalın -> game controller
# Ham oranı test penceresinde panelde gösteriyoruz, kendi nesnelerine göre ayarla.
OBJ_KUMANDA_ORAN = 3.0
OBJ_TELEFON_ORAN = 1.8


def obj_etiket(ad, bb):
    """Dedektörün etiketini düzeltir. Sadece 'remote' için kutu oranına bakar. (etiket, oran)."""
    if ad != "remote":
        return ad, None
    kisa, uzun = min(bb.width, bb.height), max(bb.width, bb.height)
    if kisa <= 0:
        return ad, None
    oran = uzun / kisa
    if oran >= OBJ_KUMANDA_ORAN:
        return "remote", oran
    if oran >= OBJ_TELEFON_ORAN:
        return "cell phone", oran
    return "game controller", oran
OBJ_SKOR_ESIK = 0.4       # dedektörün kendi alt skoru; olay için ayrıca confidence >= 0.6 gerekir
OBJ_HER_N_KARE = 3        # dedektör her N karede bir çalışır (FPS için), ~10 Hz
OBJ_GELDI_SN = 1.0        # nesne bu kadar sn kararlı görünürse object_appeared
OBJ_GITTI_SN = 3.0        # bu kadar sn görünmezse object_gone
OBJ_BOSLUK_SN = 0.5       # bu kadar kısa kayıplar "kesintisiz" sayılır
OBJ_SHOWN_EL = 0.2        # object_shown: el boyutu (hand_near'a yakın) en az bu kadar
OBJ_SHOWN_ORTUSME = 0.4   # object_shown: nesne kutusunun en az bu kadarı elin kutusunda
OBJ_SHOWN_SN = 0.5        # object_shown: bu kadar sn tutulmalı
OBJ_KUTU_CIZ = True       # test penceresinde nesne kutularını videonun üstüne de çiz (False = sadece sağ panel)

# El/nesne yüzün yakınındayken (telefonu sallamak gibi) yüz takibi bozulur ve sahte baş sallama
# çıkar. Bu sırada answer_yes / answer_no üretilmez.
SALLAMA_ENGEL_ORTUSME = 0.2   # el/nesne kutusunun en az bu kadarı genişletilmiş yüz bölgesine giriyorsa engelle
SALLAMA_ENGEL_GENISLET = 0.3  # yüz kutusu her yöne bu oranda genişletilir
SALLAMA_ENGEL_SN = 0.7        # engel kalkınca bu kadar sn daha bekle


def indir(url, yol):
    if not os.path.exists(yol):
        print(f"Model indiriliyor (tek seferlik): {yol}", file=sys.stderr)
        urllib.request.urlretrieve(url, yol)
        print("Tamam:", yol, file=sys.stderr)


# Test penceresinde göstermek için son gönderilen olaylar.
SON_OLAY = ["", -1e9]         # nesne dışı olaylar (sol alt, küçük yazı)
SON_NESNE_OLAY = ["", -1e9]   # object_* olayları (sağ panelde, nesne listesinin altında)


def olay_gonder(event, t, confidence, duration_s, label=None):
    """A2 mesajını üretir. Şimdilik konsola yazar; sonra router'a gönderme buraya gelecek."""
    if confidence < MIN_CONFIDENCE:
        return
    if event.startswith("object_"):
        SON_NESNE_OLAY[0], SON_NESNE_OLAY[1] = f"{event} ({label})", time.time()
    else:
        SON_OLAY[0], SON_OLAY[1] = event, time.time()
    mesaj = {
        "type": "event",
        "t": round(t, 2),
        "event": event,
        "confidence": round(min(confidence, 1.0), 2),
        "duration_s": round(duration_s, 2),
    }
    if label is not None:
        mesaj["label"] = label
    print(json.dumps(mesaj), flush=True)


class SureliOlay:
    """Bir skor eşiği aşılınca başlar, düşünce biter. Olayı İFADE SÜRERKEN, TEK KEZ gönderir.

    Gönderme anı: ifade en az min_sure sn sürmüş VE güven (zirve skor / guven_ref, en fazla 1)
    en az MIN_CONFIDENCE olmalı. İkisi de sağlanır sağlanmaz olay gider.
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


class YuzKapanma:
    """face_covered / face_uncovered çifti (ce-ee oyunu).

    Girdi: elin yüzü örtme oranı (0–1). Oran COVER_AC üstünde COVER_MIN_SN sürerse face_covered
    gider. El çekilip yüz geri gelince face_uncovered gider (duration_s = kapalı kalma süresi).
    El çekildi ama yüz ACILMA_BEKLE_SN içinde dönmediyse (kullanıcı gitti) uncovered gönderilmez.
    """

    def __init__(self):
        self.kapali = False         # face_covered gönderildi, face_uncovered henüz değil
        self.aday_basi = None       # örtme başladığı an (henüz gönderilmemiş olabilir)
        self.kapali_basi = 0.0
        self.zirve = 0.0
        self.el_yok_basi = None

    @property
    def el_yuzde(self):
        return self.kapali or self.aday_basi is not None

    def guncelle(self, ort, yuz_var, simdi):
        if ort >= COVER_AC:
            self.el_yok_basi = None
            if self.aday_basi is None:
                self.aday_basi = simdi
                self.zirve = ort
            self.zirve = max(self.zirve, ort)
            if not self.kapali and simdi - self.aday_basi >= COVER_MIN_SN:
                guven = min(1.0, self.zirve / COVER_REF)
                if guven >= MIN_CONFIDENCE:
                    self.kapali = True
                    self.kapali_basi = self.aday_basi
                    olay_gonder("face_covered", self.aday_basi, guven, simdi - self.aday_basi)
        elif ort < COVER_KAPAT:
            self.aday_basi = None
            if self.kapali:
                if self.el_yok_basi is None:
                    self.el_yok_basi = simdi
                if yuz_var:
                    olay_gonder("face_uncovered", simdi, 1.0, simdi - self.kapali_basi)
                    self.kapali = False
                    self.el_yok_basi = None
                elif simdi - self.el_yok_basi > ACILMA_BEKLE_SN:
                    self.kapali = False
                    self.el_yok_basi = None


def zigzag_say(degerler, genlik):
    """Seride en az `genlik` büyüklüğünde kaç kez yön değişimi olduğunu sayar."""
    if len(degerler) < 2:
        return 0
    yon, uc, donus = 0, degerler[0], 0
    for x in degerler[1:]:
        if yon == 0:
            if x - uc >= genlik:
                yon, uc = 1, x
            elif uc - x >= genlik:
                yon, uc = -1, x
        elif yon == 1:
            if x > uc:
                uc = x
            elif uc - x >= genlik:
                yon, uc, donus = -1, x, donus + 1
        else:
            if x < uc:
                uc = x
            elif x - uc >= genlik:
                yon, uc, donus = 1, x, donus + 1
    return donus


def avuc_acik(el, ad, skor, gen, yuk):
    """Avuç açık mı: GestureRecognizer Open_Palm diyorsa ya da 4 parmak da uzanmışsa."""
    if ad == "Open_Palm" and skor >= 0.5:
        return True

    def mesafe(i):
        return math.hypot((el[i].x - el[0].x) * gen, (el[i].y - el[0].y) * yuk)
    uzanan = sum(1 for uc, pip in ((8, 6), (12, 10), (16, 14), (20, 18))
                 if mesafe(uc) > 1.15 * mesafe(pip))
    return uzanan >= 4


def orta_parmak(el, gen, yuk):
    """Orta parmak çekme: orta parmak uzanık, işaret/yüzük/serçe kıvrık (baş parmak serbest).

    Skor 1.0 (jest var) ya da 0.0. Mesafeler bilek (0) noktasından ölçülür.
    """
    def mesafe(i):
        return math.hypot((el[i].x - el[0].x) * gen, (el[i].y - el[0].y) * yuk)
    if mesafe(12) <= ORTA_UZANMA * mesafe(10):
        return 0.0
    for uc, pip in ((8, 6), (16, 14), (20, 18)):
        if mesafe(uc) >= mesafe(pip):           # kıvrık parmak: ucu PIP'ten uzakta olmaz
            return 0.0
    if mesafe(12) < ORTA_FARK * max(mesafe(8), mesafe(16), mesafe(20)):
        return 0.0
    return 1.0


def sus_isareti(el, yuz, yuz_kutusu, gen, yuk):
    """Şşş: işaret parmağı uzanık, orta/yüzük/serçe kıvrık, parmak ucu ağzın yanında."""
    def mesafe(i):
        return math.hypot((el[i].x - el[0].x) * gen, (el[i].y - el[0].y) * yuk)
    if mesafe(8) <= 1.15 * mesafe(6):
        return False
    for uc, pip in ((12, 10), (16, 14), (20, 18)):
        if mesafe(uc) >= mesafe(pip):
            return False
    agiz_x = (yuz[13].x + yuz[14].x) / 2
    agiz_y = (yuz[13].y + yuz[14].y) / 2
    yuz_yuk_px = (yuz_kutusu[3] - yuz_kutusu[1]) * yuk
    if yuz_yuk_px <= 0:
        return False
    d = math.hypot((el[8].x - agiz_x) * gen, (el[8].y - agiz_y) * yuk)
    return d / yuz_yuk_px <= SUS_MESAFE


def selam_konumu(uc, yuz_kutusu):
    """Parmak ucu (landmark) alın/şakak bölgesinde mi (selam verme konumu)."""
    w, h = yuz_kutusu[2] - yuz_kutusu[0], yuz_kutusu[3] - yuz_kutusu[1]
    return (yuz_kutusu[0] - SELAM_X_PAY * w <= uc.x <= yuz_kutusu[2] + SELAM_X_PAY * w
            and yuz_kutusu[1] - SELAM_Y_YUKARI * h <= uc.y <= yuz_kutusu[1] + SELAM_Y_ASAGI * h)


class ElDurgun:
    """stop: avuç merkezi son STOP_PENCERE_SN boyunca neredeyse sabit mi."""

    def __init__(self):
        self.ornekler = []
        self.son_gorulme = 0.0

    def guncelle(self, x, y, simdi):
        if x is None:
            if simdi - self.son_gorulme > 0.3:
                self.ornekler.clear()
            return False
        self.son_gorulme = simdi
        self.ornekler.append((simdi, x, y))
        while simdi - self.ornekler[0][0] > STOP_PENCERE_SN:
            self.ornekler.pop(0)
        if simdi - self.ornekler[0][0] < 0.8 * STOP_PENCERE_SN:
            return False
        xs = [o[1] for o in self.ornekler]
        ys = [o[2] for o in self.ornekler]
        return (max(xs) - min(xs) <= STOP_HAREKET_MAX
                and max(ys) - min(ys) <= STOP_HAREKET_MAX)


class ElSallama:
    """hand_wave: açık avucun yatay salınımı. Tek kez gönderilir, sonra WAVE_BEKLEME_SN bekler."""

    def __init__(self):
        self.ornekler = []
        self.bekleme_bitis = 0.0
        self.son_gorulme = 0.0

    def guncelle(self, x, simdi):
        """x: avuç merkezinin yatay konumu (el boyu biriminde); açık avuç yoksa None."""
        if x is None:
            if simdi - self.son_gorulme > 0.3:
                self.ornekler.clear()
            return
        self.son_gorulme = simdi
        self.ornekler.append((simdi, x))
        while simdi - self.ornekler[0][0] > WAVE_PENCERE_SN:
            self.ornekler.pop(0)
        if simdi < self.bekleme_bitis:
            return
        donus = zigzag_say([o[1] for o in self.ornekler], WAVE_GENLIK)
        if donus >= WAVE_DONUS:
            ilk = self.ornekler[0][0]
            olay_gonder("hand_wave", ilk, min(1.0, 0.5 + 0.15 * donus), simdi - ilk)
            self.bekleme_bitis = simdi + WAVE_BEKLEME_SN
            self.ornekler.clear()


class BasSallama:
    """answer_yes (pitch salınımı) / answer_no (yaw salınımı).

    Ana eksen en az SALLAMA_DONUS kez yön değiştirmeli, diğer eksen ana eksenin yarısından
    az oynamalı (yoksa baş dönüyor/eğiliyordur, sallamıyordur).
    """

    def __init__(self, ad, genlik):
        self.ad, self.genlik = ad, genlik
        self.ornekler = []
        self.bekleme_bitis = 0.0

    def durdur(self, bekleme_bitis):
        self.ornekler.clear()
        self.bekleme_bitis = bekleme_bitis

    def guncelle(self, ana, diger, simdi):
        """Olay gönderirse True. Açılar nötr duruşa göre, yumuşatılmamış (derece)."""
        if ana is None or diger is None:
            self.ornekler.clear()
            return False
        self.ornekler.append((simdi, ana, diger))
        while simdi - self.ornekler[0][0] > SALLAMA_PENCERE_SN:
            self.ornekler.pop(0)
        if simdi < self.bekleme_bitis:
            return False
        anas = [o[1] for o in self.ornekler]
        digers = [o[2] for o in self.ornekler]
        donus = zigzag_say(anas, self.genlik)
        if donus < SALLAMA_DONUS:
            return False
        if (max(digers) - min(digers)) > 0.5 * (max(anas) - min(anas)):
            return False
        ilk = self.ornekler[0][0]
        olay_gonder(self.ad, ilk, min(1.0, 0.5 + 0.15 * donus), simdi - ilk)
        self.durdur(simdi + SALLAMA_BEKLEME_SN)
        return True


class ObjeTakip:
    """object_appeared / object_gone / object_shown (etiket başına ayrı durum).

    tespitler: {etiket: (skor, kutu)}, o dedektör geçişindeki en iyi tespit.
    object_shown: nesne kutusu elin kutusuyla örtüşüyor ve el yeterince yakın.
    """

    def __init__(self):
        self.d = {}

    def _durum(self, etiket):
        return self.d.setdefault(etiket, {
            "gorunme_basi": None, "son_gorulme": -1e9, "zirve": 0.0, "bildirildi": False,
            "tut_basi": None, "tut_son": -1e9, "tut_bildirildi": False,
        })

    def guncelle(self, tespitler, el_kutulari, el_boyut, simdi):
        for etiket in set(tespitler) | set(self.d):
            d = self._durum(etiket)
            t = tespitler.get(etiket)
            if t is not None:
                skor, kt = t
                d["son_gorulme"] = simdi
                if d["gorunme_basi"] is None:
                    d["gorunme_basi"] = simdi
                    d["zirve"] = skor
                d["zirve"] = max(d["zirve"], skor)
                if (not d["bildirildi"] and simdi - d["gorunme_basi"] >= OBJ_GELDI_SN
                        and d["zirve"] >= MIN_CONFIDENCE):
                    d["bildirildi"] = True
                    olay_gonder("object_appeared", d["gorunme_basi"], d["zirve"],
                                simdi - d["gorunme_basi"], etiket)
                tutuluyor = el_boyut >= OBJ_SHOWN_EL and any(
                    ortusme(ek, kt) >= OBJ_SHOWN_ORTUSME for ek in el_kutulari)
                if tutuluyor:
                    d["tut_son"] = simdi
                    if d["tut_basi"] is None:
                        d["tut_basi"] = simdi
                    if (not d["tut_bildirildi"] and simdi - d["tut_basi"] >= OBJ_SHOWN_SN
                            and skor >= MIN_CONFIDENCE):
                        d["tut_bildirildi"] = True
                        olay_gonder("object_shown", d["tut_basi"], skor,
                                    simdi - d["tut_basi"], etiket)
                elif simdi - d["tut_son"] > OBJ_BOSLUK_SN:
                    d["tut_basi"] = None
                    d["tut_bildirildi"] = False
            else:
                if simdi - d["son_gorulme"] > OBJ_BOSLUK_SN:
                    d["gorunme_basi"] = None
                    d["tut_basi"] = None
                    d["tut_bildirildi"] = False
                if d["bildirildi"] and simdi - d["son_gorulme"] >= OBJ_GITTI_SN:
                    d["bildirildi"] = False
                    olay_gonder("object_gone", d["son_gorulme"], 1.0,
                                simdi - d["son_gorulme"], etiket)


class BasYonu:
    """head_dir etiketi: center / left / right / up / down (kullanıcının kendi yönü).

    Açı DIR_AC'yi aşınca yön başlar, DIR_KAPAT'ın altına inince center olur (histerezis).
    Yaw ve pitch'ten hangisi daha büyükse o eksen seçilir.
    """

    def __init__(self):
        self.yon = "center"

    def guncelle(self, yaw, pitch):
        if yaw is None or pitch is None:
            self.yon = "center"
            return None
        deger = {"right": yaw, "left": -yaw, "up": pitch, "down": -pitch}
        if self.yon != "center" and deger[self.yon] < DIR_KAPAT:
            self.yon = "center"
        if self.yon == "center" and max(abs(yaw), abs(pitch)) >= DIR_AC:
            if abs(yaw) >= abs(pitch):
                self.yon = "right" if yaw > 0 else "left"
            else:
                self.yon = "up" if pitch > 0 else "down"
        return self.yon


class IkinciYuz:
    """second_face_appeared / second_face_gone."""

    def __init__(self):
        self.bildirildi = False
        self.gorunme_basi = None
        self.yok_basi = None

    def guncelle(self, var, simdi):
        if var:
            self.yok_basi = None
            if self.gorunme_basi is None:
                self.gorunme_basi = simdi
            if not self.bildirildi and simdi - self.gorunme_basi >= IKINCI_GELDI_SN:
                self.bildirildi = True
                olay_gonder("second_face_appeared", self.gorunme_basi, 1.0,
                            simdi - self.gorunme_basi)
        else:
            self.gorunme_basi = None
            if self.bildirildi:
                if self.yok_basi is None:
                    self.yok_basi = simdi
                if simdi - self.yok_basi >= IKINCI_GITTI_SN:
                    self.bildirildi = False
                    olay_gonder("second_face_gone", self.yok_basi, 1.0, simdi - self.yok_basi)


class IsikTakip:
    """room_dark / room_bright: küçültülmüş karenin ortalama parlaklığı (tek sayı, kare saklanmaz).

    Hızlı (~0.3 sn) ve yavaş (~5 sn) üstel ortalama karşılaştırılır. Ani değişimde hızlı olan
    yavaş tabandan ayrılır. Olaydan sonra taban yeni seviyeye çekilir. Kameranın otomatik pozlaması
    değişimi ~1 sn içinde yumuşatır; bu yüzden hızlı ortalama kısa tutuldu.
    """

    def __init__(self):
        self.hizli = None
        self.yavas = None
        self.son = 0.0
        self.baslangic = 0.0
        self.bekleme_bitis = 0.0

    @staticmethod
    def parlaklik(kare):
        kucuk = cv2.resize(kare, (64, 36), interpolation=cv2.INTER_AREA)
        return float(cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY).mean()) / 255.0

    def guncelle(self, kare, simdi, el_yakin):
        p = self.parlaklik(kare)
        if self.hizli is None:
            self.hizli = self.yavas = p
            self.son = self.baslangic = simdi
            return p
        dt = max(0.0, simdi - self.son)
        self.son = simdi
        self.hizli += (1 - math.exp(-dt / ISIK_HIZLI_SN)) * (p - self.hizli)
        self.yavas += (1 - math.exp(-dt / ISIK_YAVAS_SN)) * (p - self.yavas)
        if simdi - self.baslangic < ISIK_ISINMA_SN or simdi < self.bekleme_bitis or el_yakin:
            return p
        oran = (self.hizli + 0.02) / (self.yavas + 0.02)
        if oran <= ISIK_KARARDI_ORAN:
            olay_gonder("room_dark", simdi, min(1.0, (1 - oran) / 0.6), 0.0)
            self.yavas = self.hizli
            self.bekleme_bitis = simdi + ISIK_BEKLEME_SN
        elif oran >= ISIK_AYDINLANDI_ORAN:
            olay_gonder("room_bright", simdi, min(1.0, (oran - 1) / 1.0), 0.0)
            self.yavas = self.hizli
            self.bekleme_bitis = simdi + ISIK_BEKLEME_SN
        return p


class Kalibrasyon:
    """Nötr yüzün ortalama blendshape değerlerini ve baş açılarını çıkarır.

    Duygu skorları blendshape farkından, head_yaw/head_pitch nötr duruşa göre hesaplanır.
    """

    def __init__(self, sure):
        self.sure = sure
        self.sifirla()

    def sifirla(self):
        self.baslangic = None
        self.toplam = {}
        self.sayi = 0
        self.baz = None
        self.yaw_toplam = 0.0
        self.pitch_toplam = 0.0
        self.baz_yaw = 0.0
        self.baz_pitch = 0.0

    @property
    def bitti(self):
        return self.baz is not None

    def ekle(self, b, simdi, yaw, pitch):
        if self.baslangic is None:
            self.baslangic = simdi
        for k, v in b.items():
            self.toplam[k] = self.toplam.get(k, 0.0) + v
        self.yaw_toplam += yaw
        self.pitch_toplam += pitch
        self.sayi += 1
        if simdi - self.baslangic >= self.sure:
            self.baz = {k: v / self.sayi for k, v in self.toplam.items()}
            self.baz_yaw = self.yaw_toplam / self.sayi
            self.baz_pitch = self.pitch_toplam / self.sayi
            print("Kalibrasyon bitti.", file=sys.stderr)

    def uygula(self, b):
        return {k: max(0.0, v - self.baz.get(k, 0.0)) for k, v in b.items()}


def blendshape_sozlugu(sonuc, i):
    return {b.category_name: b.score for b in sonuc.face_blendshapes[i]}


def bas_acisi(sonuc, i):
    """Yüzün baktığı yönün (yaw, pitch) açısını derece olarak verir.

    Dönüşüm matrisinin üçüncü sütunu yüzün ileri eksenidir. yaw > 0: yüz görüntünün sağına
    bakıyor, pitch > 0: yukarı bakıyor (işaretler YAW_ISARET / PITCH_ISARET ile çevrilebilir).
    abs(z): eksen yönü sürümden sürüme değişse de sapmanın büyüklüğü bozulmasın.
    """
    m = sonuc.facial_transformation_matrixes[i]
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
    """b'nin kayıtlı ifade şablonuna benzerliği (0–1)."""
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

    Bir duygunun şablonu varsa o duygu şablonla, yoksa kuralla hesaplanır.
    Esneme ile şaşkınlığı ayıran şey ağız değil gözler ve kaşlar.
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
        skorlar["sad"] = 0.0

    baskin = max(skorlar, key=skorlar.get)
    skorlar = {ad: (v if ad == baskin else 0.0) for ad, v in skorlar.items()}
    skorlar["yawn"] = 0.0 if saskin_norm >= YAWN_AYRIM else cene

    debug = (
        f"uzgun_ham {uzgun:.2f}  agiz asagi {agiz_asagi:.2f}  ic kas {ic_kas:.2f}  "
        f"alt dudak {alt_dudak:.2f}",
        f"goz acik {goz_acik:.2f}  kas yukari {kas_yukari:.2f}  kisik {goz_kisik:.2f}",
    )
    return skorlar, debug


def kutu(noktalar):
    """Noktaların sınır kutusu (x1, y1, x2, y2), 0–1 koordinat."""
    xs = [n.x for n in noktalar]
    ys = [n.y for n in noktalar]
    return (min(xs), min(ys), max(xs), max(ys))


def kutu_alani(k):
    return max(0.0, k[2] - k[0]) * max(0.0, k[3] - k[1])


def ortusme(el_kutusu, yuz_kutusu):
    """Elin kutusu yüz kutusunun ne kadarını örtüyor (0–1)."""
    alan = kutu_alani(yuz_kutusu)
    if alan <= 0:
        return 0.0
    ix = max(0.0, min(el_kutusu[2], yuz_kutusu[2]) - max(el_kutusu[0], yuz_kutusu[0]))
    iy = max(0.0, min(el_kutusu[3], yuz_kutusu[3]) - max(el_kutusu[1], yuz_kutusu[1]))
    return min(1.0, ix * iy / alan)


def kutu_merkezi(k):
    return (k[0] + k[2]) / 2, (k[1] + k[3]) / 2


def genislet(k, oran):
    """Kutuyu her yöne genişliğinin/yüksekliğinin `oran` katı kadar büyütür."""
    w, h = k[2] - k[0], k[3] - k[1]
    return (k[0] - w * oran, k[1] - h * oran, k[2] + w * oran, k[3] + h * oran)


def birincil_yuz(yuzler, onceki_merkez):
    """Kullanıcının yüzünü seçer. Önceki merkez biliniyorsa ona en yakın, yoksa en büyük yüz."""
    kutular = [kutu(y) for y in yuzler]
    if onceki_merkez is not None and len(yuzler) > 1:
        def uzaklik(i):
            cx, cy = kutu_merkezi(kutular[i])
            return math.hypot(cx - onceki_merkez[0], cy - onceki_merkez[1])
        i = min(range(len(yuzler)), key=uzaklik)
    else:
        i = max(range(len(yuzler)), key=lambda j: kutu_alani(kutular[j]))
    return i, kutular


def yuz_merkezi(noktalar):
    """Yüzün kameradaki merkezi (x, y), 0–1, sol üst köşe (0, 0), aynalanmamış görüntü."""
    x, y = kutu_merkezi(kutu(noktalar))
    return min(1.0, max(0.0, x)), min(1.0, max(0.0, y))


def olu_bolge(v):
    """Ölü bölgeyi aşan kısmı döndürür (süreksiz sıçrama olmasın)."""
    if abs(v) <= POSE_OLU_BOLGE:
        return 0.0
    return math.copysign(abs(v) - POSE_OLU_BOLGE, v)


def face_track_gonder(t, present, x, y, looking_at_robot, head_dir, head_yaw, head_pitch):
    """A1 mesajını üretir. Şimdilik konsola yazar; sonra router'a gönderme buraya gelecek."""
    mesaj = {
        "type": "face_track",
        "t": round(t, 2),
        "present": present,
        "x": None if x is None else round(x, 3),
        "y": None if y is None else round(y, 3),
        "looking_at_robot": looking_at_robot,
        "head_dir": head_dir,
        "head_yaw": None if head_yaw is None else round(head_yaw, 1),
        "head_pitch": None if head_pitch is None else round(head_pitch, 1),
    }
    print(json.dumps(mesaj), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", action="store_true",
                    help="A1 face_track akışını da stdout'a yaz (~15 mesaj/sn)")
    args = ap.parse_args()
    track_aralik = 1.0 / TRACK_HZ

    indir(MODEL_URL, MODEL_PATH)
    indir(EL_MODEL_URL, EL_MODEL_PATH)
    indir(OBJ_MODEL_URL, OBJ_MODEL_PATH)

    secenekler = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=2,                                 # ikinci yüz tespiti için
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    el_secenekleri = vision.GestureRecognizerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=EL_MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    obj_secenekleri = vision.ObjectDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=OBJ_MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        max_results=10,
        score_threshold=OBJ_SKOR_ESIK,
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

    hand_near = SureliOlay("hand_near", HAND_AC, HAND_KAPAT, HAND_MIN_SN, HAND_REF)
    head_down = SureliOlay("head_down_long", HEAD_DOWN_AC, HEAD_DOWN_KAPAT,
                           HEAD_DOWN_MIN_SN, HEAD_DOWN_REF)
    kapanma = YuzKapanma()
    ikinci = IkinciYuz()
    bas_yonu = BasYonu()
    isik = IsikTakip()
    nesne_takip = ObjeTakip()
    son_nesneler = {}       # son dedektör geçişi: {etiket: (skor, kutu)}
    son_oranlar = {}        # "remote" kaynaklı etiketlerin ham kutu oranı (sadece panelde gösterilir)
    kare_sayac = 0
    engel_son_t = -1e9      # el/nesne yüzün yakınında en son ne zaman görüldü
    thumbs_up = SureliOlay("thumbs_up", THUMB_AC, THUMB_KAPAT, THUMB_MIN_SN)
    orta_parmak_olay = SureliOlay("middle_finger", ORTA_AC, ORTA_KAPAT, ORTA_MIN_SN)
    stop_olay = SureliOlay("stop", STOP_AC, STOP_KAPAT, STOP_MIN_SN)
    sus_olay = SureliOlay("shush", SUS_AC, SUS_KAPAT, SUS_MIN_SN)
    selam_olay = SureliOlay("salute", SELAM_AC, SELAM_KAPAT, SELAM_MIN_SN)
    el_durgun = ElDurgun()
    el_sallama = ElSallama()
    sallama_yes = BasSallama("answer_yes", NOD_GENLIK)
    sallama_no = BasSallama("answer_no", SHAKE_GENLIK)

    kal = Kalibrasyon(KALIB_SN)
    sablonlar = {}
    kayit_ad = None
    kayit_bitis = 0.0
    kayit_toplam = {}
    kayit_sayi = 0
    son_track = 0.0

    kullanici_var = False
    gorunme_basi = None
    kayip_basi = None

    son_yuz_kutu = None     # elle örtülmediği son karedeki yüz kutusu
    son_yuz_zaman = -1e9    # yüz en son ne zaman görüldü
    son_el_yakin_t = -1e9   # hand_near en son ne zaman aktifti
    son_ort_t, son_ort_val = -1e9, 0.0   # el yüzü en son ne zaman, ne kadar örttü
    yaw_ema = pitch_ema = None
    son_asagi = None
    son_asagi_t = 0.0

    baslangic = time.monotonic()
    son_ts = -1

    with vision.FaceLandmarker.create_from_options(secenekler) as landmarker, \
            vision.GestureRecognizer.create_from_options(el_secenekleri) as el_lm, \
            vision.ObjectDetector.create_from_options(obj_secenekleri) as obj_det:
        while True:
            ok, kare = kamera.read()
            if not ok:
                break
            yuk, gen = kare.shape[0], kare.shape[1]

            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            mp_kare = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            ts = int((time.monotonic() - baslangic) * 1000)
            if ts <= son_ts:
                ts = son_ts + 1
            son_ts = ts

            sonuc = landmarker.detect_for_video(mp_kare, ts)
            el_sonuc = el_lm.recognize_for_video(mp_kare, ts)
            simdi = time.time()
            yuz_var = bool(sonuc.face_landmarks)

            # --- Kullanıcının yüzü + ikinci yüz ---
            ana_i, ana_kutu, ikinci_var = None, None, False
            if yuz_var:
                onceki = kutu_merkezi(son_yuz_kutu) if (
                    son_yuz_kutu is not None and simdi - son_yuz_zaman < 2.0) else None
                ana_i, kutular = birincil_yuz(sonuc.face_landmarks, onceki)
                ana_kutu = kutular[ana_i]
                ikinci_var = any(kutu_alani(k) >= IKINCI_MIN_ALAN
                                 for j, k in enumerate(kutular) if j != ana_i)
            ikinci.guncelle(ikinci_var, simdi)

            # --- Eller: boyut (hand_near) ve yüzü örtme (face_covered) ---
            el_kutulari = []
            el_boyut = 0.0
            thumb_skor = 0.0
            orta_skor = 0.0
            sus_skor = 0.0
            selam_skor = 0.0
            durgun_x = durgun_y = None
            sallama_x = None
            for idx, el in enumerate(el_sonuc.hand_landmarks):
                el_kutulari.append(kutu(el))
                boyut_px = math.hypot((el[9].x - el[0].x) * gen, (el[9].y - el[0].y) * yuk)
                el_boyut = max(el_boyut, boyut_px / yuk)
                hareket, hareket_skor = "", 0.0
                if idx < len(el_sonuc.gestures) and el_sonuc.gestures[idx]:
                    hareket = el_sonuc.gestures[idx][0].category_name
                    hareket_skor = el_sonuc.gestures[idx][0].score
                if hareket == "Thumb_Up":
                    thumb_skor = max(thumb_skor, hareket_skor)
                orta_skor = max(orta_skor, orta_parmak(el, gen, yuk))
                if yuz_var and sus_isareti(el, sonuc.face_landmarks[ana_i], ana_kutu, gen, yuk):
                    sus_skor = 1.0
                if boyut_px > 0 and avuc_acik(el, hareket, hareket_skor, gen, yuk):
                    merkez_x = sum(el[i].x for i in (0, 5, 9, 13, 17)) / 5 * gen
                    merkez_y = sum(el[i].y for i in (0, 5, 9, 13, 17)) / 5 * yuk
                    sallama_x = merkez_x / boyut_px
                    el_dx = (el[12].x - el[0].x) * gen
                    el_dy = (el[0].y - el[12].y) * yuk
                    if el_dy > abs(el_dx):
                        # parmaklar yukarı bakıyor: stop adayı (kıpırdamıyorsa)
                        durgun_x, durgun_y = sallama_x, merkez_y / boyut_px
                    elif (abs(el_dx) > abs(el_dy) and ana_kutu is not None
                          and selam_konumu(el[12], ana_kutu)):
                        # el yatay ve parmak ucu alında: selam
                        selam_skor = 1.0
            hand_near.guncelle(el_boyut, simdi)
            thumbs_up.guncelle(thumb_skor, simdi)
            orta_parmak_olay.guncelle(orta_skor, simdi)
            stop_skor = 1.0 if el_durgun.guncelle(durgun_x, durgun_y, simdi) else 0.0
            stop_olay.guncelle(stop_skor, simdi)
            sus_olay.guncelle(sus_skor, simdi)
            selam_olay.guncelle(selam_skor, simdi)
            el_sallama.guncelle(sallama_x, simdi)

            # --- Nesne algılama (her OBJ_HER_N_KARE karede bir) ---
            kare_sayac += 1
            if kare_sayac % OBJ_HER_N_KARE == 0:
                obj_sonuc = obj_det.detect_for_video(mp_kare, ts)
                son_nesneler = {}
                for det in obj_sonuc.detections:
                    kat = det.categories[0]
                    bb = det.bounding_box
                    ad, oran = obj_etiket(kat.category_name, bb)
                    if ad not in OBJ_LISTE:
                        continue
                    k = (bb.origin_x / gen, bb.origin_y / yuk,
                         (bb.origin_x + bb.width) / gen, (bb.origin_y + bb.height) / yuk)
                    if ad not in son_nesneler or kat.score > son_nesneler[ad][0]:
                        son_nesneler[ad] = (kat.score, k)
                        if oran is not None:
                            son_oranlar[ad] = oran
                        else:
                            son_oranlar.pop(ad, None)
                nesne_takip.guncelle(son_nesneler, el_kutulari, el_boyut, simdi)
            if hand_near.aktif:
                son_el_yakin_t = simdi
            el_yakin = simdi - son_el_yakin_t < EL_YAKIN_BEKLE_SN

            ref_sn = REF_KAPALI_SN if kapanma.el_yuzde else REF_GECERLI_SN
            ref_gecerli = son_yuz_kutu is not None and (
                yuz_var or simdi - son_yuz_zaman < ref_sn)
            ort = 0.0
            if ref_gecerli:
                ort = max((ortusme(k, son_yuz_kutu) for k in el_kutulari), default=0.0)
                if ort >= COVER_KAPAT:
                    son_ort_t, son_ort_val = simdi, ort
                elif not yuz_var and simdi - son_ort_t < EL_KAYBOLMA_TUT_SN:
                    # El yüze yaklaşırken yüz kayboldu ve el modeli avucu kaçırdı:
                    # örtme sürüyor kabul et.
                    ort = son_ort_val
            kapanma.guncelle(ort, yuz_var, simdi)
            if yuz_var:
                if ort < COVER_KAPAT:
                    son_yuz_kutu = ana_kutu
                son_yuz_zaman = simdi

            # El yüzün üstündeyken yüz verisi güvenilmez: ifade, baş açısı hesaplanmaz.
            yuz_guvenilir = yuz_var and not kapanma.el_yuzde

            parlak = isik.guncelle(kare, simdi, el_yakin)

            gulme = cene = goz = merkez = ifade = None
            yuz_x = yuz_y = None
            yaw_pub = pitch_pub = None
            sal_yaw = sal_pitch = None
            debug = ("", "")

            # --- Varlık: user_arrived / user_left ---
            if yuz_var:
                kayip_basi = None
                if gorunme_basi is None:
                    gorunme_basi = simdi
                if not kullanici_var and simdi - gorunme_basi >= ARRIVED_SN:
                    kullanici_var = True
                    olay_gonder("user_arrived", gorunme_basi, 1.0, 0)
            else:
                gorunme_basi = None
                if kayip_basi is None:
                    kayip_basi = simdi
                if kullanici_var and simdi - kayip_basi >= LEFT_SN:
                    kullanici_var = False
                    olay_gonder("user_left", kayip_basi, 1.0, 0)
                # Kısa kayıp (el kapattı) kalibrasyonu bozmasın; uzun kayıpta baştan.
                if not kal.bitti and simdi - kayip_basi >= KALIB_SIFIRLA_SN:
                    kal.sifirla()

            # --- Yüz verisi (sadece güvenilirse) ---
            if yuz_guvenilir:
                b = blendshape_sozlugu(sonuc, ana_i)
                gulme = (b.get("mouthSmileLeft", 0.0) + b.get("mouthSmileRight", 0.0)) / 2
                cene = b.get("jawOpen", 0.0)
                goz = (b.get("eyeBlinkLeft", 0.0) + b.get("eyeBlinkRight", 0.0)) / 2
                yaw, pitch = bas_acisi(sonuc, ana_i)
                merkez = merkezlik_skoru(yaw, pitch, b)
                yuz_x, yuz_y = yuz_merkezi(sonuc.face_landmarks[ana_i])

                ham_yaw, ham_pitch = YAW_ISARET * yaw, PITCH_ISARET * pitch
                if not kal.bitti:
                    kal.ekle(b, simdi, ham_yaw, ham_pitch)
                else:
                    rel_yaw = ham_yaw - kal.baz_yaw
                    rel_pitch = ham_pitch - kal.baz_pitch
                    sal_yaw, sal_pitch = rel_yaw, rel_pitch
                    yaw_ema = rel_yaw if yaw_ema is None else yaw_ema + POSE_ALFA * (rel_yaw - yaw_ema)
                    pitch_ema = (rel_pitch if pitch_ema is None
                                 else pitch_ema + POSE_ALFA * (rel_pitch - pitch_ema))
                    yaw_pub, pitch_pub = olu_bolge(yaw_ema), olu_bolge(pitch_ema)

                    if kayit_ad is not None:
                        for k, v in kal.uygula(b).items():
                            kayit_toplam[k] = kayit_toplam.get(k, 0.0) + v
                        kayit_sayi += 1
                        if simdi >= kayit_bitis:
                            ort_b = {k: v / kayit_sayi for k, v in kayit_toplam.items()
                                     if not k.startswith("_") and v / kayit_sayi > 0.05}
                            sablonlar[kayit_ad] = ort_b
                            print(f"Sablon kaydedildi: {kayit_ad} ({len(ort_b)} ozellik)",
                                  file=sys.stderr)
                            kayit_ad = None
                    else:
                        ifade, debug = ifade_skorlari(kal.uygula(b), gulme, cene, sablonlar)
            else:
                kayit_ad = None                 # yüz yok / örtülü: şablon kaydı iptal
                yaw_ema = pitch_ema = None

            # --- head_down_long: nötr duruşa göre aşağı eğim ---
            if yuz_guvenilir and pitch_ema is not None:
                asagi_skor = -pitch_ema
                son_asagi, son_asagi_t = asagi_skor, simdi
            elif (son_asagi is not None and simdi - son_asagi_t < ASAGI_TOLERANS_SN
                  and son_asagi >= HEAD_DOWN_KAPAT):
                asagi_skor = son_asagi          # çok eğikken yüz kısa süre kaybolabilir
            else:
                asagi_skor = None
            head_down.guncelle(asagi_skor, simdi)

            # El ya da nesne (telefon vb.) yüzün yakınındaysa yüz takibi bozulur: baş sallama arama.
            if ana_kutu is not None:
                genis = genislet(ana_kutu, SALLAMA_ENGEL_GENISLET)
                engel_kutulari = el_kutulari + [v[1] for v in son_nesneler.values()]
                if any(ortusme(genis, k) >= SALLAMA_ENGEL_ORTUSME for k in engel_kutulari):
                    engel_son_t = simdi
            if simdi - engel_son_t < SALLAMA_ENGEL_SN:
                sal_yaw = sal_pitch = None

            # Kafa sallama: biri olay verirse diğeri susar.
            if sallama_yes.guncelle(sal_pitch, sal_yaw, simdi):
                sallama_no.durdur(sallama_yes.bekleme_bitis)
            elif sallama_no.guncelle(sal_yaw, sal_pitch, simdi):
                sallama_yes.durdur(sallama_no.bekleme_bitis)

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

            yon = bas_yonu.guncelle(yaw_ema, pitch_ema)

            # A1: ~15 Hz yüz takip akışı (sadece --track ile).
            if args.track and simdi - son_track >= track_aralik:
                son_track = simdi
                face_track_gonder(simdi, yuz_guvenilir, yuz_x, yuz_y, bakis.aktif,
                                  yon, yaw_pub, pitch_pub)

            # --- Sadece test için ekran bilgisi ---
            ekran = cv2.flip(kare, 1)
            if OBJ_KUTU_CIZ:
                for etiket, (skor, k) in son_nesneler.items():
                    x1, x2 = int((1 - k[2]) * gen), int((1 - k[0]) * gen)   # ekran aynalı
                    y1, y2 = int(k[1] * yuk), int(k[3] * yuk)
                    cv2.rectangle(ekran, (x1, y1), (x2, y2), (255, 0, 255), 1)
            # Nesneler: sağ üstte ayrı panel
            panel = ["NESNELER"] + [
                f"{e} {sk:.2f}" + (f"  oran {son_oranlar[e]:.1f}" if e in son_oranlar else "")
                for e, (sk, _) in son_nesneler.items()]
            if not son_nesneler:
                panel = ["NESNELER: yok"]
            for i, metin in enumerate(panel):
                (tw, _), _ = cv2.getTextSize(metin, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
                cv2.putText(ekran, metin, (gen - tw - 10, 25 + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 255), 1)
            # Son nesne olayı (object_appeared/gone/shown): panelin hemen altında, küçük yazı
            if simdi - SON_NESNE_OLAY[1] < 3.0:
                metin = SON_NESNE_OLAY[0]
                (tw, _), _ = cv2.getTextSize(metin, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.putText(ekran, metin, (gen - tw - 10, 25 + len(panel) * 22 + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
            if yuz_guvenilir:
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
                    satir3 = ""
                renk = (0, 255, 255)
            elif yuz_var:
                satir1, satir2, satir3, renk = "el yuzde", "", "", (0, 165, 255)
            else:
                satir1, satir2, satir3, renk = "yuz yok", "", "", (0, 0, 255)
            yaw_s = "-" if yaw_pub is None else f"{yaw_pub:+.0f}"
            pitch_s = "-" if pitch_pub is None else f"{pitch_pub:+.0f}"
            satir4 = (f"el: {el_boyut:.2f}  ortme: {ort:.2f}  yaw: {yaw_s}  pitch: {pitch_s}  "
                      f"isik: {parlak:.2f}  yuz sayisi: {len(sonuc.face_landmarks)}")
            cv2.putText(ekran, satir1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir2, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, satir3, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, renk, 2)
            cv2.putText(ekran, debug[0], (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 1)
            cv2.putText(ekran, debug[1], (10, 142), cv2.FONT_HERSHEY_SIMPLEX, 0.5, renk, 1)
            cv2.putText(ekran, satir4, (10, 164), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            etiket = {"left": "SOL", "right": "SAG", "up": "YUKARI", "down": "ASAGI",
                      "center": "ORTA"}.get(yon, "-")
            cv2.putText(ekran, f"BAS: {etiket}", (10, 215), cv2.FONT_HERSHEY_SIMPLEX,
                        1.4, (0, 255, 0), 3)
            if kapanma.kapali:
                durum = "YUZ KAPALI"
            elif kapanma.aday_basi is not None:
                durum = "kapaniyor..."
            else:
                durum = ""
            if hand_near.aktif:
                durum = (durum + "  EL YAKIN").strip()
            cv2.putText(ekran, durum, (10, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 255), 2)
            # Son olay (nesne dışı: kafa sallama, gülme, el vb.): sol altta, küçük yazı
            if simdi - SON_OLAY[1] < 3.0:
                cv2.putText(ekran, f"olay: {SON_OLAY[0]}", (10, ekran.shape[0] - 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)
            yardim = ("[s] uzgun [a] sinirli [u] saskin kaydet  [c] kalibre   sablon: "
                      + (" ".join(sorted(sablonlar)) or "yok"))
            cv2.putText(ekran, yardim, (10, ekran.shape[0] - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.imshow("CV olaylari", ekran)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            if tus == ord("c"):
                kal.sifirla()
                sablonlar.clear()
                kayit_ad = None
            elif tus in SABLON_TUSLARI and kal.bitti and yuz_guvenilir:
                kayit_ad = SABLON_TUSLARI[tus]
                kayit_bitis = simdi + SABLON_SN
                kayit_toplam = {}
                kayit_sayi = 0

    kamera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
