"""
motion/yuz.py  --  Kedinin yüz ekranını çizen kod (Yüz Atölyesi'nin Python karşılığı)

Bu dosya Tkinter'a BAĞIMLI DEĞİL. Yaptığı tek şey: "şu yüz durumunda ekranda hangi
çokgenler ve çizgiler olmalı?" sorusunun cevabını bir liste olarak üretmek.
Bu listeyi Tk Canvas'a çizmek simulator.py'deki YuzEkrani sınıfının işi.
(Ayrıca listeyi PNG'ye de çizebiliriz; test etmek için çok işe yarıyor.)

Neden böyle?
  Tk Canvas'ta saydamlık, kırpma (clip) ve dönüşüm yok; Yüz Atölyesi ise (HTML canvas)
  hepsini kullanıyor. Bu yüzden:
    - Dönüşümleri (kaydır/döndür/ölçekle) kendimiz yapıyoruz  -> Donusum sınıfı
    - Saydamlığı zemin rengiyle karıştırarak taklit ediyoruz   -> renk_karistir
    - Kırpmayı (göz bebeği gözün dışına taşmasın) çokgen kesme ile yapıyoruz -> kirp_konveks
"""

import math
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Dosya doğrudan çalıştırılırsa "klip", paket olarak içe aktarılırsa ".klip" bulunur.
try:
    from .klip import renk_karistir
except ImportError:
    from klip import renk_karistir

Nokta = Tuple[float, float]

KANVAS_GENISLIK = 420
KANVAS_YUKSEKLIK = 345
BEYAZ = "#FFFFFF"
KULAK_ICI = "#F2B6C1"


# ----------------------------------------------------------------------------
# 1) GEOMETRİ YARDIMCILARI
# ----------------------------------------------------------------------------

class Donusum:
    """2 boyutlu dönüşüm (kaydırma + dönme + ölçekleme). Değiştirilemez: her işlem yeni nesne döndürür."""

    __slots__ = ("a", "b", "c", "d", "e", "f")

    def __init__(self, a: float = 1.0, b: float = 0.0, c: float = 0.0,
                 d: float = 1.0, e: float = 0.0, f: float = 0.0):
        """Matrisi saklar. Varsayılan: hiçbir şey yapmayan 'birim' dönüşüm."""
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def carp(self, o: "Donusum") -> "Donusum":
        """Önce 'o' dönüşümünü, sonra bunu uygulayan birleşik dönüşümü döndürür."""
        return Donusum(
            self.a * o.a + self.c * o.b, self.b * o.a + self.d * o.b,
            self.a * o.c + self.c * o.d, self.b * o.c + self.d * o.d,
            self.a * o.e + self.c * o.f + self.e, self.b * o.e + self.d * o.f + self.f)

    def ofset(self, tx: float, ty: float) -> "Donusum":
        """Çizim başlangıcını (tx, ty) kadar kaydırır."""
        return self.carp(Donusum(1, 0, 0, 1, tx, ty))

    def olcekle(self, sx: float, sy: float) -> "Donusum":
        """Çizimi yatayda sx, dikeyde sy kat büyütür/küçültür."""
        return self.carp(Donusum(sx, 0, 0, sy, 0, 0))

    def dondur(self, radyan: float) -> "Donusum":
        """Çizimi saat yönünde radyan kadar döndürür (ekranda y aşağı doğru artar)."""
        c, s = math.cos(radyan), math.sin(radyan)
        return self.carp(Donusum(c, s, -s, c, 0, 0))

    def nokta(self, x: float, y: float) -> Nokta:
        """Bir noktayı bu dönüşümle ekran koordinatına çevirir."""
        return self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f

    @property
    def olcek(self) -> float:
        """Ortalama büyütme oranı; çizgi kalınlıklarını buna göre ölçekleriz."""
        return math.sqrt(abs(self.a * self.d - self.b * self.c))


def elips(cx: float, cy: float, rx: float, ry: float,
          a0: float = 0.0, a1: float = 2 * math.pi) -> List[Nokta]:
    """Elips (veya elips yayı) üzerindeki noktaları döndürür. Tam elipste son nokta tekrar edilmez."""
    tam = abs(abs(a1 - a0) - 2 * math.pi) < 1e-9
    adim = max(6, int(abs(a1 - a0) / (2 * math.pi) * 32))
    sayi = adim if tam else adim + 1
    return [(cx + rx * math.cos(a0 + (a1 - a0) * j / adim),
             cy + ry * math.sin(a0 + (a1 - a0) * j / adim)) for j in range(sayi)]


def daire(cx: float, cy: float, r: float) -> List[Nokta]:
    """Daire üzerindeki noktaları döndürür."""
    return elips(cx, cy, r, r)


def kuadratik(p0: Nokta, p1: Nokta, p2: Nokta, adim: int = 10) -> List[Nokta]:
    """İki uçlu, tek kontrol noktalı eğrinin (quadratic Bezier) noktalarını döndürür."""
    sonuc = []
    for j in range(adim + 1):
        t = j / adim
        u = 1 - t
        sonuc.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                      u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return sonuc


def kubik(p0: Nokta, p1: Nokta, p2: Nokta, p3: Nokta, adim: int = 14) -> List[Nokta]:
    """İki kontrol noktalı eğrinin (cubic Bezier) noktalarını döndürür."""
    sonuc = []
    for j in range(adim + 1):
        t = j / adim
        u = 1 - t
        sonuc.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                      u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return sonuc


def zincir(*parcalar: Sequence[Nokta]) -> List[Nokta]:
    """Uç uca eklenen eğri parçalarını tek listede birleştirir (birleşim noktasını iki kez yazmaz)."""
    sonuc: List[Nokta] = []
    for parca in parcalar:
        for p in parca:
            if not sonuc or abs(sonuc[-1][0] - p[0]) > 1e-9 or abs(sonuc[-1][1] - p[1]) > 1e-9:
                sonuc.append(p)
    return sonuc


def dikdortgen(x: float, y: float, w: float, h: float) -> List[Nokta]:
    """Dikdörtgenin dört köşesini döndürür."""
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def yuvarlak_dikdortgen(x: float, y: float, w: float, h: float, r: float) -> List[Nokta]:
    """Köşeleri yuvarlatılmış dikdörtgenin noktalarını döndürür."""
    pi = math.pi
    return (elips(x + r, y + r, r, r, pi, 1.5 * pi) + elips(x + w - r, y + r, r, r, 1.5 * pi, 2 * pi)
            + elips(x + w - r, y + h - r, r, r, 0, 0.5 * pi) + elips(x + r, y + h - r, r, r, 0.5 * pi, pi))


def kirp_konveks(konu: Sequence[Nokta], kirpici: Sequence[Nokta]) -> List[Nokta]:
    """'konu' çokgeninin, (dışbükey) 'kirpici' çokgenin içinde kalan kısmını döndürür.

    Sutherland-Hodgman algoritması: kırpıcının her kenarı için, kenarın dışında kalan
    kısmı kesip atar. Göz bebeğinin gözün dışına taşmaması gibi işler için kullanıyoruz.
    """
    kenarlar = list(zip(kirpici, list(kirpici[1:]) + [kirpici[0]]))
    alan = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in kenarlar)
    if abs(alan) < 1e-9:
        return []
    isaret = 1.0 if alan > 0 else -1.0
    cikti = list(konu)
    for (ax, ay), (bx, by) in kenarlar:
        if not cikti:
            break

        def yan(p: Nokta) -> float:
            """Noktanın bu kenarın hangi tarafında olduğunu söyleyen işaretli mesafe (içerisi >= 0)."""
            return isaret * ((bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax))

        def kesisim(p: Nokta, q: Nokta) -> Nokta:
            """p-q doğru parçasının kırpıcı kenarını kestiği noktayı hesaplar."""
            t = yan(p) / (yan(p) - yan(q))
            return p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])

        girdi, cikti = cikti, []
        onceki = girdi[-1]
        for p in girdi:
            if yan(p) >= 0:
                if yan(onceki) < 0:
                    cikti.append(kesisim(onceki, p))
                cikti.append(p)
            elif yan(onceki) >= 0:
                cikti.append(kesisim(onceki, p))
            onceki = p
    return cikti


# ----------------------------------------------------------------------------
# 2) ÇİZİM KOMUTLARI VE SAHNE
# ----------------------------------------------------------------------------

@dataclass
class Cokgen:
    """Ekrana çizilecek kapalı şekil: içi dolu ve/veya konturlu."""

    noktalar: List[Nokta]
    dolgu: Optional[str]
    cizgi: Optional[str]
    kalinlik: float


@dataclass
class Cizgi:
    """Ekrana çizilecek açık çizgi (uçları yuvarlak). 'kesik' verilirse kesik çizgi olur."""

    noktalar: List[Nokta]
    renk: str
    kalinlik: float
    kesik: Optional[Tuple[int, int]] = None


Oge = Union[Cokgen, Cizgi]


class Sahne:
    """Çizim komutlarını biriktiren 'defter'. HTML canvas'taki save/translate/rotate/scale mantığıyla çalışır."""

    def __init__(self, taban: Donusum):
        """Boş bir sahne oluşturur; 'taban' tüm çizimlere uygulanacak ilk dönüşümdür."""
        self.T = taban
        self._yigin: List[Donusum] = []
        self.ogeler: List[Oge] = []

    def kaydet(self) -> None:
        """Şu anki dönüşümü saklar (sonra geri_yukle ile dönülür)."""
        self._yigin.append(self.T)

    def geri_yukle(self) -> None:
        """Son kaydedilen dönüşüme geri döner."""
        self.T = self._yigin.pop()

    def cevir(self, tx: float, ty: float) -> None:
        """Bundan sonraki çizimleri (tx, ty) kadar kaydırır."""
        self.T = self.T.ofset(tx, ty)

    def dondur(self, radyan: float) -> None:
        """Bundan sonraki çizimleri döndürür."""
        self.T = self.T.dondur(radyan)

    def olcekle(self, sx: float, sy: float) -> None:
        """Bundan sonraki çizimleri ölçekler."""
        self.T = self.T.olcekle(sx, sy)

    def cokgen(self, noktalar: Sequence[Nokta], dolgu: Optional[str] = None, cizgi: Optional[str] = None,
               kalinlik: float = 2.0, kirp: Optional[Sequence[Nokta]] = None) -> None:
        """Kapalı şekil ekler. 'kirp' verilirse şekil o dışbükey çokgenin dışına taşırılmaz."""
        noktalar = list(noktalar)
        if kirp is not None:
            noktalar = kirp_konveks(noktalar, kirp)
        if len(noktalar) < 3:
            return
        self.ogeler.append(Cokgen([self.T.nokta(x, y) for x, y in noktalar],
                                  dolgu, cizgi, kalinlik * self.T.olcek))

    def cizgi(self, noktalar: Sequence[Nokta], renk: str, kalinlik: float,
              kesik: Optional[Tuple[int, int]] = None) -> None:
        """Açık çizgi (veya eğri) ekler."""
        if len(noktalar) < 2:
            return
        self.ogeler.append(Cizgi([self.T.nokta(x, y) for x, y in noktalar],
                                 renk, kalinlik * self.T.olcek, kesik))


# ----------------------------------------------------------------------------
# 3) YÜZ ÇİZİCİ
# ----------------------------------------------------------------------------

def _sinirla(deger: float, en_az: float, en_cok: float) -> float:
    """Değeri [en_az, en_cok] aralığına sıkıştırır."""
    return max(en_az, min(en_cok, deger))


class YuzCizici:
    """Bir yüz+poz durumunu (sözlük) çizim komutları listesine çevirir.

    Girdi sözlüğü, Enterpolator.yuz_ornekle() çıktısı ile Enterpolator.ornekle() çıktısının
    birleşimidir: {"eye_shape": ..., "mouth": ..., "ear_left": ..., "head_pan": ..., ...}
    """

    PEMBE_BURUN_ALFA = 1.0

    def __init__(self, canli: bool = True):
        """canli=True ise kedi zaman zaman göz kırpar, gözyaşı akar, spiral gözler döner."""
        self._canli = canli
        self._sonraki_kirpma_ms = time.monotonic() * 1000 + 2500
        self._kirpma_baslangic_ms = -1.0

    def _goz_kirpma(self, t_ms: float) -> float:
        """Göz kırpma çarpanını döndürür: 1 = tam açık, 0 = kapalı (170 ms'lik kısa kırpma)."""
        if not self._canli:
            return 1.0
        if self._kirpma_baslangic_ms < 0 and t_ms >= self._sonraki_kirpma_ms:
            self._kirpma_baslangic_ms = t_ms
        if self._kirpma_baslangic_ms >= 0:
            k = (t_ms - self._kirpma_baslangic_ms) / 170.0
            if k >= 1:
                self._kirpma_baslangic_ms = -1.0
                self._sonraki_kirpma_ms = t_ms + 2200 + random.random() * 3200
                return 1.0
            return 1 - math.sin(math.pi * k)
        return 1.0

    def olustur(self, p: Dict[str, Any], t_ms: float = 0.0, kirpma: Optional[float] = None) -> List[Oge]:
        """Tüm sahnenin (kulaklar, kafa, yüz ekranı) çizim komutlarını üretir.

        t_ms: Saat (ms). Spiral gözlerin dönmesi, gözyaşının akması gibi hareketler için.
        kirpma: Test için göz kırpma çarpanını elle vermek istersen (None = otomatik).
        """
        donus = p.get("body_yaw", 0.0) + p.get("head_pan", 0.0)
        egim = p.get("head_tilt", 0.0)
        # Sahte 3B: baş dönünce yana kayar ve daralır, eğilince aşağı/yukarı kayar ve basıklaşır
        taban = (Donusum()
                 .ofset(210 + donus / 135 * 42, 182 - egim / 45 * 24)
                 .olcekle(0.84 * (1 - min(abs(donus), 135) / 135 * 0.2), 0.84 * (1 - abs(egim) / 45 * 0.1))
                 .ofset(-210, -182))
        sahne = Sahne(taban)
        if kirpma is None:
            kirpma = self._goz_kirpma(t_ms)
        self._kafa(sahne, p, t_ms, kirpma)
        return sahne.ogeler

    # ---- parçalar ----------------------------------------------------------

    @staticmethod
    def _kulak(s: Sahne, taraf: str, v: float, p: Dict[str, Any]) -> None:
        """Bir kulağı çizer. v: 0 = geri yatık, 1 = dik."""
        yon = -1 if taraf == "L" else 1
        bx = 105 if taraf == "L" else 315
        s.kaydet()
        s.cevir(bx, 76)
        s.dondur(yon * (1 - v) * 1.7)
        s.cokgen([(-44, 6), (yon * 14, -72), (44, 6)], dolgu=p["head"], cizgi=p["line"], kalinlik=3)
        s.cokgen([(-24, 4), (yon * 11, -50), (24, 4)], dolgu=KULAK_ICI)
        for y in (-20, -46):   # kulağın içindeki kesik çizgiler (tüy dokusu)
            t = (6 - y) / 78
            s.cizgi([(-44 + t * (yon * 14 + 44), y), (44 + t * (yon * 14 - 44), y)],
                    renk_karistir(p["line"], KULAK_ICI, 0.6), 1.5, kesik=(3, 4))
        s.geri_yukle()

    @staticmethod
    def _damla(s: Sahne, x: float, y: float, boyut: float, dolgu: str, kontur: str) -> None:
        """Gözyaşı/ter damlası çizer."""
        nok = zincir(kuadratik((x, y - boyut * 1.5), (x + boyut * 1.1, y - boyut * 0.1), (x, y + boyut)),
                     kuadratik((x, y + boyut), (x - boyut * 1.1, y - boyut * 0.1), (x, y - boyut * 1.5)))
        s.cokgen(nok, dolgu=dolgu, cizgi=kontur, kalinlik=1.5)

    def _iris(self, s: Sahne, ix: float, iy: float, ir: float, p: Dict[str, Any],
              kirp: Sequence[Nokta]) -> None:
        """Göz bebeğini (iris + gözbebeği + parıltılar) çizer; gözün dışına taşan kısmı kırpılır."""
        s.cokgen(daire(ix, iy, ir), dolgu=p["iris"], cizgi=p["line"], kalinlik=2, kirp=kirp)
        s.cokgen(daire(ix, iy + ir * 0.05, ir * 0.46), dolgu=p["line"], kirp=kirp)
        if p["sparkle"] > 0:
            s.cokgen(daire(ix - ir * 0.36, iy - ir * 0.38, ir * 0.3),
                     dolgu=renk_karistir(BEYAZ, p["iris"], p["sparkle"]), kirp=kirp)
            s.cokgen(daire(ix + ir * 0.32, iy + ir * 0.3, ir * 0.13),
                     dolgu=renk_karistir(BEYAZ, p["line"], p["sparkle"]), kirp=kirp)

    def _goz(self, s: Sahne, cx: float, cy: float, p: Dict[str, Any], t_ms: float, kirpma: float) -> None:
        """Tek bir gözü, göz şekline (round, arc, narrow, closed, spiral, blank) göre çizer."""
        R = 32 * p["eye_size"]
        acik = _sinirla(p["eye_open"] * kirpma * p.get("_eyeDip", 1.0), 0, 1)
        lx = _sinirla(p["look_x"], -1, 1)
        ly = _sinirla(p["look_y"], -1, 1)
        cizgi = p["line"]
        sekil = p["eye_shape"]

        if sekil == "closed":   # Huzurlu kapalı göz: aşağı kıvrık kapak + dış köşede kirpikler
            s.cizgi(kuadratik((cx - R * 0.9, cy - R * 0.05), (cx, cy + R * 0.55), (cx + R * 0.9, cy - R * 0.05)),
                    cizgi, 5)
            disari = -1 if cx < 160 else 1
            for i in range(3):
                bx = cx + disari * R * (0.5 + i * 0.17)
                by = cy + R * (0.2 - i * 0.1)
                s.cizgi([(bx, by), (bx + disari * R * 0.2, by + R * 0.24)], cizgi, 3)
            return
        if sekil == "spiral":   # Başı dönmüş: spiral göz, canlıyken yavaşça döner
            tur = 3
            rmax = R * 0.9
            tam = tur * 2 * math.pi
            nok = []
            a = 0.0
            while a <= tam:
                r = rmax * a / tam
                nok.append((math.cos(a) * r, math.sin(a) * r))
                a += 0.12
            s.kaydet()
            s.cevir(cx, cy)
            s.dondur((t_ms / 260.0 if self._canli else 0.0) * (1 if cx < 160 else -1))
            s.cizgi(nok, cizgi, 4.5)
            s.geri_yukle()
            return
        if sekil == "arc":   # Mutlu kapalı göz ^^
            s.cizgi(kuadratik((cx - R * 0.85, cy + R * 0.25), (cx, cy - R * 0.8), (cx + R * 0.85, cy + R * 0.25)),
                    cizgi, 5.5)
            return
        if acik < 0.14:   # Göz neredeyse kapalı: ince aşağı kıvrık çizgi
            s.cizgi(kuadratik((cx - R * 0.95, cy), (cx, cy + R * 0.28), (cx + R * 0.95, cy)), cizgi, 5)
            return
        if sekil == "blank":   # Boş bakış: göz bebeği yok, bembeyaz
            s.cokgen(elips(cx, cy, R * 0.85, R * 0.9 * acik), dolgu=BEYAZ, cizgi=cizgi, kalinlik=3)
            return
        if sekil == "narrow":   # Dar/kısık göz: üst kısmı düz kapakla kesilmiş
            rx, ry = R * 1.05, R * 0.8 * acik
            kapak = cy - ry * 0.15
            bolge = kirp_konveks(elips(cx, cy, rx, ry), dikdortgen(cx - rx - 2, kapak, rx * 2 + 4, ry * 2 + 4))
            s.cokgen(bolge, dolgu=BEYAZ)
            if len(bolge) >= 3:
                self._iris(s, cx + lx * R * 0.35, cy + ry * 0.2 + ly * R * 0.15, R * 0.6 * p["pupil"], p, bolge)
            a = math.asin(_sinirla((kapak - cy) / ry, -1, 1))
            yarim = rx * math.cos(a)
            s.cizgi(elips(cx, cy, rx, ry, a, math.pi - a), cizgi, 2.5)
            s.cizgi([(cx - yarim - 5, kapak), (cx + yarim + 5, kapak)], cizgi, 5.5)
            return

        # Yuvarlak göz (varsayılan)
        rx, ry = R * 0.95, R * 1.08 * acik
        goz = elips(cx, cy, rx, ry)
        s.cokgen(goz, dolgu=BEYAZ)
        self._iris(s, cx + lx * R * 0.38, cy + ly * R * 0.3, R * 0.68 * p["pupil"], p, goz)
        if p["tears"] > 0.25:   # Gözün altında biriken yaş
            renk = renk_karistir(p["tear_color"], BEYAZ, 0.3 + 0.3 * p["tears"])
            s.cokgen(elips(cx, cy + ry * 0.95, rx * 1.1, ry * (0.15 + 0.3 * p["tears"])), dolgu=renk, kirp=goz)
        s.cokgen(goz, cizgi=cizgi, kalinlik=2.5)
        s.cizgi(elips(cx, cy, rx, ry, math.pi * 1.1, math.pi * 1.9), cizgi, 5.5)

    @staticmethod
    def _kas(s: Sahne, cx: float, by: float, derece: float, taraf: str, renk: str) -> None:
        """Bir kaşı çizer. Açı pozitifse iç uç yukarı (üzgün), negatifse aşağı (huysuz)."""
        s.kaydet()
        s.cevir(cx, by)
        s.dondur(derece * math.pi / 180 * (-1 if taraf == "L" else 1))
        s.cizgi(kuadratik((-24, 3), (0, -5), (24, 3)), renk, 5)
        s.geri_yukle()

    @staticmethod
    def _w_agiz(m: float) -> List[Nokta]:
        """Kedi 'w' ağzının çizgi noktalarını döndürür (birkaç ağız tipi bunu kullanıyor)."""
        d = 6 + 8 * m
        return zincir(kuadratik((140, 164), (150, 164 + d), (160, 164)),
                      kuadratik((160, 164), (170, 164 + d), (180, 164)))

    def _agiz(self, s: Sahne, p: Dict[str, Any]) -> None:
        """Ağzı, ağız tipine göre çizer. mouth_open: ağız açıklığı / ifadenin şiddeti (0-1)."""
        m = p["mouth_open"]
        cizgi = p["line"]
        dil = p["blush_color"]
        tip = p["mouth"]
        K = 3.5   # ağız çizgisi kalınlığı

        if tip == "smile":
            s.cizgi(kuadratik((142, 166), (160, 174 + 14 * m), (178, 166)), cizgi, K)
        elif tip == "w":
            s.cizgi(self._w_agiz(m), cizgi, K)
        elif tip == "o":
            rx, ry = 6 + 5 * m, 7 + 9 * m
            s.cokgen(elips(160, 172, rx, ry), dolgu=cizgi)
            s.cokgen(elips(160, 172 + ry * 0.45, rx * 0.6, ry * 0.35), dolgu=dil)
        elif tip == "wavy":
            a = 2.5 + 3 * m
            parcalar = [kuadratik((138 + i * 11, 170), (138 + i * 11 + 5.5, 170 + (a if i % 2 else -a) * 2),
                                  (138 + (i + 1) * 11, 170), 8) for i in range(4)]
            s.cizgi(zincir(*parcalar), cizgi, K)
        elif tip == "y":
            s.cizgi([(160, 153), (160, 165)], cizgi, K)
            s.cizgi([(160, 165), (148 - 6 * m, 177 + 4 * m)], cizgi, K)
            s.cizgi([(160, 165), (172 + 6 * m, 177 + 4 * m)], cizgi, K)
        elif tip == "frown":
            s.cizgi(kuadratik((143, 177), (160, 164 - 12 * m), (177, 177)), cizgi, K)
        elif tip == "grin":   # Kocaman gülüş: açık "D" ağız, içinde dil
            d = (10 + 16 * m) * 1.35
            sekil = zincir(kuadratik((140, 163), (160, 166), (180, 163)),
                           kubik((180, 163), (180, 163 + d), (140, 163 + d), (140, 163)))
            s.cokgen(sekil, dolgu=cizgi)
            s.cokgen(elips(160, 163 + d * 0.78, 12, d * 0.32), dolgu=dil, kirp=sekil)
            s.cokgen(sekil, cizgi=cizgi, kalinlik=K)
        elif tip == "fang":   # Kedi dişi: w ağız + sivri diş
            d = 6 + 8 * m
            s.cizgi(self._w_agiz(m), cizgi, K)
            fx, fy = 166, 164 + d * 0.42
            s.cokgen([(fx - 3.5, fy - 1), (fx + 3.5, fy + 0.5), (fx + 0.8, fy + 6 + 4 * m)],
                     dolgu=BEYAZ, cizgi=cizgi, kalinlik=2)
        elif tip == "tongue":   # Dil çıkarma
            L = 5 + 10 * m
            sekil = zincir([(153, 166), (153, 168 + L * 0.4)],
                           kubik((153, 168 + L * 0.4), (153, 170 + L * 1.25), (167, 170 + L * 1.25),
                                 (167, 168 + L * 0.4)),
                           [(167, 166)])
            s.cokgen(sekil, dolgu=dil, cizgi=cizgi, kalinlik=2.5)
            s.cizgi([(160, 168), (160, 168 + L * 0.6)], cizgi, 1.5)
            s.cizgi(self._w_agiz(m), cizgi, K)
        elif tip == "smirk":   # Yan gülüş
            u = 4 + 8 * m
            s.cizgi(kuadratik((143, 169), (163, 174), (176, 166 - u)), cizgi, K)
            s.cizgi(kuadratik((173, 163 - u), (178, 165 - u), (180, 169 - u)), cizgi, 2.5)
        elif tip == "zigzag":   # Titrek zikzak
            a = 2 + 3.5 * m
            s.cizgi([(138, 170)] + [(138 + (i + 1) * 7.33, 170 + (-a if i % 2 else a)) for i in range(6)],
                    cizgi, K)
        elif tip == "yawn":   # Esneme: iri açık ağız, altta dil
            rx, ry = 9 + 6 * m, 10 + 13 * m
            agiz = elips(160, 170 + ry * 0.35, rx, ry)
            s.cokgen(agiz, dolgu=cizgi)
            s.cokgen(elips(160, 170 + ry * 1.05, rx * 0.9, ry * 0.5), dolgu=dil, kirp=agiz)
            s.cokgen(agiz, cizgi=cizgi, kalinlik=K)
        elif tip == "pout":   # Öpücük / büzük ağız
            k = 0.8 + 0.5 * m
            s.cizgi(zincir(kuadratik((157, 170 - 8 * k), (157 + 11 * k, 170 - 6 * k), (158, 170)),
                           kuadratik((158, 170), (157 + 11 * k, 170 + 6 * k), (157, 170 + 8 * k))), cizgi, K)
        elif tip == "grimace":   # Gergin dişler
            h = 8 + 8 * m
            s.cokgen(yuvarlak_dikdortgen(141, 163, 38, h, 4), dolgu=BEYAZ, cizgi=cizgi, kalinlik=3)
            s.cizgi([(142, 163 + h / 2), (178, 163 + h / 2)], cizgi, 1.5)
            for x in (150, 160, 170):
                s.cizgi([(x, 163), (x, 163 + h)], cizgi, 1.5)
        elif tip == "wobble":   # Sersem: dalgalı kenarlı açık ağız
            h, a = 6 + 9 * m, 2 + 1.5 * m
            ust = [kuadratik((140 + i * 10, 165), (145 + i * 10, 165 + (a if i % 2 else -a)),
                             (150 + i * 10, 165), 6) for i in range(4)]
            alt = [kuadratik((150 + i * 10, 165 + h), (145 + i * 10, 165 + h + (-a if i % 2 else a)),
                             (140 + i * 10, 165 + h), 6) for i in range(3, -1, -1)]
            s.cokgen(zincir(*ust, [(180, 165 + h)], *alt), dolgu=dil, cizgi=cizgi, kalinlik=3)
        elif tip == "shout":   # Bağırma: üstte diş, içte dil olan açık ağız
            h = 10 + 14 * m
            sekil = zincir([(140, 163), (180, 163)],
                           kuadratik((180, 163), (179, 163 + h), (170, 163 + h), 6),
                           [(150, 163 + h)],
                           kuadratik((150, 163 + h), (141, 163 + h), (140, 163), 6))
            s.cokgen(sekil, dolgu=cizgi)
            s.cokgen(elips(160, 163 + h * 1.02, 14, h * 0.42), dolgu=dil, kirp=sekil)
            s.cokgen(dikdortgen(138, 161, 44, 2 + h * 0.26), dolgu=BEYAZ, kirp=sekil)
            s.cokgen(sekil, cizgi=cizgi, kalinlik=3)
        else:   # Bilinmeyen tip: düz çizgi
            s.cizgi([(146, 170), (174, 170)], cizgi, K)

    def _ofke_isareti(self, s: Sahne, x: float, y: float, boyut: float, renk: str) -> None:
        """Öfke işaretini (dört kıvrık çizgi) çizer."""
        s.kaydet()
        s.cevir(x, y)
        s.olcekle(boyut, boyut)
        for i in range(4):
            s.kaydet()
            s.dondur(i * math.pi / 2)
            s.cizgi(kuadratik((4, -15), (4, -4), (15, -4)), renk, 4.5)
            s.geri_yukle()
        s.geri_yukle()

    def _kafa(self, s: Sahne, p: Dict[str, Any], t_ms: float, kirpma: float) -> None:
        """Kulaklar + kafa + yüz ekranı: sahnenin tamamını sırayla çizer (arkadan öne)."""
        zemin = p["face_bg"]
        self._kulak(s, "L", p.get("ear_left", 1.0), p)
        self._kulak(s, "R", p.get("ear_right", 1.0), p)
        s.cokgen(yuvarlak_dikdortgen(40, 70, 340, 260, 22), dolgu=p["head"], cizgi=p["line"], kalinlik=3)
        s.cokgen(yuvarlak_dikdortgen(50, 80, 320, 240, 16), dolgu=zemin)

        s.kaydet()
        s.cevir(50, 80)   # Bundan sonrası yüz ekranının kendi koordinatları (320x240)

        # Alındaki süs deseni (kafa renginin %85'i)
        desen = renk_karistir(p["head"], zemin, 0.85)
        s.cokgen([(122, 0), (160, 44), (198, 0)], dolgu=desen)
        for y in (64, 82):
            s.cokgen([(0, y), (24, y + 6), (0, y + 12)], dolgu=desen)
            s.cokgen([(320, y), (296, y + 6), (320, y + 12)], dolgu=desen)

        # Alın gölgesi: mavi = dehşet, kırmızı = öfke (yukarıdan aşağı solarak, şerit şerit)
        for deger, rgb in ((p["gloom"], "#78A0D7"), (p["rage"], "#F06973")):
            if deger > 0:
                serit = 12
                for j in range(serit):
                    alfa = 0.6 * deger * (1 - (j + 0.5) / serit)
                    s.cokgen(dikdortgen(0, 115 * j / serit, 320, 115 / serit + 0.5),
                             dolgu=renk_karistir(rgb, zemin, alfa))

        ofke = p.get("_angerA", 1.0 if p["anger_mark"] else 0.0)
        if ofke > 0:
            nabiz = 1 + 0.08 * math.sin(t_ms / 120.0) if self._canli else 1.0
            self._ofke_isareti(s, 38, 32, nabiz, renk_karistir("#D7263D", zemin, ofke))

        kizar = p.get("_blushA", 1.0 if p["blush"] else 0.0)
        if kizar > 0:
            for bx in (62, 258):
                s.cokgen(elips(bx, 152, 22, 10), dolgu=renk_karistir(p["blush_color"], zemin, 0.45 * kizar))
                for i in range(4):
                    x = bx - 14 + i * 8
                    s.cizgi([(x, 158), (x + 6, 146)], renk_karistir(p["blush_color"], zemin, kizar), 2)

        self._goz(s, 100, 112, p, t_ms, kirpma)
        self._goz(s, 220, 112, p, t_ms, kirpma)

        kas = p.get("_browA", 1.0 if p["brow_show"] else 0.0)
        if kas > 0:
            by = 112 - 32 * p["eye_size"] * 1.3 - p["brow_height"] * 14
            renk = renk_karistir(p["line"], zemin, kas)
            self._kas(s, 100, by, p["brow_left"], "L", renk)
            self._kas(s, 220, by, p["brow_right"], "R", renk)

        s.cokgen([(153, 144), (167, 144), (160, 152)], dolgu=p["blush_color"], cizgi=p["line"], kalinlik=2)

        # Ağız: yana kayma, eğim ve genişlik kareler arasında yumuşakça değişir
        s.kaydet()
        s.cevir(160 + p["mouth_x"] * 22, 168)
        s.dondur(p["mouth_tilt"] * math.pi / 180)
        s.olcekle(p["mouth_width"], p.get("_mouthSq", 1.0))
        s.cevir(-160, -168)
        self._agiz(s, p)
        s.geri_yukle()

        if p["tears"] > 0:   # Akan gözyaşı damlaları
            R = 32 * p["eye_size"]
            boyut = 4 + 5 * p["tears"]
            faz = (t_ms / 45.0) % 30 if self._canli else 8.0
            for cx in (100, 220):
                self._damla(s, cx - R * 0.55, 112 + R * 0.95 + 8 + faz, boyut, p["tear_color"], p["line"])
                if p["tears"] > 0.5:
                    self._damla(s, cx + R * 0.5, 112 + R * 0.95 + 22 + ((faz + 14) % 30), boyut * 0.75,
                                p["tear_color"], p["line"])

        ter = p.get("_sweatA", 1.0 if p["sweat"] else 0.0)
        if ter > 0:
            self._damla(s, 286, 40, 9, renk_karistir("#E8F4FC", zemin, 0.9 * ter),
                        renk_karistir(p["tear_color"], zemin, 0.9 * ter))
        s.geri_yukle()
