# veri_kaydet.py için kamerasız testler: defter ve çekim zamanlaması.
import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import veri_kaydet as vk  # noqa: E402


# Sahte bir satır üretir (iki blendshape skoru).
def _satir(t=0):
    return {"t_ms": t, "yaw": 1.234, "pitch": -2.0,
            "ozellikler": {"mouthSmileLeft": 0.5, "jawOpen": 0.1}}


# Çekimler CSV'ye doğru başlık ve etiketle yazılıyor mu?
def test_defter_csv_yazar(tmp_path):
    d = vk.VeriDefteri("Ferhat!", klasor=str(tmp_path), oturum="o1")
    assert d.cekim_ekle("smile", [_satir(0), _satir(100)])
    assert d.cekim_ekle("sad", [_satir(0)])
    with open(d.yol, encoding="utf-8") as f:
        satirlar = list(csv.reader(f))
    assert satirlar[0] == vk.SABIT_SUTUNLAR + ["jawOpen", "mouthSmileLeft"]
    assert len(satirlar) == 4
    assert satirlar[1][:4] == ["ferhat", "o1", "1", "smile"]
    assert satirlar[3][:4] == ["ferhat", "o1", "2", "sad"]
    assert d.sayac()["smile"] == 1


# Geri al son çekimi siler; hepsi silinince dosya da gider.
def test_geri_al(tmp_path):
    d = vk.VeriDefteri("a", klasor=str(tmp_path), oturum="o1")
    d.cekim_ekle("yawn", [_satir()])
    assert d.geri_al() == "yawn"
    assert not os.path.exists(d.yol)
    assert d.geri_al() is None


# Boş çekim ve bilinmeyen etiket kaydedilmez.
def test_bos_ve_hatali(tmp_path):
    d = vk.VeriDefteri("a", klasor=str(tmp_path))
    assert not d.cekim_ekle("smile", [])
    with pytest.raises(ValueError):
        d.cekim_ekle("mutlu", [_satir()])
    with pytest.raises(ValueError):
        vk.temiz_ad("  !! ")


# Hazırlıkta kayıt yok, kayıtta saniyede en fazla ORNEK_HZ satır, "_" skorları atılır.
def test_cekim_zamanlama():
    c = vk.Cekim("smile", 100.0)
    oz = {"jawOpen": 0.2, "_neutral": 0.9}
    c.ornek_ekle(100.5, oz, 0, 0)                 # hazırlık
    assert c.satirlar == []
    for i in range(30):                           # 1 sn içinde 30 kare
        c.ornek_ekle(101.0 + i / 30, oz, 0, 0)
    assert 0.8 * vk.ORNEK_HZ <= len(c.satirlar) <= vk.ORNEK_HZ
    assert "_neutral" not in c.satirlar[0]["ozellikler"]
    assert c.asama(104.1) == "bitti"
