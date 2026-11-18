"""
sim/model.py  --  parcalar.Robot ayarlarından MuJoCo modeli (MJCF metni) üretir.

Robot bir "oyuncak bebek iskeleti" gibi kurulur: taban -> gövde -> boyun -> kafa -> kulaklar.
Her ok bir menteşedir (eklem) ve her menteşeyi bir servo çevirir.
Taban masanın üstünde serbesttir: hızlı dönüşte kayabilir ya da devrilebilir.
"""

import math

from .parcalar import Robot

MM = 0.001  # milimetreyi metreye çevirir
G = 0.001   # gramı kilograma çevirir

# Çarpışma kontrolünde birbirine bakılan parçalar (kafa ve kulaklar <-> gövde ve taban)
HAREKETLI_PARCALAR = ("kafa", "ekran", "kulak_sol", "kulak_sag")
SABIT_PARCALAR = ("govde", "taban")


# Bir servonun MuJoCo "position" motorunu yazar: tork sınırı satıcı bilgisinden gelir.
def _motor(ad: str, eklem: str, servo, kp: float) -> str:
    kv = 2 * math.sqrt(kp * servo.rotor_ataleti)  # titremesin diye kritik sönüm
    t = servo.tork_nm
    return (f'<position name="{ad}" joint="{eklem}" kp="{kp:.4f}" kv="{kv:.5f}" '
            f'forcelimited="true" forcerange="{-t:.4f} {t:.4f}" '
            f'ctrllimited="false"/>')


# Robot ayarlarından tam MJCF metnini üretir.
def mjcf_uret(r: Robot) -> str:
    tz = r.taban_yukseklik * MM
    gy = r.govde_yukseklik * MM
    by = r.boyun_yukseklik * MM
    ky = r.kafa_yukseklik * MM
    eks = r.egme_ekseni_yukseklik * MM
    # Kafa kutusunun merkezi, eğme eksenine göre: biraz önde (+3 mm) ve yukarıda
    kafa_x, kafa_z = 3 * MM, ky / 2 - eks
    kulak_z = ky - eks  # kulak menteşesi kafanın tepesinde
    yatma = math.radians(r.kulak_yatma_derece)

    # Servo tork / hata oranı: 2 derece sapmada tam torka ulaşır (gerçek servo davranışına yakın)
    def kp(s):
        return s.tork_nm / math.radians(2)

    kafa_kutle = (r.kafa_agirlik + r.s3.agirlik_g + r.s4.agirlik_g) * G
    return f"""
<mujoco model="kutu_kafali_kedi">
  <compiler angle="radian" autolimits="true"/>
  <option timestep="0.0005" integrator="implicitfast" gravity="0 0 -9.81"/>
  <visual><global offwidth="800" offheight="600"/><headlight ambient=".45 .45 .45" diffuse=".5 .5 .5"/><rgba haze=".93 .94 .96 1"/></visual>
  <asset>
    <texture type="skybox" builtin="gradient" rgb1=".93 .94 .96" rgb2=".80 .84 .90" width="64" height="64"/>
    <texture name="masa" type="2d" builtin="checker" rgb1=".82 .78 .72" rgb2=".76 .72 .66" width="256" height="256"/>
    <material name="masa" texture="masa" texrepeat="12 12"/>
    <material name="kabuk" rgba=".56 .57 .61 1"/>
    <material name="koyu" rgba=".35 .36 .40 1"/>
    <material name="ekran" rgba=".98 .97 .95 1" emission=".4"/>
  </asset>
  <worldbody>
    <light pos="0.2 0.2 0.6" dir="-0.3 -0.3 -1" diffuse=".9 .9 .9"/>
    <geom name="masa" type="plane" size="0.5 0.5 0.01" material="masa" friction="{r.masa_surtunme} 0.005 0.0001"/>
    <body name="taban" pos="0 0 {tz/2 + 0.0005:.5f}">
      <freejoint name="taban_serbest"/>
      <geom name="taban" type="cylinder" size="{r.taban_cap/2*MM:.4f} {tz/2:.4f}" material="koyu"
            mass="{(r.taban_agirlik + r.s0.agirlik_g)*G:.4f}" friction="{r.masa_surtunme} 0.005 0.0001"/>
      <body name="govde" pos="0 0 {tz/2:.4f}">
        <joint name="body_yaw" type="hinge" axis="0 0 1" range="{math.radians(-47):.4f} {math.radians(47):.4f}" armature="{r.s0.rotor_ataleti}"/>
        <geom name="govde" type="box" pos="0 0 {gy/2:.4f}" size="{r.govde_derinlik/2*MM:.4f} {r.govde_genislik/2*MM:.4f} {gy/2:.4f}"
              material="kabuk" mass="{(r.govde_agirlik + r.s1.agirlik_g)*G:.4f}"/>
        <body name="boyun" pos="0 0 {gy:.4f}">
          <joint name="head_pan" type="hinge" axis="0 0 1" range="{math.radians(-92):.4f} {math.radians(92):.4f}" armature="{r.s1.rotor_ataleti}"/>
          <geom name="boyun" type="box" pos="0 0 {by/2:.4f}" size="{r.boyun_derinlik/2*MM:.4f} {r.boyun_genislik/2*MM:.4f} {by/2:.4f}"
                material="koyu" mass="{(r.boyun_agirlik + r.s2.agirlik_g)*G:.4f}" contype="0" conaffinity="0"/>
          <body name="kafa" pos="0 0 {by + eks:.4f}">
            <joint name="head_tilt" type="hinge" axis="0 -1 0" range="{math.radians(-12):.4f} {math.radians(47):.4f}" armature="{r.s2.rotor_ataleti}"/>
            <geom name="kafa" type="box" pos="{kafa_x:.4f} 0 {kafa_z:.4f}" size="{r.kafa_derinlik/2*MM:.4f} {r.kafa_genislik/2*MM:.4f} {ky/2:.4f}"
                  material="kabuk" mass="{kafa_kutle:.4f}"/>
            <geom name="ekran" type="box" pos="{kafa_x + r.kafa_derinlik/2*MM + 0.0005:.4f} 0 {kafa_z:.4f}" size="0.0006 {50/2*MM:.4f} {38/2*MM:.4f}"
                  material="ekran" mass="0.0001"/>
            <body name="kulak_sol" pos="{kafa_x:.4f} {r.kulak_aralik*MM:.4f} {kulak_z:.4f}">
              <joint name="ear_left" type="hinge" axis="0 -1 0" range="-0.05 {yatma + 0.05:.4f}" armature="{r.s3.rotor_ataleti}"/>
              <geom name="kulak_sol" type="box" pos="0 0 {r.kulak_yukseklik/2*MM:.4f}" size="{r.kulak_kalinlik/2*MM:.4f} {r.kulak_genislik/2*MM:.4f} {r.kulak_yukseklik/2*MM:.4f}"
                    material="kabuk" mass="{r.kulak_agirlik*G:.4f}"/>
            </body>
            <body name="kulak_sag" pos="{kafa_x:.4f} {-r.kulak_aralik*MM:.4f} {kulak_z:.4f}">
              <joint name="ear_right" type="hinge" axis="0 -1 0" range="-0.05 {yatma + 0.05:.4f}" armature="{r.s4.rotor_ataleti}"/>
              <geom name="kulak_sag" type="box" pos="0 0 {r.kulak_yukseklik/2*MM:.4f}" size="{r.kulak_kalinlik/2*MM:.4f} {r.kulak_genislik/2*MM:.4f} {r.kulak_yukseklik/2*MM:.4f}"
                    material="kabuk" mass="{r.kulak_agirlik*G:.4f}"/>
            </body>
          </body>
        </body>
      </body>
    </body>
  </worldbody>
  <contact>
    <exclude body1="kafa" body2="kulak_sol"/>
    <exclude body1="kafa" body2="kulak_sag"/>
  </contact>
  <actuator>
    {_motor("S0", "body_yaw", r.s0, kp(r.s0))}
    {_motor("S1", "head_pan", r.s1, kp(r.s1))}
    {_motor("S2", "head_tilt", r.s2, kp(r.s2))}
    {_motor("S3", "ear_left", r.s3, kp(r.s3))}
    {_motor("S4", "ear_right", r.s4, kp(r.s4))}
  </actuator>
</mujoco>
"""
