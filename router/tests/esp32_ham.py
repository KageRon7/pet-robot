"""
Ne işe yarar: ESP32'ye (Wokwi) ham komut gönderir ve gelen her satırı olduğu gibi yazar (teşhis aracı).
Nasıl çalıştırılır (ana klasörden, Wokwi açıkken): python -m router.tests.esp32_ham happy
"""

import sys
import time

import serial

from contracts import SERIAL_BAUD, SerialCommand


def main(ad: str) -> None:
    port = serial.serial_for_url("rfc2217://localhost:4000", baudrate=SERIAL_BAUD, timeout=0.2)
    print("bağlandı")
    komutlar = [
        SerialCommand(seq=1, cmd="ping"),
        SerialCommand(seq=2, cmd="anim", name=ad),
        SerialCommand(seq=3, cmd="ping"),
    ]
    for komut in komutlar:
        satir = komut.to_line()
        print("GÖNDER:", satir.strip())
        baslangic = time.monotonic()
        port.write(satir.encode("utf-8"))
        while time.monotonic() - baslangic < 5:
            ham = port.readline()
            if ham:
                print(f"  +{time.monotonic() - baslangic:.2f}s GELDİ: {ham!r}")
    port.write(SerialCommand(seq=4, cmd="neutral").to_line().encode("utf-8"))
    time.sleep(0.5)
    port.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "happy")