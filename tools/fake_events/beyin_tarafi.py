"""
Beyin tarafının sahte mesajları: Sözleşme B1 (bağlam) ve B2 (karar).

Her A2 olayında router'ın beyne göndereceği B1 bağlamını kurar ve beynin
döndüreceği B2 kararını taklit eder. Böylece:
  - Azat, router hazır olmadan gerçekçi B1 bağlamlarıyla beynini deneyebilir,
  - Kaan ve Reşat, beyin hazır olmadan B2 kararlarıyla router'ı ve pozları
    deneyebilir.

Bu sınıf Azat'ın SahteBeyin'inin yerine geçmez; sadece test verisi üretir.
Kararlar basit bir eşlemeye göre seçilir (smile → happy gibi), arada sırada
da çeşitlilik olsun diye başka bir duygu seçilir.
"""

import random
from datetime import datetime

from contracts import BrainContext, Decision, Emotion, EventType, Mood, PerceptionEvent, RecentEvent, Session

SON_OLAY_PENCERESI_S = 5 * 60  # B1: son 5 dakikadaki olaylar
EN_FAZLA_ANI = 5  # B1: en fazla 5 anı

# Hangi olaya hangi duygularla tepki verileceği (listeden rastgele biri seçilir).
OLAY_DUYGU: dict[EventType, list[Emotion]] = {
    EventType.USER_ARRIVED: [Emotion.HAPPY, Emotion.CURIOUS],
    EventType.USER_LEFT: [Emotion.SAD],
    EventType.SMILE: [Emotion.HAPPY, Emotion.PLAYFUL],
    EventType.YAWN: [Emotion.SLEEPY],
    EventType.DROWSY: [Emotion.SLEEPY],
    EventType.LOOKING_AT_ROBOT_LONG: [Emotion.CURIOUS, Emotion.PLAYFUL],
    EventType.SAD: [Emotion.SAD],
    EventType.ANGRY: [Emotion.STARTLED],
    EventType.SURPRISED: [Emotion.CURIOUS],
}

NEDENLER: dict[EventType, str] = {
    EventType.USER_ARRIVED: "Kullanıcı masaya geldi",
    EventType.USER_LEFT: "Kullanıcı gitti, yalnız kaldım",
    EventType.SMILE: "Kullanıcı gülümsedi",
    EventType.YAWN: "Kullanıcı esniyor, ben de uykuluyum",
    EventType.DROWSY: "Kullanıcı uyukluyor",
    EventType.LOOKING_AT_ROBOT_LONG: "Kullanıcı bana uzun süre baktı",
    EventType.SAD: "Kullanıcı üzgün görünüyor",
    EventType.ANGRY: "Kullanıcı sinirli, ürktüm",
    EventType.SURPRISED: "Kullanıcı şaşırdı, merak ettim",
}

ANI_NOTLARI: dict[EventType, str] = {
    EventType.USER_ARRIVED: "Kullanıcı bu saatte masaya geldi",
    EventType.USER_LEFT: "Kullanıcı bu saatte mola verdi",
    EventType.SMILE: "Kullanıcı kedinin hareketine güldü",
    EventType.YAWN: "Kullanıcı bu saatte yorgundu",
    EventType.DROWSY: "Kullanıcı bu saatte uyukladı",
    EventType.LOOKING_AT_ROBOT_LONG: "Kullanıcı kediyle ilgilendi",
    EventType.SAD: "Kullanıcı bu saatte üzgündü",
    EventType.ANGRY: "Kullanıcı bu saatte sinirliydi",
    EventType.SURPRISED: "Kullanıcı bu saatte şaşırdı",
}


class SahteBeyinAkisi:
    """A2 olaylarını alır; her biri için bir B1 bağlamı ve bir B2 kararı üretir."""

    # Kedinin ruh halini, oturum bilgisini, son olayları ve anıları sıfırdan başlatır.
    def __init__(self, rnd: random.Random, surpriz_orani: float = 0.1):
        self._rnd = rnd
        self._surpriz_orani = surpriz_orani  # eşleme dışı duygu seçme olasılığı

        self._ruh_hali = Mood(emotion=Emotion.IDLE, intensity=0.3)
        self._ruh_hali_bitisi = 0.0
        self._masaya_gelis: float | None = None  # son user_arrived olayının t değeri
        self._son_olaylar: list[tuple[float, PerceptionEvent]] = []  # (geliş anı, olay)
        self._anilar: list[str] = []

    # Gelen olayı kaydeder ve router'ın bu anda beyne göndereceği B1 bağlamını döndürür.
    def baglam_olustur(self, olay: PerceptionEvent, simdi: float) -> BrainContext:
        if olay.event == EventType.USER_ARRIVED:
            self._masaya_gelis = olay.t
        elif olay.event == EventType.USER_LEFT:
            self._masaya_gelis = None

        self._son_olaylar.append((simdi, olay))
        self._son_olaylar = [(z, o) for z, o in self._son_olaylar if simdi - z <= SON_OLAY_PENCERESI_S]

        if simdi >= self._ruh_hali_bitisi:
            self._ruh_hali = Mood(emotion=Emotion.IDLE, intensity=0.3)

        # Bu sahte kullanıcı sadece masadan kalkarak mola verir; iki süre bu yüzden aynı.
        dakika = 0.0 if self._masaya_gelis is None else (simdi - self._masaya_gelis) / 60
        return BrainContext(
            now=datetime.fromtimestamp(simdi).replace(microsecond=0),
            current_mood=self._ruh_hali,
            session=Session(user_present_minutes=round(dakika, 1), last_break_minutes_ago=round(dakika, 1)),
            recent_events=[RecentEvent(event=o.event, ago_s=round(simdi - z, 1)) for z, o in self._son_olaylar],
            memories=self._anilar[-EN_FAZLA_ANI:],
        )

    # Olaya uygun bir B2 kararı seçer ve kedinin ruh halini bu karara göre günceller.
    def karar_ver(self, olay: PerceptionEvent, simdi: float) -> Decision:
        if self._rnd.random() < self._surpriz_orani:
            duygu: Emotion = self._rnd.choice([Emotion.CURIOUS, Emotion.PLAYFUL, Emotion.STARTLED, Emotion.IDLE])
            neden = "Sürpriz: test için eşleme dışı bir duygu"
        else:
            duygu = self._rnd.choice(OLAY_DUYGU[olay.event])
            neden = NEDENLER[olay.event]

        ani = ANI_NOTLARI[olay.event] if self._rnd.random() < 0.2 else None
        if ani is not None and ani not in self._anilar:
            self._anilar.append(ani)

        karar = Decision(
            emotion=duygu,
            intensity=round(self._rnd.uniform(0.4, 1.0), 2),
            duration_s=round(self._rnd.uniform(3.0, 10.0), 1),
            memory_note=ani,
            reason=neden,
        )
        self._ruh_hali = Mood(emotion=karar.emotion, intensity=karar.intensity)
        self._ruh_hali_bitisi = simdi + karar.duration_s
        return karar
