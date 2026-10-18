"""
Animasyon yolu.

Ne işe yarar: Router'ın animasyon istediği tek nokta. Duygu adını HAL'a iletir;
klibi bulup oynatmak (yüz + motorlar) simülatörün işi, süreyi klip belirler.
Yeni animasyon gelince eskisi kesilir.

Güvenlik: klibi olmayan duygu ya da hata olursa program çökmez, idle'a döner.
"""

from router.hal import KonsolHAL

# Klibi henüz olmayan adlar için geçici eşleme. smile klibi gelince sil.
TAKMA_AD = {"smile": "happy"}

_hal = KonsolHAL()


def hal_ayarla(hal) -> None:
    """Demo ya da ana program hangi HAL'ın kullanılacağını buradan seçer."""
    global _hal
    _hal = hal


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0) -> None:
    gercek = TAKMA_AD.get(ad, ad)
    try:
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