"""Beynin adıyla klip isteyebilmesi (B2 "clip") için router testleri. Çalıştırmak: python -m pytest"""

import asyncio

from router import animasyon


class SahteHAL:
    """Sadece verilen adları tanıyan, oynatılanları listeye yazan sahte HAL."""

    # Tanıdığı klip adlarını alır; oynatılanları self.oynananlar listesinde tutar.
    def __init__(self, adlar: set[str]) -> None:
        self._adlar = adlar
        self.oynananlar: list[str] = []

    # Bu adda bir klip var mı?
    def bilinen(self, ad: str) -> bool:
        return ad in self._adlar

    # Klibi "oynatır": sadece adını kaydeder.
    async def duygu_oynat(self, ad: str, kaynak: str, sure_s: float) -> None:
        self.oynananlar.append(ad)


# Testte sahte HAL'ı kurar, bir animasyon ister ve neyin oynatıldığını döner.
def _oynat(adlar: set[str], duygu: str, klip: str | None) -> list[str]:
    hal = SahteHAL(adlar)
    animasyon.hal_ayarla(hal)
    asyncio.run(animasyon.animasyon_oynat(duygu, kaynak="test", klip=klip))
    return hal.oynananlar


# Klip istenmezse eskisi gibi duygunun klibi oynar.
def test_klip_yoksa_duygu_oynar():
    assert _oynat({"happy", "hapsirma"}, "happy", None) == ["happy"]


# Bilinen klip istenirse o klip oynar.
def test_bilinen_klip_oynar():
    assert _oynat({"happy", "hapsirma"}, "happy", "hapsirma") == ["hapsirma"]


# ESP32 küçük harfli kimliği tanır: dosya adı yazılsa da bulunur.
def test_klip_kimligiyle_bulunur():
    assert _oynat({"playful", "head_explosion_buum"}, "playful", "Head_Explosion(BuUM)") == [
        "head_explosion_buum"
    ]


# Bilinmeyen klip yok sayılır, sistem durmaz, duyguya göre devam eder.
def test_bilinmeyen_klip_duyguya_duser():
    assert _oynat({"happy"}, "happy", "uydurma_klip") == ["happy"]
