"""Modüller arası mesajların Pydantic modelleri (Arayüz Sözleşmeleri v0.1).

Kullanım:
    from contracts import PerceptionEvent, EventType
    olay = PerceptionEvent(t=time.time(), event=EventType.SMILE, confidence=0.9, duration_s=0)
"""

from .brain import BrainContext, Decision, Mood, RecentEvent, Session
from .common import CONTRACT_VERSION, ContractModel, Emotion, EventType
from .motion import (
    EAR_DOWN_DEG,
    EAR_NEUTRAL,
    EAR_UP_DEG,
    PROTOCOL_VERSION,
    SERIAL_BAUD,
    SERVO_COUNT,
    Pose,
    SerialCommand,
    SerialReply,
    ear_to_deg,
)
from .perception import MIN_EVENT_CONFIDENCE, FaceTrack, PerceptionEvent

__all__ = [
    "CONTRACT_VERSION",
    "ContractModel",
    "Emotion",
    "EventType",
    "FaceTrack",
    "PerceptionEvent",
    "MIN_EVENT_CONFIDENCE",
    "Mood",
    "Session",
    "RecentEvent",
    "BrainContext",
    "Decision",
    "Pose",
    "SerialCommand",
    "SerialReply",
    "PROTOCOL_VERSION",
    "SERIAL_BAUD",
    "SERVO_COUNT",
    "EAR_UP_DEG",
    "EAR_DOWN_DEG",
    "EAR_NEUTRAL",
    "ear_to_deg",
]
