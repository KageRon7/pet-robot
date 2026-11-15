"""Davranış ağacı: kedinin durumunu çağrılar arasında hatırlayan kurallı beyin.

Eski kural tablosu her çağrıda sıfırdan başlıyordu. Bu beyin durumu kendi içinde tutar:
  - merdiven basamağı: dinlenme -> ilgilenme -> sıkılma -> uyku
  - ruh hali (keyifli / üzgün), zamanla sönen
  - alışma (aynı olay tekrarlanınca tepki azalır)
  - üzüntü merdiveni, yokluk süresi, kendiliğinden davranış sayaçları

Üç giriş noktası var:
  decide(b1)    -> Decision        Olay gelince. İmza eskisiyle aynı, asla hata fırlatmaz.
  karar_ver(b1) -> Decision | None Aynısı, ama "hiç tepki verme"yi None ile söyler.
  tik(b1)       -> Decision | None Yaklaşık 1 sn'de bir; yeni bir şey yoksa çoğunlukla None.

None "hiçbir şey yapma" demektir: çalan animasyon kesilmez.
Zaman kaynağı her zaman b1.now'dır (testte saati biz ilerletiriz).
Ayarların hepsi brain/ayarlar.py içindedir.
"""

from __future__ import annotations

import copy
import logging
import random
import threading
from dataclasses import dataclass, field

from contracts import BrainContext, Decision

from brain.ayarlar import VARSAYILAN, Ayarlar, Tepki

log = logging.getLogger(__name__)

DINLENME = "dinlenme"
ILGILENME = "ilgilenme"
SIKILMA = "sikilma"
UYKU = "uyku"

SAAT_GERI_TOLERANSI_S = 5.0  # saat bu kadardan fazla geri giderse durum sıfırlanır


@dataclass
class BeyinDurumu:
    """Çağrılar arasında yaşayan her şey. Sadece bu dosya değiştirir."""

    basamak: str = DINLENME
    son_zaman: float | None = None  # en son çağrının zamanı
    son_yeni_olay: float = 0.0  # en son yeni (taze) olayın zamanı
    ruh_hali: float = 0.0  # -1 üzgün ... +1 keyifli
    alisma: dict[str, float] = field(default_factory=dict)  # olay adı -> alışma puanı (0-1)
    gorulen: list[tuple[str, float]] = field(default_factory=list)  # (olay adı, mutlak zaman)
    kullanici_var: bool | None = None  # None = bilinmiyor
    varlik_zamani: float = 0.0  # kullanici_var'ı belirleyen olayın zamanı (eski olay ezmesin)
    ayrilma_zamani: float | None = None
    uzuntu_asama: int = 0  # 0 merak, 1 oyunbaz, 2 birlikte üzülme
    uzuntu_asama_zamani: float | None = None
    uzuntu_son: float | None = None
    sessizlik_bitis: float = 0.0  # bu zamana kadar kendiliğinden eylem yok
    sonraki_ilgi: float | None = None
    sonraki_kendi: float | None = None
    son_olay_karari: Decision | None = None
    son_olay_karar_zamani: float = 0.0


# --------------------------------------------------------------------------- yardımcılar


def _sinirla(deger: float, alt: float, ust: float) -> float:
    # Değeri alt ile üst arasında tutar.
    return max(alt, min(ust, deger))


def _aralik(rng: random.Random, aralik: tuple[float, float]) -> float:
    # Verilen (en az, en çok) arasında rastgele bir süre seçer.
    return rng.uniform(aralik[0], aralik[1])


def _karar_yap(tepki: Tepki, siddet: float, sebep: str) -> Decision:
    # Tepki tarifinden B2 kararı (Decision) kurar. Sözleşmeye uymayan değerde Pydantic hata verir.
    return Decision(
        emotion=tepki.duygu,
        intensity=round(_sinirla(siddet, 0.05, 1.0), 2),
        duration_s=tepki.sure_s,
        reason=sebep,
        clip=tepki.klip,
    )


def _bastan_kur(d: BeyinDurumu, t: float, rng: random.Random, ay: Ayarlar) -> None:
    # Durumu temiz bir başlangıca getirir (ilk çağrı ya da saat geri giderse).
    d.__dict__.update(copy.deepcopy(BeyinDurumu().__dict__))
    d.son_zaman = t
    d.son_yeni_olay = t
    d.sonraki_kendi = t + _aralik(rng, ay.kendi_eylem_aralik_s)


def _sondur(d: BeyinDurumu, dt: float, ay: Ayarlar) -> None:
    # Geçen süreye göre ruh halini ve alışma puanlarını söndürür (yarı ömür kuralı).
    if dt <= 0:
        return
    d.ruh_hali *= 0.5 ** (dt / ay.ruh_hali_yari_omur_s)
    carpan = 0.5 ** (dt / ay.alisma_yari_omur_s)
    d.alisma = {ad: p * carpan for ad, p in d.alisma.items() if p * carpan >= 0.01}


# --------------------------------------------------------------------------- olay tepkileri


def _uzuntu_tepkisi(d: BeyinDurumu, mt: float, ay: Ayarlar) -> tuple[Tepki, str] | None:
    # Üzgün kullanıcıya merdiven: önce merak, sürerse oyunbazlık, yine sürerse birlikte üzülme.
    if d.uzuntu_son is None or mt - d.uzuntu_son > ay.uzuntu_sifirla_s:
        d.uzuntu_asama = 0
        d.uzuntu_asama_zamani = mt
        d.uzuntu_son = mt
        return ay.uzuntu[0], "Kullanıcı üzgün: önce merak"
    d.uzuntu_son = mt
    if d.uzuntu_asama_zamani is not None and mt - d.uzuntu_asama_zamani < ay.uzuntu_asama_min_aralik_s:
        return None  # aynı üzüntü anı, aşama ilerlemez, tekrar tepki de verilmez
    d.uzuntu_asama = min(2, d.uzuntu_asama + 1)
    d.uzuntu_asama_zamani = mt
    sebepler = ("", "Üzüntü sürüyor: oyunbazlık", "Üzüntü sürüyor: birlikte üzülme")
    return ay.uzuntu[d.uzuntu_asama], sebepler[d.uzuntu_asama]


def _tepki_sec(
    d: BeyinDurumu, ad: str, mt: float, yokluk_s: float | None, ay: Ayarlar
) -> tuple[Tepki, str] | None:
    # Olay adına göre ilk tepkiyi seçer; tepki verilmeyecekse None.
    if ad == "sad":
        return _uzuntu_tepkisi(d, mt, ay)
    if ad == "user_arrived":
        if yokluk_s is None or yokluk_s < ay.kisa_yokluk_s:
            seviye = "kucuk"
        elif yokluk_s < ay.uzun_yokluk_s:
            seviye = "orta"
        else:
            seviye = "buyuk"
        return ay.karsilama[seviye], f"Karşılama ({seviye}): kullanıcı geri geldi"
    tepki = ay.tepkiler.get(ad)
    if tepki is None:
        return None
    return tepki, f"Olay: {ad}"


def _olay_isle(
    d: BeyinDurumu, ad: str, mt: float, taze: bool, rng: random.Random, ay: Ayarlar
) -> Decision | None:
    # Tek bir yeni olayı işler: varlık, ruh hali, alışma güncellenir; tepki varsa Decision döner.
    yokluk_s = None
    if ad == "user_arrived" and d.ayrilma_zamani is not None:
        yokluk_s = mt - d.ayrilma_zamani

    # Varlık bilgisi eski olaylardan da öğrenilir (program yeni açıldıysa), ama bilinen
    # durumdan daha eski bir olay, daha yeni bilgiyi ezmez.
    if ad in ("user_left", "user_arrived") and mt >= d.varlik_zamani:
        d.varlik_zamani = mt
        if ad == "user_left":
            d.kullanici_var = False
            d.ayrilma_zamani = mt
            d.sonraki_ilgi = None
        else:
            d.kullanici_var = True
            d.ayrilma_zamani = None
            d.sonraki_ilgi = mt + _aralik(rng, ay.ilgi_isteme_aralik_s)

    if not taze:
        return None  # eski olay: tepki yok

    d.son_yeni_olay = max(d.son_yeni_olay, mt)
    uyandi = d.basamak == UYKU
    if d.basamak in (UYKU, SIKILMA):
        d.basamak = DINLENME
        d.sonraki_kendi = mt + _aralik(rng, ay.kendi_eylem_aralik_s)
        if d.kullanici_var:
            d.sonraki_ilgi = mt + _aralik(rng, ay.ilgi_isteme_aralik_s)

    d.sonraki_kendi = mt + _aralik(rng, ay.kendi_eylem_aralik_s)  # tepkiden hemen sonra kendi eylemi olmasın
    d.ruh_hali = _sinirla(d.ruh_hali + ay.ruh_etkisi.get(ad, 0.0), -1.0, 1.0)

    if ad in ("smile", "looking_at_robot_long"):
        d.basamak = ILGILENME
        if d.kullanici_var:
            d.sonraki_ilgi = mt + _aralik(rng, ay.ilgi_isteme_aralik_s)
    elif ad == "angry":
        d.sessizlik_bitis = mt + ay.geri_cekilme_sessizlik_s

    secim = _tepki_sec(d, ad, mt, yokluk_s, ay)
    if secim is None:
        return None
    tepki, sebep = secim

    carpan = 1.0
    if ad not in ay.alisma_disi:
        h = d.alisma.get(ad, 0.0)
        d.alisma[ad] = min(1.0, h + ay.alisma_artis)
        carpan = max(ay.alisma_taban, 1.0 - h)
        p_sessiz = min(ay.sessiz_en_fazla, ay.sessiz_taban_olasilik + ay.sessiz_alisma_katsayisi * h)
        if not uyandi and rng.random() < p_sessiz:
            log.info("Davranış beyni: '%s' olayına bu sefer tepki verilmedi (alışma %.2f)", ad, h)
            return None

    siddet = tepki.siddet * carpan * (1.0 + ay.ruh_siddet_etkisi * d.ruh_hali)
    karar = _karar_yap(tepki, siddet, sebep)
    d.son_olay_karari = karar
    d.son_olay_karar_zamani = mt
    return karar


# --------------------------------------------------------------------------- zamana bağlı davranışlar


def _zamana_bagli(d: BeyinDurumu, t: float, rng: random.Random, ay: Ayarlar) -> Decision | None:
    # Yeni olay yokken: uyku, sıkılma, ilgi isteme ve kendiliğinden küçük eylemler.
    gecen = t - d.son_yeni_olay

    if d.basamak in (DINLENME, ILGILENME, SIKILMA) and gecen >= ay.uyku_s:
        d.basamak = UYKU
        return _karar_yap(ay.uyku_tepkisi, ay.uyku_tepkisi.siddet, "Uzun süredir bir şey olmadı: uyku")

    sikilabilir = d.basamak == ILGILENME or (
        d.basamak == DINLENME and not ay.sikilma_sadece_ilgiden_sonra
    )
    if sikilabilir and gecen >= ay.sikilma_s:
        d.basamak = SIKILMA
        return _karar_yap(ay.sikilma_tepkisi, ay.sikilma_tepkisi.siddet, "Yeni bir şey olmadı: sıkılma")

    if t < d.sessizlik_bitis:
        return None

    # Kullanıcı var ama ilgilenmiyor: 20-30 dakikada bir küçük ilgi isteme.
    # Uyuyan kedi de bunun için uyanır; sonra yine 5 dk sonra uykuya döner.
    if (
        d.kullanici_var
        and d.basamak in (DINLENME, SIKILMA, UYKU)
        and d.sonraki_ilgi is not None
        and t >= d.sonraki_ilgi
    ):
        d.basamak = DINLENME
        d.son_yeni_olay = t
        d.sonraki_ilgi = t + _aralik(rng, ay.ilgi_isteme_aralik_s)
        d.sonraki_kendi = t + _aralik(rng, ay.kendi_eylem_aralik_s)
        tepki = rng.choice(ay.ilgi_isteme_tepkileri)
        return _karar_yap(tepki, tepki.siddet, "İlgi isteme: kullanıcı var ama ilgilenmiyor")

    # Dinlenirken arada kendi başına küçük eylem; ruh hali havuzu belirler.
    if d.basamak == DINLENME and d.sonraki_kendi is not None and t >= d.sonraki_kendi:
        d.sonraki_kendi = t + _aralik(rng, ay.kendi_eylem_aralik_s)
        if d.ruh_hali >= 0.3:
            havuz = ay.eylem_keyifli
        elif d.ruh_hali <= -0.3:
            havuz = ay.eylem_uzgun
        else:
            havuz = ay.eylem_normal
        tepki = rng.choice(havuz)
        return _karar_yap(tepki, tepki.siddet, "Kendiliğinden küçük eylem")
    return None


# --------------------------------------------------------------------------- çekirdek


def adim(d: BeyinDurumu, b1: BrainContext, rng: random.Random, ay: Ayarlar, tik: bool = False) -> Decision | None:
    """Durumu (d) günceller ve karar döner; tepki yoksa None. Durumu doğrudan değiştirir."""
    t = b1.now.timestamp()
    if d.son_zaman is None or t < d.son_zaman - SAAT_GERI_TOLERANSI_S:
        _bastan_kur(d, t, rng, ay)
    dt = max(0.0, t - d.son_zaman)
    d.son_zaman = t
    _sondur(d, dt, ay)

    # Program ortadayken açıldıysa kullanıcının masada olduğunu oturum bilgisinden öğren.
    if d.kullanici_var is None and b1.session.user_present_minutes > 0:
        d.kullanici_var = True
        d.sonraki_ilgi = t + _aralik(rng, ay.ilgi_isteme_aralik_s)

    # Yeni olayları bul: B1 son 5 dk'yı taşır, aynı olayı tekrar saymamak için mutlak zamana bak.
    yeniler: list[tuple[float, str, float]] = []
    for olay in b1.recent_events:
        if olay.ago_s > ay.gorulen_saklama_s:
            continue  # sözleşmeye göre B1 son 5 dk'yı taşır; daha eskisi sızıntıdır, yok say
        ad = olay.event.value
        mt = t - olay.ago_s
        if any(a == ad and abs(mt - z) <= ay.olay_tekrar_toleransi_s for a, z in d.gorulen):
            continue
        d.gorulen.append((ad, mt))
        yeniler.append((mt, ad, olay.ago_s))
    d.gorulen = [(a, z) for a, z in d.gorulen if t - z <= ay.gorulen_saklama_s]
    yeniler.sort()

    karar = None
    taze_var = False
    for mt, ad, ago_s in yeniler:
        taze = ago_s <= ay.taze_olay_s
        taze_var = taze_var or taze
        k = _olay_isle(d, ad, mt, taze, rng, ay)
        if k is not None:
            karar = k  # aynı anda birden çok olay gelirse en yenisi kazanır
    if taze_var:
        return karar  # yeni olay varsa zamana bağlı davranışlar bu çağrıda beklesin

    karar = _zamana_bagli(d, t, rng, ay)
    if (
        karar is None
        and not tik
        and d.son_olay_karari is not None
        and t - d.son_olay_karar_zamani <= ay.tekrar_karar_s
    ):
        # Olay için tik zaten işlediyse, decide aynı kararı tekrar döner (idle ile kesmesin).
        return d.son_olay_karari
    return karar


class DavranisBeyni:
    """Durumu tutan tek nesne. Kilitli: router beyni ayrı thread'lerden çağırabilir."""

    # Ayarları ve rastgelelik kaynağını alır. tohum verilirse davranış tekrarlanabilir olur.
    def __init__(self, ayarlar: Ayarlar = VARSAYILAN, tohum: int | None = None) -> None:
        self.ayarlar = ayarlar
        self._rng = random.Random(tohum)
        self._kilit = threading.Lock()
        self.durum = BeyinDurumu()

    # Bağlamı işler. Durum önce kopyada güncellenir; hata olursa temiz başlanır ve idle döner.
    def isle(self, b1: BrainContext, tik: bool = False) -> Decision | None:
        with self._kilit:
            try:
                kopya = copy.deepcopy(self.durum)
                karar = adim(kopya, b1, self._rng, self.ayarlar, tik)
                self.durum = kopya
                return karar
            except Exception as hata:
                log.warning("Davranış beyni hata verdi (%r), durum sıfırlanıp idle'a düşülüyor", hata)
                self.durum = BeyinDurumu()
                return Decision.idle("Hata, bekleme durumu")

    # Durumu sıfırlar (testlerde ve elle denemede işe yarar).
    def sifirla(self) -> None:
        with self._kilit:
            self.durum = BeyinDurumu()


# --------------------------------------------------------------------------- dışarıya açılan fonksiyonlar

_beyin = DavranisBeyni()


def decide(b1: BrainContext) -> Decision:
    """Olay gelince çağrılır. Asla exception fırlatmaz; tepki yoksa ya da hata olursa idle döner."""
    try:
        karar = _beyin.isle(b1, tik=False)
        return karar if karar is not None else Decision.idle("Bu sefer tepki yok")
    except Exception:
        return Decision.idle("Hata, bekleme durumu")


def karar_ver(b1: BrainContext) -> Decision | None:
    """decide ile aynı, ama 'hiç tepki verme' None döner (router çalan animasyonu kesmez)."""
    try:
        return _beyin.isle(b1, tik=False)
    except Exception:
        return Decision.idle("Hata, bekleme durumu")


def tik(b1: BrainContext) -> Decision | None:
    """Yaklaşık 1 sn'de bir çağrılır. Sıkılma, uyku, ilgi isteme ve kendi eylemlerini üretir."""
    try:
        return _beyin.isle(b1, tik=True)
    except Exception:
        return Decision.idle("Hata, bekleme durumu")


def sifirla(ayarlar: Ayarlar | None = None, tohum: int | None = None) -> None:
    """Küresel beyni baştan kurar (ayar değiştirmek ya da testler için)."""
    global _beyin
    _beyin = DavranisBeyni(ayarlar or VARSAYILAN, tohum)
