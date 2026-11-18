"""
Ne işe yarar: Animasyon seçim kurallarını (rastgele varyant, adla klip, açılış) donanımsız dener.
Nasıl çalıştırılır (ana klasörden): python -m unittest router.tests.test_animasyon -v
"""

import asyncio
import unittest

from router import animasyon


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


class AnimasyonTestleri(unittest.TestCase):
    def kur(self, adlar):
        hal = SahteHAL(adlar)
        animasyon.hal_ayarla(hal)
        animasyon._son_secim.clear()
        animasyon._klip_bitis = 0.0
        return hal

    def test_ayni_duygunun_varyantlari_secilir(self):
        hal = self.kur({"curious", "curious2", "idle"})
        for _ in range(20):
            asyncio.run(animasyon.animasyon_oynat("curious", "test"))
        self.assertEqual(set(hal.oynanan), {"curious", "curious2"})
        for onceki, sonraki in zip(hal.oynanan, hal.oynanan[1:]):
            self.assertNotEqual(onceki, sonraki)

    def test_idle_ozel_kliplerle_karismaz(self):
        hal = self.kur({"idle", "tsundere", "head_explosion_buum", "im_so_boored"})
        for _ in range(10):
            asyncio.run(animasyon.animasyon_oynat("idle", "test"))
        self.assertEqual(set(hal.oynanan), {"idle"})

    def test_beynin_istedigi_klip_oynar(self):
        hal = self.kur({"idle", "head_explosion_buum"})
        asyncio.run(animasyon.animasyon_oynat("idle", "karar", klip="Head_Explosion(BuUM)"))
        self.assertEqual(hal.oynanan, ["head_explosion_buum"])

    def test_bilinmeyen_klip_duyguya_duser(self):
        hal = self.kur({"idle", "happy"})
        asyncio.run(animasyon.animasyon_oynat("happy", "karar", klip="hapsirma"))
        self.assertEqual(hal.oynanan, ["happy"])

    def test_acilis_klibi_yoksa_yedek_oynar(self):
        hal = self.kur({"idle", "happy"})
        asyncio.run(animasyon.acilis_oynat())
        self.assertEqual(hal.oynanan, ["happy"])

    def test_acilis_klibi_varsa_o_oynar(self):
        hal = self.kur({"idle", "happy", "gunaydin"})
        asyncio.run(animasyon.acilis_oynat())
        self.assertEqual(hal.oynanan, ["gunaydin"])

    def test_klip_oynuyor_bayragi(self):
        self.kur({"idle", "happy"})
        asyncio.run(animasyon.animasyon_oynat("happy", "test"))
        self.assertTrue(animasyon.klip_oynuyor())
        asyncio.run(animasyon.animasyon_oynat("idle", "test"))
        self.assertFalse(animasyon.klip_oynuyor())


if __name__ == "__main__":
    unittest.main()