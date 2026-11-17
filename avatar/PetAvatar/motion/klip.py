"""
motion/klip.py  --  Animasyon klibi (C3-taslak) okuma ve ara değer hesaplama

Bu dosyada Tkinter YOK; sadece "veri ve matematik" var. Böylece:
  - Simülatör de, ileride router/HAL de aynı kodu kullanabilir,
  - Pencere açmadan test edilebilir.

Klip formatı (Tuğra'nın Yüz Atölyesi'nden çıkan JSON):
    {"format": "C3-taslak", "name": ..., "emotion": ..., "loop": true/false,
     "duration_ms": ..., "keys": [{"t_ms": ..., "ease": ..., "face": {...}, "pose": {...}}, ...]}

Her anahtar karenin iki parçası var:
  - "pose": motor açıları (çubuklara gider)
  - "face": yüz ekranı (gözler, ağız, kaşlar, gözyaşı...) -> motion/yuz.py çizer

Matematik, Yüz Atölyesi'nin kendi oynatma kodundaki mantıkla aynıdır; böylece
simülatörde gördüğümüz hareket, Tuğra'nın atölyede gördüğüyle aynı olur.
"""

import bisect
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# SABİTLER
# ----------------------------------------------------------------------------

# Her eklemin adı ve gidebileceği mantıksal aralık (en_az, en_cok).
# Açılar derece, kulaklar 0 (yatık) ile 1 (dik) arasındadır.
EKLEMLER: Dict[str, Tuple[float, float]] = {
    "body_yaw": (-45, 45),   # gövde sağ-sol, derece
    "head_pan": (-90, 90),   # baş sağ-sol, derece
    "head_tilt": (-10, 45),  # baş aşağı-yukarı, derece
    "ear_left": (0, 1),      # sol kulak: 0 yatık, 1 dik
    "ear_right": (0, 1),     # sağ kulak: 0 yatık, 1 dik
}

FORMAT_ADI = "C3-taslak"

# Atölyedeki geçiş türleri:
#   smooth = akıcı (ara karelerde durmadan akar), linear = düz, snap = ani,
#   bounce = hafif aşıp geri gelen esnek hareket, stop = yavaşlayıp durur
GECERLI_GECISLER = ("smooth", "linear", "snap", "bounce", "stop")

# bounce geçişinin ne kadar "aşacağını" belirleyen sabit (atölyedeki değerle aynı)
ESNEKLIK = 1.70158 * 1.2

# Yüzün başlangıç değerleri (klipte eksik bırakılan alanlar için)
YUZ_VARSAYILAN: Dict[str, Any] = {
    "eye_shape": "round", "eye_open": 0.9, "eye_size": 1.0, "pupil": 0.9, "sparkle": 0.8,
    "look_x": 0.0, "look_y": 0.0,
    "brow_show": True, "brow_left": 0.0, "brow_right": 0.0, "brow_height": 0.0,
    "mouth": "w", "mouth_open": 0.4, "mouth_width": 1.0, "mouth_x": 0.0, "mouth_tilt": 0.0,
    "tears": 0.0, "blush": True, "sweat": False, "gloom": 0.0, "rage": 0.0, "anger_mark": False,
    "line": "#2B2A33", "iris": "#6B4A3A", "blush_color": "#F09AA6",
    "tear_color": "#5DADE2", "face_bg": "#FBF8F3", "head": "#8E929C",
}

# Sayısal yüz alanları ve izin verilen aralıkları (Yüz Atölyesi'ndeki kaydırıcı sınırları)
YUZ_SAYISAL_SINIRLAR: Dict[str, Tuple[float, float]] = {
    "eye_open": (0.1, 1), "eye_size": (0.7, 1.4), "pupil": (0.4, 1.3), "sparkle": (0, 1),
    "look_x": (-1, 1), "look_y": (-1, 1),
    "brow_left": (-30, 30), "brow_right": (-30, 30), "brow_height": (-1, 1),
    "mouth_open": (0, 1), "mouth_width": (0.6, 1.5), "mouth_x": (-1, 1), "mouth_tilt": (-25, 25),
    "tears": (0, 1), "gloom": (0, 1), "rage": (0, 1),
}

YUZ_MANTIKSAL = ("brow_show", "blush", "sweat", "anger_mark")
YUZ_RENKLER = ("line", "iris", "blush_color", "tear_color", "face_bg", "head")
GOZ_SEKILLERI = ("round", "arc", "narrow", "closed", "spiral", "blank")

# Dosyadaki "colors" anahtarları -> bizim iç adlarımız
RENK_ESLEME = {"line": "line", "iris": "iris", "blush": "blush_color",
               "tear": "tear_color", "face_bg": "face_bg", "head": "head"}

_RENK_DESENI = re.compile(r"#[0-9a-fA-F]{6}")


# ----------------------------------------------------------------------------
# RENK YARDIMCILARI (yuz.py de kullanır)
# ----------------------------------------------------------------------------

def hex_rgb(renk: str) -> Tuple[int, int, int]:
    """'#RRGGBB' metnini (r, g, b) sayılarına çevirir."""
    n = int(renk[1:7], 16)
    return (n >> 16) & 255, (n >> 8) & 255, n & 255


def rgb_hex(r: float, g: float, b: float) -> str:
    """(r, g, b) sayılarını '#rrggbb' metnine çevirir."""
    return "#{:02x}{:02x}{:02x}".format(
        int(round(min(max(r, 0), 255))), int(round(min(max(g, 0), 255))), int(round(min(max(b, 0), 255))))


def renk_karistir(on: str, arka: str, alfa: float) -> str:
    """'on' rengini 'arka' rengin üstüne alfa (0-1) saydamlıkla koyunca çıkan rengi hesaplar.

    Tk Canvas saydamlık bilmez; zemin rengini bildiğimiz için karışımı kendimiz hesaplıyoruz.
    """
    alfa = min(max(alfa, 0.0), 1.0)
    x, y = hex_rgb(on), hex_rgb(arka)
    return rgb_hex(*(y[i] + (x[i] - y[i]) * alfa for i in range(3)))


# ----------------------------------------------------------------------------
# VERİ YAPILARI
# ----------------------------------------------------------------------------

class KlipHatasi(Exception):
    """Klip dosyası bozuk veya okunamadığında fırlatılan özel hata."""


@dataclass(frozen=True)
class Kare:
    """Klipteki tek bir anahtar kare: 'şu anda kedi şu pozda ve şu yüzde olsun'."""

    t_ms: float                  # Bu karenin klip başından itibaren zamanı (ms)
    gecis: str                   # Bu kareye ÖNCEKİ kareden nasıl gidileceği (smooth, snap...)
    poz: Dict[str, float]        # Eklem adı -> değer
    yuz: Dict[str, Any]          # Yüz alanı adı -> değer (göz şekli, ağız, renkler...)


@dataclass(frozen=True)
class Klip:
    """Bir animasyon klibi: ad, duygu, döngü bilgisi ve anahtar kareler."""

    ad: str
    duygu: str
    dongu: bool
    kareler: Tuple[Kare, ...]

    @property
    def sure_ms(self) -> float:
        """Klibin toplam süresi: son karenin zamanı."""
        return self.kareler[-1].t_ms


# ----------------------------------------------------------------------------
# YÜKLEYİCİ
# ----------------------------------------------------------------------------

class KlipYukleyici:
    """JSON dosyalarını okuyup doğrular ve Klip nesnesine çevirir."""

    @staticmethod
    def dosyadan_yukle(yol: Path) -> Klip:
        """Tek bir JSON dosyasını okur. Dosya okunamazsa veya bozuksa KlipHatasi fırlatır."""
        try:
            with open(yol, "r", encoding="utf-8") as dosya:
                veri = json.load(dosya)
        except (OSError, json.JSONDecodeError) as hata:
            raise KlipHatasi(f"{yol.name} okunamadı: {hata}") from hata
        return KlipYukleyici.sozlukten_olustur(veri, varsayilan_ad=yol.stem)

    @staticmethod
    def _yuz_olustur(ham_yuz: Any, sira: int) -> Dict[str, Any]:
        """Karedeki 'face' bölümünü doğrular; eksik/bozuk alanlarda varsayılanları kullanır."""
        yuz = dict(YUZ_VARSAYILAN)
        if not isinstance(ham_yuz, dict):
            return yuz

        for ad, (en_az, en_cok) in YUZ_SAYISAL_SINIRLAR.items():
            if ad in ham_yuz:
                try:
                    yuz[ad] = min(max(float(ham_yuz[ad]), en_az), en_cok)
                except (TypeError, ValueError):
                    logger.warning("%d. karede '%s' sayı değil; varsayılan kullanıldı.", sira, ad)

        for ad in YUZ_MANTIKSAL:
            if ad in ham_yuz:
                yuz[ad] = bool(ham_yuz[ad])

        sekil = ham_yuz.get("eye_shape", "round")
        if sekil in GOZ_SEKILLERI:
            yuz["eye_shape"] = sekil
        else:
            logger.warning("%d. karede bilinmeyen göz şekli '%s'; 'round' kullanıldı.", sira, sekil)

        agiz = ham_yuz.get("mouth")
        if isinstance(agiz, str) and agiz:
            yuz["mouth"] = agiz   # Bilinmeyen ağız tipi çizimde düz çizgi olarak görünür

        renkler = ham_yuz.get("colors")
        if isinstance(renkler, dict):
            for dosya_adi, ic_ad in RENK_ESLEME.items():
                deger = renkler.get(dosya_adi)
                if isinstance(deger, str) and _RENK_DESENI.fullmatch(deger):
                    yuz[ic_ad] = deger.upper()
        return yuz

    @staticmethod
    def sozlukten_olustur(veri: Any, varsayilan_ad: str = "adsız") -> Klip:
        """JSON'dan gelen sözlüğü doğrular; eksik/bozuk alanlarda güvenli varsayılanlar kullanır."""
        if not isinstance(veri, dict):
            raise KlipHatasi("Klip bir JSON nesnesi ({...}) olmalı.")
        if veri.get("format") != FORMAT_ADI:
            logger.warning("Beklenmeyen format: %r (beklenen: %r)", veri.get("format"), FORMAT_ADI)

        ham_kareler = veri.get("keys")
        if not isinstance(ham_kareler, list) or not ham_kareler:
            raise KlipHatasi("Klipte hiç anahtar kare ('keys') yok.")

        kareler = []
        onceki_poz: Dict[str, float] = {}
        for sira, ham in enumerate(ham_kareler, start=1):
            if not isinstance(ham, dict):
                raise KlipHatasi(f"{sira}. kare bozuk.")
            try:
                t_ms = float(ham["t_ms"])
            except (KeyError, TypeError, ValueError) as hata:
                raise KlipHatasi(f"{sira}. karede geçerli bir 't_ms' yok.") from hata

            gecis = ham.get("ease", "smooth")
            if gecis not in GECERLI_GECISLER:
                logger.warning("%d. karede bilinmeyen geçiş '%s'; 'smooth' kullanıldı.", sira, gecis)
                gecis = "smooth"

            ham_poz = ham.get("pose")
            if not isinstance(ham_poz, dict):
                ham_poz = {}
            # Pozda eksik eklem varsa bir önceki karedeki değer korunur (ilk karede 0).
            poz = {}
            for ad in EKLEMLER:
                try:
                    poz[ad] = float(ham_poz.get(ad, onceki_poz.get(ad, 0.0)))
                except (TypeError, ValueError):
                    poz[ad] = onceki_poz.get(ad, 0.0)
            onceki_poz = poz
            kareler.append(Kare(t_ms=t_ms, gecis=gecis, poz=poz,
                                yuz=KlipYukleyici._yuz_olustur(ham.get("face"), sira)))

        kareler.sort(key=lambda k: k.t_ms)   # Zamana göre sırala (python sort kararlıdır)
        return Klip(
            ad=str(veri.get("name") or varsayilan_ad).strip(),
            duygu=str(veri.get("emotion") or "idle"),
            dongu=bool(veri.get("loop", False)),
            kareler=tuple(kareler),
        )

    @staticmethod
    def klasorden_yukle(klasor: Path) -> Dict[str, Klip]:
        """Klasördeki tüm .json klipleri okur; bozuk olanı atlar, diğerlerini yüklemeye devam eder.

        Dönen sözlüğün anahtarı dosya adıdır (uzantısız): {"idle": Klip, "sad": Klip, ...}
        """
        klipler: Dict[str, Klip] = {}
        if not klasor.is_dir():
            logger.warning("Klip klasörü bulunamadı: %s", klasor)
            return klipler
        for yol in sorted(klasor.glob("*.json")):
            try:
                klipler[yol.stem] = KlipYukleyici.dosyadan_yukle(yol)
            except KlipHatasi as hata:
                logger.error("Klip atlandı: %s", hata)
        logger.info("%d klip yüklendi: %s", len(klipler), ", ".join(klipler))
        return klipler


# ----------------------------------------------------------------------------
# ARA DEĞER HESABI
# ----------------------------------------------------------------------------

class Enterpolator:
    """Bir klibin herhangi bir andaki pozunu ve yüzünü hesaplar (iki kare arasını doldurur)."""

    @staticmethod
    def _yumusak(k: float) -> float:
        """0'dan 1'e giden değeri başta ve sonda yavaşlatan 'smoothstep' eğrisi."""
        return k * k * (3 - 2 * k)

    @staticmethod
    def _esnek(k: float) -> float:
        """0'dan 1'e giderken hedefi biraz aşıp geri dönen eğri (bounce geçişi)."""
        x = k - 1
        return 1 + (ESNEKLIK + 1) * x ** 3 + ESNEKLIK * x ** 2

    @staticmethod
    def _kirp(deger: float, aralik: Tuple[float, float]) -> float:
        """Değeri izin verilen aralığa sıkıştırır (bounce aşması sınırı delmesin)."""
        return min(max(deger, aralik[0]), aralik[1])

    @staticmethod
    def _poz_al(kare: Kare, ad: str) -> float:
        """Karenin pozundan bir eklemin değerini okur."""
        return kare.poz[ad]

    @staticmethod
    def _yuz_al(kare: Kare, ad: str) -> float:
        """Karenin yüzünden bir sayısal alanın değerini okur."""
        return kare.yuz[ad]

    @staticmethod
    def _egim(kareler: Tuple[Kare, ...], j: int, ad: str, al: Callable[[Kare, str], float]) -> float:
        """Akıcı geçişte j. karedeki hareket hızını hesaplar.

        Hareket ara karelerde durmasın diye iki yanındaki hızların uyumlu ortalaması alınır.
        İlk/son karede, yön değiştirilen yerde ve smooth olmayan geçişte hız 0'dır (durur).
        """
        if j <= 0 or j >= len(kareler) - 1:
            return 0.0
        if kareler[j].gecis != "smooth" or kareler[j + 1].gecis != "smooth":
            return 0.0
        onceki_hiz = (al(kareler[j], ad) - al(kareler[j - 1], ad)) / max(1.0, kareler[j].t_ms - kareler[j - 1].t_ms)
        sonraki_hiz = (al(kareler[j + 1], ad) - al(kareler[j], ad)) / max(1.0, kareler[j + 1].t_ms - kareler[j].t_ms)
        if onceki_hiz * sonraki_hiz <= 0:   # Yön değişiyor: orada durup dönmeli
            return 0.0
        return 2 * onceki_hiz * sonraki_hiz / (onceki_hiz + sonraki_hiz)

    @staticmethod
    def _bul(kareler: Tuple[Kare, ...], t_ms: float) -> Tuple[int, float]:
        """t_ms hangi iki karenin arasında? (önceki kare sırası, 0-1 arası ilerleme) döndürür."""
        n = len(kareler)
        if n == 1 or t_ms <= kareler[0].t_ms:
            return 0, 0.0
        if t_ms >= kareler[-1].t_ms:
            return n - 2, 1.0
        zamanlar = [k.t_ms for k in kareler]
        i = bisect.bisect_left(zamanlar, t_ms) - 1
        sure = max(1.0, kareler[i + 1].t_ms - kareler[i].t_ms)
        return i, min(max((t_ms - kareler[i].t_ms) / sure, 0.0), 1.0)

    @classmethod
    def _sayi(cls, kareler: Tuple[Kare, ...], i: int, s: float, ad: str,
              al: Callable[[Kare, str], float]) -> float:
        """i. ve i+1. kare arasında, s ilerlemesinde, 'ad' alanının değerini hesaplar."""
        a = kareler[i]
        b = kareler[min(i + 1, len(kareler) - 1)]
        baslangic, hedef = al(a, ad), al(b, ad)
        sure = max(1.0, b.t_ms - a.t_ms)
        if b.gecis == "snap":
            return hedef if s > 0 else baslangic
        if b.gecis == "linear":
            return baslangic + (hedef - baslangic) * s
        if b.gecis == "bounce":
            return baslangic + (hedef - baslangic) * cls._esnek(s)
        if b.gecis == "stop":
            return baslangic + (hedef - baslangic) * cls._yumusak(s)
        # smooth: iki karenin hızlarını da hesaba katan eğri (Hermite)
        ma = cls._egim(kareler, i, ad, al)
        mb = cls._egim(kareler, i + 1, ad, al)
        s2, s3 = s * s, s * s * s
        return ((2 * s3 - 3 * s2 + 1) * baslangic + (s3 - 2 * s2 + s) * sure * ma
                + (-2 * s3 + 3 * s2) * hedef + (s3 - s2) * sure * mb)

    @classmethod
    def ornekle(cls, klip: Klip, t_ms: float) -> Dict[str, float]:
        """Klibin t_ms anındaki motor pozunu döndürür: {"head_pan": 12.3, "ear_left": 0.8, ...}."""
        kareler = klip.kareler
        i, s = cls._bul(kareler, t_ms)
        return {ad: cls._kirp(cls._sayi(kareler, i, s, ad, cls._poz_al), EKLEMLER[ad]) for ad in EKLEMLER}

    @staticmethod
    def _gecis_katsayisi(gecis: str, s: float) -> float:
        """Renk, şekil gibi 'ara değeri olmayan' yüz alanları için geçiş katsayısı (0-1)."""
        if gecis == "snap":
            return 1.0 if s > 0 else 0.0
        if gecis == "linear":
            return s
        return Enterpolator._yumusak(s)

    @staticmethod
    def _ayrik_alanlari_karistir(sonuc: Dict[str, Any], a: Dict[str, Any], b: Dict[str, Any], k: float) -> None:
        """Renkler, göz/ağız şekli ve aç-kapa alanlarını a'dan b'ye k (0-1) oranında geçirir.

        - Renkler karışır.
        - Şekil değişince göz "kırpar gibi" kapanıp yeni şekille açılır, ağız inceltilip yeni şekle döner
          (_eyeDip / _mouthSq değerleri bunu yuz.py'ye bildirir).
        - Kızarıklık, ter, öfke işareti ve kaşlar yavaşça belirir/kaybolur (_blushA gibi 0-1 değerler).
        """
        for ad in YUZ_RENKLER:
            sonuc[ad] = renk_karistir(b[ad], a[ad], k)
        yari = k < 0.5
        dip = max(0.08, abs(1 - 2 * k))
        sonuc["eye_shape"] = a["eye_shape"] if yari else b["eye_shape"]
        if a["eye_shape"] != b["eye_shape"]:
            sonuc["_eyeDip"] = dip
        sonuc["mouth"] = a["mouth"] if yari else b["mouth"]
        if a["mouth"] != b["mouth"]:
            sonuc["_mouthSq"] = dip
        for ad, anahtar in (("blush", "_blushA"), ("sweat", "_sweatA"),
                            ("anger_mark", "_angerA"), ("brow_show", "_browA")):
            x = 1.0 if a[ad] else 0.0
            y = 1.0 if b[ad] else 0.0
            alfa = x + (y - x) * k
            sonuc[anahtar] = alfa
            sonuc[ad] = alfa > 0.5

    @classmethod
    def yuz_ornekle(cls, klip: Klip, t_ms: float) -> Dict[str, Any]:
        """Klibin t_ms anındaki yüzünü döndürür (sayısal alanlar akıcı, şekil/renk alanları geçişli)."""
        kareler = klip.kareler
        i, s = cls._bul(kareler, t_ms)
        a = kareler[i]
        b = kareler[min(i + 1, len(kareler) - 1)]
        sonuc: Dict[str, Any] = {
            ad: cls._kirp(cls._sayi(kareler, i, s, ad, cls._yuz_al), aralik)
            for ad, aralik in YUZ_SAYISAL_SINIRLAR.items()
        }
        cls._ayrik_alanlari_karistir(sonuc, a.yuz, b.yuz, cls._gecis_katsayisi(b.gecis, s))
        return sonuc

    @classmethod
    def yuz_karistir(cls, a: Dict[str, Any], b: Dict[str, Any], k: float) -> Dict[str, Any]:
        """İki yüzü k (0-1) oranında karıştırır. Klip başlarken eski yüzden yeni yüze geçişte kullanılır."""
        sonuc: Dict[str, Any] = {}
        for ad, aralik in YUZ_SAYISAL_SINIRLAR.items():
            sonuc[ad] = cls._kirp(a[ad] + (b[ad] - a[ad]) * k, aralik)
        cls._ayrik_alanlari_karistir(sonuc, a, b, k)
        return sonuc
