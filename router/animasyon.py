"""
Animasyon yolu (taslak).

Ne işe yarar: Router'ın animasyon istediği tek nokta burası.
Şimdilik sadece ekrana yazar. Animasyon sistemi hazır olunca
_oynat içini HAL / klip seçici çağrısıyla değiştir, router koduna dokunma.

Güvenlik: bilinmeyen bir ad gelirse ya da oynatma hata verirse program
çökmez, idle'a döner.
"""

# Animasyon sistemindeki bilinen adlar. Yeni klip eklenince buraya da ekle.
BILINEN = {"idle", "smile", "happy", "sad", "sleepy", "curious", "playful", "startled"}


async def _oynat(ad: str, kaynak: str, sure_s: float) -> None:
    # İleride burası gerçek animasyon / klip çağrısı olacak.
    print(f"[ANİMASYON] {ad:<9} kaynak={kaynak}  süre={sure_s}s")


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0) -> None:
    if ad not in BILINEN:
        print(f"[ANİMASYON] UYARI: bilinmeyen '{ad}', idle'a dönülüyor")
        ad, sure_s = "idle", 0.0
    try:
        await _oynat(ad, kaynak, sure_s)
    except Exception as hata:
        print(f"[ANİMASYON] HATA: {hata!r}, idle'a dönülüyor")
        if ad != "idle":
            await _oynat("idle", "hata", 0.0)