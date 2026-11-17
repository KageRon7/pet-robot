import os
import math
import random
import ctypes
from pathlib import Path
from PySide6.QtWidgets import QWidget, QMenu, QApplication
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt, QPoint

from avatar.face_renderer import FaceRenderer
from avatar.body_renderer import BodyRenderer
from integration.robot_koprusu import PetRobotKoprusu
from motion.klip import Enterpolator

KARAKTER_OLCEGI = 0.40


class KediKarakteri(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        genislik = round(420 * KARAKTER_OLCEGI)
        yukseklik = round(550 * KARAKTER_OLCEGI)
        self.setFixedSize(genislik, yukseklik)

        self.govde = BodyRenderer(self)
        self.govde.setFixedSize(
            round(420 * KARAKTER_OLCEGI),
            round(220 * KARAKTER_OLCEGI)
        )
        self.govde.move(0, round(300 * KARAKTER_OLCEGI))

        self.yuz = FaceRenderer(self)
        self.yuz.setGeometry(
            0,
            round(30 * KARAKTER_OLCEGI),
            round(420 * KARAKTER_OLCEGI),
            round(420 * KARAKTER_OLCEGI)
        )
        self.yuz.raise_()

        su_anki_dizin = os.path.dirname(os.path.abspath(__file__))
        ana_dizin = os.path.dirname(su_anki_dizin)
        clips_klasoru = Path(ana_dizin) / 'motion' / 'clips'

        # --- ORTAK PET ROBOT DAVRANIŞ KÖPRÜSÜ ---
        self.kopru = PetRobotKoprusu(clips_klasoru, port=5555, parent=self)
        self.kopru.duygu_komutu_geldi.connect(self.duygu_degistir)
        self.kopru.bakis_komutu_geldi.connect(self.mediapipe_bakis_guncelle)

        # --- DURUM VE YÜRÜYÜŞ DEĞİŞKENLERİ ---
        self.hareket_durumu = "bekliyor"
        self.yurume_yonu = 1
        self.sonraki_karar_zamani = 3.0
        self.klip_baslangic_zamani = 0.0
        self.son_zaman = 0.0

        # --- GÖZ VE KAFA TAKİP DEĞİŞKENLERİ ---
        self.fare_takibi_aktif = True
        self.son_mediapipe_zamani = -10.0
        self.mp_hedef_x = 0.0
        self.mp_hedef_y = 0.0
        self.yumusak_bakis_x = 0.0
        self.yumusak_bakis_y = 0.0

        self.aktif_klip = self.kopru.klip_getir("idle")

    def mediapipe_bakis_guncelle(self, lx: float, ly: float):
        """Kaan'ın kamerasından gelen bakış koordinatlarını kaydeder."""
        self.mp_hedef_x = lx
        self.mp_hedef_y = ly
        self.son_mediapipe_zamani = self.son_zaman

    def duygu_degistir(self, duygu_adi: str):
        yeni_klip = self.kopru.klip_getir(duygu_adi)
        if yeni_klip:
            self.aktif_klip = yeni_klip
            self.klip_baslangic_zamani = self.son_zaman

            if duygu_adi == "sleepy":
                self.hareket_durumu = "uyuyor"
            else:
                if self.hareket_durumu == "uyuyor":
                    self.hareket_durumu = "bekliyor"
                self.sonraki_karar_zamani = self.son_zaman + 5.0

    def yon_degistir(self, yeni_yon: int):
        self.yurume_yonu = yeni_yon

    def _fare_takibi_degistir(self):
        self.fare_takibi_aktif = not self.fare_takibi_aktif

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2B2A33;
                color: #F8F4EF;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4A4856;
            }
        """)

        duygular_menusu = menu.addMenu("İfade / Animasyon Seç")
        for klip_adi in self.kopru.mevcut_duygulari_getir():
            aksiyon = duygular_menusu.addAction(klip_adi)
            aksiyon.triggered.connect(lambda checked=False, ad=klip_adi: self.duygu_degistir(ad))

        menu.addSeparator()

        takip_metni = "Fare Takibini Kapat" if self.fare_takibi_aktif else "Fare Takibini Aç"
        takip_aksiyon = menu.addAction(takip_metni)
        takip_aksiyon.triggered.connect(self._fare_takibi_degistir)

        if self.hareket_durumu == "uyuyor":
            uyandir_aksiyon = menu.addAction("Uyandır")
            uyandir_aksiyon.triggered.connect(lambda: self.duygu_degistir("idle"))
        else:
            uyut_aksiyon = menu.addAction("Uyut (Zzz)")
            uyut_aksiyon.triggered.connect(lambda: self.duygu_degistir("sleepy"))

        yuru_aksiyon = menu.addAction("Yürüyüşe Çıkar")
        yuru_aksiyon.triggered.connect(self._yuruyuse_cikar)

        menu.addSeparator()

        cikis_aksiyon = menu.addAction("Kapat")
        cikis_aksiyon.triggered.connect(QApplication.quit)

        menu.exec(event.globalPos())

    def _yuruyuse_cikar(self):
        self.hareket_durumu = "yuruyor"
        self.yurume_yonu = random.choice([-1, 1])
        self.aktif_klip = self.kopru.klip_getir("happy") or self.kopru.klip_getir("idle")
        self.klip_baslangic_zamani = self.son_zaman
        self.sonraki_karar_zamani = self.son_zaman + 5.0

    def mousePressEvent(self, event):
        sol_alt_basili = bool(ctypes.windll.user32.GetAsyncKeyState(0xA4) & 0x8000)
        if sol_alt_basili or (event.modifiers() & Qt.KeyboardModifier.AltModifier):
            event.ignore()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self.hareket_durumu != "uyuyor":
                self.duygu_degistir("sleepy")
            else:
                self.duygu_degistir("idle")
                self.sonraki_karar_zamani = self.son_zaman + 2.0
            event.accept()

    def _hedef_bakisi_hesapla(self, t: float) -> tuple[float, float]:
        """Öncelik sırasına göre (MediaPipe -> Fare İmleci -> Nötr) hedef bakışı belirler."""
        if self.hareket_durumu == "uyuyor":
            return 0.0, 0.0

        # 1. Öncelik: Son 3 saniye içinde Kaan'ın MediaPipe modülünden veri geldiyse onu kullan
        if (t - self.son_mediapipe_zamani) <= 3.0:
            return self.mp_hedef_x, self.mp_hedef_y

        # 2. Öncelik: Yürümüyorsa ve fare takibi açıksa imleci takip et
        if self.fare_takibi_aktif and self.hareket_durumu == "bekliyor":
            imlec_konumu = QCursor.pos()
            yuz_merkezi_yerel = QPoint(self.yuz.width() // 2, self.yuz.y() + self.yuz.height() // 2)
            yuz_merkezi_ekran = self.mapToGlobal(yuz_merkezi_yerel)

            fark_x = imlec_konumu.x() - yuz_merkezi_ekran.x()
            fark_y = imlec_konumu.y() - yuz_merkezi_ekran.y()

            # 350 piksellik yarıçapı [-1.0, 1.0] aralığına normalize et
            hedef_x = max(-1.0, min(1.0, fark_x / 350.0))
            hedef_y = max(-1.0, min(1.0, fark_y / 350.0))
            return hedef_x, hedef_y

        # 3. Öncelik: Yürüyorsa gittiği yöne baksın
        if self.hareket_durumu == "yuruyor":
            return 0.7 * self.yurume_yonu, 0.0

        return 0.0, 0.0

    def zaman_guncelle(self, t):
        self.son_zaman = t
        if not self.aktif_klip:
            return

        # Otonom karar mekanizması (MediaPipe aktif değilken çalışır)
        mediapipe_aktif = (t - self.son_mediapipe_zamani) <= 3.0
        if self.hareket_durumu != "uyuyor" and not mediapipe_aktif and t >= self.sonraki_karar_zamani:
            secim = random.choice(["bekliyor", "bekliyor", "yuruyor"])
            self.hareket_durumu = secim

            if secim == "yuruyor":
                self.yurume_yonu = random.choice([-1, 1])
                klip_adi = random.choice(["idle", "happy", "playful"])
                self.aktif_klip = self.kopru.klip_getir(klip_adi)
            else:
                self.aktif_klip = self.kopru.klip_getir("idle")

            self.klip_baslangic_zamani = t
            self.sonraki_karar_zamani = t + random.uniform(4.0, 7.0)

        gecen_sure = max(0.0, t - self.klip_baslangic_zamani)
        t_ms = gecen_sure * 1000

        if self.aktif_klip.dongu and self.aktif_klip.sure_ms > 0:
            t_ms = t_ms % self.aktif_klip.sure_ms
        elif t_ms > self.aktif_klip.sure_ms:
            t_ms = self.aktif_klip.sure_ms

        guncel_yuz = Enterpolator.yuz_ornekle(self.aktif_klip, t_ms)
        guncel_poz = Enterpolator.ornekle(self.aktif_klip, t_ms)
        tum_degerler = {**guncel_yuz, **guncel_poz}

        # --- GÖZ VE KAFA TAKİBİ UYGULAMASI ---
        hedef_x, hedef_y = self._hedef_bakisi_hesapla(t)
        # Yumuşak geçiş (Lerp) ile gözlerin ve kafanın doğal süzülmesini sağla
        self.yumusak_bakis_x += (hedef_x - self.yumusak_bakis_x) * 0.15
        self.yumusak_bakis_y += (hedef_y - self.yumusak_bakis_y) * 0.15

        if self.hareket_durumu != "uyuyor":
            tum_degerler["look_x"] = max(-1.0, min(1.0, tum_degerler.get("look_x", 0.0) + self.yumusak_bakis_x))
            tum_degerler["look_y"] = max(-1.0, min(1.0, tum_degerler.get("look_y", 0.0) + self.yumusak_bakis_y))
            tum_degerler["head_pan"] = max(-90.0, min(90.0, tum_degerler.get("head_pan", 0.0) + (self.yumusak_bakis_x * 30.0)))
            tum_degerler["head_tilt"] = max(-10.0, min(45.0, tum_degerler.get("head_tilt", 0.0) - (self.yumusak_bakis_y * 15.0)))

        self.yuz.yuz_durumunu_guncelle(tum_degerler)
        self.yuz.zamani_guncelle(t_ms)

        head_tilt = tum_degerler.get("head_tilt", 0.0)
        nefes_etkisi = math.sin(t * 3) * 5
        yurume_sekmesi = abs(math.sin(t * 10)) * 3 if self.hareket_durumu == "yuruyor" else 0.0

        y_kayma = int((head_tilt * 1.5) + nefes_etkisi + yurume_sekmesi)

        if self.hareket_durumu == "uyuyor":
            baslangic_y = round(65 * KARAKTER_OLCEGI)
        else:
            baslangic_y = round(30 * KARAKTER_OLCEGI)

        self.yuz.move(0, baslangic_y - y_kayma)

        telafi_edilmis_esneme = y_kayma / KARAKTER_OLCEGI

        self.govde.durum_guncelle({
            "nefes_esnemesi": telafi_edilmis_esneme,
            "hareket_durumu": self.hareket_durumu,
            "yurume_fazi": t,
            "yon": self.yurume_yonu
        })