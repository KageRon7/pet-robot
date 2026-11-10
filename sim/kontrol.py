"""
sim/kontrol.py  --  Senaryoları oynatır, ölçümleri izler ve Türkçe rapor yazar.

Bir senaryo = robota sırayla verilen C1 komutları (bir klip veya bir zorlama testi).
Gözlemci, her senaryoda 5 sorunu arar ve en kötü anı kaydeder:
  1. Çarpışma      : kafa/kulak gövdeye veya tabana değiyor ya da çok yaklaşıyor
  2. Zorlanma      : servo uzun süre tam torkta (takılma, ısınma)
  3. Yetişememe    : istenen açı ile gerçek açı arasında büyük fark
  4. Devrilme/kayma: taban eğiliyor, masada kayıyor ya da dönüyor
  5. Akım          : anlık toplam akım adaptörü aşıyor
"""

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Tuple

import numpy as np

from .ikiz import EKLEMLER, NOTR_POZ, DijitalIkiz

KLIP_KLASORU = Path(__file__).resolve().parent.parent / "motion" / "clips"
ROUTER_ADIM_MS = 40  # Router klibi 40 ms'de bir örnekler (Sözleşme C3)
SERVO_ADLARI = ("S0 gövde", "S1 baş sağ-sol", "S2 baş eğme", "S3 sol kulak", "S4 sağ kulak")

# Eşikler: SARI = dikkat, KIRMIZI = gerçek robotta sorun çıkar
BOSLUK_SARI_MM = 3.0
TAM_TORK = 0.98
TORK_KIRMIZI_MS = 150
HATA_SARI_DERECE, HATA_SURE_MS = 5.0, 100   # 100 ms boyunca 5° geride = istenen hız fazla
HATA_KIRMIZI_MS = 400                       # 400 ms boyunca geride = motor takılmış olabilir
EGIM_SARI, EGIM_KIRMIZI = 1.0, 3.0
KAYMA_SARI_MM, KAYMA_KIRMIZI_MM = 2.0, 10.0
DONME_SARI, DONME_KIRMIZI = 2.0, 10.0
AKIM_PENCERE_MS = 20  # 1000 µF kondansatör çok kısa sıçramaları yutar; 20 ms ortalamasına bakılır

# Senaryo: (zaman_ms, C1 poz, ms) komutlarını üreten fonksiyon
Komut = Tuple[float, Dict[str, float], float]


@dataclass
class Bulgu:
    """Raporda bir satır."""

    seviye: str   # "KIRMIZI", "SARI"
    sorun: str
    detay: str
    t: float
    parca: str = ""  # sorunlu parça: "kafa-govde", "S0", "taban", "guc"


@dataclass
class SenaryoSonucu:
    """Bir senaryonun özeti."""

    ad: str
    sure_s: float
    bulgular: List[Bulgu] = field(default_factory=list)
    en_kucuk_bosluk: Tuple[str, float] = ("", 99.0)
    en_yuksek_tork: List[float] = field(default_factory=lambda: [0.0] * 5)
    en_buyuk_hata: List[float] = field(default_factory=lambda: [0.0] * 5)
    en_yuksek_akim: float = 0.0
    en_buyuk_egim: float = 0.0
    en_buyuk_kayma: float = 0.0
    en_buyuk_donme: float = 0.0

    @property
    def seviye(self) -> str:
        seviyeler = {b.seviye for b in self.bulgular}
        return "KIRMIZI" if "KIRMIZI" in seviyeler else "SARI" if "SARI" in seviyeler else "YEŞİL"


class Gozlemci:
    """Ölçümleri izler; her sorun türünden senaryo başına en kötü olanı bulgu yapar."""

    def __init__(self, ad: str, dt: float) -> None:
        self.s = SenaryoSonucu(ad, 0.0)
        self._dt = dt
        self._tork_sure = np.zeros(5)    # her servonun kesintisiz tam torkta kaldığı süre
        self._hata_sure = np.zeros(5)    # her servonun 5° üstü geride kaldığı süre
        self._akim = deque()
        self._akim_toplam = 0.0
        self._akim_t = 0.0
        self._en_kotu: Dict[str, Bulgu] = {}

    # Aynı türden bulguların en kötüsünü tutar (rapor kısa kalsın).
    def _bildir(self, anahtar: str, seviye: str, sorun: str, detay: str, t: float, puan: float,
                parca: str = "") -> None:
        eski = self._en_kotu.get(anahtar)
        sira = {"SARI": 0, "KIRMIZI": 1}
        if eski is None or (sira[seviye], puan) > (sira[eski.seviye], eski._puan):
            b = Bulgu(seviye, sorun, detay, t, parca)
            b._puan = puan
            self._en_kotu[anahtar] = b

    # Her ölçümde çağrılır; adim_sayisi kadar fizik adımını temsil eder.
    def izle(self, o, adim_sayisi: int = 1) -> None:
        s, sure = self.s, self._dt * adim_sayisi
        s.sure_s = o.t
        # 1. Çarpışma
        for cift, mm in o.bosluk_mm.items():
            if mm < s.en_kucuk_bosluk[1]:
                s.en_kucuk_bosluk = (cift, mm)
            if mm < 0:
                self._bildir("bosluk", "KIRMIZI", "Çarpışma", f"{cift.replace('-', ' ↔ ')} {-mm:.1f} mm iç içe", o.t, -mm, cift)
            elif mm < BOSLUK_SARI_MM:
                self._bildir("bosluk", "SARI", "Çok yakın geçiş", f"{cift.replace('-', ' ↔ ')} arası {mm:.1f} mm", o.t, -mm, cift)
        # 2. Zorlanma ve 3. Yetişememe
        for i in range(5):
            s.en_yuksek_tork[i] = max(s.en_yuksek_tork[i], float(o.tork_oran[i]))
            s.en_buyuk_hata[i] = max(s.en_buyuk_hata[i], abs(float(o.hata_derece[i])))
            self._tork_sure[i] = self._tork_sure[i] + sure if o.tork_oran[i] >= TAM_TORK else 0
            if self._tork_sure[i] * 1000 >= TORK_KIRMIZI_MS:
                self._bildir(f"tork{i}", "KIRMIZI", "Motor takılıyor", f"{SERVO_ADLARI[i]} {self._tork_sure[i]*1000:.0f} ms tam torkta", o.t, self._tork_sure[i], f"S{i}")
            hata = abs(float(o.hata_derece[i]))
            self._hata_sure[i] = self._hata_sure[i] + sure if hata > HATA_SARI_DERECE else 0
            if self._hata_sure[i] * 1000 >= HATA_SURE_MS:
                seviye = "KIRMIZI" if self._hata_sure[i] * 1000 >= HATA_KIRMIZI_MS else "SARI"
                self._bildir(f"hata{i}", seviye, "Motor yetişemiyor", f"{SERVO_ADLARI[i]} hedefin {hata:.0f}° gerisinde ({self._hata_sure[i]*1000:.0f} ms)", o.t, hata, f"S{i}")
        # 4. Devrilme / kayma / dönme
        s.en_buyuk_egim = max(s.en_buyuk_egim, o.egim_derece)
        s.en_buyuk_kayma = max(s.en_buyuk_kayma, o.kayma_mm)
        s.en_buyuk_donme = max(s.en_buyuk_donme, abs(o.donme_derece))
        if o.egim_derece > EGIM_SARI:
            self._bildir("egim", "KIRMIZI" if o.egim_derece > EGIM_KIRMIZI else "SARI", "Devrilme eğilimi", f"taban {o.egim_derece:.1f}° kalkıyor", o.t, o.egim_derece, "taban")
        if o.kayma_mm > KAYMA_SARI_MM:
            self._bildir("kayma", "KIRMIZI" if o.kayma_mm > KAYMA_KIRMIZI_MM else "SARI", "Masada kayıyor", f"taban {o.kayma_mm:.1f} mm kaydı", o.t, o.kayma_mm, "taban")
        if abs(o.donme_derece) > DONME_SARI:
            self._bildir("donme", "KIRMIZI" if abs(o.donme_derece) > DONME_KIRMIZI else "SARI", "Masada dönüyor", f"taban {abs(o.donme_derece):.1f}° döndü", o.t, abs(o.donme_derece), "taban")
        # 5. Akım (20 ms kayan ortalama)
        self._akim.append((o.t, o.akim_a))
        self._akim_toplam += o.akim_a
        while self._akim and o.t - self._akim[0][0] > AKIM_PENCERE_MS / 1000:
            self._akim_toplam -= self._akim.popleft()[1]
        ort = self._akim_toplam / len(self._akim)
        if ort > s.en_yuksek_akim:
            s.en_yuksek_akim, self._akim_t = ort, o.t

    # Senaryo bitince akım bulgusunu ekler ve sonucu döndürür.
    def bitir(self, adaptor_a: float) -> SenaryoSonucu:
        s = self.s
        if s.en_yuksek_akim > adaptor_a:
            self._bildir("akim", "KIRMIZI", "Adaptör yetmiyor", f"anlık {s.en_yuksek_akim:.1f} A > {adaptor_a:.0f} A", self._akim_t, s.en_yuksek_akim, "guc")
        elif s.en_yuksek_akim > 0.8 * adaptor_a:
            self._bildir("akim", "SARI", "Adaptör sınırda", f"anlık {s.en_yuksek_akim:.1f} A (sınır {adaptor_a:.0f} A)", self._akim_t, s.en_yuksek_akim, "guc")
        s.bulgular = sorted(self._en_kotu.values(), key=lambda b: (b.seviye != "KIRMIZI", b.t))
        return s


# Bir komut listesini ikizde oynatır, sonra robotun durulması için 0.5 s bekler.
def senaryo_oynat(ikiz: DijitalIkiz, ad: str, komutlar: List[Komut],
                  her_olcumde: Callable[[DijitalIkiz, object], None] | None = None) -> SenaryoSonucu:
    ikiz.sifirla()
    goz = Gozlemci(ad, ikiz.dt)
    olcum_araligi = 10  # her 10 adımda (5 ms) bir ölç
    bitis = (komutlar[-1][0] / 1000 if komutlar else 0) + 0.5
    sira, adim = 0, 0
    while ikiz.data.time < bitis:
        while sira < len(komutlar) and komutlar[sira][0] / 1000 <= ikiz.data.time + 1e-9:
            _, poz, ms = komutlar[sira]
            ikiz.poz_gonder(poz, ms)
            sira += 1
        ikiz.adim()
        adim += 1
        if adim % olcum_araligi == 0:
            o = ikiz.olc()
            goz.izle(o, olcum_araligi)
            if her_olcumde:
                her_olcumde(ikiz, o)
    return goz.bitir(ikiz.robot.adaptor_a)


# Bir klibi router gibi 40 ms'de bir örnekleyip C1 komut listesine çevirir.
def klip_komutlari(klip) -> List[Komut]:
    from motion.klip import Enterpolator
    komutlar: List[Komut] = []
    t = 0.0
    while t <= klip.sure_ms:
        komutlar.append((t, Enterpolator.ornekle(klip, t), ROUTER_ADIM_MS))
        t += ROUTER_ADIM_MS
    return komutlar


# motion/clips içindeki bütün klipleri yükler: {dosya_adı: Klip}.
def klipleri_yukle(klasor: Path = KLIP_KLASORU) -> Dict[str, object]:
    from motion.klip import KlipYukleyici
    return KlipYukleyici.klasorden_yukle(klasor)


# "En kötü durum" testleri: kliplerde olmayan ama router/beyin isteyebilecek sert hareketler.
def zorlama_senaryolari() -> Dict[str, List[Komut]]:
    def poz(**k):
        p = dict(NOTR_POZ)
        p.update(k)
        return p

    hepsi_uc = poz(body_yaw=45, head_pan=90, head_tilt=45, ear_left=0, ear_right=0)
    hepsi_ters = poz(body_yaw=-45, head_pan=-90, head_tilt=-10, ear_left=1, ear_right=1)
    return {
        "zorlama: bütün motorlar aynı anda uçtan uca (ani)": [
            (0, hepsi_uc, 0), (600, hepsi_ters, 0), (1200, hepsi_uc, 0), (1800, NOTR_POZ, 0)],
        "zorlama: gövde hızlı sallanma (±45°, 150 ms)": [
            (i * 150, poz(body_yaw=45 if i % 2 else -45), 150) for i in range(10)] + [(1500, NOTR_POZ, 150)],
        "zorlama: baş en geride + yana dönük": [
            (0, poz(head_tilt=45), 300), (400, poz(head_tilt=45, head_pan=90, body_yaw=45), 400),
            (1000, poz(head_tilt=45, head_pan=-90, body_yaw=-45), 400), (1600, NOTR_POZ, 300)],
        "zorlama: baş en önde + yana dönük": [
            (0, poz(head_tilt=-10), 200), (300, poz(head_tilt=-10, head_pan=90), 300),
            (800, poz(head_tilt=-10, head_pan=-90), 400), (1400, NOTR_POZ, 300)],
    }


# Bütün senaryoları çalıştırıp sonuç listesi döndürür.
def hepsini_calistir(ikiz: DijitalIkiz, klipler: Dict[str, object] | None = None,
                     zorlama: bool = True) -> List[SenaryoSonucu]:
    sonuclar = []
    for ad, klip in sorted((klipler if klipler is not None else klipleri_yukle()).items()):
        sonuclar.append(senaryo_oynat(ikiz, f"klip: {ad}", klip_komutlari(klip)))
    if zorlama:
        for ad, komutlar in zorlama_senaryolari().items():
            sonuclar.append(senaryo_oynat(ikiz, ad, komutlar))
    return sonuclar


# Sonuçları okunur bir Markdown rapora çevirir.
def rapor_yaz(sonuclar: List[SenaryoSonucu], ikiz: DijitalIkiz) -> str:
    r = ikiz.robot
    isaret = {"KIRMIZI": "🔴", "SARI": "🟡", "YEŞİL": "🟢"}
    satirlar = [
        "# Dijital ikiz raporu",
        "",
        f"Robot: {r.toplam_agirlik:.0f} g · S0 {r.s0.ad} · S1 {r.s1.ad} · S2 {r.s2.ad} · "
        f"kulaklar {r.s3.ad} · masa sürtünmesi {r.masa_surtunme} · adaptör {r.adaptor_a:.0f} A",
        "",
        "🔴 gerçek robotta sorun çıkar · 🟡 dikkat · 🟢 sorun yok",
        "",
        "| Senaryo | Durum | En küçük boşluk | En yüksek akım | Taban dönmesi |",
        "|---|---|---|---|---|",
    ]
    for s in sonuclar:
        satirlar.append(f"| {s.ad} | {isaret[s.seviye]} | {s.en_kucuk_bosluk[1]:.1f} mm | "
                        f"{s.en_yuksek_akim:.1f} A | {s.en_buyuk_donme:.1f}° |")
    satirlar += ["", "## Bulgular", ""]
    bulgu_var = False
    for s in sonuclar:
        for b in s.bulgular:
            bulgu_var = True
            satirlar.append(f"- {isaret[b.seviye]} **{s.ad}** ({b.t:.2f}. sn): {b.sorun}: {b.detay}")
    if not bulgu_var:
        satirlar.append("Hiç sorun bulunmadı.")
    satirlar += ["", "## Motorların en çok zorlandığı an (durma torkunun yüzdesi)", "",
                 "Harekete başlarken kısa süre %100'e çıkmak normaldir; sorun, uzun süre orada kalmasıdır.", "",
                 "| Senaryo | " + " | ".join(SERVO_ADLARI) + " |", "|---|" + "---|" * 5]
    for s in sonuclar:
        satirlar.append(f"| {s.ad} | " + " | ".join(f"%{100*t:.0f}" for t in s.en_yuksek_tork) + " |")
    return "\n".join(satirlar) + "\n"
