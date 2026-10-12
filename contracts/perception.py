"""Sözleşme A: Algı olayları (Computer Vision → Router).

A1 yüz takip akışıdır (saniyede ~15 mesaj, sadece refleks katmanı kullanır).
A2 anlamlı olaylardır (sadece bir şey değiştiğinde gönderilir, beyin kullanır).
Kamera görüntüsünün kendisi hiçbir mesajda yer almaz.
"""

from typing import Literal

from pydantic import Field, model_validator

from .common import ContractModel, EventType

# A2: bu değerin altındaki güven skoruyla olay gönderilmez.
MIN_EVENT_CONFIDENCE = 0.6


class FaceTrack(ContractModel):
    """A1. Yüz takip mesajı."""

    type: Literal["face_track"] = "face_track"
    t: float = Field(ge=0, description="Unix zaman damgası (saniye)")
    present: bool = Field(description="Kadrajda yüz var mı")
    x: float | None = Field(default=None, ge=0, le=1, description="Yüzün yatay konumu; sol kenar 0")
    y: float | None = Field(default=None, ge=0, le=1, description="Yüzün dikey konumu; üst kenar 0")
    looking_at_robot: bool = Field(description="Kullanıcı kameraya/robota bakıyor mu")

    # Yüz varsa x ve y dolu olmalı; yüz yoksa ikisi de null olmalı.
    @model_validator(mode="after")
    def _check_position(self) -> "FaceTrack":
        if self.present and (self.x is None or self.y is None):
            raise ValueError("present=true iken x ve y dolu olmalı")
        if not self.present and (self.x is not None or self.y is not None):
            raise ValueError("present=false iken x ve y null olmalı")
        return self


class PerceptionEvent(ContractModel):
    """A2. Anlamlı olay mesajı."""

    type: Literal["event"] = "event"
    t: float = Field(ge=0, description="Olayın başladığı an (Unix saniye)")
    event: EventType
    confidence: float = Field(ge=MIN_EVENT_CONFIDENCE, le=1, description="Tespitin güven skoru")
    duration_s: float = Field(ge=0, description="Olayın sürdüğü süre; anlık olaylarda 0")
