import asyncio

from router.animasyon import animasyon_oynat
from tools.fake_events import SahteOlayUreteci

# REFLEKS TABLOSU (bu bölüm router'ın, yani senin): olay -> (animasyon, süre sn)
# Olay gelince beyne sormadan hemen oynar.
REFLEKS_TABLOSU = {
    "user_arrived": ("idle", 0.0),
    "smile": ("smile", 1.5),  # küçük gülümseme: kullanıcı gülünce kedi de gülsün
}


def ad_al(deger) -> str:
    # Enum ise içindeki yazıyı, değilse kendisini döndürür.
    return str(getattr(deger, "value", deger))


async def mesaji_isle(mesaj) -> None:
    if mesaj.kanal == "A2":
        olay = ad_al(mesaj.veri.event)
        if olay in REFLEKS_TABLOSU:
            # REFLEKS YOLU: beklemeden küçük animasyon
            animasyon, sure = REFLEKS_TABLOSU[olay]
            print(f"[ROUTER] refleks   <- {olay}")
            await animasyon_oynat(animasyon, kaynak="refleks", sure_s=sure)
        else:
            # Gerçek sistemde burada B1 bağlamı beyne gönderilecek (Faz 2).
            print(f"[ROUTER] beyne soruluyor <- {olay}")

    elif mesaj.kanal == "B2":
        # KARAR YOLU: beynin kararı gelince duygusuna göre animasyon
        karar = mesaj.veri
        duygu = ad_al(karar.emotion)
        print(f"[ROUTER] karar     <- {duygu} ({karar.reason})")
        await animasyon_oynat(duygu, kaynak="karar", sure_s=karar.duration_s)


async def router(kuyruk: asyncio.Queue) -> None:
    while True:
        mesaj = await kuyruk.get()
        try:
            await mesaji_isle(mesaj)
        except Exception as hata:
            # Tek bir bozuk mesaj router'ı çökertmesin; kedi idle'a dönsün.
            print(f"[ROUTER] HATA: {hata!r}, idle'a dönülüyor")
            await animasyon_oynat("idle", kaynak="hata")
        finally:
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