"""Dijital ikiz testleri. MuJoCo kurulu değilse atlanır (ekibin diğer testlerini bozmaz)."""

import pytest

pytest.importorskip("mujoco")

from sim.ikiz import NOTR_POZ, DijitalIkiz  # noqa: E402
from sim.kontrol import klip_komutlari, klipleri_yukle, senaryo_oynat, zorlama_senaryolari  # noqa: E402
from sim.parcalar import MG90S, Robot  # noqa: E402


# Toplam ağırlık İç Mimari v0.3 bütçesine (≈295 g) yakın olmalı.
def test_agirlik_butcesi():
    assert 285 <= Robot().toplam_agirlik <= 305
    assert Robot(s0=MG90S).toplam_agirlik < Robot().toplam_agirlik


# Nötr pozda robot kıpırdamadan durmalı ve hiçbir sorun çıkmamalı.
def test_notr_pozda_sorun_yok():
    ikiz = DijitalIkiz()
    sonuc = senaryo_oynat(ikiz, "nötr", [(0, NOTR_POZ, 0), (500, NOTR_POZ, 0)])
    assert sonuc.seviye == "YEŞİL"
    assert sonuc.en_kucuk_bosluk[1] > 15      # kafa ile gövde arası boyun kadar (20 mm)
    assert sonuc.en_yuksek_akim < 1.0


# S2 (baş eğme) dururken torkunun küçük bir kısmını kullanmalı (elle hesap: ~%7).
def test_s2_yuku_elle_hesapla_uyumlu():
    ikiz = DijitalIkiz()
    ikiz.poz_gonder(dict(NOTR_POZ, head_tilt=45), 500)
    for _ in range(3000):
        ikiz.adim()
    assert 0.02 < ikiz.olc().tork_oran[2] < 0.15


# Servo, satıcının verdiği hızdan hızlı dönememeli (MG90S: 90° en az 0.15 s).
def test_servo_hiz_siniri():
    ikiz = DijitalIkiz()
    ikiz.poz_gonder(dict(NOTR_POZ, head_pan=90), 0)
    for _ in range(200):  # 0.1 s
        ikiz.adim()
    assert abs(ikiz.olc().hata_derece[1]) > 20   # 0.1 saniyede henüz varamamış olmalı
    for _ in range(1000):
        ikiz.adim()
    assert abs(ikiz.olc().hata_derece[1]) < 2    # sonunda varır


# Baş en geriye eğilince gövdeye çok yaklaştığını gözlemci yakalamalı.
def test_yakin_gecis_yakalanir():
    ikiz = DijitalIkiz()
    sonuc = senaryo_oynat(ikiz, "geri", zorlama_senaryolari()["zorlama: baş en geride + yana dönük"])
    assert any(b.sorun == "Çok yakın geçiş" for b in sonuc.bulgular)


# Ekipteki bütün klipler bugünkü tasarımda KIRMIZI vermeden oynamalı.
def test_klipler_kirmizi_vermez():
    ikiz = DijitalIkiz()
    for ad, klip in klipleri_yukle().items():
        sonuc = senaryo_oynat(ikiz, ad, klip_komutlari(klip))
        assert sonuc.seviye != "KIRMIZI", f"{ad}: {[b.detay for b in sonuc.bulgular]}"
