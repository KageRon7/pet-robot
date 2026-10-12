"""
Sahte olay üretecinin testleri.

Repo kök klasöründen çalıştır:
    python -m unittest tools.fake_events.test_uretec -v
"""

import asyncio
import json
import unittest

from contracts import BrainContext, Decision, PerceptionEvent, FaceTrack
from .uretec import SahteOlayUreteci

MODELLER = {"A1": FaceTrack, "A2": PerceptionEvent, "B1": BrainContext, "B2": Decision}


# Verilen tohumla on dakikalık bir oturumu beklemeden üretir ve listeye toplar.
def oturum_uret(tohum: int, sure_s: float = 600, kanallar=("A1", "A2", "B1", "B2")) -> list:
    async def topla():
        uretec = SahteOlayUreteci(tohum=tohum, hiz=0, kanallar=kanallar, baslangic_zamani=1_791_800_000.0)
        return [m async for m in uretec.akis(sure_s)]

    return asyncio.run(topla())


class UretecTestleri(unittest.TestCase):
    # Her mesajın JSON hali, sözleşme modeline geri okunabilmeli (format bozulmamalı).
    def test_her_mesaj_sozlesmeye_uyar(self):
        for tohum in range(5):
            for mesaj in oturum_uret(tohum):
                MODELLER[mesaj.kanal].model_validate_json(mesaj.json())

    # Aynı tohum her seferinde birebir aynı akışı vermeli; hata tekrar üretilebilsin diye.
    def test_ayni_tohum_ayni_akis(self):
        birinci = [m.json() for m in oturum_uret(7, 120)]
        ikinci = [m.json() for m in oturum_uret(7, 120)]
        self.assertEqual(birinci, ikinci)

    # Her A2 olayının ardından bir B1 gelmeli; B2 sayısı da olay sayısına eşit olmalı.
    def test_her_olaya_baglam_ve_karar(self):
        mesajlar = oturum_uret(3, kanallar=("A2", "B1", "B2"))
        kanallar = [m.kanal for m in mesajlar]
        for i, kanal in enumerate(kanallar):
            if kanal == "A2":
                self.assertEqual(kanallar[i + 1], "B1")
        # Oturumun son anındaki kararlar bekleyen listede kalabilir.
        self.assertLessEqual(kanallar.count("A2") - kanallar.count("B2"), 1)
        self.assertGreater(kanallar.count("A2"), 10)

    # user_arrived ve user_left sırayla gelmeli; gelmeden gitmek olmaz.
    def test_gelis_gidis_sirasi(self):
        for tohum in range(5):
            gelis_gidis = [m.veri.event for m in oturum_uret(tohum, kanallar=("A2",))
                           if m.veri.event in ("user_arrived", "user_left")]
            self.assertEqual(gelis_gidis[0], "user_arrived")
            for onceki, sonraki in zip(gelis_gidis, gelis_gidis[1:]):
                self.assertNotEqual(onceki, sonraki)

    # A1 saniyede ~15 mesaj olmalı; yüz yokken konum null olmalı.
    def test_yuz_takibi(self):
        a1 = oturum_uret(1, sure_s=60, kanallar=("A1",))
        self.assertAlmostEqual(len(a1), 900, delta=2)
        for mesaj in a1:
            veri = json.loads(mesaj.json())
            if not veri["present"]:
                self.assertIsNone(veri["x"])

    # Kanal filtresi verildiğinde sadece o kanalın mesajları gelmeli.
    def test_kanal_filtresi(self):
        self.assertEqual({m.kanal for m in oturum_uret(2, kanallar=("B2",))}, {"B2"})

    # kuyruga_aktar, router testleri için mesajları asyncio.Queue'ya koymalı.
    def test_kuyruga_aktar(self):
        async def calistir():
            kuyruk: asyncio.Queue = asyncio.Queue()
            await SahteOlayUreteci(tohum=1, hiz=0, kanallar=("A1",)).kuyruga_aktar(kuyruk, sure_s=1)
            return kuyruk.qsize()

        self.assertEqual(asyncio.run(calistir()), 15)


if __name__ == "__main__":
    unittest.main()
