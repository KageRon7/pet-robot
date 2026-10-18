import asyncio

from router.animasyon import animasyon_oynat
from tools.fake_events import SahteOlayUreteci

# Router'ın beyne sormadan kendisi halledeceği olaylar (refleks).
REFLEKS_OLAYLARI = {"user_arrived"}


def ad_al(deger) -> str:
    # Enum ise içindeki yazıyı, değilse kendisini döndürür.
    return str(getattr(deger, "value", deger))


async def router(kuyruk: asyncio.Queue) -> None:
    while True:
        mesaj = await kuyruk.get()

        if mesaj.kanal == "A2":
            olay = ad_al(mesaj.veri.event)
            if olay in REFLEKS_OLAYLARI:
                # REFLEKS YOLU: beklemeden idle animasyonu
                print(f"[ROUTER] refleks   <- {olay}")
                await animasyon_oynat("idle", kaynak="refleks")
            else:
                # Gerçek sistemde burada B1 bağlamı beyne gönderilecek (Faz 2).
                print(f"[ROUTER] beyne soruluyor <- {olay}")

        elif mesaj.kanal == "B2":
            # KARAR YOLU: beynin kararı gelince duygusuna göre animasyon
            karar = mesaj.veri
            duygu = ad_al(karar.emotion)
            print(f"[ROUTER] karar     <- {duygu} ({karar.reason})")
            await animasyon_oynat(duygu, kaynak="karar", sure_s=karar.duration_s)

        kuyruk.task_done()


async def main() -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    uretec = SahteOlayUreteci(tohum=42, hiz=20, kanallar=("A2", "B2"))
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