"""
HAL (donanım katmanı, taslak).

Ne işe yarar: Router'ın poz gönderdiği tek nokta. Router simülatöre mi gerçek
robota mı konuştuğunu bilmez. pose_gonder bir poz sözlüğü ve geçiş süresi alır.

KonsolHAL: sadece ekrana yazar.
SimulatorHAL: motion/simulator2.py penceresindeki kaydırma çubuklarını oynatır.
"""

import queue


class KonsolHAL:
    async def pose_gonder(self, poz: dict, sure_ms: float) -> None:
        print(f"[HAL] poz={poz} süre={sure_ms:.0f}ms")


class SimulatorHAL:
    """Tkinter ana thread'de çalışır; asyncio başka thread'den buraya komut bırakır."""

    def __init__(self, simulator, pencere) -> None:
        from motion.simulator2 import EKLEMLER  # tkinter'ı sadece gerekince yükle

        self._araliklar = EKLEMLER
        self._sim = simulator
        self._pencere = pencere
        self._kuyruk: queue.Queue = queue.Queue()
        self._bosalt()

    def _bosalt(self) -> None:
        # Tkinter thread'inde 20 ms'de bir kuyruğa bakar ve komutları uygular.
        try:
            while True:
                ad, hedef, sure_ms = self._kuyruk.get_nowait()
                self._sim.git(ad, hedef, sure_ms)
        except queue.Empty:
            pass
        self._pencere.after(20, self._bosalt)

    async def pose_gonder(self, poz: dict, sure_ms: float) -> None:
        for ad, hedef in poz.items():
            if ad not in self._araliklar:
                continue
            en_az, en_cok = self._araliklar[ad]
            hedef = min(en_cok, max(en_az, hedef))  # servo güvenliği: aralığa sıkıştır
            self._kuyruk.put((ad, hedef, int(sure_ms)))