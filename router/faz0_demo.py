import asyncio
import random
import time


async def olay_uretici(kuyruk: asyncio.Queue) -> None:
    """Computer Vision'ın yerine geçen sahte görev: belli aralıkla olay üretir."""
    sayac = 0
    while True:
        await asyncio.sleep(random.uniform(0.2, 0.8))  # üretici hızı
        sayac += 1
        olay = {"id": sayac, "tip": random.choice(["yuz", "hareket", "ses"]), "t": time.time()}
        await kuyruk.put(olay)
        print(f"[CV]     üretildi  -> {olay['id']} ({olay['tip']})")


async def router(kuyruk: asyncio.Queue) -> None:
    """Olayları alır; refleksleri kendisi halleder, gerisini 'beyne' sorar."""
    while True:
        olay = await kuyruk.get()
        if olay["tip"] == "ses":
            print(f"[ROUTER] refleks   <- {olay['id']} (anında karar)")
        else:
            # Beyne sormayı ayrı görev yapıyoruz ki router beklemesin
            asyncio.create_task(beyne_sor(olay))
        kuyruk.task_done()


async def beyne_sor(olay: dict) -> None:
    await asyncio.sleep(1.0)  # LLM gecikmesini taklit eder
    print(f"[BEYİN]  karar     <- {olay['id']} ({olay['tip']})")


async def main() -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    gorevler = [
        asyncio.create_task(olay_uretici(kuyruk)),
        asyncio.create_task(router(kuyruk)),
    ]
    try:
        await asyncio.sleep(10)  # demo: 10 sn çalış
    finally:
        for g in gorevler:
            g.cancel()
        await asyncio.gather(*gorevler, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())