# Kurallı beyin. Karar mantığı artık brain/davranis.py içindeki davranış ağacında.
# Bu dosya, router (beyin_istemcisi.py) ve Claude beyni (yedek yol) eskisi gibi
# `from brain.kurallar import decide` yazabilsin diye duruyor: onların kodu değişmez.
# Süreler ve tepkiler brain/ayarlar.py içinde.

from brain.davranis import decide, karar_ver, tik  # noqa: F401  (dışarıya açılan fonksiyonlar)
from contracts import BrainContext

__all__ = ["decide", "karar_ver", "tik"]


# Elle test: repo kökünden  python -m brain.kurallar  ile çalıştır
# (Zamanla ilgili senaryolar için: python -m tools.fake_events.senaryo hepsi)
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
        ("kullanıcı sinirli", ctx([{"event": "angry", "ago_s": 0}])),
        ("kullanıcı üzgün", ctx([{"event": "sad", "ago_s": 0}])),
        ("kullanıcı kalktı", ctx([{"event": "user_left", "ago_s": 0}], present=0)),
        ("bozuk veri", {}),
    ]
    for ad, b1 in tests:
        r = decide(b1)
        klip = f" klip={r.clip}" if r.clip else ""
        print(f"{ad:20} -> {r.emotion.value:8} {r.intensity}{klip}  ({r.reason})")
