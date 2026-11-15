"""
Animasyon yolu.

Ne işe yarar: Router'ın animasyon istediği tek nokta. Duygu adını HAL'a iletir;
klibi bulup oynatmak HAL'ın (simülatör ya da ESP32) işi, süreyi klip belirler.
Yeni animasyon gelince eskisi kesilir.

Güvenlik: klibi olmayan duygu ya da hata olursa program çökmez, idle'a döner.
"""

import asyncio

from contracts import clip_id
from router.hal import KonsolHAL

# HAL'ın klibi olmayan adlar için geçici eşleme (örn. simülatörde smile klibi yok).
TAKMA_AD = {"smile": "happy"}

_hal = KonsolHAL()


def hal_ayarla(hal) -> None:
    """Demo ya da ana program hangi HAL'ın kullanılacağını buradan seçer."""
    global _hal
    _hal = hal


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


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0, klip: str | None = None) -> None:
    """Duyguyu (ya da beynin adıyla istediği klibi) HAL'a oynatır; hata olursa idle'a döner.

    klip boşsa ya da bilinmiyorsa eskisi gibi duygu adına göre oynatılır.
    """
    gercek = istenen_klibi_bul(klip) or ad
    try:
        if not _hal.bilinen(gercek):
            gercek = TAKMA_AD.get(ad, ad)  # HAL'ın klibi yoksa takma ad dene
        if not _hal.bilinen(gercek):
            print(f"[ANİMASYON] UYARI: '{ad}' için klip yok, idle'a dönülüyor")
            gercek = "idle"
        print(f"[ANİMASYON] {gercek:<9} kaynak={kaynak}")
        await _hal.duygu_oynat(gercek, kaynak, sure_s)
    except Exception as hata:
        print(f"[ANİMASYON] HATA: {hata!r}, idle'a dönülüyor")
        if gercek != "idle":
            try:
                await _hal.duygu_oynat("idle", "hata", 0.0)
            except Exception as hata2:
                print(f"[ANİMASYON] idle de oynatılamadı: {hata2!r}")


async def kapat() -> None:
    """Program kapanırken HAL'a haber verir (ESP32HAL nötr komutunu burada gönderir)."""
    kapat_fonksiyonu = getattr(_hal, "kapat", None)
    if kapat_fonksiyonu is not None:
        await asyncio.to_thread(kapat_fonksiyonu)