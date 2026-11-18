"""Canlı mod: Mustafa'nın kamerasını Kaan'ın router'ına boru (|) ile bağlar.

Kamera her olayı ekrana tek satır JSON olarak yazar. Bu dosya o satırları okuyup
sahte olay programının yerine router'ın posta kutusuna (kuyruk) atar.
--track ile gelen yüz takibi (A1) satırları kafa takipçisine gider (sadece --esp32'de kafa döner).

Çalıştırma (pet-robot klasöründe):
    python computer_vision/faz1.py | python -m router.canli
    python computer_vision/faz1.py | python -m router.canli --penceresiz   # sadece yazı
    python computer_vision/faz1.py --track | python -m router.canli --esp32  # Wokwi'deki ESP32 + kafa takibi

Kamerayı kapatınca (q) router da kendiliğinden kapanır; --esp32'de kapanırken kediye nötr komutu gider.
PowerShell'de olaylar gecikmeli gelirse aynı komutu cmd üzerinden çalıştır:
    cmd /c "python computer_vision/faz1.py --track | python -u -m router.canli --esp32"
"""

import asyncio
import re
import sys
import threading
import time

from contracts import FaceTrack, PerceptionEvent
from router import animasyon
from router.animasyon import acilis_oynat, kapat
from router.beyin_istemcisi import BaglamTutucu, beyin_basamagi
from router.kafa_takibi import KafaTakipci
from router.tests.faz0_demo import router, tik_dongusu
from tools.fake_events.uretec import Mesaj

OLAY_DESENI = re.compile(r'"type"\s*:\s*"event"')  # boşluklu ya da boşluksuz JSON'u tanır
TAKIP_DESENI = re.compile(r'"type"\s*:\s*"face_track"')


# Borudan gelen tek bir satırı A2 mesajına çevirir; olay değilse veya bozuksa None döner.
def satiri_cevir(satir: str) -> Mesaj | None:
    satir = satir.strip()
    if not satir.startswith("{") or not OLAY_DESENI.search(satir):
        return None  # boş satır, yüz takibi (A1) ya da düz yazı: olay değil
    try:
        return Mesaj(kanal="A2", veri=PerceptionEvent.from_json(satir))
    except ValueError as hata:
        # Sözleşmeye uymayan olay: çökme, söyle ve geç.
        print(f"[CANLI] sözleşmeye uymayan satır atlandı: {satir} ({hata.__class__.__name__})")
        return None


# Borudan gelen tek bir satırı A1 yüz takibine çevirir; değilse ya da bozuksa None döner.
def yuz_takibi_cevir(satir: str) -> FaceTrack | None:
    satir = satir.strip()
    if not satir.startswith("{") or not TAKIP_DESENI.search(satir):
        return None
    try:
        return FaceTrack.from_json(satir)
    except ValueError:
        return None  # A1 saniyede ~15 kez geliyor, bozuğu sessizce atla


# Ayrı bir thread'de boruyu okur: olayları router'ın kuyruğuna, yüz takibini kafa takipçisine verir.
def boruyu_oku(kuyruk: asyncio.Queue, dongu: asyncio.AbstractEventLoop, bitti: threading.Event, takipci) -> None:
    for satir in sys.stdin:
        mesaj = satiri_cevir(satir)
        if mesaj is not None:
            asyncio.run_coroutine_threadsafe(kuyruk.put(mesaj), dongu)
            continue
        if takipci is not None:
            iz = yuz_takibi_cevir(satir)
            if iz is not None:
                dongu.call_soon_threadsafe(
                    takipci.yuz_geldi, iz.x, iz.y, iz.present, iz.looking_at_robot, time.monotonic()
                )
    print("[CANLI] kamera kapandı, router durduruluyor")
    bitti.set()


# HAL kafa çevirmeyi destekliyorsa (ESP32HAL) kafa takipçisini kurar, desteklemiyorsa None.
def takipci_kur() -> KafaTakipci | None:
    kafa_gonder = getattr(animasyon.hal_al(), "kafa_gonder", None)
    if kafa_gonder is None:
        return None
    gorevler: set = set()

    def idle_don() -> None:
        gorev = asyncio.ensure_future(animasyon.animasyon_oynat("idle", kaynak="takip"))
        gorevler.add(gorev)
        gorev.add_done_callback(gorevler.discard)

        # Kafa sadece beyin "ilgilenme" basamağındayken takip eder, "sikilma"ya geçince ortaya döner.
    return KafaTakipci(
        gonder=kafa_gonder,
        idle_don=idle_don,
        klip_oynuyor=animasyon.klip_oynuyor,
        ilgilenme_mi=lambda bakiyor: beyin_basamagi() == "ilgilenme",
        sikildi_mi=lambda: beyin_basamagi() == "sikilma",
    )


# Router'ı başlatır ve kamera kapanana kadar çalıştırır.
async def main(bitti: threading.Event) -> None:
    kuyruk: asyncio.Queue = asyncio.Queue(maxsize=100)
    dongu = asyncio.get_running_loop()
    baglam = BaglamTutucu()  # router ve tik aynı bağlamı kullanır
    takipci = takipci_kur()
    threading.Thread(target=boruyu_oku, args=(kuyruk, dongu, bitti, takipci), daemon=True).start()
    gorevler = [asyncio.create_task(router(kuyruk, baglam))]
    print("[CANLI] router hazır, kameradan olay bekleniyor" + (" (kafa takibi açık)" if takipci else ""))
    await acilis_oynat()
    gorevler.append(asyncio.create_task(tik_dongusu(baglam)))  # tik, Günaydın klibinden sonra başlar
    try:
        await asyncio.to_thread(bitti.wait)
    finally:
        for g in gorevler:
            g.cancel()
        await asyncio.gather(*gorevler, return_exceptions=True)
        await kapat()  # İyi geceler klibi, sonra ESP32HAL nötr komutunu gönderip bağlantıyı kapatır

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
        from router.hal import ESP32HAL

        animasyon.hal_ayarla(ESP32HAL())
        asyncio.run(main(bitti))
    elif "--penceresiz" in sys.argv:
        asyncio.run(main(bitti))
    else:
        # faz0_demo --pencere ile aynı düzen: Tkinter ana thread'de, asyncio arka planda.
        from router.hal import simulator_penceresi_kur

        kok, hal = simulator_penceresi_kur()
        animasyon.hal_ayarla(hal)
        threading.Thread(target=lambda: asyncio.run(main(bitti)), daemon=True).start()
        pencereyi_izle(kok, bitti)
        kok.mainloop()
        bitti.set()