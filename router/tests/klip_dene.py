"""
Ne işe yarar: Verilen klibi simülatör penceresinde hemen oynatır (olay beklemeden).
Nasıl çalıştırılır (ana klasörden): python -m router.tests.klip_dene happy
Klip adı yazılmazsa idle oynar.
"""

import asyncio
import sys
import threading
import tkinter as tk

from motion.simulator2 import KediSimulatoru
from router import animasyon
from router.hal import SimulatorHAL


def arka_planda(ad: str) -> None:
    async def calis() -> None:
        await animasyon.animasyon_oynat(ad, kaynak="test", sure_s=0)
        await asyncio.sleep(20)  # klip oynarken loop açık kalsın

    asyncio.run(calis())


if __name__ == "__main__":
    ad = sys.argv[1] if len(sys.argv) > 1 else "idle"
    kok = tk.Tk()
    simulator = KediSimulatoru(kok)
    animasyon.hal_ayarla(SimulatorHAL(simulator, kok))
    threading.Thread(target=arka_planda, args=(ad,), daemon=True).start()
    kok.mainloop()