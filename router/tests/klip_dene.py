"""
Ne işe yarar: Verilen duyguyu simülatör penceresinde hemen oynatır (olay beklemeden).
Nasıl çalıştırılır (ana klasörden): python -m router.tests.klip_dene happy
Duygu adı yazılmazsa idle oynar.
"""

import asyncio
import sys
import threading

from router import animasyon
from router.hal import simulator_penceresi_kur


def arka_planda(ad: str) -> None:
    async def calis() -> None:
        await animasyon.animasyon_oynat(ad, kaynak="test")
        await asyncio.sleep(20)  # klip oynarken loop açık kalsın

    asyncio.run(calis())


if __name__ == "__main__":
    ad = sys.argv[1] if len(sys.argv) > 1 else "idle"
    kok, hal = simulator_penceresi_kur()
    animasyon.hal_ayarla(hal)
    threading.Thread(target=arka_planda, args=(ad,), daemon=True).start()
    kok.mainloop()