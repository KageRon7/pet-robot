import asyncio

from tools.fake_events import SahteOlayUreteci


async def router(kuyruk: asyncio.Queue) -> None:
    while True:
        mesaj = await kuyruk.get()
        olay = mesaj.veri                      # olayın kendisi
        ad = getattr(olay.event, "value", olay.event)

        if ad == "user_arrived":
            print(f"[ROUTER] refleks   <- {ad} (anında karar)")
        else:
            # Beyne sormayı ayrı görev yapıyoruz ki router beklemesin
            asyncio.create_task(beyne_sor(ad))
        kuyruk.task_done()


async def beyne_sor(ad: str) -> None:
    await asyncio.sleep(1.0)                   # LLM gecikmesini taklit eder
    print(f"[BEYİN]  karar     <- {ad}")


async def main() -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    uretec = SahteOlayUreteci(tohum=42, hiz=20, kanallar=("A2",))
    gorevler = [
        asyncio.create_task(uretec.kuyruga_aktar(kuyruk, sure_s=300)),
        asyncio.create_task(router(kuyruk)),
    ]
    try:
        await asyncio.sleep(15)                # demo: 15 sn çalış
    finally:
        for g in gorevler:
            g.cancel()
        await asyncio.gather(*gorevler, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())