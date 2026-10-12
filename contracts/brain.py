"""Sözleşme B: Beyin (Router ↔ LLM).

B1 router'ın beyne gönderdiği bağlamdır, B2 beynin döndürdüğü karardır.
Kurallı beyin de LLM de aynı B2 formatını döndürür.
"""

import logging
from datetime import datetime

from pydantic import Field, ValidationError

from .common import ContractModel, Emotion
from .perception import PerceptionEvent

logger = logging.getLogger(__name__)


class Mood(ContractModel):
    """B1 içindeki current_mood: kedinin şu anki duygusu ve şiddeti."""

    emotion: Emotion
    intensity: float = Field(ge=0, le=1)


class Session(ContractModel):
    """B1 içindeki session: kullanıcının masadaki oturumu (dakika cinsinden)."""

    minutes_at_desk: float = Field(ge=0, description="Kullanıcının masada geçirdiği süre")
    minutes_since_break: float = Field(ge=0, description="Son moladan beri geçen süre")


class BrainContext(ContractModel):
    """B1. Router'ın beyne gönderdiği bağlam."""

    now: datetime = Field(description="Yerel saat (ISO 8601)")
    current_mood: Mood
    session: Session
    recent_events: list[PerceptionEvent] = Field(
        default_factory=list, description="Son 5 dakikadaki A2 olayları, en yeni sonda"
    )
    memories: list[str] = Field(
        default_factory=list, max_length=5, description="RAG'dan gelen en fazla 5 anı"
    )


class Decision(ContractModel):
    """B2. Beynin döndürmesi gereken karar."""

    emotion: Emotion
    intensity: float = Field(ge=0, le=1, description="Duygunun şiddeti; hareketin büyüklüğü")
    duration_s: float = Field(ge=0, description="Duygunun süresi; sonra idle'a dönülür")
    memory_note: str | None = Field(default=None, description="Hafızaya yazılacak not veya null")
    reason: str = Field(default="", description="Sadece log ve debug için")

    # Güvenli varsayılan karar: hiçbir şey anlaşılamadığında kedi sakin durur.
    @classmethod
    def idle(cls, reason: str = "fallback") -> "Decision":
        return cls(emotion=Emotion.IDLE, intensity=0.0, duration_s=0.0, reason=reason)

    # Beyinden gelen metni karara çevirir; bozuk JSON veya liste dışı duygu gelirse
    # hatayı loglar ve idle döner. Sözleşmedeki "sistem LLM yüzünden asla durmaz" kuralı budur.
    @classmethod
    def parse_or_idle(cls, text: str | bytes) -> "Decision":
        try:
            return cls.model_validate_json(text)
        except ValidationError as error:
            logger.warning("Beyinden geçersiz karar geldi, idle'a düşülüyor: %s", error)
            return cls.idle(reason="invalid_brain_output")
