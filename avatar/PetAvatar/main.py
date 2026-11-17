import sys
import time
import ctypes

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QTimer, QPoint

from avatar.character import KediKarakteri


class AvatarPenceresi(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pet Avatar")
        self.kedi = KediKarakteri(self)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True
        )

        self.setStyleSheet("background: transparent;")

        # Tam kediyi pencereye ekle.
        self.resize(self.kedi.size())
        self.kedi.move(0, 0)

        # --- SÜRÜKLEME VE GİZLEME DURUM DEĞİŞKENLERİ ---
        self.surukleniyor = False
        self.surukleme_ofseti = QPoint()
        self.f8_basiliydi = False  # Tuşa basılı tutulduğunda sürekli tetiklenmeyi önler

        # --- ZAMANLAYICI (QTIMER) ---
        self.baslangic_zamani = time.time()
        self.zamanlayici = QTimer(self)
        self.zamanlayici.timeout.connect(self.animasyon_guncelle)
        self.zamanlayici.start(16)  # ~60 FPS

    def animasyon_guncelle(self):
        # 1. Global F8 Tuşu Kontrolü
        f8_durumu = ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000
        if f8_durumu and not self.f8_basiliydi:
            self.gorunurluk_degistir()
        self.f8_basiliydi = bool(f8_durumu)

        # 2. Zaman, Animasyon ve Masaüstü Hareketi
        if self.isVisible():
            t = time.time() - self.baslangic_zamani
            self.kedi.zaman_guncelle(t)

            # Kedi yürüyorsa ve kullanıcı fareyle sürüklemiyorsa pencereyi kaydır
            if not self.surukleniyor and self.kedi.hareket_durumu == "yuruyor":
                hiz = 2  # Piksel / kare hızı
                mevcut_x = self.x()
                mevcut_y = self.y()
                yeni_x = mevcut_x + (hiz * self.kedi.yurume_yonu)

                # Aktif ekranın kullanılabilir genişliğini al (Görev çubuğu hariç)
                ekran_alani = QApplication.primaryScreen().availableGeometry()
                sol_sinir = ekran_alani.left()
                sag_sinir = ekran_alani.right() - self.width()

                # Ekranın sağına çarptıysa sola dön
                if yeni_x >= sag_sinir:
                    yeni_x = sag_sinir
                    self.kedi.yon_degistir(-1)
                # Ekranın soluna çarptıysa sağa dön
                elif yeni_x <= sol_sinir:
                    yeni_x = sol_sinir
                    self.kedi.yon_degistir(1)

                self.move(yeni_x, mevcut_y)

            self.kedi.update()

    def gorunurluk_degistir(self):
        """F8'e basıldığında pencereyi gizler veya tekrar gösterir."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    # --- SOL ALT + FARE İLE SÜRÜKLEME OLAYLARI ---
    def mousePressEvent(self, event):
        # Sol tık ve klavyede Alt tuşu aynı anda basılıysa sürüklemeyi başlat
        if (event.button() == Qt.MouseButton.LeftButton and 
                event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.surukleniyor = True
            self.surukleme_ofseti = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            # Alt tuşuna basılmadıysa olayı normal tıklama (uyuma/uyanma) için alt katmana bırak
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.surukleniyor:
            yeni_konum = event.globalPosition().toPoint() - self.surukleme_ofseti
            self.move(yeni_konum)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.surukleniyor:
            self.surukleniyor = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)


app = QApplication(sys.argv)

pencere = AvatarPenceresi()
pencere.show()

sys.exit(app.exec())