"""
Animasyon yolu (taslak).

Ne işe yarar: Router'ın animasyon istediği tek nokta burası.
Şimdilik sadece ekrana yazar. Animasyon sistemi hazır olunca
animasyon_oynat içini HAL çağrısıyla değiştir, router koduna dokunma.
"""


async def animasyon_oynat(ad: str, kaynak: str, sure_s: float = 0.0) -> None:
    print(f"[ANİMASYON] {ad:<9} kaynak={kaynak}  süre={sure_s}s")