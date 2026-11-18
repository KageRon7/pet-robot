"""
Ne işe yarar: Gece/gündüz hesabını ve döneme göre klip seçimini donanımsız dener.
Nasıl çalıştırılır (ana klasörden): python -m unittest router.tests.test_gun_zamani -v
"""

import asyncio
import os
import unittest
from datetime import datetime

from router import animasyon, gun_zamani


class SahteHAL:
    def __init__(self, adlar):
        self.adlar = set(adlar)
        self.oynanan = []

    def bilinen(self, ad):
        return ad in self.adlar

    def klip_adlari(self):
        return set(self.adlar)

    async def duygu_oynat(self, ad, kaynak, sure_s):
        self.oynanan.append(ad)


class GunZamaniTestleri(unittest.TestCase):
    def setUp(self):
        os.environ.pop("KEDI_DONEM", None)

    def test_kasim_gece_ve_gunduz(self):
        for saat, beklenen in [(3, "gece"), (12, "gunduz"), (17, "gunduz"), (21, "gece")]:
            self.assertEqual(gun_zamani.donem(datetime(2026, 11, 16, saat, 0)), beklenen, saat)

    def test_haziran_gece_ve_gunduz(self):
        for saat, beklenen in [(2, "gece"), (5, "gunduz"), (12, "gunduz"), (21, "gunduz"), (23, "gece")]:
            self.assertEqual(gun_zamani.donem(datetime(2026, 6, 21, saat, 30)), beklenen, saat)

    def test_vakitler_makul(self):
        imsak, yatsi = gun_zamani.vakitler(datetime(2026, 11, 16).date())
        self.assertTrue(5 * 60 < imsak < 7 * 60, imsak)
        self.assertTrue(18 * 60 < yatsi < 20 * 60 + 30, yatsi)

    def test_ortam_degiskeni_donemi_zorlar(self):
        os.environ["KEDI_DONEM"] = "gece"
        self.assertEqual(gun_zamani.donem(datetime(2026, 11, 16, 12, 0)), "gece")


class DonemeGoreKlipTestleri(unittest.TestCase):
    def kur(self, adlar, donem):
        os.environ["KEDI_DONEM"] = donem
        hal = SahteHAL(adlar)
        animasyon.hal_ayarla(hal)
        animasyon._son_secim.clear()
        return hal

    def tearDown(self):
        os.environ.pop("KEDI_DONEM", None)

    def test_gece_gece_klibi_secilir(self):
        hal = self.kur({"idle", "sleepy", "sleepy_gece", "sleepy_gunduz"}, "gece")
        for _ in range(5):
            asyncio.run(animasyon.animasyon_oynat("sleepy", "test"))
        self.assertEqual(set(hal.oynanan), {"sleepy_gece"})

    def test_gunduz_gunduz_klibi_secilir(self):
        hal = self.kur({"idle", "sleepy", "sleepy_gece", "sleepy_gunduz"}, "gunduz")
        asyncio.run(animasyon.animasyon_oynat("sleepy", "test"))
        self.assertEqual(hal.oynanan, ["sleepy_gunduz"])

    def test_ozel_klip_yoksa_eksiz_klip(self):
        hal = self.kur({"idle", "sleepy", "sleepy_gunduz"}, "gece")
        asyncio.run(animasyon.animasyon_oynat("sleepy", "test"))
        self.assertEqual(hal.oynanan, ["sleepy"])

    def test_gunduz_acilis_gunaydin(self):
        hal = self.kur({"idle", "happy", "sleepy", "gunaydin"}, "gunduz")
        asyncio.run(animasyon.acilis_oynat())
        self.assertEqual(hal.oynanan, ["gunaydin"])

    def test_gece_acilis_gunaydin_oynamaz(self):
        hal = self.kur({"idle", "happy", "sleepy", "gunaydin"}, "gece")
        asyncio.run(animasyon.acilis_oynat())
        self.assertEqual(hal.oynanan, ["sleepy"])

    def test_gece_acilis_gece_klibi_varsa_o(self):
        hal = self.kur({"idle", "sleepy", "gunaydin", "gunaydin_gece"}, "gece")
        asyncio.run(animasyon.acilis_oynat())
        self.assertEqual(hal.oynanan, ["gunaydin_gece"])


if __name__ == "__main__":
    unittest.main()