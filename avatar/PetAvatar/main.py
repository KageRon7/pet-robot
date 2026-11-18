import sys
import ctypes
import time
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer, QRect, QPoint
from PySide6.QtGui import QCursor, QPainter
from avatar.character import KediKarakteri, KARAKTER_OLCEGI

# 1. Arkadaşının hazırladığı yuva çizimini içe aktarıyoruz
from avatar.yuva_cizim import ciz_yuva

# --- 1. YENİ MİNDER/YUVA PENCERESİ ---
class YuvaPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.w = int(600 * KARAKTER_OLCEGI)
        self.h = int(650 * KARAKTER_OLCEGI)
        self.resize(self.w, self.h)
        
        self.kedi_iceride = False
        
        # Kedinin minderde nefes alması için kısa bir zamanlayıcı ekliyoruz
        self.nefes_t = 0.0
        self.animasyon_timer = QTimer(self)
        self.animasyon_timer.timeout.connect(self.nefes_guncelle)
        self.animasyon_timer.start(50) # 50ms (20 fps)
        
    def nefes_guncelle(self):
        if self.kedi_iceride:
            self.nefes_t += 0.05
            self.update() # Ekranı tazele
        
    def paintEvent(self, event):
        # 3. Bizim eski ev çizimini sildik, yerine arkadaşının ciz_yuva fonksiyonunu koyduk
        painter = QPainter(self)
        ciz_yuva(painter, self.w, self.h, self.kedi_iceride)
        painter.end()


# --- 2. ANA KEDİ PENCERESİ VE KONTROLCÜ ---
class AvatarPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.kedi = KediKarakteri(self)
        self.setCentralWidget(self.kedi)
        self.resize(self.kedi.width(), self.kedi.height())
        
        ekran_geometrisi = QApplication.primaryScreen().availableGeometry()
        self.ekran_genisligi = ekran_geometrisi.width()
        self.ekran_yuksekligi = ekran_geometrisi.height()
        
        self.move(self.ekran_genisligi - self.width() - 50, self.ekran_yuksekligi - self.height())
        
        self.yuva = YuvaPenceresi()
        yuva_y = self.y() + self.height() - self.yuva.height()
        self.yuva.move(0, yuva_y)
        
        # Başlangıçta yuva ekranda GİZLİ başlıyor
        # (İstersen self.yuva.show() yapıp görünür başlatabilirsin)
        self.yuva.hide()
        
        self.f8_basili_mi = False
        self.alt_basili_mi = False
        self.surukleniyor = False
        self.eski_konum = None
        self.baslangic_zamani = time.time()
        
        self.zamanlayici = QTimer(self)
        self.zamanlayici.timeout.connect(self.guncelle)
        self.zamanlayici.start(16)

    def guncelle(self):
        su_an = time.time() - self.baslangic_zamani
        self.kedi.zaman_guncelle(su_an)
        
        alt_durum = bool(ctypes.windll.user32.GetAsyncKeyState(0x12) & 0x8000)
        if alt_durum != self.alt_basili_mi:
            self.alt_basili_mi = alt_durum
            self.setWindowFlag(Qt.WindowTransparentForInput, not self.alt_basili_mi)
            self.show()
        
        # F8 Tuşu: Sadece kediyi değil, duruma göre yuvayı da gizle/göster
        f8_durum = bool(ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000)
        if f8_durum and not self.f8_basili_mi:
            if self.kedi.hareket_durumu == "evde":
                self.yuva.setVisible(not self.yuva.isVisible())
            else:
                self.setVisible(not self.isVisible())
        self.f8_basili_mi = f8_durum
        
        if not self.isVisible() and self.kedi.hareket_durumu != "evde":
            return
            
        # --- YENİ YUVA VE IŞINLANMA MANTIĞI ---
        if self.kedi.hareket_durumu == "evde":
            # Kedi evde. Eğer fare yuvanın üstüne gelirse kedi dışarı çıkar.
            if self.yuva.isVisible() and self.yuva.geometry().contains(QCursor.pos()):
                self.yuva.kedi_iceride = False
                self.yuva.update()
                
                self.setVisible(True)
                if hasattr(self.kedi, '_yuruyuse_cikar'):
                    self.kedi._yuruyuse_cikar()
                else:
                    self.kedi.duygu_degistir("idle")
                    
                self.kedi.hareket_durumu = "yuruyor"
                self.kedi.yon_degistir(1)
                
                # Kediyi minderin hemen sağından çıkart
                self.move(int(self.yuva.width() * 0.8), self.yuva.y() + self.yuva.height() - self.height())
        
        elif self.kedi.hareket_durumu == "yuruyor":
            yeni_x = self.x() + (2 * self.kedi.yurume_yonu)
            
            if yeni_x > self.ekran_genisligi - self.width():
                # Sağ kenardan dışarı çıkış (Gizli Işınlanma Senaryosu)
                if not self.yuva.isVisible():
                    self.kedi.hareket_durumu = "evde"
                    self.kedi.aktif_klip = None
                    self.setVisible(False)
                    self.yuva.kedi_iceride = True
                    self.yuva.update()
                    return
                else:
                    # Yuva açıksa sekip geri döner
                    yeni_x = self.ekran_genisligi - self.width()
                    self.kedi.yon_degistir(-1)
            
            elif yeni_x < 0:
                if self.yuva.isVisible():
                    # Senaryo 2: Yuva açıksa, minderin içine (x=0) girer
                    if yeni_x < self.yuva.width() // 3:
                        self.kedi.hareket_durumu = "evde"
                        self.kedi.aktif_klip = None
                        self.setVisible(False)
                        self.yuva.kedi_iceride = True
                        self.yuva.update()
                        return
                else:
                    # Senaryo 1: Yuva gizliyse, ekranın solundan çıkıp gizlice mindere ışınlanır
                    if yeni_x < -self.width():
                        self.kedi.hareket_durumu = "evde"
                        self.kedi.aktif_klip = None
                        self.setVisible(False)
                        self.yuva.kedi_iceride = True
                        self.yuva.update()
                        return
                        
            self.move(yeni_x, self.y())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.alt_basili_mi:
            self.surukleniyor = True
            self.eski_konum = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.surukleniyor and self.eski_konum:
            fark = event.globalPos() - self.eski_konum
            yeni_y = self.y() + fark.y()
            
            self.move(self.x() + fark.x(), yeni_y)
            
            # Yuvanın Y konumunu kediyle eşitle
            yuva_y = yeni_y + self.height() - self.yuva.height()
            self.yuva.move(0, yuva_y)
            
            self.eski_konum = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.surukleniyor = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = AvatarPenceresi()
    pencere.show()
    sys.exit(app.exec())