import asyncio
import time

from router.animasyon import animasyon_oynat
from router.beyin_istemcisi import BaglamTutucu, beyne_sor
from tools.fake_events import SahteOlayUreteci

# REFLEKS TABLOSU: olay -> (animasyon, süre sn). Beyne sormadan hemen oynar.
REFLEKS_TABLOSU = {
    "user_arrived": ("idle", 0.0),
    "smile": ("smile", 1.5),
}

# Arka plandaki beyin görevleri; referansı tutmazsak Python görevi silebilir.
ARKA_GOREVLER: set[asyncio.Task] = set()


def ad_al(deger) -> str:
    # Enum ise içindeki yazıyı, değilse kendisini döndürür.
    return str(getattr(deger, "value", deger))


def arka_planda(coro) -> None:
    gorev = asyncio.create_task(coro)
    ARKA_GOREVLER.add(gorev)
    gorev.add_done_callback(ARKA_GOREVLER.discard)


async def sor_ve_oyna(baglam_nesnesi) -> None:
    # Beyne sorar; cevap gelirse karar animasyonunu oynatır, gelmezse refleksle devam.
    cevap = await beyne_sor(baglam_nesnesi)
    if cevap is None:
        return
    try:
        duygu = str(cevap["emotion"])
        sure = float(cevap["duration_s"])
        sebep = cevap.get("reason", "")
    except (KeyError, TypeError, ValueError, AttributeError) as hata:
        # Saçma cevap: çökme, idle oynat ve devam et.
        print(f"[ROUTER] saçma cevap {cevap!r} ({hata!r}), idle'a dönülüyor")
        await animasyon_oynat("idle", kaynak="hata")
        return
    print(f"[ROUTER] karar     <- {duygu} ({sebep})")
    await animasyon_oynat(duygu, kaynak="karar", sure_s=sure)

async def mesaji_isle(mesaj, baglam: BaglamTutucu) -> None:
    if mesaj.kanal == "A2":
        olay = mesaj.veri.event
        ad = ad_al(olay)
        simdi = time.time()
        baglam.olay_ekle(olay, simdi)

        # 1) REFLEKS: beklemeden oynar
        if ad in REFLEKS_TABLOSU:
            animasyon, sure = REFLEKS_TABLOSU[ad]
            print(f"[ROUTER] refleks   <- {ad}")
            await animasyon_oynat(animasyon, kaynak="refleks", sure_s=sure)

        # 2) BEYİN: refleksten sonra aynı olay için soru gider, router beklemez
        print(f"[ROUTER] beyne soruluyor <- {ad}")
        arka_planda(sor_ve_oyna(baglam.olustur(simdi)))


async def router(kuyruk: asyncio.Queue) -> None:
    baglam = BaglamTutucu()
    while True:
        mesaj = await kuyruk.get()
        try:
            await mesaji_isle(mesaj, baglam)
        except Exception as hata:
            # Tek bir bozuk mesaj router'ı çökertmesin; kedi idle'a dönsün.
            print(f"[ROUTER] HATA: {hata!r}, idle'a dönülüyor")
            await animasyon_oynat("idle", kaynak="hata")
        finally:
            kuyruk.task_done()


async def main(sure_s: float = 15, hiz: float = 20) -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    uretec = SahteOlayUreteci(tohum=42, hiz=hiz, kanallar=("A2",))
    gorevler = [
        asyncio.create_task(uretec.kuyruga_aktar(kuyruk, sure_s=300)),
        asyncio.create_task(router(kuyruk)),
    ]
    try:
        await asyncio.sleep(sure_s)
    finally:
        for g in gorevler:
            g.cancel()
        await asyncio.gather(*gorevler, return_exceptions=True)


if __name__ == "__main__":
    import sys

    if "--pencere" in sys.argv:
        # Simülatör penceresiyle, gerçek zamanlı. Tkinter ana thread'de, asyncio arka planda.
        import threading
        import tkinter as tk

        from motion.simulator2 import KediSimulatoru
        from router import animasyon
        from router.hal import SimulatorHAL

        kok = tk.Tk()
        simulator = KediSimulatoru(kok)
        animasyon.hal_ayarla(SimulatorHAL(simulator, kok))
        threading.Thread(target=lambda: asyncio.run(main(sure_s=120, hiz=1)), daemon=True).start()
        kok.mainloop()
    else:
        asyncio.run(main())