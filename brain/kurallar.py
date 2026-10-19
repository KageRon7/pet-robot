# Kurallı beyin (durumsal): B1 bağlamına bakıp duygu seçer, B2 (Decision) döndürür.

from contracts import BrainContext, Decision, Emotion, EventType


def _karar(emotion, intensity, duration_s, reason):
    # Decision modeli yanlış alan ya da değer görürse hata verir (sözleşme kontrolü)
    return Decision(emotion=emotion, intensity=intensity, duration_s=duration_s, reason=reason)


def decide(b1: BrainContext) -> Decision:
    """B1 bağlamını alır, B2 kararını (Decision) döner. Asla exception fırlatmaz."""
    try:
        # --- Son 5 dakikada olay varsa: en yeni olay (listenin sonu) tetikleyicidir ---
        if b1.recent_events:
            son = b1.recent_events[-1]
            karar = None

            if son.event == EventType.SMILE:
                karar = _karar(Emotion.HAPPY, 0.8, 5, "Kullanıcı gülümsedi")
            elif son.event == EventType.YAWN:
                karar = _karar(Emotion.SLEEPY, 0.6, 8, "Kullanıcı esnedi")
            elif son.event == EventType.DROWSY:
                karar = _karar(Emotion.SLEEPY, 0.6, 8, "Kullanıcı uykulu görünüyor")
            elif son.event == EventType.USER_LEFT:
                karar = _karar(Emotion.SAD, 0.7, 6, "Kullanıcı masadan kalktı")
            elif son.event == EventType.SAD:
                karar = _karar(Emotion.SAD, 0.7, 6, "Kullanıcı üzgün görünüyor")
            elif son.event == EventType.ANGRY:
                karar = _karar(Emotion.STARTLED, 0.6, 5, "Kullanıcı sinirli, ürktüm")
            elif son.event == EventType.SURPRISED:
                karar = _karar(Emotion.CURIOUS, 0.6, 5, "Kullanıcı şaşırdı, merak ettim")
            elif son.event == EventType.USER_ARRIVED:
                karar = _karar(Emotion.CURIOUS, 0.6, 5, "Kullanıcı geldi")
            elif son.event == EventType.LOOKING_AT_ROBOT_LONG:
                karar = _karar(Emotion.PLAYFUL, 0.6, 5, "Kullanıcı uzun süre robota baktı")

            # Olay tazeyse tepki ver. Duygunun süresi dolduysa tekrar tepki verme,
            # aşağıdaki idle'a düş (üzgün → idle gibi doğal bir geçiş olur).
            if karar is not None and son.ago_s <= karar.duration_s:
                return karar

        # --- Son 5 dakikada hiç olay yoksa: masada kimse var mı? ---
        elif b1.session.user_present_minutes == 0:
            return _karar(Emotion.SLEEPY, 0.6, 8, "Uzun süredir kimse yok")

        # Kural eşleşmediyse ya da duygunun süresi dolduysa bekle
        return Decision.idle("Kural eşleşmedi ya da süre doldu")
    except Exception:
        # Sistem beyin yüzünden asla durmaz (Sözleşme B hata kuralı)
        return Decision.idle("Hata, bekleme durumu")


# Elle test: repo kökünden  python -m brain.kurallar  ile çalıştır
if __name__ == "__main__":

    def ctx(events, present=30):
        # Gerçek BrainContext modeli kurar
        return BrainContext.model_validate({
            "now": "2026-10-14T14:34:00",
            "current_mood": {"emotion": "idle", "intensity": 0.3},
            "session": {"user_present_minutes": present, "last_break_minutes_ago": present},
            "recent_events": events,
        })

    tests = [
        ("gülümseme", ctx([{"event": "smile", "ago_s": 0}])),
        ("esneme", ctx([{"event": "yawn", "ago_s": 0}])),
        ("uykulu görünüyor", ctx([{"event": "drowsy", "ago_s": 0}])),
        ("kullanıcı kalktı", ctx([{"event": "user_left", "ago_s": 0}])),
        ("kullanıcı üzgün", ctx([{"event": "sad", "ago_s": 0}])),
        ("kullanıcı sinirli", ctx([{"event": "angry", "ago_s": 0}])),
        ("kullanıcı şaşırdı", ctx([{"event": "surprised", "ago_s": 0}])),
        ("kullanıcı geldi", ctx([{"event": "user_arrived", "ago_s": 0}])),
        ("uzun süre robota baktı", ctx([{"event": "looking_at_robot_long", "ago_s": 0}])),
        ("kalktı, 60 sn sonra", ctx([{"event": "user_left", "ago_s": 60}], present=0)),
        ("olay yok, masada kimse yok", ctx([], present=0)),
        ("olay yok, kullanıcı masada", ctx([], present=30)),
        ("bozuk veri", {}),
    ]
    for ad, b1 in tests:
        r = decide(b1)
        print(f"{ad:28} -> {r.emotion.value:8} {r.intensity}  ({r.reason})")