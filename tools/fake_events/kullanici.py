"""
Sahte kullanıcı: kameranın önünde oturan hayali bir insan.

Gerçek Computer Vision kodu hazır olana kadar, onun göndereceği mesajları
(Sözleşme A1 ve A2) bu sınıf üretir. Kullanıcı masaya gelir, bir süre oturur,
arada gülümser, esner, robota bakar, sonra kalkıp gider. Bütün eşikler
sözleşmedekiyle aynıdır: user_arrived için 2 sn, user_left için 10 sn,
looking_at_robot_long için 3 sn.

Bu sınıf kendi saatini tutmaz; kaç saniye geçtiğini üreteç söyler. Böylece
testlerde 10 dakikalık bir oturumu bir saniyede simüle edebiliriz.
"""

import random
from dataclasses import dataclass

from contracts import EventType, FaceTrack, PerceptionEvent

# Sözleşme A2'deki süre eşikleri (saniye).
GELIS_ESIGI_S = 2.0
GIDIS_ESIGI_S = 10.0
BAKIS_ESIGI_S = 3.0


@dataclass
class KullaniciAyarlari:
    """Sahte kullanıcının ne kadar sık ne yapacağını belirleyen ayarlar."""

    masada_kalma_s: tuple[float, float] = (40.0, 120.0)  # oturma süresi aralığı
    uzakta_kalma_s: tuple[float, float] = (5.0, 40.0)  # 10 sn altı: user_left gitmez
    gulumseme_dakikada: float = 3.0
    esneme_dakikada: float = 1.0
    uyuklama_dakikada: float = 0.3
    bakma_s: tuple[float, float] = (1.0, 6.0)  # robota bakış süresi aralığı
    bakmama_s: tuple[float, float] = (10.0, 40.0)


class SahteKullanici:
    """Her `adim` çağrısında bir A1 mesajı ve o anda biten A2 olaylarını üretir."""

    # Kullanıcıyı başlangıçta "uzakta" kurar; ilk geliş birkaç saniye içinde olur.
    def __init__(self, rnd: random.Random, ayarlar: KullaniciAyarlari | None = None):
        self._rnd = rnd
        self._ayar = ayarlar or KullaniciAyarlari()

        self._masada = False
        self._durum_baslangici: float | None = None  # masaya geliş / gidiş anı
        self._durum_bitisi: float | None = None  # bir sonraki geliş / gidiş anı
        self._gelis_bildirildi = False  # user_arrived gönderildi mi

        self._x, self._y = 0.5, 0.5
        self._bakiyor = False
        self._bakis_baslangici = 0.0
        self._bakis_bitisi = 0.0
        self._bakis_bildirildi = False

        self._mesgul_bitis = 0.0  # süren bir gülümseme/esneme bitmeden yenisi başlamaz
        self._bekleyen: list[tuple[float, PerceptionEvent]] = []  # (gönderilme anı, olay)

    # Bir zaman adımı ilerler: A1 mesajını ve gönderilme zamanı gelen A2 olaylarını döndürür.
    def adim(self, simdi: float, dt: float) -> tuple[FaceTrack, list[PerceptionEvent]]:
        if self._durum_bitisi is None:
            # İlk adım: kullanıcı 1-3 sn sonra masaya gelecek.
            self._durum_baslangici = simdi
            self._durum_bitisi = simdi + self._rnd.uniform(1.0, 3.0)

        self._gelme_gitme(simdi)
        if self._masada:
            self._yuzu_oynat(dt)
            self._bakisi_guncelle(simdi)
            self._ifade_dene(simdi, dt)

        hazir = [olay for zaman, olay in self._bekleyen if zaman <= simdi]
        self._bekleyen = [(z, o) for z, o in self._bekleyen if z > simdi]
        return self._yuz_takibi(simdi), hazir

    # Kullanıcının masaya gelişini ve gidişini yönetir; eşikler aşılınca olay üretir.
    def _gelme_gitme(self, simdi: float) -> None:
        if simdi >= self._durum_bitisi:
            self._masada = not self._masada
            self._durum_baslangici = simdi
            aralik = self._ayar.masada_kalma_s if self._masada else self._ayar.uzakta_kalma_s
            self._durum_bitisi = simdi + self._rnd.uniform(*aralik)
            if self._masada:
                self._bakiyor = False
                self._bakis_bitisi = simdi + self._rnd.uniform(*self._ayar.bakmama_s)

        sure = simdi - self._durum_baslangici
        if self._masada and not self._gelis_bildirildi and sure >= GELIS_ESIGI_S:
            self._gelis_bildirildi = True
            self._olay_ekle(simdi, EventType.USER_ARRIVED, self._durum_baslangici, 0.0)
        elif not self._masada and self._gelis_bildirildi and sure >= GIDIS_ESIGI_S:
            self._gelis_bildirildi = False
            self._olay_ekle(simdi, EventType.USER_LEFT, self._durum_baslangici, 0.0)

    # Yüzün kameradaki konumunu küçük rastgele adımlarla kaydırır (0-1 arasında tutar).
    def _yuzu_oynat(self, dt: float) -> None:
        self._x = min(0.95, max(0.05, self._x + self._rnd.gauss(0, 0.10) * dt**0.5))
        self._y = min(0.95, max(0.05, self._y + self._rnd.gauss(0, 0.05) * dt**0.5))

    # Kullanıcının robota bakıp bakmadığını değiştirir; 3 sn'yi geçen bakışta olay üretir.
    def _bakisi_guncelle(self, simdi: float) -> None:
        if simdi >= self._bakis_bitisi:
            self._bakiyor = not self._bakiyor
            aralik = self._ayar.bakma_s if self._bakiyor else self._ayar.bakmama_s
            self._bakis_baslangici = simdi
            self._bakis_bitisi = simdi + self._rnd.uniform(*aralik)
            self._bakis_bildirildi = False

        sure = simdi - self._bakis_baslangici
        if self._bakiyor and not self._bakis_bildirildi and sure >= BAKIS_ESIGI_S:
            self._bakis_bildirildi = True
            if self._gelis_bildirildi:
                self._olay_ekle(simdi, EventType.LOOKING_AT_ROBOT_LONG, self._bakis_baslangici, sure)

    # Gülümseme, esneme veya uyuklamayı dakikadaki ortalama sıklığa göre rastgele başlatır.
    def _ifade_dene(self, simdi: float, dt: float) -> None:
        if not self._gelis_bildirildi or simdi < self._mesgul_bitis:
            return
        secenekler: list[tuple[EventType, float, tuple[float, float]]] = [
            (EventType.SMILE, self._ayar.gulumseme_dakikada, (0.5, 3.0)),
            (EventType.YAWN, self._ayar.esneme_dakikada, (1.5, 4.0)),
            (EventType.DROWSY, self._ayar.uyuklama_dakikada, (5.0, 20.0)),
        ]
        for olay_tipi, dakikada, sure_araligi in secenekler:
            if self._rnd.random() < dakikada / 60.0 * dt:
                sure = self._rnd.uniform(*sure_araligi)
                self._mesgul_bitis = simdi + sure
                # PerceptionEvent bittiğinde gönderilir; t başladığı anı, duration_s süresini taşır.
                self._olay_ekle(simdi + sure, olay_tipi, simdi, sure)
                return

    # Bir A2 olayını, gönderilme anı gelene kadar bekleyenler listesine koyar.
    def _olay_ekle(self, gonderim: float, olay_tipi: EventType, baslangic: float, sure: float) -> None:
        olay = PerceptionEvent(
            t=round(baslangic, 2),
            event=olay_tipi,
            confidence=round(self._rnd.uniform(0.6, 0.99), 2),
            duration_s=round(sure, 1),
        )
        self._bekleyen.append((gonderim, olay))

    # O anki duruma göre bir A1 yüz takip mesajı oluşturur.
    def _yuz_takibi(self, simdi: float) -> FaceTrack:
        if not self._masada:
            return FaceTrack(t=round(simdi, 2), present=False, looking_at_robot=False)
        return FaceTrack(
            t=round(simdi, 2),
            present=True,
            x=round(self._x, 3),
            y=round(self._y, 3),
            looking_at_robot=self._bakiyor,
        )
