"""
Kedi yuvası: Yumak minder çizimi.

Arkadaşının YuvaPenceresi.paintEvent'i bu dosyadaki ciz_yuva() fonksiyonunu çağırır.
Tasarım sayfasında (Yumak Minder Tasarımı) seçilen ayarlar aşağıdaki AYARLAR sözlüğündedir.

Birim: "avatar birimi". Yuva penceresi 600 x 650 birimdir, ekranda KARAKTER_OLCEGI (0,40) ile
240 x 260 piksel olur. Kedi penceresi 420 x 550 birimdir. Her ikisinin de alt kenarı aynı hizadadır.

Kedi içeri girince kedi penceresi gizlenir. Bu yüzden "içeride" halinde minderde uyuyan kediyi
yuvanın kendisi çizer: gövde body_renderer.py'deki uyku geometrisiyle, yüz robotun
motion/yuz.py çizicisiyle (Yüz Atölyesi'ndeki "Uyuyan" ifade).

Tek başına deneme (PetAvatar klasöründeyken):
    python -m avatar.yuva_cizim
"""

import math
import sys
import time
from pathlib import Path

# Dosya doğrudan çalıştırılırsa da "avatar" ve "motion" paketleri bulunsun
_KOK = Path(__file__).resolve().parent.parent
if str(_KOK) not in sys.path:
    sys.path.insert(0, str(_KOK))

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont

from motion.yuz import YuzCizici, Cokgen, Cizgi
from motion.klip import YUZ_VARSAYILAN
from avatar.face_renderer import FaceRenderer


# --- Tasarım sayfasından gelen ayarlar (18 Kas 2026) ---
AYARLAR = {
    "minder_genislik": 250,
    "minder_yukseklik": 70,
    "kenar_kalinligi": 70,
    "kedi_gomulme": 10,
    "renk_kenar": "#F4C3CC",
    "renk_golge": "#E7A6B3",
    "renk_ic": "#FCEDEF",
    "renk_cizgi": "#777982",
    "dikis": True,
    "pati_izi": True,
    "zzz": False,
}

YUVA_W, YUVA_H = 600, 650       # yuva penceresi (birim)
ZEMIN = 610                      # kedinin ayakları kendi penceresinde alttan 40 birim yukarıda

# Kedinin gövde renkleri (body_renderer.py ile aynı)
GOVDE_CIZGI = "#777982"
GOVDE_RENK = "#E6E4E5"
KARIN_RENK = "#F8F4EF"

# Uyuyan yüz: Yüz Atölyesi'ndeki "Uyuyan" hazır ifadesi
UYUYAN_YUZ = dict(YUZ_VARSAYILAN)
UYUYAN_YUZ.update({
    "eye_shape": "closed", "brow_show": False, "mouth": "smile", "mouth_open": 0.1, "blush": True,
    "body_yaw": 0.0, "head_pan": 0.0, "head_tilt": -6.0, "ear_left": 0.5, "ear_right": 0.5,
})

_yuz_cizici = YuzCizici(canli=False)   # uyurken göz kırpmaz


# --- küçük yardımcılar ---
def _elips(cx, cy, rx, ry):
    return QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry)


def _renk(hex_renk, alfa=1.0):
    c = QColor(hex_renk)
    c.setAlphaF(max(0.0, min(1.0, alfa)))
    return c


def _kalem(renk, kalinlik, kesik=None):
    k = QPen(renk, kalinlik)
    k.setCapStyle(Qt.PenCapStyle.RoundCap)
    k.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    if kesik:
        k.setStyle(Qt.PenStyle.CustomDashLine)
        k.setDashPattern([kesik[0] / kalinlik, kesik[1] / kalinlik])   # Qt kesik uzunluğunu kalem kalınlığı cinsinden ister
    return k


def _pati(painter, x, y, olcek, renk):
    painter.save()
    painter.translate(x, y)
    painter.scale(olcek, olcek)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(renk)))
    painter.drawEllipse(_elips(0, 6, 11, 9))
    for px, py in ((-12, -6), (-4, -12), (4, -12), (12, -6)):
        painter.drawEllipse(_elips(px, py, 4.2, 5))
    painter.restore()


# --- uyuyan kedi ---
def _uyuyan_govde(painter, nefes):
    """body_renderer.py'nin 'uyuyor' dalı (420 x 220'lik gövde alanında)."""
    govde_y = 70 - nefes
    govde_h = 130 + nefes
    karin_y = 90 - nefes * 0.7
    karin_h = 80 + nefes * 0.7
    sapma = 60

    kuyruk = QPainterPath()
    kuyruk.moveTo(130, 130 + sapma * 0.5)
    kuyruk.cubicTo(55, 135 + sapma, 30, 75 + sapma, 70, 45 + nefes / 2 + sapma)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(_kalem(QColor(GOVDE_CIZGI), 22))
    painter.drawPath(kuyruk)
    painter.setPen(_kalem(QColor(GOVDE_RENK), 15))
    painter.drawPath(kuyruk)

    painter.setPen(QPen(QColor(GOVDE_CIZGI), 6))
    painter.setBrush(QBrush(QColor(GOVDE_RENK)))
    painter.drawEllipse(QRectF(85, govde_y, 260, govde_h))

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(KARIN_RENK)))
    painter.drawEllipse(QRectF(165, karin_y, 105, karin_h))


def _uyuyan_kedi(painter, x, y, t, olcek):
    """Kedi penceresini (420 x 550) sol üst köşesi (x, y) olacak şekilde, uyurken çizer.
    Nefes hesabı character.py ile aynı: kayma piksel cinsinden, gövdeye birim olarak aktarılır."""
    kayma_px = int(UYUYAN_YUZ["head_tilt"] * 1.5 + math.sin(t * 3) * 5)
    nefes = kayma_px / olcek

    painter.save()
    painter.translate(x, y)

    # Gövde: kedi penceresinde y = 300'deki 420 x 220'lik alan
    painter.save()
    painter.translate(0, 300)
    painter.setClipRect(QRectF(-40, 0, 500, 220), Qt.ClipOperation.IntersectClip)
    _uyuyan_govde(painter, nefes)
    painter.restore()

    # Baş: yüz widget'ı uyurken y = 65'te, 420 x 345'lik sahne 420'lik kutuda dikey ortalanır (+37,5)
    painter.save()
    painter.translate(0, 65 + 37.5 - nefes)
    for oge in _yuz_cizici.olustur(UYUYAN_YUZ, t_ms=t * 1000):
        if isinstance(oge, Cokgen):
            FaceRenderer.cokgen_ciz(painter, oge)
        elif isinstance(oge, Cizgi):
            FaceRenderer.cizgi_ciz(painter, oge)
    painter.restore()

    painter.restore()


def _zzz(painter, x, y, t, renk):
    font = QFont("Segoe UI", 40)
    font.setBold(True)
    painter.setFont(font)
    for i in range(3):
        k = ((t * 1000 / 2600) + i / 3) % 1
        s = 0.5 + k * 0.7
        painter.save()
        painter.translate(x + k * 60 + math.sin(k * 6 + i) * 8, y - k * 130)
        painter.scale(s, s)
        painter.setPen(_renk(renk, math.sin(k * math.pi) * 0.85))
        painter.drawText(QPointF(-12, 0), "z")
        painter.restore()


# --- ana fonksiyon ---
def ciz_yuva(painter: QPainter, w: float, h: float, kedi_iceride: bool, t: float = None, ayarlar: dict = None):
    """Yumak minderi (ve içerideyse uyuyan kediyi) w x h piksellik yuva penceresine çizer.

    painter: YuvaPenceresi.paintEvent içindeki QPainter
    w, h: pencere boyutu (piksel); 600 x 650 birim buna ölçeklenir
    kedi_iceride: True ise minderde uyuyan kedi çizilir
    t: saniye cinsinden zaman (nefes için); verilmezse saat kullanılır
    """
    A = dict(AYARLAR)
    if ayarlar:
        A.update(ayarlar)
    if t is None:
        t = time.monotonic()

    rx, ry, kenar = A["minder_genislik"], A["minder_yukseklik"], A["kenar_kalinligi"]
    cizgi = QColor(A["renk_cizgi"])
    cx = YUVA_W / 2
    cy = ZEMIN - 20 - ry * 0.84
    irx, iry = rx - kenar, ry - kenar * 0.64
    on_alt, ic_alt = cy + 20 + ry * 0.84, cy + 12 + iry

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    olcek = w / YUVA_W
    painter.scale(olcek, h / YUVA_H)

    # 0. yumuşak gölge
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(_renk("#2B2A33", 0.16)))
    painter.drawEllipse(_elips(cx, ZEMIN, rx + 6, 12))

    # 1. arka kenar
    painter.setPen(_kalem(cizgi, 6))
    painter.setBrush(QBrush(QColor(A["renk_kenar"])))
    painter.drawEllipse(_elips(cx, cy, rx, ry))

    # 2. iç yastık ve üstündeki gölge
    ic = QPainterPath()
    ic.addEllipse(_elips(cx, cy + 12, irx, iry))
    painter.setPen(_kalem(cizgi, 3.5))
    painter.setBrush(QBrush(QColor(A["renk_ic"])))
    painter.drawPath(ic)
    painter.save()
    painter.setClipPath(ic, Qt.ClipOperation.IntersectClip)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(_renk(A["renk_golge"], 0.33)))
    painter.drawEllipse(_elips(cx, cy + 12 - iry * 0.58, irx * 1.08, iry * 0.6))
    painter.restore()

    # 3. uyuyan kedi (sadece içerideyken)
    if kedi_iceride:
        _uyuyan_kedi(painter, cx - 210 + 6, cy + 60 + A["kedi_gomulme"] - 500, t, olcek)

    # 4. ön kenar: kedinin önünden geçer
    dis = _elips(cx, cy, rx, on_alt - cy)
    ic_r = _elips(cx, cy + 12, irx, iry)
    on = QPainterPath()
    on.arcMoveTo(dis, 0)
    on.arcTo(dis, 0, -180)        # dış elipsin alt yarısı, sağdan sola
    on.arcTo(ic_r, 180, 180)      # iç elipsin alt yarısı, soldan sağa
    on.closeSubpath()
    painter.setPen(_kalem(cizgi, 6))
    painter.setBrush(QBrush(QColor(A["renk_kenar"])))
    painter.drawPath(on)

    bant_y = (on_alt + ic_alt) / 2
    if A["dikis"]:
        srx, sry = (rx + irx) / 2, bant_y - (cy + 16)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(_kalem(_renk("#FFFFFF", 0.6), 2.5, kesik=(6, 9)))
        r = _elips(cx, cy + 16, srx, sry)
        painter.drawArc(r, int(-18 * 16), int(-54 * 16))     # sağ alt
        painter.drawArc(r, int(-108 * 16), int(-54 * 16))    # sol alt
    if A["pati_izi"]:
        _pati(painter, cx, bant_y + 2, 1.0, A["renk_golge"])

    if kedi_iceride and A["zzz"]:
        _zzz(painter, cx + 150, cy - 150 + A["kedi_gomulme"], t, A["renk_cizgi"])

    painter.restore()


# --- tek başına deneme: iki hali yan yana gösterir ---
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel
    from PySide6.QtCore import QTimer

    OLCEK = 0.40

    class Onizleme(QWidget):
        def __init__(self, iceride):
            super().__init__()
            self.iceride = iceride
            self.setFixedSize(round(YUVA_W * OLCEK), round(YUVA_H * OLCEK))

        def paintEvent(self, event):
            p = QPainter(self)
            p.fillRect(self.rect(), QColor("#E4ECF6"))
            ciz_yuva(p, self.width(), self.height(), self.iceride)
            p.end()

    app = QApplication(sys.argv)
    pencere = QWidget()
    pencere.setWindowTitle("Yumak minder: boş / kedi içeride")
    satir = QHBoxLayout(pencere)
    kutular = []
    for baslik, iceride in (("Boş", False), ("Kedi içeride", True)):
        kolon = QVBoxLayout()
        kolon.addWidget(QLabel(baslik))
        kutu = Onizleme(iceride)
        kolon.addWidget(kutu)
        satir.addLayout(kolon)
        kutular.append(kutu)
    zaman = QTimer()
    zaman.timeout.connect(lambda: [k.update() for k in kutular])
    zaman.start(33)
    pencere.show()

    if "--png" in sys.argv:   # ekran görüntüsü alıp çık (test için)
        def kaydet():
            pencere.grab().save(sys.argv[sys.argv.index("--png") + 1])
            app.quit()
        QTimer.singleShot(300, kaydet)

    sys.exit(app.exec())
