# Claude beyni testleri: sahte Claude ile çalışır, API anahtarı gerekmez.
# Çalıştırma (repo kökünden):  python -m pytest brain/tests/test_claude_beyin.py

import asyncio
import json

from brain.claude_beyin import ClaudeBeyin, SahteClaudeIstemci, baglami_metne_cevir
from contracts import BrainContext, Decision, Emotion


# Testler için gülümseme olaylı örnek bir B1 bağlamı kurar.
def _baglam(olay="smile", ago_s=0):
    return BrainContext.model_validate({
        "now": "2026-11-02T22:15:00",
        "current_mood": {"emotion": "idle", "intensity": 0.3},
        "session": {"user_present_minutes": 120, "last_break_minutes_ago": 90},
        "recent_events": [{"event": olay, "ago_s": ago_s}],
    })


# Verilen sahte cevaplarla beyne bir kez sorar ve kararı döner.
def _sor(cevaplar, gecikme_s=0.0, zaman_asimi_s=1.0, olay="smile"):
    beyin = ClaudeBeyin(SahteClaudeIstemci(cevaplar, gecikme_s), zaman_asimi_s=zaman_asimi_s)
    return asyncio.run(beyin.karar_ver(_baglam(olay)))


# Düzgün bir cevap aynen karara dönüşmeli.
def test_gecerli_cevap_kullanilir():
    cevap = json.dumps({"emotion": "playful", "intensity": 0.7, "duration_s": 6, "reason": "Oynayalım"})
    karar = _sor([cevap])
    assert isinstance(karar, Decision)
    assert karar.emotion == Emotion.PLAYFUL
    assert karar.intensity == 0.7
    assert karar.reason.startswith("[claude]")


# Liste dışı duygu ("angry") gelirse kural beyni karar vermeli (smile -> happy).
def test_liste_disi_duygu_kural_beynine_duser():
    karar = _sor(['{"emotion": "angry", "intensity": 0.5, "duration_s": 5, "reason": "x"}'])
    assert karar.emotion == Emotion.HAPPY
    assert "geçersiz cevap" in karar.reason


# 0-1 dışındaki şiddet de sözleşmeye aykırıdır.
def test_sinir_disi_siddet_kural_beynine_duser():
    karar = _sor(['{"emotion": "happy", "intensity": 5, "duration_s": 5, "reason": "x"}'])
    assert "[kural" in karar.reason


# Bozuk JSON kediyi çökertmemeli.
def test_bozuk_json_kural_beynine_duser():
    karar = _sor(["bu json değil"])
    assert karar.emotion == Emotion.HAPPY
    assert "geçersiz cevap" in karar.reason


# Claude geç kalırsa beklemeyip kural beynine dönmeli.
def test_zaman_asimi_kural_beynine_duser():
    karar = _sor([], gecikme_s=0.5, zaman_asimi_s=0.05, olay="yawn")
    assert karar.emotion == Emotion.SLEEPY
    assert "zaman aşımı" in karar.reason


# İnternet kopması gibi hatalar da yakalanmalı.
def test_baglanti_hatasi_kural_beynine_duser():
    karar = _sor([ConnectionError("internet yok")], olay="user_left")
    assert karar.emotion == Emotion.SAD
    assert "ConnectionError" in karar.reason


# Claude'a giden mesaj olayları ve masada geçen süreyi içermeli.
def test_baglam_metni_olaylari_icerir():
    metin = baglami_metne_cevir(_baglam("yawn", 3))
    assert "yawn, 3" in metin
    assert "120" in metin
    assert "22:15" in metin
