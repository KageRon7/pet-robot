"""
sim/parcalar.py  --  Robotun ölçüleri, ağırlıkları ve motor bilgileri (tek yer).

Kaynak: Teknik Resim v0.2 + İç Mimari v0.3 taslak (21 Ekim).
Ölçüler milimetre, ağırlıklar gram. Montajda parçalar tartılıp ölçülünce
SADECE bu dosyadaki sayılar düzeltilir; geri kalan kod kendiliğinden uyar.

Eksen yönleri (robotun kendi gözünden):
  x = ileri (kullanıcıya doğru), y = sola, z = yukarı.
"""

from dataclasses import dataclass, field, replace
from typing import Dict


@dataclass(frozen=True)
class Servo:
    """Bir servo motor modelinin satıcı bilgileri (4.8 V için)."""

    ad: str
    tork_kgcm: float        # durma torku (en fazla zorlanma), kg·cm
    sn_60_derece: float     # yüksüz 60 dereceyi kaç saniyede döner
    akim_bos_a: float       # dururken çektiği akım
    akim_hareket_a: float   # yüksüz dönerken çektiği akım
    akim_durma_a: float     # takılınca (tam zorlanma) çektiği akım
    agirlik_g: float
    rotor_ataleti: float    # dişlilerden yansıyan iç atalet, kg·m² (tahmin)

    # Torku N·m birimine çevirir (fizik motoru bu birimi kullanır).
    @property
    def tork_nm(self) -> float:
        return self.tork_kgcm * 0.0980665

    # En yüksek dönüş hızını radyan/saniye olarak verir.
    @property
    def hiz_rad_s(self) -> float:
        return 1.0471976 / self.sn_60_derece


MG90S = Servo("MG90S", 1.8, 0.10, 0.01, 0.15, 0.70, 13.4, 5e-5)
MG996R = Servo("MG996R", 9.4, 0.17, 0.01, 0.20, 2.50, 55.0, 2e-4)
SG90 = Servo("SG90", 1.6, 0.10, 0.01, 0.12, 0.65, 9.0, 4e-5)
SERVOLAR: Dict[str, Servo] = {s.ad: s for s in (MG90S, MG996R, SG90)}


@dataclass(frozen=True)
class Robot:
    """Kedinin bütün fiziksel ayarları. Varsayılanlar Teknik Resim v0.2'dir."""

    # Taban: Ø110, 22 mm yüksek (ESP32, güç girişi, S0 burada)
    taban_cap: float = 110
    taban_yukseklik: float = 22
    # Gövde: 64 geniş, 72 derin, 52 yüksek
    govde_genislik: float = 64
    govde_derinlik: float = 72
    govde_yukseklik: float = 52
    # Boyun çatalı (S2 burada): 20 mm
    boyun_yukseklik: float = 20
    boyun_genislik: float = 30
    boyun_derinlik: float = 24
    # Kafa: 78 geniş, 50 yüksek, derinlik çizimde yok -> 60 tahmini
    kafa_genislik: float = 78
    kafa_yukseklik: float = 50
    kafa_derinlik: float = 60
    # Eğme ekseni kafanın altından ne kadar yukarıda (mm)
    egme_ekseni_yukseklik: float = 2
    # Kulak: tek plaka gibi düşünülür (3 menteşeli parça)
    kulak_genislik: float = 20
    kulak_kalinlik: float = 8
    kulak_yukseklik: float = 22
    kulak_aralik: float = 26          # kulak merkezi kafa ortasından ne kadar yanda
    kulak_yatma_derece: float = 80    # 0 değerinde kulak kaç derece geriye yatar

    # Ağırlıklar (gram) -- İç Mimari v0.3 ağırlık bütçesi
    taban_agirlik: float = 45 + 10 + 30 + 10   # taban + ESP32 + rulman + kablo/klemens
    govde_agirlik: float = 35 + 8              # gövde kabuğu + kablo
    boyun_agirlik: float = 5                   # çatal
    kafa_agirlik: float = 25 + 10 + 5          # kabuk + ekran + kablo (servolar ayrıca)
    kulak_agirlik: float = 3

    # Motorlar
    s0: Servo = MG996R   # gövde dönüşü (tabanda)
    s1: Servo = MG90S    # baş sağ-sol (gövdede)
    s2: Servo = MG90S    # baş yukarı-aşağı (boyunda)
    s3: Servo = MG90S    # sol kulak (kafada)
    s4: Servo = MG90S    # sağ kulak (kafada)

    # Masa: 0.3 ≈ PLA masada kayar, 0.8 ≈ lastik ayak
    masa_surtunme: float = 0.5
    # Güç: adaptör sınırı ve sabit tüketiciler (amper)
    adaptor_a: float = 5.0
    esp32_a: float = 0.25
    ekran_a: float = 0.08

    # Bir ayarı değiştirilmiş yeni robot döndürür: robot.degistir(s0=MG90S)
    def degistir(self, **ayarlar) -> "Robot":
        return replace(self, **ayarlar)

    # Robotun toplam ağırlığını (gram) hesaplar.
    @property
    def toplam_agirlik(self) -> float:
        return (self.taban_agirlik + self.govde_agirlik + self.boyun_agirlik + self.kafa_agirlik
                + 2 * self.kulak_agirlik
                + self.s0.agirlik_g + self.s1.agirlik_g + self.s2.agirlik_g
                + self.s3.agirlik_g + self.s4.agirlik_g)


# Eklem adları (C1 sözleşmesindeki sırayla) ve hangi servoya bağlı oldukları
EKLEM_SERVO = {
    "body_yaw": "s0",
    "head_pan": "s1",
    "head_tilt": "s2",
    "ear_left": "s3",
    "ear_right": "s4",
}
