"""Sözleşme C: Hareket (Router → HAL → ESP32).

C1 mantıksal pozdur (derece ve 0–1 kulak değerleri, Python içinde kalır).
C2 ESP32'ye USB seri porttan giden tek satırlık JSON protokolüdür (fiziksel açılar, 0–180).
"""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from .common import ContractModel

# C2 seri port hızı; iki tarafta aynı olmalı.
SERIAL_BAUD = 115200
# C2 protokol sürümü ("v" alanı).
PROTOCOL_VERSION = 1
# Servo sayısı (S0–S4).
SERVO_COUNT = 5

ErrorCode = Literal["bad_json", "bad_cmd", "out_of_range"]
PhysicalAngle = Annotated[int, Field(ge=0, le=180)]


class Pose(ContractModel):
    """C1. Mantıksal poz: router'ın HAL'e "nereye bakılsın" demesi."""

    body_yaw: float = Field(ge=-45, le=45, description="S0 gövde; − sola, + sağa")
    head_pan: float = Field(ge=-90, le=90, description="S1 baş; − sola, + sağa")
    head_tilt: float = Field(ge=-10, le=45, description="S2 baş; − aşağı, + yukarı")
    ear_left: float = Field(ge=0, le=1, description="S3 sol kulak; 0 geri yatık, 1 dik")
    ear_right: float = Field(ge=0, le=1, description="S4 sağ kulak; 0 geri yatık, 1 dik")
    ms: int = Field(ge=0, description="Bu poza kaç milisaniyede varılacağı")


class SerialCommand(ContractModel):
    """C2. Bilgisayardan ESP32'ye giden komut."""

    v: Literal[1] = PROTOCOL_VERSION
    seq: int = Field(ge=0, description="Artan mesaj numarası")
    cmd: Literal["move", "ping", "neutral"]
    deg: list[PhysicalAngle] | None = Field(
        default=None, description="S0–S4 fiziksel açıları; sadece move'da"
    )
    ms: int | None = Field(default=None, ge=0, description="Hareket süresi; sadece move'da")

    # move komutunda 5 açı ve süre zorunlu; ping ve neutral'da bu alanlar olmamalı.
    @model_validator(mode="after")
    def _check_move_fields(self) -> "SerialCommand":
        if self.cmd == "move":
            if self.deg is None or len(self.deg) != SERVO_COUNT:
                raise ValueError(f"move komutu tam {SERVO_COUNT} açı içermeli")
            if self.ms is None:
                raise ValueError("move komutu ms içermeli")
        elif self.deg is not None or self.ms is not None:
            raise ValueError(f"{self.cmd} komutu deg veya ms içermez")
        return self

    # Komutu seri porta yazılacak tek satıra çevirir (boş alanlar atılır, sonuna \n eklenir).
    def to_line(self) -> str:
        return self.model_dump_json(exclude_none=True) + "\n"


class SerialReply(ContractModel):
    """C2. ESP32'nin her komuta döndürdüğü cevap."""

    ack: int = Field(ge=0, description="Cevaplanan komutun seq numarası")
    ok: bool
    err: ErrorCode | None = None

    # ok=false ise hata kodu zorunlu; ok=true ise hata kodu olmamalı.
    @model_validator(mode="after")
    def _check_error(self) -> "SerialReply":
        if not self.ok and self.err is None:
            raise ValueError("ok=false iken err zorunlu")
        if self.ok and self.err is not None:
            raise ValueError("ok=true iken err olmamalı")
        return self
