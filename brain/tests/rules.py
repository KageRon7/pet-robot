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
            son_olay = b1.recent_events[-1].event

            if son_olay == EventType.SMILE:
                return _karar(Emotion.HAPPY, 0.8, 5, "Kullanıcı gülümsedi")

            if son_olay == EventType.YAWN:
                return _karar(Emotion.SLEEPY, 0.6, 8, "Kullanıcı esnedi")

            if son_olay == EventType.USER_LEFT:
                return _karar(Emotion.SAD, 0.7, 6, "Kullanıcı masadan kalktı")

        # --- Son 5 dakikada hiç olay yoksa: masada kimse var mı? ---
        elif b1.session.user_present_minutes == 0:
            return _karar(Emotion.SLEEPY, 0.6, 8, "Uzun süredir kimse yok")

        # Hiçbir kural eşleşmediyse bekle (sözleşmedeki güvenli karar)
        return Decision.idle("Kural eşleşmedi")
    except Exception:
        # Sistem beyin yüzünden asla durmaz (Sözleşme B hata kuralı)
        return Decision.idle("Hata, bekleme durumu")


# Elle test: repo kökünden  python -m brain.tests.rules  ile çalıştır
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
        ("kullanıcı kalktı", ctx([{"event": "user_left", "ago_s": 0}])),
        ("kuralı olmayan olay", ctx([{"event": "user_arrived", "ago_s": 0}])),
        ("olay yok, masada kimse yok", ctx([], present=0)),
        ("olay yok, kullanıcı masada", ctx([], present=30)),
        ("bozuk veri", {}),
    ]
    for ad, b1 in tests:
        r = decide(b1)
        print(f"{ad:28} -> {r.emotion.value:8} {r.intensity}  ({r.reason})")