import json
import logging
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QUdpSocket, QHostAddress

from motion.klip import KlipYukleyici, Klip

logger = logging.getLogger(__name__)


class PetRobotKoprusu(QObject):
    duygu_komutu_geldi = Signal(str)
    # Kaan'ın MediaPipe modülünden gelen (-1.0 ile 1.0 arası) bakış koordinatları
    bakis_komutu_geldi = Signal(float, float)

    def __init__(self, clips_klasoru: Path, port: int = 5555, parent=None):
        super().__init__(parent)
        self.clips_klasoru = clips_klasoru
        self.klipler: Dict[str, Klip] = KlipYukleyici.klasorden_yukle(self.clips_klasoru)
        self.aktif_duygu: str = "idle"
        self.port = port

        print(f"[Köprü] Yüklü klipler: {list(self.klipler.keys())}")

        self.udp_socket = QUdpSocket(self)
        if self.udp_socket.bind(QHostAddress.SpecialAddress.Any, self.port):
            self.udp_socket.readyRead.connect(self._veri_oku)
            print(f"[Köprü] UDP dinleyicisi {self.port} portunda aktif!")
        else:
            print(f"[Köprü HATA] {self.port} portuna bağlanılamadı! Hata: {self.udp_socket.errorString()}")

    def mevcut_duygulari_getir(self) -> list[str]:
        return sorted(self.klipler.keys())

    def klip_getir(self, klip_adi: str) -> Optional[Klip]:
        if klip_adi in self.klipler:
            self.aktif_duygu = klip_adi
            return self.klipler[klip_adi]
        return self.klipler.get("idle")

    def _veri_oku(self):
        while self.udp_socket.hasPendingDatagrams():
            boyut = self.udp_socket.pendingDatagramSize()
            veri, _, _ = self.udp_socket.readDatagram(boyut)
            try:
                metin = bytes(veri).decode("utf-8").strip()
                mesaj = json.loads(metin)
                if isinstance(mesaj, dict):
                    self.router_komutu_isle(mesaj)
            except (UnicodeDecodeError, json.JSONDecodeError) as hata:
                print(f"[Köprü HATA] Geçersiz JSON paketi: {hata}")

    def router_komutu_isle(self, mesaj: dict) -> Optional[Klip]:
        # 1. Bakış / Kafa Takip Verisi Kontrolü (MediaPipe)
        if "look_x" in mesaj or "look_y" in mesaj:
            try:
                lx = max(-1.0, min(1.0, float(mesaj.get("look_x", 0.0))))
                ly = max(-1.0, min(1.0, float(mesaj.get("look_y", 0.0))))
                self.bakis_komutu_geldi.emit(lx, ly)
            except (TypeError, ValueError):
                pass

        # 2. Duygu Değişimi Kontrolü
        hedef_duygu = mesaj.get("emotion")
        if hedef_duygu:
            eslesen_anahtar = next(
                (k for k in self.klipler.keys() if k.lower() == hedef_duygu.lower()),
                None
            )
            if eslesen_anahtar:
                self.aktif_duygu = eslesen_anahtar
                print(f"[Köprü] Duygu uygulanıyor: {eslesen_anahtar}")
                self.duygu_komutu_geldi.emit(eslesen_anahtar)
                return self.klipler[eslesen_anahtar]
            else:
                print(f"[Köprü UYARI] '{hedef_duygu}' adında bir klip bulunamadı!")
        return None