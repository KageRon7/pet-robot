"""
HAL (donanım katmanı).

Ne işe yarar: Router'ın bir duyguyu oynattığı tek nokta. Router simülatöre mi
gerçek robota mı konuştuğunu bilmez.

KonsolHAL: pencere yok, sadece ekrana yazar.
SimulatorHAL: motion/simulator.py'deki KediKontrolcusu'nu kullanır (yüz + motorlar).
simulator_penceresi_kur(): simülatör penceresini kurar, (pencere, hal) döndürür.
"""

import queue
from pathlib import Path

KLIP_KLASORU = Path(__file__).resolve().parent.parent / "motion" / "clips"


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
    # Karar klibi bitince düz poza değil idle'a dönmesi istenirse (ekibe sor):
    # kontrolcu.BITINCE_DAVRANIS = "idle"
    return kok, SimulatorHAL(kontrolcu, kok)