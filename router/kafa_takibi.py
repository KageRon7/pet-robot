"""
Kafa takibi: A1 face_track (x, y) -> kedinin head_pan / head_tilt hareketi.

Kurallar (kaptanın istediği):
  - Sürekli değil, sadece kedi "İlgilenme" basamağındayken takip eder.
  - Yüz ortadayken küçük bir ölü bölge var, kafa titremez.
  - Klip oynarken takip durur (move komutu klibin hareketini bozardı).
  - Sıkılınca (ilgi bitince) ya da yüz kaybolunca kafa ortaya döner, sonra idle klibi yeniden başlar.

UYARI: "İlgilenme basamağı" repoda tanımlı değil. ilgilenme_varsayilan() GEÇİCİ bir kuralı uygular
(yüz kamerada ve robota bakıyor). Gerçek tanım gelince sadece o fonksiyon değişir.
Bu sınıf kamera sabit varsayar (yüz kameranın görüntüsünde nerede ise kafa mutlak olarak oraya bakar).
Kamera robotun kafasındaysa hedef_acilar'ın artımlı (kapalı döngü) olması gerekir.
"""

from typing import Callable

# --- Ayar sabitleri (hepsi ilk tahmin, Wokwi/robotta denenip ayarlanır) ---
PAN_MAX_DERECE = 35.0  # yüz kadrajın kenarındayken kafa bu kadar döner
TILT_MAX_DERECE = 15.0  # head_tilt sınırı -10..45
YON_PAN = 1.0  # kafa ters tarafa dönerse -1.0 yap
YON_TILT = 1.0  # kafa ters yukarı/aşağı giderse -1.0 yap
OLU_BOLGE = 0.08  # görüntü merkezinden ±%8 içinde kafa ortada kalır
YUMUSATMA = 0.35  # 0-1, büyüdükçe takip hızlanır ama titrer
MIN_FARK_DERECE = 1.0  # bundan küçük açı değişiminde komut gönderilmez
GONDERME_HZ = 25.0  # en fazla saniyede bu kadar move komutu
ILK_HAREKET_MS = 300  # takibin ilk hareketi yumuşak olsun
HAREKET_MS = 80  # sonraki hareketler
KAYIP_S = 2.0  # yüz bu kadar sn yoksa kafa ortaya döner
SIKILMA_S = 15.0  # ilgilenme bu kadar sn yoksa kafa ortaya döner
ORTALA_MS = 800  # ortaya dönüş süresi
ORTALA_BEKLE_S = 0.9  # ortalandıktan sonra idle klibine dönmeden önce bekleme


def ilgilenme_varsayilan(bakiyor: bool) -> bool:
    """GEÇİCİ İlgilenme kuralı: kullanıcı robota bakıyorsa kedi ilgileniyor."""
    return bool(bakiyor)


class KafaTakipci:
    """A1 mesajlarını alır, uygunsa kafayı çevirir. Zamanı dışarıdan alır, bu yüzden donanımsız test edilir."""

    def __init__(
        self,
        gonder: Callable[[float, float, int], None],
        idle_don: Callable[[], None],
        klip_oynuyor: Callable[[float], bool],
        ilgilenme_mi: Callable[[bool], bool] = ilgilenme_varsayilan,
        sikildi_mi: Callable[[], bool] = lambda: False,
    ) -> None:
        self.gonder = gonder  # gonder(pan, tilt, ms)
        self.idle_don = idle_don  # ortalandıktan sonra idle klibini yeniden başlatır
        self.klip_oynuyor = klip_oynuyor  # klip_oynuyor(simdi) -> bool
        self.ilgilenme_mi = ilgilenme_mi  # ilgilenme_mi(bakiyor) -> bool  (1 argüman alır)
        self.sikildi_mi = sikildi_mi  # sikildi_mi() -> bool  (argüman almaz); True ise kafa beklemeden ortaya döner
        self._ilgi_yok_basi: float | None = None
        self._kayip_basi: float | None = None
        self._idle_zamani: float | None = None
        self._son_gonderme = -1e9
        self._takip_sifirla()
        
    def _takip_sifirla(self) -> None:
        self._takipte = False
        self._pan = 0.0
        self._tilt = 0.0
        self._son_gonderilen: tuple[float, float] | None = None

    @staticmethod
    def _olu_bolge(fark: float) -> float:
        """fark -0.5..0.5; ölü bölgede 0, dışında 0'dan başlayıp ±1'e çıkar."""
        if abs(fark) <= OLU_BOLGE:
            return 0.0
        deger = (abs(fark) - OLU_BOLGE) / (0.5 - OLU_BOLGE)
        return min(1.0, deger) * (1.0 if fark > 0 else -1.0)

    def hedef_acilar(self, x: float, y: float) -> tuple[float, float]:
        """Yüzün görüntüdeki konumundan (0-1, sol üst 0,0) kafanın hedef açısını (pan, tilt) hesaplar."""
        pan = YON_PAN * self._olu_bolge(x - 0.5) * PAN_MAX_DERECE
        tilt = YON_TILT * self._olu_bolge(0.5 - y) * TILT_MAX_DERECE
        return pan, tilt

    def yuz_geldi(self, x, y, present: bool, bakiyor: bool, simdi: float) -> None:
        """Her A1 mesajında çağrılır (simdi = time.monotonic() cinsinden saniye)."""
        if self.klip_oynuyor(simdi):
            self._takip_sifirla()  # klip oynarken takip durur
            self._idle_zamani = None
            return
        if self._idle_zamani is not None and simdi >= self._idle_zamani:
            self._idle_zamani = None
            self.idle_don()

        ilgi = bool(present) and x is not None and y is not None and bool(self.ilgilenme_mi(bakiyor))
        if present:
            self._kayip_basi = None
        elif self._kayip_basi is None:
            self._kayip_basi = simdi
        if ilgi:
            self._ilgi_yok_basi = None
        elif self._ilgi_yok_basi is None:
            self._ilgi_yok_basi = simdi

        if self._takipte and self._bitti_mi(simdi):
            self._ortala(simdi)
            return
        if ilgi:
            self._takip_et(x, y, simdi)

    def _bitti_mi(self, simdi: float) -> bool:
        kayip = self._kayip_basi is not None and simdi - self._kayip_basi >= KAYIP_S
        sikildi = (
            self._ilgi_yok_basi is not None and simdi - self._ilgi_yok_basi >= SIKILMA_S
        ) or bool(self.sikildi_mi())
        return kayip or sikildi

    def _ortala(self, simdi: float) -> None:
        self.gonder(0.0, 0.0, ORTALA_MS)
        self._takip_sifirla()
        self._ilgi_yok_basi = None
        self._kayip_basi = None
        self._idle_zamani = simdi + ORTALA_BEKLE_S

    def _takip_et(self, x: float, y: float, simdi: float) -> None:
        hedef_pan, hedef_tilt = self.hedef_acilar(x, y)
        if not self._takipte:
            self._takipte = True
            self._pan, self._tilt = hedef_pan, hedef_tilt
        else:
            self._pan += YUMUSATMA * (hedef_pan - self._pan)
            self._tilt += YUMUSATMA * (hedef_tilt - self._tilt)
        if simdi - self._son_gonderme < 1.0 / GONDERME_HZ:
            return
        if self._son_gonderilen is not None:
            fark = max(abs(self._pan - self._son_gonderilen[0]), abs(self._tilt - self._son_gonderilen[1]))
            if fark < MIN_FARK_DERECE:
                return
        ms = ILK_HAREKET_MS if self._son_gonderilen is None else HAREKET_MS
        self.gonder(self._pan, self._tilt, ms)
        self._son_gonderme = simdi
        self._son_gonderilen = (self._pan, self._tilt)