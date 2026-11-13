"""Canlı mod: Mustafa'nın kamerasını Kaan'ın router'ına boru (|) ile bağlar.

Kamera her olayı ekrana tek satır JSON olarak yazar. Bu dosya o satırları okuyup
sahte olay programının yerine router'ın posta kutusuna (kuyruk) atar.

Çalıştırma (pet-robot klasöründe):
    python computer_vision/faz1.py | python -m router.canli
    python computer_vision/faz1.py | python -m router.canli --penceresiz   # sadece yazı
    python computer_vision/faz1.py | python -m router.canli --esp32        # Wokwi'deki ESP32 (pencere açılmaz)

Kamerayı kapatınca (q) router da kendiliğinden kapanır; --esp32'de kapanırken kediye nötr komutu gider.
PowerShell'de olaylar gecikmeli gelirse aynı komutu cmd üzerinden çalıştır:
    cmd /c "python computer_vision/faz1.py | python -m router.canli --esp32"
"""

import asyncio
import re
import sys
import threading

from contracts import PerceptionEvent
from router.animasyon import kapat
from router.tests.faz0_demo import router
from tools.fake_events.uretec import Mesaj

OLAY_DESENI = re.compile(r'"type"\s*:\s*"event"')  # boşluklu ya da boşluksuz JSON'u tanır


# Borudan gelen tek bir satırı A2 mesajına çevirir; olay değilse veya bozuksa None döner.
def satiri_cevir(satir: str) -> Mesaj | None:
    satir = satir.strip()
    if not satir.startswith("{") or not OLAY_DESENI.search(satir):
        return None  # boş satır, yüz takibi (A1) ya da düz yazı: router'ın işi değil
    try:
        return Mesaj(kanal="A2", veri=PerceptionEvent.from_json(satir))
    except ValueError as hata:
        # Sözleşmeye uymayan olay: çökme, söyle ve geç.
        print(f"[CANLI] sözleşmeye uymayan satır atlandı: {satir} ({hata.__class__.__name__})")
        return None


# Ayrı bir thread'de boruyu okur, her olayı router'ın kuyruğuna koyar. Boru kapanınca bitti'yi işaretler.
def boruyu_oku(kuyruk: asyncio.Queue, dongu: asyncio.AbstractEventLoop, bitti: threading.Event) -> None:
    for satir in sys.stdin:
        mesaj = satiri_cevir(satir)
        if mesaj is not None:
            asyncio.run_coroutine_threadsafe(kuyruk.put(mesaj), dongu)
    print("[CANLI] kamera kapandı, router durduruluyor")
    bitti.set()


# Router'ı başlatır ve kamera kapanana kadar çalıştırır.
async def main(bitti: threading.Event) -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    dongu = asyncio.get_running_loop()
    threading.Thread(target=boruyu_oku, args=(kuyruk, dongu, bitti), daemon=True).start()
    gorev = asyncio.create_task(router(kuyruk))
    print("[CANLI] router hazır, kameradan olay bekleniyor")
    try:
        await asyncio.to_thread(bitti.wait)
    finally:
        gorev.cancel()
        await asyncio.gather(gorev, return_exceptions=True)
        await kapat()  # ESP32HAL varsa nötr komutunu gönderip bağlantıyı kapatır


# Pencere açıkken kamera kapandı mı diye bakar; kapandıysa pencereyi de kapatır.
def pencereyi_izle(kok, bitti: threading.Event) -> None:
    if bitti.is_set():
        kok.destroy()
    else:
        kok.after(200, pencereyi_izle, kok, bitti)


if __name__ == "__main__":
    bitti = threading.Event()
    if "--esp32" in sys.argv:
        # Wokwi'deki ESP32'ye bağlanır (rfc2217://localhost:4000); simülatör penceresi açılmaz.
        from router import animasyon
        from router.hal import ESP32HAL

        animasyon.hal_ayarla(ESP32HAL())
        asyncio.run(main(bitti))
    elif "--penceresiz" in sys.argv:
        asyncio.run(main(bitti))
    else:
        # faz0_demo --pencere ile aynı düzen: Tkinter ana thread'de, asyncio arka planda.
        from router import animasyon
        from router.hal import simulator_penceresi_kur

        kok, hal = simulator_penceresi_kur()
        animasyon.hal_ayarla(hal)
        threading.Thread(target=lambda: asyncio.run(main(bitti)), daemon=True).start()
        pencereyi_izle(kok, bitti)
        kok.mainloop()
        bitti.set()