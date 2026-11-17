
from typing import Any, Dict

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPolygonF
)

from motion.yuz import (
    YuzCizici,
    Cokgen,
    Cizgi,
    KANVAS_GENISLIK,
    KANVAS_YUKSEKLIK
)

from motion.klip import YUZ_VARSAYILAN


class FaceRenderer(QWidget):
    """
    Eski kedi yüzü çizim sistemini PySide6 ile ekrana aktarır.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Eski yüz çizim sistemimiz.
        self.yuz_cizici = YuzCizici(canli=True)

        # Başlangıç yüz değerleri.
        self.yuz_durumu: Dict[str, Any] = dict(YUZ_VARSAYILAN)

        # Baş ve kulakların başlangıç pozisyonları.
        self.yuz_durumu.update({
            "body_yaw": 0.0,
            "head_pan": 0.0,
            "head_tilt": 0.0,
            "ear_left": 1.0,
            "ear_right": 1.0
        })

        self.zaman_ms = 0.0

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

    def yuz_durumunu_guncelle(self, yeni_durum: Dict[str, Any]):
        """Yüz ve hareket değerlerini günceller."""

        self.yuz_durumu.update(yeni_durum)
        self.update()

    def zamani_guncelle(self, zaman_ms: float):
        """Animasyon zamanını günceller."""

        self.zaman_ms = zaman_ms
        self.update()

    def paintEvent(self, event):
        """Kedi yüzünü ekrana çizer."""

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True
        )

        # Orijinal yüz boyutunu pencereye ölçekle.
        olcek_x = self.width() / KANVAS_GENISLIK
        olcek_y = self.height() / KANVAS_YUKSEKLIK

        olcek = min(olcek_x, olcek_y)

        # Ortalamak için boşluk hesapla.
        x = (self.width() - KANVAS_GENISLIK * olcek) / 2
        y = (self.height() - KANVAS_YUKSEKLIK * olcek) / 2

        painter.translate(x, y)
        painter.scale(olcek, olcek)

        # Eski çizim sisteminden şekilleri al.
        ogeler = self.yuz_cizici.olustur(
            self.yuz_durumu,
            t_ms=self.zaman_ms
        )

        # Şekilleri tek tek çiz.
        for oge in ogeler:

            if isinstance(oge, Cokgen):
                self.cokgen_ciz(painter, oge)

            elif isinstance(oge, Cizgi):
                self.cizgi_ciz(painter, oge)

        painter.end()

    @staticmethod
    def cokgen_ciz(painter: QPainter, oge: Cokgen):
        """Kapalı geometrik şekilleri çizer."""

        noktalar = QPolygonF([
            QPointF(x, y)
            for x, y in oge.noktalar
        ])

        if oge.dolgu:
            painter.setBrush(QBrush(QColor(oge.dolgu)))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)

        if oge.cizgi:
            kalem = QPen(
                QColor(oge.cizgi),
                max(0.1, oge.kalinlik)
            )
            kalem.setCapStyle(Qt.PenCapStyle.RoundCap)
            kalem.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(kalem)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawPolygon(noktalar)

    @staticmethod
    def cizgi_ciz(painter: QPainter, oge: Cizgi):
        """Açık çizgileri ve eğrileri çizer."""

        kalem = QPen(
            QColor(oge.renk),
            max(0.1, oge.kalinlik)
        )

        kalem.setCapStyle(Qt.PenCapStyle.RoundCap)
        kalem.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        if oge.kesik:
            kalem.setStyle(Qt.PenStyle.CustomDashLine)
            kalem.setDashPattern([
                float(oge.kesik[0]),
                float(oge.kesik[1])
            ])

        painter.setPen(kalem)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        noktalar = QPolygonF([
            QPointF(x, y)
            for x, y in oge.noktalar
        ])

        painter.drawPolyline(noktalar)

