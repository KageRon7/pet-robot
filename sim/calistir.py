"""
sim/calistir.py  --  Dijital ikizi çalıştıran komut.

Kullanım (pet-robot klasöründe, .venv açıkken):
    python -m sim.calistir                       # bütün klipler + zorlama testleri, rapor yazar
    python -m sim.calistir --pencere             # 3B pencerede kediyi izle (fare ile çevir/yakınlaş)
    python -m sim.calistir --pencere --klip curious
    python -m sim.calistir --s0 MG90S            # "S0'ı küçültelim" önerisini dene
    python -m sim.calistir --surtunme 0.8        # lastik ayak takılmış gibi dene
    python -m sim.calistir --karsilastir         # bugünkü tasarım ile önerileri yan yana koy
"""

import argparse
import sys
import time
from pathlib import Path

from .ikiz import DijitalIkiz
from .kontrol import (BOSLUK_SARI_MM, hepsini_calistir, klip_komutlari, klipleri_yukle,
                      rapor_yaz, zorlama_senaryolari)
from .parcalar import SERVOLAR, Robot

RAPOR_YOLU = Path(__file__).resolve().parent / "rapor.md"


# Komut satırı ayarlarından Robot nesnesi kurar.
def robot_kur(arg) -> Robot:
    r = Robot()
    ayar = {}
    if arg.s0:
        ayar["s0"] = SERVOLAR[arg.s0]
    if arg.kulak:
        ayar["s3"] = ayar["s4"] = SERVOLAR[arg.kulak]
    if arg.surtunme is not None:
        ayar["masa_surtunme"] = arg.surtunme
    return r.degistir(**ayar)


# Testleri pencere açmadan çalıştırır, raporu ekrana ve sim/rapor.md dosyasına yazar.
def rapor_modu(robot: Robot, cikti: Path) -> int:
    ikiz = DijitalIkiz(robot)
    sonuclar = hepsini_calistir(ikiz)
    metin = rapor_yaz(sonuclar, ikiz)
    print(metin)
    cikti.write_text(metin, encoding="utf-8")
    print(f"Rapor kaydedildi: {cikti}")
    return 1 if any(s.seviye == "KIRMIZI" for s in sonuclar if s.ad.startswith("klip")) else 0


# Bugünkü tasarımı önerilen değişikliklerle karşılaştırır (sadece özet satırları).
def karsilastir_modu() -> int:
    secenekler = {
        "Bugünkü tasarım (v0.2)": Robot(),
        "S0 → MG90S": Robot(s0=SERVOLAR["MG90S"]),
        "Lastik ayak (sürtünme 0.8)": Robot(masa_surtunme=0.8),
        "S0 → MG90S + lastik ayak": Robot(s0=SERVOLAR["MG90S"], masa_surtunme=0.8),
        "Kulaklar SG90": Robot(s3=SERVOLAR["SG90"], s4=SERVOLAR["SG90"]),
    }
    klipler = klipleri_yukle()
    print("| Seçenek | Ağırlık | 🔴 | 🟡 | En yüksek akım | En çok taban dönmesi | En küçük boşluk |")
    print("|---|---|---|---|---|---|---|")
    for ad, robot in secenekler.items():
        ikiz = DijitalIkiz(robot)
        s = hepsini_calistir(ikiz, klipler)
        kirmizi = sum(b.seviye == "KIRMIZI" for x in s for b in x.bulgular)
        sari = sum(b.seviye == "SARI" for x in s for b in x.bulgular)
        print(f"| {ad} | {robot.toplam_agirlik:.0f} g | {kirmizi} | {sari} | "
              f"{max(x.en_yuksek_akim for x in s):.1f} A | {max(x.en_buyuk_donme for x in s):.1f}° | "
              f"{min(x.en_kucuk_bosluk[1] for x in s):.1f} mm |")
    return 0


# 3B pencerede kediyi gerçek zamanlı oynatır; çok yaklaşan parçalar kırmızıya döner.
def pencere_modu(robot: Robot, klip_adi: str | None) -> int:
    import mujoco
    import mujoco.viewer

    ikiz = DijitalIkiz(robot)
    klipler = klipleri_yukle()
    if klip_adi:
        if klip_adi not in klipler:
            print(f"'{klip_adi}' bulunamadı. Klipler: {', '.join(sorted(klipler))}")
            return 2
        sira = [(f"klip: {klip_adi}", klip_komutlari(klipler[klip_adi]))]
    else:
        sira = [(f"klip: {ad}", klip_komutlari(k)) for ad, k in sorted(klipler.items())]
        sira += list(zorlama_senaryolari().items())

    m = ikiz.model
    asil_renk = {ad: m.geom_rgba[m.geom(ad).id].copy() for ad in ("kafa", "kulak_sol", "kulak_sag", "govde")}
    asil_mat = {ad: m.geom_matid[m.geom(ad).id] for ad in asil_renk}

    # Boşluğu 3 mm'den az olan parçaları kırmızı, diğerlerini normal rengine boyar.
    def boya(bosluk):
        yakin = {p for cift, mm in bosluk.items() if mm < BOSLUK_SARI_MM for p in cift.split("-")}
        for ad in asil_renk:
            gid = m.geom(ad).id
            if ad in yakin:
                m.geom_matid[gid] = -1
                m.geom_rgba[gid] = (0.9, 0.15, 0.15, 1)
            else:
                m.geom_matid[gid] = asil_mat[ad]
                m.geom_rgba[gid] = asil_renk[ad]

    with mujoco.viewer.launch_passive(m, ikiz.data) as ekran:
        ekran.cam.distance, ekran.cam.elevation, ekran.cam.azimuth = 0.45, -15, 150
        ekran.cam.lookat[:] = (0, 0, 0.08)
        while ekran.is_running():
            for ad, komutlar in sira:
                print(f"▶ {ad}")
                ikiz.sifirla()
                bitis = komutlar[-1][0] / 1000 + 0.8
                i, baslangic = 0, time.perf_counter()
                while ekran.is_running() and ikiz.data.time < bitis:
                    while i < len(komutlar) and komutlar[i][0] / 1000 <= ikiz.data.time:
                        ikiz.poz_gonder(komutlar[i][1], komutlar[i][2])
                        i += 1
                    # 16 ms'lik (bir ekran karesi) fizik adımı, sonra gerçek saate yetiş
                    with ekran.lock():  # pencere çizerken model değişmesin
                        for _ in range(32):
                            ikiz.adim()
                        o = ikiz.olc()
                        boya(o.bosluk_mm)
                    try:
                        ekran.set_texts((mujoco.mjtFontScale.mjFONTSCALE_150, mujoco.mjtGridPos.mjGRID_TOPLEFT,
                                         ad, f"{ikiz.data.time:.1f} s · {o.akim_a:.1f} A"))
                    except AttributeError:
                        pass  # eski MuJoCo sürümünde ekrana yazı yok
                    ekran.sync()
                    bekle = ikiz.data.time - (time.perf_counter() - baslangic)
                    if bekle > 0:
                        time.sleep(bekle)
                if not ekran.is_running():
                    break
    return 0


# Komut satırını okur ve seçilen modu çalıştırır.
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Kutu Kafalı Kedi dijital ikizi")
    p.add_argument("--pencere", action="store_true", help="3B pencerede izle")
    p.add_argument("--klip", help="sadece bu klibi oynat (pencere modunda)")
    p.add_argument("--s0", choices=sorted(SERVOLAR), help="gövde servosu modeli")
    p.add_argument("--kulak", choices=sorted(SERVOLAR), help="kulak servoları modeli")
    p.add_argument("--surtunme", type=float, help="masa sürtünmesi (0.3 PLA, 0.8 lastik)")
    p.add_argument("--karsilastir", action="store_true", help="önerileri yan yana karşılaştır")
    p.add_argument("--cikti", type=Path, default=RAPOR_YOLU, help="rapor dosyası")
    arg = p.parse_args(argv)
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe ve emoji bozulmasın
    if arg.karsilastir:
        return karsilastir_modu()
    robot = robot_kur(arg)
    if arg.pencere:
        return pencere_modu(robot, arg.klip)
    return rapor_modu(robot, arg.cikti)


if __name__ == "__main__":
    sys.exit(main())
