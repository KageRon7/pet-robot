"""
sim/ikiz.py  --  Dijital ikiz: fizik modeli + sanal ESP32 + gerçekçi servolar.

Zincir, gerçek robotla aynı:
  C1 poz (router) -> sanal ESP32 (ms içinde düz geçiş, Eda'nın kodu gibi)
  -> servo (en fazla hız ve tork sınırı) -> fizik (ağırlık, atalet, sürtünme)

Her adımda ölçülenler: motor torku, akım, hedef ile gerçek açı farkı,
tabanın kayması / dönmesi / eğilmesi ve parçalar arası en kısa boşluk.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import mujoco
import numpy as np

from .model import HAREKETLI_PARCALAR, SABIT_PARCALAR, mjcf_uret
from .parcalar import EKLEM_SERVO, Robot

# C1 eklem sırası = MuJoCo motor sırası (S0..S4)
EKLEMLER: Tuple[str, ...] = tuple(EKLEM_SERVO)

# Robot açılışta bu pozda durur (Sözleşme: kulak nötr 0.8)
NOTR_POZ = {"body_yaw": 0.0, "head_pan": 0.0, "head_tilt": 0.0, "ear_left": 0.8, "ear_right": 0.8}


@dataclass
class Olcum:
    """Tek bir andaki ölçüm (gözlemci bunları toplar)."""

    t: float                     # saniye
    tork_oran: np.ndarray        # her servo için |tork| / durma torku (0..1)
    hata_derece: np.ndarray      # ESP32'nin istediği açı - gerçek açı (derece)
    akim_a: float                # toplam akım (amper)
    egim_derece: float           # tabanın masaya göre eğimi
    kayma_mm: float              # tabanın masada kayması
    donme_derece: float          # tabanın kendi etrafında dönmesi
    bosluk_mm: Dict[str, float]  # "kafa-govde": 12.3 gibi (eksi = iç içe girmiş)


class DijitalIkiz:
    """Kedinin fiziksel ikizi. poz_gonder ile komut alır, adim ile zamanı ilerletir."""

    def __init__(self, robot: Robot | None = None) -> None:
        self.robot = robot or Robot()
        self.model = mujoco.MjModel.from_xml_string(mjcf_uret(self.robot))
        self.data = mujoco.MjData(self.model)
        self.dt = self.model.opt.timestep
        self._servolar = [getattr(self.robot, EKLEM_SERVO[e]) for e in EKLEMLER]
        self._qadr = [self.model.jnt_qposadr[self.model.joint(e).id] for e in EKLEMLER]
        self._dadr = [self.model.jnt_dofadr[self.model.joint(e).id] for e in EKLEMLER]
        self._geom = {ad: self.model.geom(ad).id for ad in HAREKETLI_PARCALAR + SABIT_PARCALAR}
        self._yatma = math.radians(self.robot.kulak_yatma_derece)
        self._fromto = np.zeros(6)
        self.sifirla()

    # Robotu nötr pozda, masanın ortasında yeniden başlatır.
    def sifirla(self) -> None:
        mujoco.mj_resetData(self.model, self.data)
        notr = self.c1_to_eklem(NOTR_POZ)
        for i, q in enumerate(notr):
            self.data.qpos[self._qadr[i]] = q
        self._esp_bas = notr.copy()     # ESP32 geçişinin başladığı açı
        self._esp_hedef = notr.copy()   # ESP32 geçişinin hedefi
        self._esp_sure = 0.0
        self._esp_t0 = 0.0
        self._servo_ic = notr.copy()    # servonun iç hedefi (hız sınırıyla ilerler)
        self.data.ctrl[:] = notr
        mujoco.mj_forward(self.model, self.data)
        self._taban_bas = self.data.qpos[:7].copy()

    # C1 pozunu (derece, kulak 0-1) eklem açısına (radyan) çevirir.
    def c1_to_eklem(self, poz: Dict[str, float]) -> np.ndarray:
        return np.array([
            -math.radians(poz["body_yaw"]),       # + sağa = robotun sağı = -y yönü
            -math.radians(poz["head_pan"]),
            math.radians(poz["head_tilt"]),       # + yukarı
            (1 - poz["ear_left"]) * self._yatma,  # 1 dik, 0 geriye yatık
            (1 - poz["ear_right"]) * self._yatma,
        ])

    # Router'ın C1 komutu: ESP32 şimdiki komuttan yeni hedefe ms içinde düz geçer.
    def poz_gonder(self, poz: Dict[str, float], ms: float) -> None:
        self._esp_bas = self._esp_komutu()
        self._esp_hedef = self.c1_to_eklem(poz)
        self._esp_sure = max(ms, 0) / 1000
        self._esp_t0 = self.data.time

    # ESP32'nin şu an servolara gönderdiği açı (millis() ile düz geçiş).
    def _esp_komutu(self) -> np.ndarray:
        if self._esp_sure <= 0:
            return self._esp_hedef.copy()
        k = min((self.data.time - self._esp_t0) / self._esp_sure, 1.0)
        return self._esp_bas + (self._esp_hedef - self._esp_bas) * k

    # Zamanı bir fizik adımı (0.5 ms) ilerletir.
    def adim(self) -> None:
        komut = self._esp_komutu()
        # Gerçek servo hedefe en fazla kendi hızıyla gidebilir (MG90S: 60° / 0.1 s)
        for i, s in enumerate(self._servolar):
            fark = komut[i] - self._servo_ic[i]
            adim = s.hiz_rad_s * self.dt
            self._servo_ic[i] += max(-adim, min(adim, fark))
        self.data.ctrl[:] = self._servo_ic
        mujoco.mj_step(self.model, self.data)

    # Bu anın bütün ölçümlerini toplar (boşluk hesabı istenirse yapılır, biraz yavaştır).
    def olc(self, bosluk: bool = True) -> Olcum:
        d = self.data
        tork = np.array([abs(d.actuator_force[i]) / s.tork_nm for i, s in enumerate(self._servolar)])
        q = np.array([d.qpos[a] for a in self._qadr])
        hiz = np.array([d.qvel[a] for a in self._dadr])
        hata = np.degrees(self._esp_komutu() - q)
        akim = self.robot.esp32_a + self.robot.ekran_a
        for i, s in enumerate(self._servolar):
            akim += min(s.akim_durma_a,
                        s.akim_bos_a + (s.akim_hareket_a - s.akim_bos_a) * min(abs(hiz[i]) / s.hiz_rad_s, 1)
                        + (s.akim_durma_a - s.akim_hareket_a) * min(tork[i], 1))
        # Taban: eğim (dik eksenin sapması), kayma (xy), dönme (z ekseni etrafında)
        quat = d.qpos[3:7]
        mat = np.zeros(9)
        mujoco.mju_quat2Mat(mat, quat)
        egim = math.degrees(math.acos(max(-1.0, min(1.0, mat[8]))))
        kayma = 1000 * float(np.linalg.norm(d.qpos[:2] - self._taban_bas[:2]))
        donme = math.degrees(math.atan2(mat[3], mat[0]))
        bosluklar: Dict[str, float] = {}
        if bosluk:
            for h in HAREKETLI_PARCALAR:
                for s in SABIT_PARCALAR:
                    mesafe = mujoco.mj_geomDistance(self.model, d, self._geom[h], self._geom[s], 0.05, self._fromto)
                    bosluklar[f"{h}-{s}"] = 1000 * mesafe
        return Olcum(d.time, tork, hata, akim, egim, kayma, donme, bosluklar)
