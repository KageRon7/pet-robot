"""
sim/disa_aktar.py  --  Simülasyon sonuçlarını web sayfası için tek bir JSON dosyasına yazar.

Sayfa (dijital ikiz paneli) fiziği kendisi hesaplamaz; burada hesaplanan
kaydı oynatır. Her seçenek (bugünkü tasarım, S0 küçük motor, ...) için her senaryo
25 kare/saniye kaydedilir: gerçek eklem açıları, tabanın yeri, motor yükleri,
akım, en küçük boşluk ve bulunan sorunlar. Kliplerin yüz bilgisi de eklenir.

Kullanım:
    python -m sim.disa_aktar                  # sim/panel_verisi.json
    python -m sim.disa_aktar --cikti yol.json
"""

import argparse
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .ikiz import EKLEMLER, DijitalIkiz
from .kontrol import (ROUTER_ADIM_MS, klip_komutlari, klipleri_yukle, senaryo_oynat,
                      zorlama_senaryolari)
from .parcalar import MG90S, Robot

KARE_MS = 40  # kayıt aralığı (25 kare/saniye)
VARSAYILAN_CIKTI = Path(__file__).resolve().parent / "panel_verisi.json"

# Sayfadaki "ya şöyle olsaydı" düğmeleri: (kimlik, ad, açıklama, robot)
SECENEKLER = [
    ("bugun", "Bugünkü tasarım", "Teknik Resim v0.2: S0 MG996R, PLA taban masada", Robot()),
    ("s0_kucuk", "S0 küçük motor", "S0 MG996R yerine MG90S: 14 mm yer, 40 g hafif", Robot(s0=MG90S)),
    ("s0_kucuk_agir", "S0 küçük + tabana 60 g", "MG90S ve tabana 60 g ağırlık (somun, çelik pul)",
     Robot(s0=MG90S, taban_agirlik=Robot().taban_agirlik + 60)),
    ("lastik", "Lastik ayak", "Lastik ayak (sürtünme 0.5 → 0.8): kaymayı azaltır ama en sert testte robot kayamayınca kalkmaya başlar", Robot(masa_surtunme=0.8)),
]

# Yüz alanları: sayılar listede, yazılar ayrı (dosya küçük kalsın)
YUZ_ALANLARI = ["eye_open", "eye_size", "pupil", "sparkle", "look_x", "look_y", "brow_left", "brow_right",
                "brow_height", "mouth_open", "mouth_width", "mouth_x", "mouth_tilt", "tears", "gloom", "rage",
                "_eyeDip", "_mouthSq", "_blushA", "_sweatA", "_angerA", "_browA",
                "eye_shape", "mouth", "line", "iris", "blush_color", "tear_color", "face_bg", "head"]


# Sayıyı kısaltır (dosya boyutu için).
def _y(v: float, n: int = 3) -> float:
    return round(float(v), n)


# Bir klibin yüzünü 40 ms'de bir örnekler: [[alanlar...], ...]
def _yuz_kareleri(klip, sure_ms: float) -> List[List[Any]]:
    from motion.klip import Enterpolator
    kareler = []
    t = 0.0
    while t <= sure_ms:
        y = Enterpolator.yuz_ornekle(klip, min(t, klip.sure_ms))
        satir = []
        for ad in YUZ_ALANLARI:
            v = y.get(ad, 1.0 if ad in ("_eyeDip", "_mouthSq") else 0.0)
            satir.append(_y(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
        kareler.append(satir)
        t += KARE_MS
    return kareler


# Robotun 3B çizimi için ölçüleri sözlük olarak verir.
def _olculer(r: Robot) -> Dict[str, float]:
    return {k: getattr(r, k) for k in (
        "taban_cap", "taban_yukseklik", "govde_genislik", "govde_derinlik", "govde_yukseklik",
        "boyun_yukseklik", "boyun_genislik", "boyun_derinlik", "kafa_genislik", "kafa_yukseklik",
        "kafa_derinlik", "egme_ekseni_yukseklik", "kulak_genislik", "kulak_kalinlik", "kulak_yukseklik",
        "kulak_aralik", "kulak_yatma_derece")}


# Bir senaryoyu bir seçenekte oynatıp kaydeder.
def _kaydet(ikiz: DijitalIkiz, ad: str, komutlar) -> Dict[str, Any]:
    kareler: List[List[float]] = []
    sonraki = [0.0]
    yatma = math.radians(ikiz.robot.kulak_yatma_derece)

    def topla(iz: DijitalIkiz, o) -> None:
        if iz.data.time + 1e-9 < sonraki[0]:
            return
        sonraki[0] += KARE_MS / 1000
        d = iz.data
        q = [d.qpos[a] for a in iz._qadr]
        komut = iz._esp_komutu()
        # Eklemleri C1 birimine geri çevir: derece, kulak 0-1
        def c1(v, i):
            if i < 2:
                return _y(-math.degrees(v), 2)
            if i == 2:
                return _y(math.degrees(v), 2)
            return _y(1 - v / yatma, 3)
        cift, mm = min(o.bosluk_mm.items(), key=lambda kv: kv[1])
        kareler.append(
            [_y(d.time, 3)]
            + [c1(q[i], i) for i in range(5)]
            + [c1(komut[i], i) for i in range(5)]
            + [_y(v * 1000, 2) for v in d.qpos[0:3]]       # taban yeri (mm)
            + [_y(v, 5) for v in d.qpos[3:7]]              # taban yönü (dörtlü sayı)
            + [_y(min(t, 1.5), 3) for t in o.tork_oran]   # motor yükü (0-1)
            + [_y(o.akim_a, 3), _y(mm, 2), cift])
    sonuc = senaryo_oynat(ikiz, ad, komutlar, topla)
    return {
        "kareler": kareler,
        "durum": sonuc.seviye,
        "bulgular": [{"seviye": b.seviye, "sorun": b.sorun, "detay": b.detay, "t": _y(b.t, 2), "parca": b.parca}
                     for b in sonuc.bulgular],
        "ozet": {"bosluk_mm": _y(sonuc.en_kucuk_bosluk[1], 2), "bosluk_cift": sonuc.en_kucuk_bosluk[0],
                 "akim_a": _y(sonuc.en_yuksek_akim, 2), "donme": _y(sonuc.en_buyuk_donme, 2),
                 "kayma_mm": _y(sonuc.en_buyuk_kayma, 2), "egim": _y(sonuc.en_buyuk_egim, 2),
                 "tork": [_y(t, 3) for t in sonuc.en_yuksek_tork]},
    }


# Bütün seçenek × senaryo kayıtlarını üretir.
def veri_uret() -> Dict[str, Any]:
    klipler = klipleri_yukle()
    senaryolar = []
    for ad, klip in sorted(klipler.items()):
        komutlar = klip_komutlari(klip)
        sure = komutlar[-1][0] + 500
        senaryolar.append({"id": f"klip:{ad}", "ad": klip.ad.strip() or ad, "dosya": f"{ad}.json",
                           "tur": "klip", "duygu": klip.duygu, "komutlar": komutlar,
                           "yuz": _yuz_kareleri(klip, sure)})
    for ad, komutlar in zorlama_senaryolari().items():
        senaryolar.append({"id": ad, "ad": ad.replace("zorlama: ", "").capitalize(), "tur": "zorlama",
                           "duygu": None, "komutlar": komutlar, "yuz": None})
    sonuclar: Dict[str, Dict[str, Any]] = {}
    for kimlik, _, _, robot in SECENEKLER:
        ikiz = DijitalIkiz(robot)
        sonuclar[kimlik] = {s["id"]: _kaydet(ikiz, s["id"], s["komutlar"]) for s in senaryolar}
        print(f"  {kimlik}: tamam")
    try:
        surum = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                               cwd=Path(__file__).resolve().parent).stdout.strip()
    except OSError:
        surum = ""
    r = Robot()
    return {
        "bicim": 1,
        "uretildi": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git": surum,
        "kare_ms": KARE_MS,
        "kare_alanlari": (["t"] + [f"q_{e}" for e in EKLEMLER] + [f"komut_{e}" for e in EKLEMLER]
                          + ["taban_x", "taban_y", "taban_z", "taban_qw", "taban_qx", "taban_qy", "taban_qz"]
                          + [f"yuk_S{i}" for i in range(5)] + ["akim_a", "bosluk_mm", "bosluk_cift"]),
        "yuz_alanlari": YUZ_ALANLARI,
        "olculer": _olculer(r),
        "adaptor_a": r.adaptor_a,
        "secenekler": [{"id": k, "ad": a, "aciklama": d, "agirlik_g": _y(rb.toplam_agirlik, 0),
                        "s0": rb.s0.ad, "surtunme": rb.masa_surtunme} for k, a, d, rb in SECENEKLER],
        "senaryolar": [{k: v for k, v in s.items() if k != "komutlar"} for s in senaryolar],
        "sonuclar": sonuclar,
    }


# Komut satırı: veriyi üretip dosyaya yazar.
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Dijital ikiz panel verisini üretir")
    p.add_argument("--cikti", type=Path, default=VARSAYILAN_CIKTI)
    arg = p.parse_args(argv)
    print("Simülasyon çalışıyor (her seçenek ~10 sn)...")
    veri = veri_uret()
    arg.cikti.write_text(json.dumps(veri, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Yazıldı: {arg.cikti} ({arg.cikti.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
