"""
Animasyon yolu.

Ne işe yarar: Router'ın animasyon istediği tek nokta. Duygu adına göre
motion/clips klasöründen klibi seçer ve pose anahtarlarını HAL'a sırayla
gönderir. Oynatma arka planda yapılır, animasyon_oynat hemen döner.
Yeni animasyon gelince eskisi kesilir.

Güvenlik: klip yoksa ya da bozuksa program çökmez, idle'a döner.
"""

import asyncio
import json
import time
from pathlib import Path

from router.hal import KonsolHAL

# router/animasyon.py -> repo kökü -> motion/clips
KLIP_KLASORU = Path(__file__).resolve().parent.parent / "motion" / "clips"

# Klibi henüz olmayan adlar için geçici eşleme. smile klibi gelince sil.
TAKMA_AD = {"smile": "happy"}

POZ_EKLEMLERI = ("body_yaw", "head_pan", "head_tilt", "ear_left", "ear_right")
ILK_GECIS_MS = 300  # klibin ilk pozuna yumuşak geçiş


def klipleri_tara() -> dict[str, Path]:
    """motion/clips içindeki her .json dosyasını ada göre listeler (dosya adı = klip adı)."""
    return {yol.stem: yol for yol in KLIP_KLASORU.glob("*.json")}


KLIPLER = klipleri_tara()
if "idle" not in KLIPLER:
    print(f"[ANİMASYON] UYARI: idle klibi bulunamadı, aranan klasör: {KLIP_KLASORU}")

_hal = KonsolHAL()
_mevcut: asyncio.Task | None = None
_gorevler: set[asyncio.Task] = set()  # referans tut, görevler silinmesin


def hal_ayarla(hal) -> None:
    """Demo ya da ana program hangi HAL'ın kullanılacağını buradan seçer."""
    global _hal
    _hal = hal


def _klibi_oku(yol: Path):
    with open(yol, encoding="utf-8") as dosya:
        return json.load(dosya)


async def _klibi_cal(ad: str, kaynak: str, sure_s: float) -> None:
    yol = KLIPLER[ad]
    klip = await asyncio.to_thread(_klibi_oku, yol)  # bozuk JSON burada hata verir
    anahtarlar = klip["keys"]
    print(f"[ANİMASYON] {ad:<9} klip={yol.name}  kaynak={kaynak}  süre={sure_s}s")

    baslangic = time.monotonic()
    while True:
        onceki_t = 0
        for i, anahtar in enumerate(anahtarlar):
            gecis_ms = ILK_GECIS_MS if i == 0 else max(anahtar["t_ms"] - onceki_t, 0)
            poz = {k: v for k, v in anahtar.get("pose", {}).items() if k in POZ_EKLEMLERI}
            await _hal.pose_gonder(poz, gecis_ms)
            await asyncio.sleep(gecis_ms / 1000)
            onceki_t = anahtar["t_ms"]
        # Döngülü klip, istenen süre dolana kadar tekrarlanır; değilse bir kez oynar.
        if not (klip.get("loop") and time.monotonic() - baslangic < sure_s):
            break


async def _guvenli_cal(ad: str, kaynak: str, sure_s: float) -> None:
    try:
        await _klibi_cal(ad, kaynak, sure_s)
    except asyncio.CancelledError:
        raise  # yeni animasyon geldi, normal
    except Exception as hata:
        print(f"[ANİMASYON] HATA: {hata!r}, idle'a dönülüyor")
        if ad != "idle" and "idle" in KLIPLER:
            try:
                await _klibi_cal("idle", "hata", 0.0)
            except Exception as hata2:
                print(f"[ANİMASYON] idle de oynatılamadı: {hata2!r}")


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0) -> None:
    """Animasyonu başlatır ve hemen döner. Önceki animasyon varsa keser."""
    global _mevcut
    gercek = TAKMA_AD.get(ad, ad)
    if gercek not in KLIPLER:
        print(f"[ANİMASYON] UYARI: '{ad}' için klip yok, idle'a dönülüyor")
        gercek, sure_s = "idle", 0.0
        if gercek not in KLIPLER:
            return
    if _mevcut is not None and not _mevcut.done():
        _mevcut.cancel()
    _mevcut = asyncio.create_task(_guvenli_cal(gercek, kaynak, sure_s))
    _gorevler.add(_mevcut)
    _mevcut.add_done_callback(_gorevler.discard)