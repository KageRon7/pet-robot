"""
Animasyon yolu.

Ne işe yarar: Router'ın animasyon istediği tek nokta. Duygu adını (ve beyin belirli bir klip
istediyse klip adını) HAL'a iletir. Seçim sırası:
  1. Beyin klip istediyse (Decision.clip) ve HAL o klibi biliyorsa o oynar.
  2. Aynı duygunun birden çok klibi varsa (curious, curious2, happy_2 ...) rastgele biri seçilir,
     arka arkaya aynı klip tekrarlanmaz. Eşleşme klip ADINA göredir (emotion alanına değil).
  3. Hiçbiri yoksa takma ad, o da yoksa idle.
Açılışta "gunaydin", kapanırken "iyi_geceler" klibi oynar (klip yoksa happy / sleepy).
klip_oynuyor(): kafa takibi, klip sürerken durmak için bunu sorar.

Güvenlik: klip yoksa ya da hata olursa program çökmez, idle'a döner.
"""

import asyncio
import json
import random
import re
import time
from pathlib import Path

from contracts import clip_id
from router.gun_zamani import donem
from router.hal import KonsolHAL

KLIP_KLASORU = Path(__file__).resolve().parent.parent / "motion" / "clips"

# HAL'ın klibi olmayan adlar için geçici eşleme (örn. simülatörde smile klibi yok).
TAKMA_AD = {"smile": "happy"}

# Açılış ve kapanış klipleri; klip henüz yoksa yedeği oynar. Tuğra klibi ekleyince kod değişmez.
# Açılış ve kapanış klipleri, döneme göre (gun_zamani.donem(): "gunduz" / "gece").
# Sıradaki ilk bilinen klip oynar; hiçbiri yoksa yedek duygu. Tuğra klip ekleyince sadece burası değişir.
# Açılış ve kapanış klipleri, döneme göre (gun_zamani.donem(): "gunduz" / "gece").
# Sıradaki ilk bilinen klip oynar; hiçbiri yoksa yedek duygu. Gece Günaydın oynamaz.
ACILIS_ADAYLARI = {
    "gunduz": ("gunaydin_gunduz", "gunaydin"),
    "gece": ("gunaydin_gece",),
}
ACILIS_YEDEK = {"gunduz": "happy", "gece": "sleepy"}
KAPANIS_ADAYLARI = {
    "gunduz": ("iyi_geceler_gunduz", "iyi_geceler"),
    "gece": ("iyi_geceler_gece", "iyi_geceler"),
}
KAPANIS_YEDEK = {"gunduz": "sleepy", "gece": "sleepy"}
KAPANIS_EN_FAZLA_S = 8.0  # kapanırken klibi en fazla bu kadar bekle
VARSAYILAN_KLIP_S = 4.0  # süresi bilinmeyen klip için
KLIP_PAYI_S = 0.3  # klip bittikten sonra kısa pay

_hal = KonsolHAL()
_son_secim: dict[str, str] = {}  # duygu -> en son seçilen klip (arka arkaya tekrarı önlemek için)
_sureler: dict[str, float] | None = None  # klip kimliği -> süre (sn), motion/clips'ten okunur
_klip_bitis = 0.0  # time.monotonic() cinsinden, şu an oynayan (idle dışı) klibin bitişi


def hal_ayarla(hal) -> None:
    """Demo ya da ana program hangi HAL'ın kullanılacağını buradan seçer."""
    global _hal
    _hal = hal


def hal_al():
    """Şu an seçili HAL (kafa takibi move komutu için ona ulaşır)."""
    return _hal


def klip_oynuyor(simdi: float | None = None) -> bool:
    """Idle dışı bir klip şu an oynuyor mu? (süre motion/clips'teki duration_ms'ten)"""
    simdi = time.monotonic() if simdi is None else simdi
    return simdi < _klip_bitis


def _klip_sureleri() -> dict[str, float]:
    global _sureler
    if _sureler is None:
        _sureler = {}
        for yol in KLIP_KLASORU.glob("*.json"):
            try:
                with open(yol, encoding="utf-8") as dosya:
                    ms = json.load(dosya).get("duration_ms")
                if ms:
                    _sureler[clip_id(yol.stem)] = float(ms) / 1000
            except (OSError, ValueError):
                pass
    return _sureler


def _klip_bitisini_ayarla(klip: str) -> None:
    global _klip_bitis
    if klip == "idle":
        _klip_bitis = 0.0
    else:
        sure = _klip_sureleri().get(clip_id(klip), VARSAYILAN_KLIP_S)
        _klip_bitis = time.monotonic() + sure + KLIP_PAYI_S


def istenen_klibi_bul(klip: str | None) -> str | None:
    """Beynin adıyla istediği klibi (B2 "clip") HAL'da arar; bulamazsa None döner.

    Önce adın kendisine, sonra kalıcı kimliğine bakar (simülatör dosya adını,
    ESP32 küçük harfli kimliği tanır). Bilinmeyen ad sadece loglanır, hata vermez.
    """
    if not klip:
        return None
    try:
        for aday in (klip, clip_id(klip)):
            if _hal.bilinen(aday):
                return aday
    except Exception as hata:
        print(f"[ANİMASYON] HATA: klip aranırken {hata!r}")
        return None
    print(f"[ANİMASYON] UYARI: '{klip}' adında klip yok, duyguya göre devam ediliyor")
    return None


def varyant_sec(duygu: str) -> str:
    """Duygunun klibini seçer. Kurallar:
      - Döneme özel klip varsa (sleepy_gece / sleepy_gunduz) o dönemde sadece o seçilir.
      - Yoksa eksiz klipler arasından seçilir (curious / curious2 / happy_2); öbür dönemin klibi seçilmez.
      - Birden çok aday varsa rastgele, art arda aynısı olmaz.
    HAL klip listesini vermiyorsa (klip_adlari yok) ya da hiç aday yoksa duygunun kendi adı döner.
    """
    fonksiyon = getattr(_hal, "klip_adlari", None)
    if fonksiyon is None:
        return duygu
    kalip = re.compile(re.escape(duygu) + r"(?:_(gece|gunduz))?(_?\d+)?")
    eslesenler = []  # (klip adı, dönem eki ya da None)
    for ad in fonksiyon():
        eslesme = kalip.fullmatch(ad)
        if eslesme:
            eslesenler.append((ad, eslesme.group(1)))
    d = donem()
    adaylar = sorted(ad for ad, ek in eslesenler if ek == d) or sorted(ad for ad, ek in eslesenler if ek is None)
    if not adaylar:
        return duygu
    if len(adaylar) > 1 and _son_secim.get(duygu) in adaylar:
        adaylar = [ad for ad in adaylar if ad != _son_secim[duygu]]
    secim = random.choice(adaylar)
    _son_secim[duygu] = secim
    return secim


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0, klip: str | None = None) -> None:
    """Duyguyu (ya da beynin adıyla istediği klibi) HAL'a oynatır; hata olursa idle'a döner."""
    gercek = ad
    try:
        gercek = istenen_klibi_bul(klip) or varyant_sec(ad)
        if not _hal.bilinen(gercek):
            gercek = varyant_sec(TAKMA_AD.get(ad, ad))  # HAL'ın klibi yoksa takma ad dene
        if not _hal.bilinen(gercek):
            print(f"[ANİMASYON] UYARI: '{ad}' için klip yok, idle'a dönülüyor")
            gercek = "idle"
        print(f"[ANİMASYON] {gercek:<9} kaynak={kaynak}")
        _klip_bitisini_ayarla(gercek)
        await _hal.duygu_oynat(gercek, kaynak, sure_s)
    except Exception as hata:
        print(f"[ANİMASYON] HATA: {hata!r}, idle'a dönülüyor")
        if gercek != "idle":
            try:
                _klip_bitisini_ayarla("idle")
                await _hal.duygu_oynat("idle", "hata", 0.0)
            except Exception as hata2:
                print(f"[ANİMASYON] idle de oynatılamadı: {hata2!r}")


async def _ozel_klip_oynat(adaylar: tuple[str, ...], yedek: str, kaynak: str) -> float:
    """Adaylardan ilk bilineni oynatır; hiçbiri yoksa yedek duyguyu. Süresini (sn) döndürür, hiçbiri yoksa 0."""
    for ad in adaylar:
        if _hal.bilinen(ad):
            await animasyon_oynat(ad, kaynak, klip=ad)
            return _klip_sureleri().get(clip_id(ad), VARSAYILAN_KLIP_S)
    print(f"[ANİMASYON] {', '.join(adaylar)} klibi yok, yerine '{yedek}' oynuyor")
    if not (_hal.bilinen(yedek) or getattr(_hal, "klip_adlari", None)):
        return 0.0
    await animasyon_oynat(yedek, kaynak)
    return _klip_sureleri().get(clip_id(_son_secim.get(yedek, yedek)), VARSAYILAN_KLIP_S)


async def acilis_oynat() -> None:
    """Program açılınca (döneme göre) açılış klibi. Gerçek robotta bağlantı kurulana kadar (en fazla 5 sn) bekler."""
    try:
        bekle = getattr(_hal, "baglanti_bekle", None)
        if bekle is not None:
            await bekle(5.0)
        d = donem()
        await _ozel_klip_oynat(ACILIS_ADAYLARI[d], ACILIS_YEDEK[d], "acilis")
    except Exception as hata:
        print(f"[ANİMASYON] açılış klibi oynatılamadı: {hata!r}")


async def kapat() -> None:
    """Program kapanırken İyi geceler klibi, sonra HAL'a haber (ESP32HAL nötr komutunu gönderir)."""
    kapat_fonksiyonu = getattr(_hal, "kapat", None)
    try:
        d = donem()
        sure = await _ozel_klip_oynat(KAPANIS_ADAYLARI[d], KAPANIS_YEDEK[d], "kapanis")
        if sure and kapat_fonksiyonu is not None:  # sadece gerçek robotta klibin bitmesini bekle
            await asyncio.sleep(min(sure, KAPANIS_EN_FAZLA_S))
    except Exception as hata:
        print(f"[ANİMASYON] kapanış klibi oynatılamadı: {hata!r}")
    if kapat_fonksiyonu is not None:
        await asyncio.to_thread(kapat_fonksiyonu)