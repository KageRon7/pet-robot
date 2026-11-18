"""
Gün zamanı: gece mi gündüz mü? (yatsıdan sonra sabah namazına kadar gece, geri kalanı gündüz)

Ne işe yarar: router'ın klip seçimi bunu sorar (sleepy_gece / sleepy_gunduz gibi klipler için).
İmsak (sabah namazı) ve yatsı vakitleri güneşin konumundan hesaplanır (Diyanet açıları: imsak 18°, yatsı 17°),
Türkiye sabit UTC+3. Hesap Diyanet'in tablosundan birkaç dakika sapabilir.
Tam vakitler istenirse router/vakitler.json yazılır, varsa hesabın önüne geçer:
    {"2026-11-16": {"imsak": "06:18", "yatsi": "19:20"}}

Test için ortam değişkeni: KEDI_DONEM=gece  ya da  KEDI_DONEM=gunduz  (ne saat olursa olsun o dönem sayılır).
"""

import json
import math
import os
from datetime import date, datetime
from pathlib import Path

# Soma, Manisa. Robot başka bir şehirde gösterilecekse değiştir.
ENLEM = 39.1853
BOYLAM = 27.6097
UTC_FARKI_SAAT = 3.0  # Türkiye yıl boyunca UTC+3
IMSAK_ACISI = 18.0
YATSI_ACISI = 17.0
YEDEK_IMSAK_DK = 5 * 60 + 30  # hesap yapılamazsa (kutup bölgesi gibi) sabit değerler
YEDEK_YATSI_DK = 20 * 60
VAKIT_DOSYASI = Path(__file__).resolve().parent / "vakitler.json"


def _sin(d: float) -> float:
    return math.sin(math.radians(d))


def _cos(d: float) -> float:
    return math.cos(math.radians(d))


def _julian(gun: date) -> float:
    """Günün 00:00 UT'sindeki Jülyen gün sayısı."""
    y, m = gun.year, gun.month
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + gun.day + b - 1524.5


def _gunes(jd: float) -> tuple[float, float]:
    """Güneşin (sapma açısı derece, zaman denklemi saat) değeri."""
    d = jd - 2451545.0
    g = (357.529 + 0.98560028 * d) % 360
    q = (280.459 + 0.98564736 * d) % 360
    boylam = (q + 1.915 * _sin(g) + 0.020 * _sin(2 * g)) % 360
    egiklik = 23.439 - 0.00000036 * d
    sag_yukselim = math.degrees(math.atan2(_cos(egiklik) * _sin(boylam), _cos(boylam))) / 15
    sag_yukselim %= 24
    zaman_denklemi = ((q / 15 - sag_yukselim + 12) % 24) - 12
    sapma = math.degrees(math.asin(_sin(egiklik) * _sin(boylam)))
    return sapma, zaman_denklemi


def _vakit_dk(gun: date) -> tuple[float, float]:
    """Günün (imsak, yatsı) vakti, gece yarısından beri dakika."""
    jd = _julian(gun) + 0.5 - BOYLAM / 360
    sapma, zaman_denklemi = _gunes(jd)
    ogle = 12 + UTC_FARKI_SAAT - BOYLAM / 15 - zaman_denklemi

    def saat_acisi(aci: float) -> float | None:
        pay = -_sin(aci) - _sin(sapma) * _sin(ENLEM)
        payda = _cos(sapma) * _cos(ENLEM)
        oran = pay / payda
        if not -1.0 <= oran <= 1.0:
            return None
        return math.degrees(math.acos(oran)) / 15

    imsak_t, yatsi_t = saat_acisi(IMSAK_ACISI), saat_acisi(YATSI_ACISI)
    if imsak_t is None or yatsi_t is None:
        return YEDEK_IMSAK_DK, YEDEK_YATSI_DK
    return (ogle - imsak_t) * 60, (ogle + yatsi_t) * 60


def _dosyadan(gun: date) -> tuple[float, float] | None:
    try:
        with open(VAKIT_DOSYASI, encoding="utf-8") as dosya:
            kayit = json.load(dosya).get(gun.isoformat())
        if not kayit:
            return None

        def dakika(metin: str) -> float:
            saat, dk = metin.split(":")
            return int(saat) * 60 + int(dk)

        return dakika(kayit["imsak"]), dakika(kayit["yatsi"])
    except (OSError, ValueError, KeyError, AttributeError):
        return None


def vakitler(gun: date) -> tuple[float, float]:
    """Günün (imsak, yatsı) vakti (dakika). Önce vakitler.json, yoksa hesap."""
    return _dosyadan(gun) or _vakit_dk(gun)


def donem(simdi: datetime | None = None) -> str:
    """'gece' (yatsıdan sonra sabah namazına kadar) ya da 'gunduz' döndürür."""
    zorla = os.environ.get("KEDI_DONEM", "").strip().lower()
    if zorla in ("gece", "gunduz"):
        return zorla
    simdi = simdi or datetime.now()
    dakika = simdi.hour * 60 + simdi.minute + simdi.second / 60
    imsak, yatsi = vakitler(simdi.date())
    return "gece" if dakika < imsak or dakika >= yatsi else "gunduz"