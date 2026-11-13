"""
HAL (donanım katmanı).

Ne işe yarar: Router'ın bir duyguyu oynattığı tek nokta. Router simülatöre mi
gerçek robota mı konuştuğunu bilmez. Her HAL'da şunlar var:
    bilinen(duygu)                  -> bu duygunun klibi var mı
    await duygu_oynat(duygu, ...)   -> klibi oynatır, hemen döner

KonsolHAL: pencere yok, sadece ekrana yazar.
SimulatorHAL: motion/simulator.py'deki KediKontrolcusu'nu kullanır (yüz + motorlar).
ESP32HAL: seri port (rfc2217, Wokwi) üzerinden C2 "anim" komutu gönderir.
"""

import atexit
import queue
import re
import threading
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KLIP_KLASORU = KOK / "motion" / "clips"
FIRMWARE_KLIPLERI = KOK / "firmware" / "animasyon_oynatma" / "include" / "animasyonlar.h"
VARSAYILAN_KLIPLER = {"idle", "happy", "playful", "sad", "sleepy", "smile", "startled", "tsundere", "curious"}


class KonsolHAL:
    def __init__(self) -> None:
        self._adlar = {yol.stem for yol in KLIP_KLASORU.glob("*.json")}

    def bilinen(self, duygu: str) -> bool:
        return duygu in self._adlar

    async def duygu_oynat(self, duygu: str, kaynak: str, sure_s: float) -> None:
        print(f"[HAL] duygu={duygu} kaynak={kaynak}")


class SimulatorHAL:
    """Tkinter ana thread'de çalışır; asyncio başka thread'den buraya komut bırakır."""

    def __init__(self, kontrolcu, pencere) -> None:
        self._kontrolcu = kontrolcu
        self._pencere = pencere
        self._kuyruk: queue.Queue = queue.Queue()
        self._bosalt()

    def _bosalt(self) -> None:
        # Tkinter thread'inde 20 ms'de bir kuyruğa bakar ve komutları uygular.
        try:
            while True:
                duygu = self._kuyruk.get_nowait()
                try:
                    self._kontrolcu.duygu_cagir(duygu)
                except Exception as hata:
                    print(f"[HAL] HATA: {hata!r}")
        except queue.Empty:
            pass
        self._pencere.after(20, self._bosalt)

    def bilinen(self, duygu: str) -> bool:
        return self._kontrolcu.klip_bul(duygu) is not None

    async def duygu_oynat(self, duygu: str, kaynak: str, sure_s: float) -> None:
        self._kuyruk.put(duygu)


class ESP32HAL:
    """
    ESP32'ye (Wokwi) seri port üzerinden C2 komutları gönderir.

    - Seri port işleri ayrı thread'lerde: bir yazıcı, bir okuyucu. asyncio hiç bloklanmaz.
    - Bağlantı yoksa ya da koparsa router çökmez; komut atlanır, 2 sn'de bir yeniden bağlanılır.
    - Her komutun seq numarası var (1'den başlar). ack gelmezse sadece uyarı yazılır.
    - ack içermeyen satırlar (ESP32 yankısı vb.) atlanır; hatalı cevaplar sadece loglanır.
    - Komut gitmediği her saniye ping gider (firmware 3 sn sessizlikte nötre döner).
    - kapat() nötr komutu gönderip bağlantıyı kapatır.
    """

    def __init__(self, url: str = "rfc2217://localhost:4000",
                 ping_aralik_s: float = 1.0, ack_zaman_asimi_s: float = 6.0) -> None:
        self._url = url
        self._ping_aralik_s = ping_aralik_s
        self._ack_zaman_asimi_s = ack_zaman_asimi_s
        self._klipler = self._firmware_kliplerini_oku()

        self._cikis: queue.Queue = queue.Queue(maxsize=200)
        self._durdur = threading.Event()
        self._kapandi = False

        self._port = None
        self._port_kilidi = threading.Lock()
        self._sonraki_deneme = 0.0
        self._baglanti_uyarisi_verildi = False

        self._yazma_kilidi = threading.Lock()
        self._seq = 0
        self._bekleyen: dict[int, tuple[float, str]] = {}  # seq -> (gönderilme anı, komut adı)
        self._bekleyen_kilidi = threading.Lock()
        self._son_ack_uyarisi = 0.0

        self._yazici = threading.Thread(target=self._yazici_dongusu, name="esp32-yazici", daemon=True)
        self._okuyucu = threading.Thread(target=self._okuyucu_dongusu, name="esp32-okuyucu", daemon=True)
        self._yazici.start()
        self._okuyucu.start()
        atexit.register(self.kapat)

    # ---------------------------------------------------------------- dışarıya açık kısım

    def bilinen(self, duygu: str) -> bool:
        return duygu in self._klipler

    def komut_gonder(self, komut: str, **alanlar) -> None:
        """Komutu kuyruğa bırakır ve hemen döner (ileride move için de bu kullanılacak)."""
        try:
            self._cikis.put_nowait((komut, alanlar))
        except queue.Full:
            print(f"[ESP32] UYARI: komut kuyruğu dolu, '{komut}' atlandı")

    async def duygu_oynat(self, duygu: str, kaynak: str, sure_s: float) -> None:
        # Yeni klip eskisini keser (firmware tarafında). Süreyi klibin kendisi belirler.
        self.komut_gonder("anim", name=duygu)

    def kapat(self) -> None:
        """Nötr komutunu gönderir, thread'leri durdurur, bağlantıyı kapatır. Birden çok çağrılabilir."""
        if self._kapandi:
            return
        self._kapandi = True
        self._durdur.set()
        if self._yazici.is_alive() and threading.current_thread() is not self._yazici:
            self._yazici.join(timeout=self._ping_aralik_s + 0.5)
        try:
            while True:
                self._cikis.get_nowait()
        except queue.Empty:
            pass
        if self._yaz("neutral", {}):
            time.sleep(0.3)  # komutun portan çıkması için
        with self._port_kilidi:
            port, self._port = self._port, None
        if port is not None:
            try:
                port.close()
            except Exception:
                pass

    # ---------------------------------------------------------------- iç işler

    @staticmethod
    def _firmware_kliplerini_oku() -> set[str]:
        # animasyonlar.h içindeki {"idle", IDLE_JSON} satırlarından klip adlarını okur.
        try:
            metin = FIRMWARE_KLIPLERI.read_text(encoding="utf-8")
            adlar = set(re.findall(r'\{"(\w+)",\s*\w+_JSON\}', metin))
            if adlar:
                return adlar
        except OSError:
            pass
        return set(VARSAYILAN_KLIPLER)

    def _port_al(self):
        """Açık portu döndürür; yoksa (2 sn'de bir) açmayı dener. Başaramazsa None."""
        with self._port_kilidi:
            if self._port is not None:
                return self._port
            simdi = time.monotonic()
            if simdi < self._sonraki_deneme:
                return None
            try:
                import serial  # pyserial
                from contracts import SERIAL_BAUD

                port = serial.serial_for_url(
                       self._url, baudrate=SERIAL_BAUD, timeout=0.2
                   )
            except Exception as hata:
                self._sonraki_deneme = simdi + 2.0
                if not self._baglanti_uyarisi_verildi:
                    print(f"[ESP32] bağlanılamadı ({self._url}): {hata!r}. Wokwi açık mı? Yeniden denenecek.")
                    self._baglanti_uyarisi_verildi = True
                return None
            self._port = port
            self._baglanti_uyarisi_verildi = False
            print(f"[ESP32] bağlandı: {self._url}")
            return port

    def _port_kapat(self, port) -> None:
        with self._port_kilidi:
            if self._port is port:
                self._port = None
            self._sonraki_deneme = time.monotonic() + 1.0
        try:
            port.close()
        except Exception:
            pass
        with self._bekleyen_kilidi:
            self._bekleyen.clear()

    def _yaz(self, komut: str, alanlar: dict) -> bool:
        """Tek komutu seri porta yazar. Bağlantı yoksa komut atılır (False)."""
        from contracts import SerialCommand

        port = self._port_al()
        if port is None:
            if komut != "ping":
                print(f"[ESP32] bağlantı yok, '{komut}' atlandı")
            return False
        with self._yazma_kilidi:
            self._seq += 1
            seq = self._seq
            try:
                satir = SerialCommand(seq=seq, cmd=komut, **alanlar).to_line()
            except Exception as hata:
                print(f"[ESP32] geçersiz komut {komut} {alanlar}: {hata!r}")
                return False
            ad = komut + (f":{alanlar['name']}" if "name" in alanlar else "")
            with self._bekleyen_kilidi:
                self._bekleyen[seq] = (time.monotonic(), ad)
            try:
                port.write(satir.encode("utf-8"))
            except Exception as hata:
                print(f"[ESP32] yazma hatası: {hata!r}, bağlantı kapatılıyor")
                self._port_kapat(port)
                return False
        return True

    def _yazici_dongusu(self) -> None:
        while not self._durdur.is_set():
            try:
                komut, alanlar = self._cikis.get(timeout=self._ping_aralik_s)
            except queue.Empty:
                komut, alanlar = "ping", {}  # sessizlik: firmware sigortası için canlı tut
            self._yaz(komut, alanlar)

    def _okuyucu_dongusu(self) -> None:
        while not self._durdur.is_set():
            port = self._port_al()
            if port is None:
                time.sleep(0.2)
                continue
            try:
                ham = port.readline()
            except Exception as hata:
                if self._durdur.is_set():
                    break
                print(f"[ESP32] okuma hatası: {hata!r}, bağlantı kapatılıyor")
                self._port_kapat(port)
                continue
            if ham:
                self._satiri_isle(ham)
            self._ack_kontrol()

    def _satiri_isle(self, ham: bytes) -> None:
        from contracts import SerialReply

        satir = ham.decode("utf-8", errors="replace").strip()
        if '"ack"' not in satir:
            return  # ack içermeyen satır: ESP32 yankısı ya da başka çıktı
        try:
            cevap = SerialReply.from_json(satir)
        except Exception as hata:
            print(f"[ESP32] okunamayan cevap {satir[:80]!r}: {hata!r}")
            return
        with self._bekleyen_kilidi:
            kayit = self._bekleyen.pop(cevap.ack, None)
        if not cevap.ok:
            komut = kayit[1] if kayit else "?"
            print(f"[ESP32] HATA cevabı: ack={cevap.ack} err={cevap.err} komut={komut}")

    def _ack_kontrol(self) -> None:
        simdi = time.monotonic()
        with self._bekleyen_kilidi:
            gecikenler = [
                (seq, kayit[1]) for seq, kayit in self._bekleyen.items()
                if simdi - kayit[0] > self._ack_zaman_asimi_s
            ]
            for seq, _ in gecikenler:
                del self._bekleyen[seq]
        if gecikenler and simdi - self._son_ack_uyarisi > 5.0:
            self._son_ack_uyarisi = simdi
            seq, ad = gecikenler[0]
            print(f"[ESP32] UYARI: ack gelmedi seq={seq} komut={ad} (toplam {len(gecikenler)})")


def simulator_penceresi_kur():
    """Reşat'ın simülatör penceresini kurar (yüz, motor çubukları, duygu butonları)."""
    import tkinter as tk
    from tkinter import ttk

    from motion.klip import KlipYukleyici
    from motion.simulator import (
        KLIP_KLASORU as SIM_KLIPLERI,
        KediKontrolcusu,
        KediSimulatoru,
        KlipPaneli,
        YuzEkrani,
    )

    klipler = KlipYukleyici.klasorden_yukle(SIM_KLIPLERI)
    kok = tk.Tk()
    sol = ttk.Frame(kok)
    sol.grid(row=0, column=0, padx=8, pady=8, sticky="n")
    sag = ttk.Frame(kok)
    sag.grid(row=0, column=1, padx=8, pady=8, sticky="n")

    yuz_ekrani = YuzEkrani(sol)
    simulator = KediSimulatoru(kok, kap=sag)
    kontrolcu = KediKontrolcusu(simulator, yuz_ekrani, klipler)
    KlipPaneli(sol, kontrolcu)
    kontrolcu.baslat()
    return kok, SimulatorHAL(kontrolcu, kok)