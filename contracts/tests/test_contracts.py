"""Sözleşme modellerinin testleri. Çalıştırmak için repo kökünde: python -m pytest"""

import json

import pytest
from pydantic import ValidationError

from contracts import (
    BrainContext,
    Decision,
    Emotion,
    EventType,
    FaceTrack,
    PerceptionEvent,
    Pose,
    SerialCommand,
    SerialReply,
    ear_to_deg,
)


# ---------- A1: yüz takip ----------

# Yüz görünürken konum dolu bir mesaj kabul edilmeli.
def test_face_track_present():
    msg = FaceTrack(t=1760000000.0, present=True, x=0.5, y=0.4, looking_at_robot=True)
    assert msg.type == "face_track"


# Yüz yokken x ve y null olmalı.
def test_face_track_absent_requires_null_position():
    FaceTrack(t=1.0, present=False, x=None, y=None, looking_at_robot=False)
    with pytest.raises(ValidationError):
        FaceTrack(t=1.0, present=False, x=0.5, y=0.5, looking_at_robot=False)


# Yüz varken konum eksikse veya 0–1 dışındaysa hata vermeli.
def test_face_track_bad_position():
    with pytest.raises(ValidationError):
        FaceTrack(t=1.0, present=True, looking_at_robot=True)
    with pytest.raises(ValidationError):
        FaceTrack(t=1.0, present=True, x=1.2, y=0.5, looking_at_robot=True)


# ---------- A2: olaylar ----------

# Dokümandaki gülümseme örneği JSON'dan okunabilmeli.
def test_event_from_json():
    raw = '{"type": "event", "t": 1760000000.0, "event": "smile", "confidence": 0.82, "duration_s": 1.4}'
    msg = PerceptionEvent.from_json(raw)
    assert msg.event is EventType.SMILE


# Liste dışı olay, düşük güven ve fazladan alan reddedilmeli.
@pytest.mark.parametrize(
    "changes",
    [
        {"event": "gulumseme"},
        {"confidence": 0.59},
        {"confidence": 1.1},
        {"duration_s": -1},
        {"extra_field": 1},
    ],
)
def test_event_rejects_bad_values(changes):
    data = {"t": 1.0, "event": "smile", "confidence": 0.9, "duration_s": 0} | changes
    with pytest.raises(ValidationError):
        PerceptionEvent(**data)


# Mesaj JSON'a çevrilip geri okunduğunda aynı kalmalı.
def test_event_round_trip():
    msg = PerceptionEvent(t=5.0, event=EventType.YAWN, confidence=0.7, duration_s=2.0)
    assert PerceptionEvent.from_json(msg.to_json()) == msg


# Mesajlar sonradan değiştirilememeli.
def test_messages_are_frozen():
    msg = PerceptionEvent(t=5.0, event=EventType.YAWN, confidence=0.7, duration_s=2.0)
    with pytest.raises(ValidationError):
        msg.confidence = 0.1


# ---------- B1 / B2: beyin ----------

# Dokümandaki B1 örneği birebir okunabilmeli.
def test_brain_context_doc_example():
    raw = """{
      "now": "2026-10-11T14:34:00",
      "current_mood": {"emotion": "idle", "intensity": 0.3},
      "session": {"user_present_minutes": 47, "last_break_minutes_ago": 47},
      "recent_events": [{"event": "yawn", "ago_s": 30}, {"event": "drowsy", "ago_s": 5}],
      "memories": ["Kullanıcı dün de öğleden sonra uykuluydu", "Kullanıcı kedinin kafasını eğmesine güldü"]
    }"""
    ctx = BrainContext.from_json(raw)
    assert ctx.session.user_present_minutes == 47
    assert ctx.recent_events[-1].event is EventType.DROWSY


# Geçerli bir bağlam kurulabilmeli; 5'ten fazla anı reddedilmeli.
def test_brain_context():
    ctx = BrainContext(
        now="2026-10-12T21:00:00+03:00",
        current_mood={"emotion": "idle", "intensity": 0.2},
        session={"user_present_minutes": 45, "last_break_minutes_ago": 20},
        recent_events=[{"event": "smile", "ago_s": 0}],
        memories=["Kullanıcı akşamları yorgun oluyor"],
    )
    assert ctx.recent_events[0].event is EventType.SMILE
    with pytest.raises(ValidationError):
        BrainContext(**ctx.model_dump() | {"memories": ["a"] * 6})


# Geçerli karar olduğu gibi okunmalı.
def test_decision_valid():
    raw = '{"emotion": "happy", "intensity": 0.8, "duration_s": 4, "memory_note": null, "reason": "smile"}'
    assert Decision.parse_or_idle(raw).emotion is Emotion.HAPPY


# Bozuk JSON veya liste dışı duygu gelirse idle'a düşülmeli.
@pytest.mark.parametrize(
    "raw",
    [
        "bu json değil",
        '{"emotion": "angry", "intensity": 0.5, "duration_s": 3}',
        '{"emotion": "happy", "intensity": 2, "duration_s": 3}',
    ],
)
def test_decision_falls_back_to_idle(raw):
    assert Decision.parse_or_idle(raw).emotion is Emotion.IDLE


# ---------- C1: mantıksal poz ----------

# Sınır içindeki poz kabul edilmeli, sınır dışı reddedilmeli.
def test_pose_limits():
    Pose(body_yaw=-45, head_pan=90, head_tilt=-10, ear_left=1, ear_right=0, ms=300)
    with pytest.raises(ValidationError):
        Pose(body_yaw=50, head_pan=0, head_tilt=0, ear_left=1, ear_right=1, ms=300)
    with pytest.raises(ValidationError):
        Pose(body_yaw=0, head_pan=0, head_tilt=-20, ear_left=1, ear_right=1, ms=300)


# Kulak 0–1 değeri servo derecesine doğru çevrilmeli; sağ kulak ayna gibi ters dönmeli.
def test_ear_to_deg():
    assert ear_to_deg(1) == 150
    assert ear_to_deg(0) == 60
    assert ear_to_deg(0.8) == 132
    assert ear_to_deg(1, mirrored=True) == 30
    assert ear_to_deg(0, mirrored=True) == 120
    with pytest.raises(ValueError):
        ear_to_deg(1.2)


# ---------- C2: seri protokol ----------

# move komutu tek satır JSON olmalı ve \n ile bitmeli.
def test_move_command_line():
    cmd = SerialCommand(seq=42, cmd="move", deg=[90, 90, 100, 150, 150], ms=300)
    line = cmd.to_line()
    assert line.endswith("\n") and "\n" not in line[:-1]
    assert json.loads(line) == {"v": 1, "seq": 42, "cmd": "move", "deg": [90, 90, 100, 150, 150], "ms": 300}


# ping komutunda deg ve ms yazılmamalı.
def test_ping_command_line():
    assert json.loads(SerialCommand(seq=43, cmd="ping").to_line()) == {"v": 1, "seq": 43, "cmd": "ping"}


# Hatalı komutlar reddedilmeli.
@pytest.mark.parametrize(
    "data",
    [
        {"seq": 1, "cmd": "move", "deg": [90, 90, 90, 90], "ms": 300},  # 4 açı
        {"seq": 1, "cmd": "move", "deg": [90, 90, 90, 90, 181], "ms": 300},  # 180 üstü
        {"seq": 1, "cmd": "move", "deg": [90, 90, 90, 90, 90]},  # ms yok
        {"seq": 1, "cmd": "ping", "deg": [90, 90, 90, 90, 90]},  # ping'de açı
        {"seq": 1, "cmd": "dance"},  # liste dışı komut
        {"v": 2, "seq": 1, "cmd": "ping"},  # yanlış sürüm
    ],
)
def test_bad_commands(data):
    with pytest.raises(ValidationError):
        SerialCommand(**data)


# ESP32 cevapları: başarılı, hatalı ve tutarsız örnekler.
def test_serial_reply():
    assert SerialReply.from_json('{"ack": 42, "ok": true}').ok
    assert SerialReply.from_json('{"ack": 42, "ok": false, "err": "bad_json"}').err == "bad_json"
    with pytest.raises(ValidationError):
        SerialReply.from_json('{"ack": 42, "ok": false}')
    with pytest.raises(ValidationError):
        SerialReply.from_json('{"ack": 42, "ok": false, "err": "on_fire"}')
