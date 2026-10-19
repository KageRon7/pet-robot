"""Bütün sözleşmelerin ortak parçaları: sürüm numarası, sabit listeler ve temel model.

Bu dosyadaki listeler "kapalı"dır: listede olmayan bir değer gelirse Pydantic hata verir.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

# Arayüz Sözleşmeleri dokümanının sürümü. Doküman değişince burası da değişir.
CONTRACT_VERSION = "0.1"


class EventType(StrEnum):
    """A2 olay listesi: CV modülünün gönderebileceği anlamlı olaylar."""

    USER_ARRIVED = "user_arrived"
    USER_LEFT = "user_left"
    SMILE = "smile"
    YAWN = "yawn"
    DROWSY = "drowsy"
    LOOKING_AT_ROBOT_LONG = "looking_at_robot_long"
    # 19 Ekim (Ferhat onayı): Mustafa'nın yüz ifadesi olayları
    SAD = "sad"  # kullanıcı üzgün görünüyor -> önerilen tepki: sad
    ANGRY = "angry"  # kullanıcı sinirli görünüyor -> önerilen tepki: startled
    SURPRISED = "surprised"  # kullanıcı şaşkın görünüyor -> önerilen tepki: curious


class Emotion(StrEnum):
    """B2 duygu listesi: beynin seçebileceği duygular."""

    IDLE = "idle"
    HAPPY = "happy"
    CURIOUS = "curious"
    SLEEPY = "sleepy"
    SAD = "sad"
    PLAYFUL = "playful"
    STARTLED = "startled"


class ContractModel(BaseModel):
    """Bütün mesaj modellerinin atası.

    - extra="forbid": dokümanda olmayan bir alan gelirse hata verir ("gulumseme" gibi yazım hataları yakalanır).
    - frozen=True: mesaj oluşturulduktan sonra değiştirilemez; bir modül başkasının mesajını yanlışlıkla bozamaz.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Mesajı tek satırlık JSON metnine çevirir (göndermeden önce kullanılır).
    def to_json(self) -> str:
        return self.model_dump_json()

    # Gelen JSON metnini kontrol edip modele çevirir; format yanlışsa ValidationError fırlatır.
    @classmethod
    def from_json(cls, text: str | bytes):
        return cls.model_validate_json(text)
