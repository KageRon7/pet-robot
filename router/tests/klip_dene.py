"""
Ne işe yarar: Verilen duyguyu hemen oynatır (olay beklemeden).
Nasıl çalıştırılır (ana klasörden):
    python -m router.tests.klip_dene happy            # simülatör penceresinde
    python -m router.tests.klip_dene happy --esp32    # Wokwi'deki ESP32'de (Wokwi açık olmalı)
Duygu adı yazılmazsa idle oynar.
"""

import asyncio
import sys
import threading

from router import animasyon


def pencereli(ad: str) -> None:
    from router.hal import simulator_penceresi_kur

    async def calis() -> None:
        await animasyon.animasyon_oynat(ad, kaynak="test")
        await asyncio.sleep(20)  # klip oynarken loop açık kalsın

    kok, hal = simulator_penceresi_kur()
    animasyon.hal_ayarla(hal)
    threading.Thread(target=lambda: asyncio.run(calis()), daemon=True).start()
    kok.mainloop()


def esp32de(ad: str) -> None:
    from router.hal import ESP32HAL

    async def calis() -> None:
        hal = ESP32HAL()
        animasyon.hal_ayarla(hal)
        await asyncio.sleep(1.5)  # bağlantı kurulsun
        await animasyon.animasyon_oynat(ad, kaynak="test")
        await asyncio.sleep(12)
        await animasyon.kapat()  # nötr komutu gider

    asyncio.run(calis())


if __name__ == "__main__":
    argumanlar = [a for a in sys.argv[1:] if not a.startswith("--")]
    ad = argumanlar[0] if argumanlar else "idle"
    if "--esp32" in sys.argv:
        esp32de(ad)
    else:
        pencereli(ad)