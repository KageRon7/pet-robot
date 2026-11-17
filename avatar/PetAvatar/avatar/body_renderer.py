import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPainterPath
)
from PySide6.QtCore import Qt


class BodyRenderer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )
        
        self.govde_durumu = {
            "nefes_esnemesi": 0.0,
            "hareket_durumu": "bekliyor",  # "bekliyor", "uyuyor", "yuruyor"
            "yurume_fazi": 0.0,            # Adım atma döngüsü için zaman değeri
            "yon": 1                       # 1: Sağa, -1: Sola
        }

    def durum_guncelle(self, yeni_durum: dict):
        self.govde_durumu.update(yeni_durum)
        self.update() 

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.scale(
            self.width() / 420,
            self.height() / 220
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        dis_cizgi = QColor("#777982")
        govde_rengi = QColor("#E6E4E5")
        karin_rengi = QColor("#F8F4EF")

        nefes = self.govde_durumu.get("nefes_esnemesi", 0.0)
        durum = self.govde_durumu.get("hareket_durumu", "bekliyor")
        faz = self.govde_durumu.get("yurume_fazi", 0.0)
        yon = self.govde_durumu.get("yon", 1)

        # --- DURUM BAZLI ANATOMİ VE ADIM HESAPLAMALARI ---
        sol_ayak_x = 0.0
        sol_ayak_y = 0.0
        sag_ayak_x = 0.0
        sag_ayak_y = 0.0
        kuyruk_sallanma = 0.0

        if durum == "uyuyor":
            govde_y = 70 - nefes
            govde_h = 130 + nefes
            govde_w = 260
            govde_x = 85
            
            karin_y = 90 - (nefes * 0.7)
            karin_h = 80 + (nefes * 0.7)
            
            kuyruk_y_sapma = 60
            ayaklari_ciz = False
        else:
            # Yürüme sırasında gövde hafifçe yaylanır (sekme efekti)
            sekme = abs(math.sin(faz * 10)) * 5 if durum == "yuruyor" else 0.0
            
            govde_y = 35 - nefes - sekme
            govde_h = 165 + nefes
            govde_w = 220
            govde_x = 105
            
            karin_y = 65 - (nefes * 0.7) - sekme
            karin_h = 115 + (nefes * 0.7)
            
            kuyruk_y_sapma = 0
            ayaklari_ciz = True

            if durum == "yuruyor":
                # Sol ve sağ ayak ters yönlerde adım atar (X ileri-geri, Y hafif yukarı kalkar)
                sol_ayak_x = math.sin(faz * 10) * 14
                sol_ayak_y = -max(0.0, math.cos(faz * 10)) * 6
                
                sag_ayak_x = -math.sin(faz * 10) * 14
                sag_ayak_y = -max(0.0, -math.cos(faz * 10)) * 6
                
                kuyruk_sallanma = math.sin(faz * 8) * 15

        # --- 1. KUYRUK ---
        # Kedi sola gidiyorsa kuyruğu gövdenin sağına, sağa gidiyorsa soluna doğru çizelim
        kuyruk = QPainterPath()
        if yon == 1:  # Sağa yürürken kuyruk solda
            kuyruk.moveTo(130, 130 + (kuyruk_y_sapma * 0.5))
            kuyruk.cubicTo(55, 135 + kuyruk_y_sapma, 30, 75 + kuyruk_y_sapma + kuyruk_sallanma, 70, 45 + (nefes / 2) + kuyruk_y_sapma)
        else:         # Sola yürürken veya beklerken kuyruk sağda
            kuyruk.moveTo(290, 130 + (kuyruk_y_sapma * 0.5))
            kuyruk.cubicTo(365, 135 + kuyruk_y_sapma, 390, 75 + kuyruk_y_sapma + kuyruk_sallanma, 350, 45 + (nefes / 2) + kuyruk_y_sapma)

        painter.setPen(QPen(dis_cizgi, 22, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(kuyruk)

        painter.setPen(QPen(govde_rengi, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(kuyruk)

        # --- 2. GÖVDE ---
        painter.setPen(QPen(dis_cizgi, 6))
        painter.setBrush(QBrush(govde_rengi))
        painter.drawEllipse(govde_x, govde_y, govde_w, govde_h)

        # --- 3. KARIN ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(karin_rengi))
        painter.drawEllipse(165, karin_y, 105, karin_h)

        # --- 4. AYAKLAR ---
        if ayaklari_ciz:
            # Sol Bacak
            painter.save()
            painter.translate(sol_ayak_x, sol_ayak_y)
            
            sol_bacak = QPainterPath()
            sol_bacak.moveTo(183, 154)
            sol_bacak.cubicTo(181, 166, 177, 181, 181, 194)
            sol_bacak.cubicTo(184, 207, 198, 210, 207, 202)
            sol_bacak.cubicTo(212, 196, 209, 181, 207, 158)
            sol_bacak.closeSubpath()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(karin_rengi))
            painter.drawPath(sol_bacak)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(dis_cizgi, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            sol_dis_hat = QPainterPath()
            sol_dis_hat.moveTo(183, 157)
            sol_dis_hat.cubicTo(181, 171, 177, 185, 181, 196)
            sol_dis_hat.cubicTo(185, 207, 198, 210, 207, 202)
            painter.drawPath(sol_dis_hat)

            painter.setPen(QPen(dis_cizgi, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(192, 198, 191, 203)
            painter.drawLine(200, 198, 200, 203)
            painter.restore()

            # Sağ Bacak
            painter.save()
            painter.translate(sag_ayak_x, sag_ayak_y)

            sag_bacak = QPainterPath()
            sag_bacak.moveTo(247, 154)
            sag_bacak.cubicTo(249, 166, 253, 181, 249, 194)
            sag_bacak.cubicTo(246, 207, 232, 210, 223, 202)
            sag_bacak.cubicTo(218, 196, 221, 181, 223, 158)
            sag_bacak.closeSubpath()

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(karin_rengi))
            painter.drawPath(sag_bacak)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(dis_cizgi, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            sag_dis_hat = QPainterPath()
            sag_dis_hat.moveTo(247, 157)
            sag_dis_hat.cubicTo(249, 171, 253, 185, 249, 196)
            sag_dis_hat.cubicTo(245, 207, 232, 210, 223, 202)
            painter.drawPath(sag_dis_hat)

            painter.setPen(QPen(dis_cizgi, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(230, 198, 230, 203)
            painter.drawLine(238, 198, 239, 203)
            painter.restore()

        painter.end()