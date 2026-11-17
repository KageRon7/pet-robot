"""Davranış ağacının bütün ayarları tek yerde: süreler, olasılıklar, tepkiler, klip adları.

Bir şeyi değiştirmek istediğinde (örneğin uyku süresini) başka hiçbir dosyaya dokunma,
sadece buraya bak. Simülatörde hızlı denemek için Ayarlar.hizli() kullanılır.
"""

from dataclasses import dataclass, field, replace
from typing import NamedTuple


class Tepki(NamedTuple):
    """Bir tepkinin tarifi: hangi duygu, ne şiddette, kaç sn, hangi klip (yoksa None)."""

    duygu: str
    siddet: float
    sure_s: float
    klip: str | None = None


# Klip adları = motion/clips/ içindeki dosya adları (.json olmadan).
# Bilinmeyen ad olursa router yok sayar ve duyguya göre devam eder, yani sistem durmaz.
KLIP_SIKILMA = "Im_so_boored"
KLIP_MERAK = "curious"
KLIP_MERAK_2 = "curious2"
KLIP_MUTLU = "happy"
KLIP_OYUN = "playful"
KLIP_UZGUN = "sad"
KLIP_UYKU = "sleepy"
KLIP_KORKU = "startled"
KLIP_KOSE = None  # köşeye çekilme için özel klip yok; Reşat/Tuğra yapınca adı buraya yaz


def _varsayilan_tepkiler() -> dict[str, Tepki]:
    # Olay adı -> ilk tepki. (smile/yawn/user_left gibi adlar contracts.EventType değerleridir.)
    return {
        "smile": Tepki("happy", 0.8, 5, KLIP_MUTLU),
        "looking_at_robot_long": Tepki("playful", 0.6, 5, KLIP_OYUN),
        "yawn": Tepki("sleepy", 0.6, 8, KLIP_UYKU),  # esneme klibi yok: uykulu klibi
        "drowsy": Tepki("sleepy", 0.5, 10, KLIP_UYKU),
        "angry": Tepki("startled", 0.5, 5, KLIP_KORKU),  # geri çekilme
        "surprised": Tepki("curious", 0.6, 5, KLIP_MERAK),
        "user_left": Tepki("curious", 0.5, 6, KLIP_MERAK),  # üzülmez, merakla arkasından bakar
    }


def _varsayilan_uzuntu() -> tuple[Tepki, Tepki, Tepki]:
    # Kullanıcı üzgünken merdiven: 1) merak 2) oyun teklifi 3) köşesine çekilme
    return (
        Tepki("curious", 0.5, 6, KLIP_MERAK),
        Tepki("playful", 0.6, 6, KLIP_OYUN),
        Tepki("idle", 0.2, 30, KLIP_KOSE),
    )


def _varsayilan_karsilama() -> dict[str, Tepki]:
    # Geri gelince karşılama, yokluk süresine göre küçük / orta / büyük.
    return {
        "kucuk": Tepki("curious", 0.4, 4, KLIP_MERAK),
        "orta": Tepki("happy", 0.65, 5, KLIP_MUTLU),
        "buyuk": Tepki("playful", 0.95, 7, KLIP_OYUN),
    }


def _varsayilan_ruh_etkisi() -> dict[str, float]:
    # Her olayın ruh haline etkisi (-1 üzgün ... +1 keyifli).
    return {
        "smile": 0.5,
        "looking_at_robot_long": 0.2,
        "user_arrived": 0.2,
        "user_left": 0.0,  # kalkınca üzülmez
        "sad": 0.0,  # kullanıcı üzgünken kedi onunla birlikte üzülmez
        "angry": -0.2,
        "yawn": -0.05,
    }


@dataclass(frozen=True)
class Ayarlar:
    # --- Merdiven süreleri (saniye) ---
    sikilma_s: float = 10.0  # yeni bir şey olmazsa sıkılma
    uyku_s: float = 300.0  # 5 dk yeni bir şey olmazsa uyku
    # True: sıkılma sadece bir ilgiden (gülümseme, uzun bakış) sonra gelir.
    # False: hiçbir şey olmazsa dinlenirken de 10 sn sonra sıkılır (dinlenme 10 sn sürer).
    sikilma_sadece_ilgiden_sonra: bool = True

    # --- Olay takibi ---
    taze_olay_s: float = 10.0  # bundan eski olay (program yeni açıldı) tepki doğurmaz
    olay_tekrar_toleransi_s: float = 2.0  # aynı olayı iki kez saymamak için zaman toleransı
    gorulen_saklama_s: float = 330.0  # B1 son 5 dk'yı taşır

    # --- Ruh hali ---
    ruh_hali_yari_omur_s: float = 180.0  # ruh hali bu sürede yarıya iner
    ruh_etkisi: dict[str, float] = field(default_factory=_varsayilan_ruh_etkisi)
    ruh_siddet_etkisi: float = 0.2  # tam keyifli kedi tepkileri %20 büyük yapar

    # --- Alışma ve tepkisizlik ---
    alisma_artis: float = 0.25  # her olayda alışma puanı artışı
    alisma_yari_omur_s: float = 300.0  # alışma puanı bu sürede yarıya iner
    alisma_taban: float = 0.3  # alışınca tepki en az bu kadarı kalır
    sessiz_taban_olasilik: float = 0.08  # bazen hiç tepki verme
    sessiz_alisma_katsayisi: float = 0.4  # alıştıkça sessiz kalma artar
    sessiz_en_fazla: float = 0.6
    alisma_disi: frozenset[str] = frozenset({"user_arrived", "user_left", "sad"})

    # --- Üzüntü merdiveni ---
    uzuntu_asama_min_aralik_s: float = 20.0  # bu süre dolmadan aşama ilerlemez
    uzuntu_sifirla_s: float = 180.0  # üzgün olay gelmezse merdiven sıfırlanır

    # --- Köşeye çekilme (oyun teklifi de işe yaramazsa) ---
    kose_s: float = 600.0  # köşede kalma süresi (10 dk)

    # --- Sinirli kullanıcı ---
    geri_cekilme_sessizlik_s: float = 60.0  # bu süre kendi kendine eylem yok

    # --- Yokluk süresine göre karşılama ---
    kisa_yokluk_s: float = 120.0
    uzun_yokluk_s: float = 900.0

    # --- Kendiliğinden davranışlar ---
    ilgi_isteme_aralik_s: tuple[float, float] = (1200.0, 1800.0)  # 20-30 dk
    kendi_eylem_aralik_s: tuple[float, float] = (60.0, 180.0)
    tekrar_karar_s: float = 3.0  # aynı olay için ikinci çağrıda aynı karar döner

    # --- Tepkiler ---
    tepkiler: dict[str, Tepki] = field(default_factory=_varsayilan_tepkiler)
    uzuntu: tuple[Tepki, Tepki, Tepki] = field(default_factory=_varsayilan_uzuntu)
    karsilama: dict[str, Tepki] = field(default_factory=_varsayilan_karsilama)
    kose_cikis_tepkisi: Tepki = Tepki("curious", 0.3, 4, KLIP_MERAK)  # köşeden çıkarken
    sikilma_tepkisi: Tepki = Tepki("idle", 0.4, 6, KLIP_SIKILMA)
    uyku_tepkisi: Tepki = Tepki("sleepy", 0.5, 60, KLIP_UYKU)
    # Dinlenirken küçük eylemler: ruh haline göre havuz seçilir.
    eylem_keyifli: tuple[Tepki, ...] = (Tepki("happy", 0.3, 3, KLIP_MUTLU),)
    eylem_normal: tuple[Tepki, ...] = (
        Tepki("curious", 0.3, 3, KLIP_MERAK),
        Tepki("curious", 0.3, 3, KLIP_MERAK_2),
    )
    eylem_uzgun: tuple[Tepki, ...] = (Tepki("sad", 0.25, 3, KLIP_UZGUN),)
    ilgi_isteme_tepkileri: tuple[Tepki, ...] = (
        Tepki("curious", 0.5, 5, KLIP_MERAK_2),
        Tepki("playful", 0.5, 5, KLIP_OYUN),
    )

    # Simülatörde denemek için süreleri kısaltılmış ayarlar.
    @classmethod
    def hizli(cls) -> "Ayarlar":
        return replace(
            cls(),
            sikilma_s=5.0,
            uyku_s=40.0,
            ilgi_isteme_aralik_s=(60.0, 90.0),
            kendi_eylem_aralik_s=(10.0, 20.0),
            ruh_hali_yari_omur_s=30.0,
            kisa_yokluk_s=10.0,
            uzun_yokluk_s=40.0,
            uzuntu_asama_min_aralik_s=5.0,
            uzuntu_sifirla_s=40.0,
            kose_s=60.0,
            geri_cekilme_sessizlik_s=15.0,
        )


VARSAYILAN = Ayarlar()