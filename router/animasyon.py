"""
Animasyon yolu.

Ne iÅŸe yarar: Router'Ä±n animasyon istediÄŸi tek nokta. Duygu adÄ±nÄ± (ve beyin belirli bir klip
istediyse klip adÄ±nÄ±) HAL'a iletir. SeÃ§im sÄ±rasÄ±:
  1. Beyin klip istediyse (Decision.clip) ve HAL o klibi biliyorsa o oynar.
  2. AynÄ± duygunun birden Ã§ok klibi varsa (curious, curious2, happy_2 ...) rastgele biri seÃ§ilir,
     arka arkaya aynÄ± klip tekrarlanmaz. EÅŸleÅŸme klip ADINA gÃ¶redir (emotion alanÄ±na deÄŸil).
  3. HiÃ§biri yoksa takma ad, o da yoksa idle.
AÃ§Ä±lÄ±ÅŸta "gunaydin", kapanÄ±rken "iyi_geceler" klibi oynar (klip yoksa happy / sleepy).
klip_oynuyor(): kafa takibi, klip sÃ¼rerken durmak iÃ§in bunu sorar.

GÃ¼venlik: klip yoksa ya da hata olursa program Ã§Ã¶kmez, idle'a dÃ¶ner.
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

# HAL'Ä±n klibi olmayan adlar iÃ§in geÃ§ici eÅŸleme (Ã¶rn. simÃ¼latÃ¶rde smile klibi yok).
TAKMA_AD = {"smile": "happy"}

# AÃ§Ä±lÄ±ÅŸ ve kapanÄ±ÅŸ klipleri; klip henÃ¼z yoksa yedeÄŸi oynar. TuÄŸra klibi ekleyince kod deÄŸiÅŸmez.
# AÃ§Ä±lÄ±ÅŸ ve kapanÄ±ÅŸ klipleri, dÃ¶neme gÃ¶re (gun_zamani.donem(): "gunduz" / "gece").
# SÄ±radaki ilk bilinen klip oynar; hiÃ§biri yoksa yedek duygu. TuÄŸra klip ekleyince sadece burasÄ± deÄŸiÅŸir.
# AÃ§Ä±lÄ±ÅŸ ve kapanÄ±ÅŸ klipleri, dÃ¶neme gÃ¶re (gun_zamani.donem(): "gunduz" / "gece").
# SÄ±radaki ilk bilinen klip oynar; hiÃ§biri yoksa yedek duygu. Gece GÃ¼naydÄ±n oynamaz.
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
KAPANIS_EN_FAZLA_S = 8.0  # kapanÄ±rken klibi en fazla bu kadar bekle
VARSAYILAN_KLIP_S = 4.0  # sÃ¼resi bilinmeyen klip iÃ§in
KLIP_PAYI_S = 0.3  # klip bittikten sonra kÄ±sa pay

_hal = KonsolHAL()
_son_secim: dict[str, str] = {}  # duygu -> en son seÃ§ilen klip (arka arkaya tekrarÄ± Ã¶nlemek iÃ§in)
_sureler: dict[str, float] | None = None  # klip kimliÄŸi -> sÃ¼re (sn), motion/clips'ten okunur
_klip_bitis = 0.0  # time.monotonic() cinsinden, ÅŸu an oynayan (idle dÄ±ÅŸÄ±) klibin bitiÅŸi


def hal_ayarla(hal) -> None:
    """Demo ya da ana program hangi HAL'Ä±n kullanÄ±lacaÄŸÄ±nÄ± buradan seÃ§er."""
    global _hal
    _hal = hal


def hal_al():
    """Å�u an seÃ§ili HAL (kafa takibi move komutu iÃ§in ona ulaÅŸÄ±r)."""
    return _hal


def klip_oynuyor(simdi: float | None = None) -> bool:
    """Idle dÄ±ÅŸÄ± bir klip ÅŸu an oynuyor mu? (sÃ¼re motion/clips'teki duration_ms'ten)"""
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
    """Beynin adÄ±yla istediÄŸi klibi (B2 "clip") HAL'da arar; bulamazsa None dÃ¶ner.

    Ã–nce adÄ±n kendisine, sonra kalÄ±cÄ± kimliÄŸine bakar (simÃ¼latÃ¶r dosya adÄ±nÄ±,
    ESP32 kÃ¼Ã§Ã¼k harfli kimliÄŸi tanÄ±r). Bilinmeyen ad sadece loglanÄ±r, hata vermez.
    """
    if not klip:
        return None
    try:
        for aday in (klip, clip_id(klip)):
            if _hal.bilinen(aday):
                return aday
    except Exception as hata:
        print(f"[ANÄ°MASYON] HATA: klip aranÄ±rken {hata!r}")
        return None
    print(f"[ANÄ°MASYON] UYARI: '{klip}' adÄ±nda klip yok, duyguya gÃ¶re devam ediliyor")
    return None


def varyant_sec(duygu: str) -> str:
    """Duygunun klibini seÃ§er. Kurallar:
      - DÃ¶neme Ã¶zel klip varsa (sleepy_gece / sleepy_gunduz) o dÃ¶nemde sadece o seÃ§ilir.
      - Yoksa eksiz klipler arasÄ±ndan seÃ§ilir (curious / curious2 / happy_2); Ã¶bÃ¼r dÃ¶nemin klibi seÃ§ilmez.
      - Birden Ã§ok aday varsa rastgele, art arda aynÄ±sÄ± olmaz.
    HAL klip listesini vermiyorsa (klip_adlari yok) ya da hiÃ§ aday yoksa duygunun kendi adÄ± dÃ¶ner.
    """
    fonksiyon = getattr(_hal, "klip_adlari", None)
    if fonksiyon is None:
        return duygu
    kalip = re.compile(re.escape(duygu) + r"(?:_(gece|gunduz))?(_?\d+)?")
    eslesenler = []  # (klip adÄ±, dÃ¶nem eki ya da None)
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
    """Duyguyu (ya da beynin adÄ±yla istediÄŸi klibi) HAL'a oynatÄ±r; hata olursa idle'a dÃ¶ner."""
    gercek = ad
    try:
        gercek = istenen_klibi_bul(klip) or varyant_sec(ad)
        if not _hal.bilinen(gercek):
            gercek = varyant_sec(TAKMA_AD.get(ad, ad))  # HAL'Ä±n klibi yoksa takma ad dene
        if not _hal.bilinen(gercek):
            print(f"[ANÄ°MASYON] UYARI: '{ad}' iÃ§in klip yok, idle'a dÃ¶nÃ¼lÃ¼yor")
            gercek = "idle"
        print(f"[ANÄ°MASYON] {gercek:<9} kaynak={kaynak}")
        _klip_bitisini_ayarla(gercek)
        await _hal.duygu_oynat(gercek, kaynak, sure_s)
    except Exception as hata:
        print(f"[ANÄ°MASYON] HATA: {hata!r}, idle'a dÃ¶nÃ¼lÃ¼yor")
        if gercek != "idle":
            try:
                _klip_bitisini_ayarla("idle")
                await _hal.duygu_oynat("idle", "hata", 0.0)
            except Exception as hata2:
                print(f"[ANÄ°MASYON] idle de oynatÄ±lamadÄ±: {hata2!r}")


async def _ozel_klip_oynat(adaylar: tuple[str, ...], yedek: str, kaynak: str) -> float:
    """Adaylardan ilk bilineni oynatÄ±r; hiÃ§biri yoksa yedek duyguyu. SÃ¼resini (sn) dÃ¶ndÃ¼rÃ¼r, hiÃ§biri yoksa 0."""
    for ad in adaylar:
        if _hal.bilinen(ad):
            await animasyon_oynat(ad, kaynak, klip=ad)
            return _klip_sureleri().get(clip_id(ad), VARSAYILAN_KLIP_S)
    print(f"[ANÄ°MASYON] {', '.join(adaylar)} klibi yok, yerine '{yedek}' oynuyor")
    if not (_hal.bilinen(yedek) or getattr(_hal, "klip_adlari", None)):
        return 0.0
    await animasyon_oynat(yedek, kaynak)
    return _klip_sureleri().get(clip_id(_son_secim.get(yedek, yedek)), VARSAYILAN_KLIP_S)


async def acilis_oynat() -> None:
    """Program aÃ§Ä±lÄ±nca (dÃ¶neme gÃ¶re) aÃ§Ä±lÄ±ÅŸ klibi. GerÃ§ek robotta baÄŸlantÄ± kurulana kadar (en fazla 5 sn) bekler."""
    try:
        bekle = getattr(_hal, "baglanti_bekle", None)
        if bekle is not None:
            await bekle(5.0)
        d = donem()
        await _ozel_klip_oynat(ACILIS_ADAYLARI[d], ACILIS_YEDEK[d], "acilis")
    except Exception as hata:
        print(f"[ANÄ°MASYON] aÃ§Ä±lÄ±ÅŸ klibi oynatÄ±lamadÄ±: {hata!r}")


async def kapat() -> None:
    """Program kapanÄ±rken Ä°yi geceler klibi, sonra HAL'a haber (ESP32HAL nÃ¶tr komutunu gÃ¶nderir)."""
    kapat_fonksiyonu = getattr(_hal, "kapat", None)
    try:
        d = donem()
        sure = await _ozel_klip_oynat(KAPANIS_ADAYLARI[d], KAPANIS_YEDEK[d], "kapanis")
        if sure and kapat_fonksiyonu is not None:  # sadece gerÃ§ek robotta klibin bitmesini bekle
            await asyncio.sleep(min(sure, KAPANIS_EN_FAZLA_S))
    except Exception as hata:
        print(f"[ANÄ°MASYON] kapanÄ±ÅŸ klibi oynatÄ±lamadÄ±: {hata!r}")
    if kapat_fonksiyonu is not None:
        await asyncio.to_thread(kapat_fonksiyonu)