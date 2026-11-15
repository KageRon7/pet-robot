"""Davranış ağacını elle yazılmış senaryolarla dener (kamera, router ve simülatör gerekmez).

Sanal bir saat kullanır: 5 dakikalık uyku bile saniyeler içinde görülür. Router'ın
BaglamTutucu'sunu kullandığı için beyne giden B1, gerçek router'dakiyle aynıdır.

Çalıştırma (repo kökünden):
    python -m tools.fake_events.senaryo                 # senaryo listesi
    python -m tools.fake_events.senaryo uzuntu          # tek senaryo
    python -m tools.fake_events.senaryo hepsi           # hepsi
    python -m tools.fake_events.senaryo yokluk --hizli  # kısaltılmış süreli ayarlarla
"""

import sys

from brain.ayarlar import VARSAYILAN, Ayarlar
from brain.davranis import DavranisBeyni
from contracts import EventType
from router.beyin_istemcisi import BaglamTutucu

BASLANGIC = 1_800_000_000.0  # sanal saatin başlangıcı (gerçek saatle ilgisi yok)

# Senaryo = (açıklama, toplam_süre_sn, [(saniye, olay), ...])
SENARYOLAR: dict[str, tuple[str, int, list[tuple[int, str]]]] = {
    "uzuntu": (
        "Kullanıcı üzgün kalıyor: merak -> oyunbazlık -> birlikte üzülme",
        120,
        [(5, "sad"), (30, "sad"), (60, "sad"), (90, "sad")],
    ),
    "yokluk": (
        "Küçük, orta ve büyük yokluktan sonra karşılama",
        7000,
        [(5, "user_arrived"), (20, "user_left"), (50, "user_arrived"),   # 30 sn yokluk: küçük
         (400, "user_left"), (700, "user_arrived"),                      # 5 dk: orta
         (800, "user_left"), (3000, "user_arrived")],                    # ~37 dk: büyük
    ),
    "merdiven": (
        "Gülümseme -> 10 sn sıkılma -> 5 dk sonra uyku -> esneyince uyanma",
        420,
        [(5, "smile"), (380, "yawn")],
    ),
    "alisma": (
        "Aynı olay üst üste: tepki azalıyor, bazen hiç gelmiyor",
        200,
        [(sn, "smile") for sn in range(5, 200, 15)],
    ),
    "sinirli": (
        "Sinirli kullanıcı: geri çekilme, sonra bir süre sessizlik",
        120,
        [(5, "angry"), (30, "angry")],
    ),
    "ilgi": (
        "Kullanıcı masada ama ilgilenmiyor: 20-30 dk'da bir ilgi isteme",
        4000,
        [(5, "user_arrived")],
    ),
}


# Tek bir senaryoyu sanal saatle çalıştırıp her kararı zamanıyla yazdırır.
def calistir(ad: str, ayarlar: Ayarlar, tohum: int = 1) -> int:
    aciklama, sure, olaylar = SENARYOLAR[ad]
    beyin = DavranisBeyni(ayarlar, tohum=tohum)
    tutucu = BaglamTutucu()
    program = {sn: [] for sn in range(sure + 1)}
    for sn, olay in olaylar:
        program[sn].append(EventType(olay))

    print(f"\n=== {ad}: {aciklama} ===")
    karar_sayisi = 0
    for sn in range(sure + 1):
        simdi = BASLANGIC + sn
        for olay in program[sn]:
            tutucu.olay_ekle(olay, simdi)
            print(f"  {sn:5d} sn  OLAY    {olay.value}")
        baglam = tutucu.olustur(simdi)
        karar = beyin.isle(baglam, tik=not program[sn])
        if karar is not None:
            karar_sayisi += 1
            klip = f" klip={karar.clip}" if karar.clip else ""
            print(f"  {sn:5d} sn  KARAR   {karar.emotion.value:8} {karar.intensity:<5}{klip}  ({karar.reason})")
        elif program[sn]:
            print(f"  {sn:5d} sn  KARAR   (tepki yok)")
    d = beyin.durum
    print(f"  -- son durum: basamak={d.basamak} ruh_hali={d.ruh_hali:.2f} alisma={ {k: round(v, 2) for k, v in d.alisma.items()} }")
    return karar_sayisi


def main(argumanlar: list[str]) -> None:
    ayarlar = Ayarlar.hizli() if "--hizli" in argumanlar else VARSAYILAN
    adlar = [a for a in argumanlar if not a.startswith("--")]
    if not adlar:
        print("Senaryolar:")
        for ad, (aciklama, _, _) in SENARYOLAR.items():
            print(f"  {ad:10} {aciklama}")
        print("\nÖrnek: python -m tools.fake_events.senaryo uzuntu")
        return
    if adlar == ["hepsi"]:
        adlar = list(SENARYOLAR)
    for ad in adlar:
        if ad not in SENARYOLAR:
            print(f"Bilinmeyen senaryo: {ad}")
            continue
        calistir(ad, ayarlar)


if __name__ == "__main__":
    main(sys.argv[1:])
