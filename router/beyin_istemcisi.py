"""
Beyne soru sorma yolu.

Ne işe yarar: Router'ın bir olay için beyne B1 bağlamı gönderdiği yer.
Soru ayrı görevde gider, router beklemez. Cevap gelmezse (zaman aşımı,
hata) None döner ve kedi refleksle devam eder.
Hangi beyin? .env dosyasındaki BEYIN ayarı seçer:
  BEYIN=kurallar (varsayılan) -> brain/kurallar.py
  BEYIN=claude                -> brain/claude_beyin.py, gerçek Claude (ANTHROPIC_API_KEY gerekir)
  BEYIN=sahte                 -> brain/claude_beyin.py, sahte Claude (anahtarsız deneme)
Claude beyni sorun yaşarsa kendisi kural beynine döner.
"""

import asyncio
import os
from datetime import datetime

from contracts import BrainContext, Emotion, Mood, RecentEvent, Session

SON_OLAY_PENCERESI_S = 5 * 60  # B1: son 5 dakikadaki olaylar
BEYIN_ZAMAN_ASIMI_S = 5.0


class BaglamTutucu:
    """Gelen olayları hatırlar ve her olay için B1 bağlamını kurar."""

    def __init__(self) -> None:
        self._son_olaylar: list[tuple[float, object]] = []  # (zaman, olay)
        self._masaya_gelis: float | None = None

    def olay_ekle(self, olay, simdi: float) -> None:
        ad = str(getattr(olay, "value", olay))
        if ad == "user_arrived":
            self._masaya_gelis = simdi
        elif ad == "user_left":
            self._masaya_gelis = None
        self._son_olaylar.append((simdi, olay))
        self._son_olaylar = [(z, o) for z, o in self._son_olaylar if simdi - z <= SON_OLAY_PENCERESI_S]

    def olustur(self, simdi: float) -> BrainContext:
        dakika = 0.0 if self._masaya_gelis is None else (simdi - self._masaya_gelis) / 60
        return BrainContext(
            now=datetime.fromtimestamp(simdi).replace(microsecond=0),
            current_mood=Mood(emotion=Emotion.IDLE, intensity=0.3),  # ileride gerçek ruh hali
            session=Session(user_present_minutes=round(dakika, 1), last_break_minutes_ago=round(dakika, 1)),
            recent_events=[RecentEvent(event=o, ago_s=round(simdi - z, 1)) for z, o in self._son_olaylar],
            memories=[],  # ileride RAG / hafıza buraya gelecek
        )


_claude_beyin = None  # Claude beyni bir kez kurulur, sonra hep aynısı kullanılır
_secim_yapildi = False  # .env bir kez okunur


# .env'deki BEYIN ayarına göre Claude beynini bir kez kurar; kural beyni seçiliyse None döner.
def _claude_beynini_al():
    global _claude_beyin, _secim_yapildi
    if not _secim_yapildi:
        _secim_yapildi = True
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        secim = os.environ.get("BEYIN", "kurallar").strip().lower()
        if secim not in ("claude", "sahte"):
            print("[BEYİN] kural beyni kullanılıyor")
            return None
        from brain.claude_beyin import ClaudeBeyin, GercekClaudeIstemci, SahteClaudeIstemci

        try:
            istemci = GercekClaudeIstemci() if secim == "claude" else SahteClaudeIstemci()
        except Exception as hata:  # anahtar yoksa kedi kural beyniyle devam eder
            print(f"[BEYİN] Claude beyni kurulamadı ({hata}), kural beyni kullanılıyor")
            return None
        _claude_beyin = ClaudeBeyin(istemci)
        print(f"[BEYİN] {secim} beyni kullanılıyor")
    return _claude_beyin


# Bağlamı seçili beyne gönderir ve kararı döner.
async def _beyne_gonder(baglam: BrainContext):
    from brain.kurallar import decide

    print(f"[BEYİN-SORU] gönderildi ({len(baglam.recent_events)} son olay)")
    claude = _claude_beynini_al()
    if claude is not None:
        return await claude.karar_ver(baglam)
    # decide senkron bir fonksiyon; ayrı thread'de çalıştırıyoruz ki router donmasın.
    return await asyncio.to_thread(decide, baglam)


async def beyne_sor(baglam: BrainContext):
    """Beyne sorar. Cevap alınamazsa None döner, asla hata fırlatmaz."""
    try:
        return await asyncio.wait_for(_beyne_gonder(baglam), timeout=BEYIN_ZAMAN_ASIMI_S)
    except asyncio.TimeoutError:
        print("[BEYİN-SORU] cevap gelmedi (zaman aşımı), refleksle devam")
    except Exception as hata:
        print(f"[BEYİN-SORU] HATA: {hata!r}, refleksle devam")
    return None