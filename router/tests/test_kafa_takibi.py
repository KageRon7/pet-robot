"""
Ne işe yarar: Kafa takibi kurallarını (ölü bölge, klip sırasında durma, sıkılınca ortalama) donanımsız dener.
Nasıl çalıştırılır (ana klasörden): python -m unittest router.tests.test_kafa_takibi -v
"""

import unittest

from router.kafa_takibi import ORTALA_MS, KafaTakipci


def kur(klip_oynuyor=lambda simdi: False):
    gonderilen, idle_sayisi = [], []
    takipci = KafaTakipci(
        gonder=lambda pan, tilt, ms: gonderilen.append((pan, tilt, ms)),
        idle_don=lambda: idle_sayisi.append(1),
        klip_oynuyor=klip_oynuyor,
    )
    return takipci, gonderilen, idle_sayisi


class KafaTakibiTestleri(unittest.TestCase):
    def test_yuz_sagda_kafa_saga_doner(self):
        takipci, gonderilen, _ = kur()
        takipci.yuz_geldi(0.9, 0.5, True, True, 0.0)
        self.assertEqual(len(gonderilen), 1)
        self.assertGreater(gonderilen[0][0], 20)

    def test_olu_bolge_ortada_kafa_oynamaz(self):
        takipci, _, _ = kur()
        self.assertEqual(takipci.hedef_acilar(0.53, 0.47), (0.0, 0.0))

    def test_robota_bakmiyorsa_takip_yok(self):
        takipci, gonderilen, _ = kur()
        takipci.yuz_geldi(0.9, 0.5, True, False, 0.0)
        self.assertEqual(gonderilen, [])

    def test_klip_oynarken_takip_durur(self):
        takipci, gonderilen, _ = kur(klip_oynuyor=lambda simdi: True)
        takipci.yuz_geldi(0.9, 0.5, True, True, 0.0)
        self.assertEqual(gonderilen, [])

    def test_hiz_siniri(self):
        takipci, gonderilen, _ = kur()
        takipci.yuz_geldi(0.9, 0.5, True, True, 0.00)
        takipci.yuz_geldi(0.1, 0.5, True, True, 0.01)  # 40 ms dolmadı
        self.assertEqual(len(gonderilen), 1)
        takipci.yuz_geldi(0.1, 0.5, True, True, 0.05)
        self.assertEqual(len(gonderilen), 2)

    def test_sikilinca_kafa_ortaya_doner_sonra_idle(self):
        takipci, gonderilen, idle_sayisi = kur()
        takipci.yuz_geldi(0.9, 0.5, True, True, 0.0)  # takip başlar
        takipci.yuz_geldi(0.9, 0.5, True, False, 1.0)  # artık bakmıyor
        takipci.yuz_geldi(0.9, 0.5, True, False, 10.0)  # 9 sn: henüz sıkılmadı
        self.assertEqual(len(gonderilen), 1)
        takipci.yuz_geldi(0.9, 0.5, True, False, 16.5)  # 15,5 sn: sıkıldı
        self.assertEqual(gonderilen[-1], (0.0, 0.0, ORTALA_MS))
        takipci.yuz_geldi(0.9, 0.5, True, False, 16.6)
        self.assertEqual(idle_sayisi, [])
        takipci.yuz_geldi(0.9, 0.5, True, False, 17.5)
        self.assertEqual(idle_sayisi, [1])

    def test_yuz_kaybolunca_ortalar(self):
        takipci, gonderilen, _ = kur()
        takipci.yuz_geldi(0.9, 0.5, True, True, 0.0)
        takipci.yuz_geldi(None, None, False, False, 1.0)
        takipci.yuz_geldi(None, None, False, False, 3.5)  # 2,5 sn: yüz yok
        self.assertEqual(gonderilen[-1], (0.0, 0.0, ORTALA_MS))


if __name__ == "__main__":
    unittest.main()