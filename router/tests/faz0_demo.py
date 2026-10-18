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
    print(f"[ROUTER] karar     <- {cevap['emotion']} ({cevap['reason']})")
    await animasyon_oynat(cevap["emotion"], kaynak="karar", sure_s=cevap["duration_s"])


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


async def main() -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    # Sahte üretecin B2 kararları kapalı: karar artık sahte beyinden (decide) geliyor.
    uretec = SahteOlayUreteci(tohum=42, hiz=20, kanallar=("A2",))
    gorevler = [
        asyncio.create_task(uretec.kuyruga_aktar(kuyruk, sure_s=300)),
        asyncio.create_task(router(kuyruk)),
    ]
    try:
        await asyncio.sleep(15)  # demo: 15 sn çalış
    finally:
        for g in gorevler:
            g.cancel()
        await asyncio.gather(*gorevler, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())