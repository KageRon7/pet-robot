# Davranış ağacı testleri: saati biz ilerlettiğimiz için dakikalar saniyede denenir.
# Çalıştırma (repo kökünden):  python -m pytest brain/tests/test_davranis.py

from dataclasses import replace
from datetime import datetime, timedelta

from brain.ayarlar import VARSAYILAN, Ayarlar
from brain.davranis import DavranisBeyni, DINLENME, ILGILENME, KOSE, SIKILMA, UYKU, decide, karar_ver, sifirla
from contracts import BrainContext, Decision

T0 = datetime(2026, 11, 14, 12, 0, 0)


# Verilen saniyede (T0'dan sonra) bir B1 kurar. olaylar: [(olay_adı, kaç_sn_önce), ...]
def b1(sn, olaylar=(), masada=30):
    return BrainContext.model_validate({
        "now": (T0 + timedelta(seconds=sn)).isoformat(),
        "current_mood": {"emotion": "idle", "intensity": 0.3},
        "session": {"user_present_minutes": masada, "last_break_minutes_ago": masada},
        "recent_events": [{"event": ad, "ago_s": ago} for ad, ago in olaylar],
    })


# Rastgelelik kapalı ayarlar: tepkisizlik olmasın ki testler kesin sonuç versin.
def kesin(**degisiklik):
    return replace(VARSAYILAN, sessiz_taban_olasilik=0.0, sessiz_alisma_katsayisi=0.0, **degisiklik)


# Beyni sn aralığında saniye saniye tikletir, (saniye, karar) çiftlerini döner.
def tiklet(beyin, bas, son, olaylar_fn=lambda sn: (), masada=30):
    sonuc = []
    for sn in range(bas, son + 1):
        k = beyin.isle(b1(sn, olaylar_fn(sn), masada), tik=True)
        if k is not None:
            sonuc.append((sn, k))
    return sonuc


# ---------------------------------------------------------------- temel tepkiler

def test_gulumseme_mutlu_ve_klip():
    beyin = DavranisBeyni(kesin(), tohum=1)
    k = beyin.isle(b1(0, [("smile", 0)]))
    assert k.emotion == "happy" and k.clip == "happy"
    assert 0 < k.intensity <= 1
    assert beyin.durum.basamak == ILGILENME


def test_esneme_sleepy():
    k = DavranisBeyni(kesin(), tohum=1).isle(b1(0, [("yawn", 0)]))
    assert k.emotion == "sleepy"


def test_sinirli_geri_cekilme_ve_sessizlik():
    beyin = DavranisBeyni(kesin(), tohum=1)
    k = beyin.isle(b1(0, [("angry", 0)]))
    assert k.emotion == "startled"
    # 60 sn boyunca kendi başına eylem yok
    gelenler = tiklet(beyin, 1, 59, lambda sn: [("angry", sn)])
    assert gelenler == []


def test_bilinmeyen_ya_da_tepkisiz_olay_none():
    # drowsy dışındaki tüm olaylar tanımlı; user_arrived karşılama verir, listede olmayan yok.
    beyin = DavranisBeyni(kesin(), tohum=1)
    assert beyin.isle(b1(0, [("surprised", 0)])).emotion == "curious"


# ---------------------------------------------------------------- olay tekrar sayımı

def test_ayni_olay_iki_kez_islenmez():
    beyin = DavranisBeyni(kesin(), tohum=1)
    assert beyin.isle(b1(0, [("smile", 0)]), tik=True) is not None
    # 1 sn sonra aynı olay B1'de ago_s=1 ile duruyor: yeni olay sayılmamalı
    assert beyin.isle(b1(1, [("smile", 1)]), tik=True) is None
    assert beyin.isle(b1(2, [("smile", 2.1)]), tik=True) is None


def test_decide_tik_islediyse_ayni_karari_doner():
    beyin = DavranisBeyni(kesin(), tohum=1)
    k1 = beyin.isle(b1(0, [("smile", 0)]), tik=True)
    k2 = beyin.isle(b1(0.5, [("smile", 0.5)]), tik=False)
    assert k2 == k1  # idle ile animasyonu kesmez


def test_program_yeni_acildiysa_eski_olaya_tepki_yok():
    beyin = DavranisBeyni(kesin(), tohum=1)
    assert beyin.isle(b1(0, [("smile", 100)])) is None


# ---------------------------------------------------------------- merdiven

def test_sikilma_ilgiden_10sn_sonra():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("smile", 0)]), tik=True)
    gelen = tiklet(beyin, 1, 30, lambda sn: [("smile", sn)])
    sn, k = gelen[0]
    assert sn == 10 and k.clip == "Im_so_boored" and beyin.durum.basamak == SIKILMA


def test_ilgi_yokken_sikilma_olmaz_uyku_5dk():
    beyin = DavranisBeyni(kesin(kendi_eylem_aralik_s=(1e9, 1e9), ilgi_isteme_aralik_s=(1e9, 1e9)), tohum=1)
    gelen = tiklet(beyin, 0, 400)
    assert [(sn, k.emotion.value) for sn, k in gelen] == [(300, "sleepy")]
    assert beyin.durum.basamak == UYKU


def test_sikilma_ayari_kapaliysa_dinlenirken_de_sikilir():
    beyin = DavranisBeyni(kesin(sikilma_sadece_ilgiden_sonra=False, kendi_eylem_aralik_s=(1e9, 1e9)), tohum=1)
    gelen = tiklet(beyin, 0, 20)
    assert gelen[0][0] == 10 and gelen[0][1].clip == "Im_so_boored"


def test_sikilma_sonra_uyku():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("smile", 0)]), tik=True)
    gelen = tiklet(beyin, 1, 400, lambda sn: [("smile", sn)])
    assert [k.emotion.value for _, k in gelen if _ in (10, 300)] == ["idle", "sleepy"]


def test_uykudan_olayla_uyanir_sessiz_kalma_olsa_bile():
    ay = replace(VARSAYILAN, sessiz_taban_olasilik=1.0, sessiz_en_fazla=1.0)
    beyin = DavranisBeyni(ay, tohum=1)
    tiklet(beyin, 0, 310)
    assert beyin.durum.basamak == UYKU
    k = beyin.isle(b1(320, [("yawn", 0)]))
    assert k is not None and beyin.durum.basamak == DINLENME


# ---------------------------------------------------------------- üzüntü merdiveni

def test_uzuntu_merdiveni_merak_oyun_kose():
    beyin = DavranisBeyni(kesin(), tohum=1)
    a = beyin.isle(b1(0, [("sad", 0)]))
    b = beyin.isle(b1(30, [("sad", 0)]))
    c = beyin.isle(b1(60, [("sad", 0)]))
    assert [a.emotion, b.emotion, c.emotion] == ["curious", "playful", "idle"]
    assert "köşe" in c.reason and beyin.durum.basamak == KOSE
    # birlikte üzülme yok: üzgün kullanıcıya kedi hiçbir aşamada "sad" olmaz
    assert "sad" not in [a.emotion, b.emotion, c.emotion]
    assert beyin.isle(b1(90, [("sad", 0)])) is None  # köşedeyken üzüntü sürse de yeni tepki yok


def test_uzuntu_ayni_anda_tekrar_asama_ilerletmez():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("sad", 0)]))
    assert beyin.isle(b1(5, [("sad", 0)])) is None  # 20 sn dolmadı
    assert beyin.durum.uzuntu_asama == 0


def test_uzuntu_merdiveni_sifirlanir():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("sad", 0)]))
    beyin.isle(b1(30, [("sad", 0)]))
    k = beyin.isle(b1(400, [("sad", 0)]))  # 180 sn'den uzun süre geçti
    assert k.emotion == "curious"


# ---------------------------------------------------------------- gitme ve geri gelme

def test_masadan_kalkinca_uzulmez_merakla_arkasindan_bakar():
    beyin = DavranisBeyni(kesin(), tohum=1)
    k = beyin.isle(b1(0, [("user_left", 0)]))
    assert k.emotion == "curious" and k.clip == "curious"
    assert beyin.durum.kullanici_var is False
    assert beyin.durum.ruh_hali >= 0  # üzüntü ruh haline işlemez


def karsilama(yokluk_s):
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("user_left", 0)]))
    return beyin.isle(b1(yokluk_s, [("user_arrived", 0)], masada=0))


def test_karsilama_buyuklugu_yokluga_gore():
    kucuk, orta, buyuk = karsilama(60), karsilama(300), karsilama(3600)
    assert (kucuk.emotion, orta.emotion, buyuk.emotion) == ("curious", "happy", "playful")
    assert kucuk.intensity < orta.intensity < buyuk.intensity


def test_ilk_gelis_yokluk_bilinmiyor_kucuk_karsilama():
    k = DavranisBeyni(kesin(), tohum=1).isle(b1(0, [("user_arrived", 0)], masada=0))
    assert k.emotion == "curious"


# ---------------------------------------------------------------- ruh hali, alışma

def test_ruh_hali_sonar_ama_hemen_sifirlanmaz():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, [("smile", 0)]), tik=True)
    ilk = beyin.durum.ruh_hali
    beyin.isle(b1(60), tik=True)
    assert 0.5 * ilk < beyin.durum.ruh_hali < ilk  # 60 sn'de azaldı ama durur
    beyin.isle(b1(180), tik=True)
    assert abs(beyin.durum.ruh_hali - ilk / 2) < 0.02  # yarı ömür 180 sn


def test_keyifli_ruh_hali_kendi_eylemini_mutlu_secer():
    beyin = DavranisBeyni(kesin(sikilma_s=1e9, uyku_s=1e9, kendi_eylem_aralik_s=(100, 100)), tohum=1)
    beyin.isle(b1(0, [("smile", 0)]), tik=True)
    beyin.durum.basamak = DINLENME
    beyin.durum.sonraki_kendi = 5.0 + T0.timestamp()
    k = beyin.isle(b1(6), tik=True)
    assert k.emotion == "happy" and k.intensity <= 0.3


def test_alisma_tepkiyi_azaltir():
    beyin = DavranisBeyni(kesin(sikilma_s=1e9, uyku_s=1e9), tohum=1)
    siddetler = [beyin.isle(b1(sn, [("smile", 0)])).intensity for sn in (0, 10, 20, 30, 40)]
    assert siddetler[-1] < siddetler[0]
    assert siddetler == sorted(siddetler, reverse=True)


def test_alisma_zamanla_gecer():
    beyin = DavranisBeyni(kesin(), tohum=1)
    for sn in (0, 10, 20):
        beyin.isle(b1(sn, [("smile", 0)]))
    yorgun = beyin.durum.alisma["smile"]
    beyin.isle(b1(2000), tik=True)
    assert beyin.durum.alisma.get("smile", 0.0) < yorgun / 10


def test_bazen_hic_tepki_vermez():
    ay = replace(VARSAYILAN, sessiz_taban_olasilik=1.0, sessiz_en_fazla=1.0)
    beyin = DavranisBeyni(ay, tohum=1)
    assert beyin.isle(b1(0, [("smile", 0)])) is None
    sifirla(ay, 1)
    import brain.davranis as dv
    assert dv.decide(b1(0, [("smile", 0)])).emotion == "idle"  # decide yine Decision döner


def test_gelme_gitme_alismaz_ve_sessiz_kalmaz():
    ay = replace(VARSAYILAN, sessiz_taban_olasilik=1.0, sessiz_en_fazla=1.0)
    assert DavranisBeyni(ay, tohum=1).isle(b1(0, [("user_left", 0)])) is not None


# ---------------------------------------------------------------- kendiliğinden davranışlar

def test_dinlenirken_kendi_basina_kucuk_eylem():
    beyin = DavranisBeyni(kesin(kendi_eylem_aralik_s=(60, 60), ilgi_isteme_aralik_s=(1e9, 1e9)), tohum=1)
    gelen = tiklet(beyin, 0, 200)
    assert gelen and 55 <= gelen[0][0] <= 65
    assert gelen[0][1].intensity <= 0.3


def test_ilgi_isteme_20_30_dk():
    ay = kesin(uyku_s=1e9, kendi_eylem_aralik_s=(1e9, 1e9))
    beyin = DavranisBeyni(ay, tohum=3)
    beyin.isle(b1(0, [("user_arrived", 0)], masada=0), tik=True)
    gelen = tiklet(beyin, 1, 2400, masada=5)
    ilgi = [(sn, k) for sn, k in gelen if k.clip in ("curious2", "playful")]
    assert ilgi and 1200 <= ilgi[0][0] <= 1800
    assert ilgi[0][1].intensity <= 0.5


def test_kullanici_yokken_ilgi_istemez():
    ay = kesin(uyku_s=1e9, kendi_eylem_aralik_s=(1e9, 1e9))
    beyin = DavranisBeyni(ay, tohum=3)
    beyin.isle(b1(0, [("user_left", 0)], masada=0), tik=True)
    gelen = tiklet(beyin, 1, 2400, masada=0)
    assert [k for _, k in gelen if k.clip in ("curious2", "playful")] == []


def test_oturumdan_masada_oldugunu_ogrenir():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(0, masada=12), tik=True)
    assert beyin.durum.kullanici_var is True


# ---------------------------------------------------------------- dayanıklılık

def test_bozuk_veri_idle_doner_cokmez():
    sifirla(tohum=1)
    for bozuk in ({}, None, "x", 5):
        k = decide(bozuk)
        assert isinstance(k, Decision) and k.emotion == "idle"
    assert karar_ver({}).emotion == "idle"


def test_bozuk_veriden_sonra_beyin_calismaya_devam_eder():
    ay = kesin()
    beyin = DavranisBeyni(ay, tohum=1)
    assert beyin.isle({}).emotion == "idle"
    assert beyin.isle(b1(0, [("smile", 0)])).emotion == "happy"


def test_saat_geri_giderse_cokmez():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(1000, [("smile", 0)]))
    k = beyin.isle(b1(10, [("yawn", 0)]))
    assert k is not None and k.emotion == "sleepy"


def test_donen_karar_sozlesmeye_uyar():
    beyin = DavranisBeyni(kesin(), tohum=5)
    for sn, k in tiklet(beyin, 0, 700, lambda sn: [("smile", 0)] if sn % 25 == 0 else []):
        assert isinstance(k, Decision) and 0 <= k.intensity <= 1 and k.duration_s >= 0


def test_hizli_ayarlar_gecerli():
    ay = Ayarlar.hizli()
    assert ay.uyku_s < VARSAYILAN.uyku_s and ay.sikilma_s < VARSAYILAN.sikilma_s


# ---------------------------------------------------------------- B1'de sızan eski olaylar

def test_b1de_kalan_eski_olaylar_varligi_ezmez_ve_uykuyu_engellemez():
    # Router eski olayları B1'den temizlemese bile (5 dk'dan eski), beyin onları yok sayar.
    ay = kesin(kendi_eylem_aralik_s=(1e9, 1e9), ilgi_isteme_aralik_s=(1e9, 1e9))
    beyin = DavranisBeyni(ay, tohum=1)
    beyin.isle(b1(0, [("user_arrived", 0)], masada=0), tik=True)
    beyin.isle(b1(800, [("user_left", 0)], masada=0), tik=True)
    gelen = []
    for sn in range(801, 1300):
        eskiler = [("user_arrived", sn - 700), ("user_left", sn - 800)]  # sızan olaylar
        k = beyin.isle(b1(sn, eskiler, masada=0), tik=True)
        if k is not None:
            gelen.append((sn, k.emotion.value))
    assert beyin.durum.kullanici_var is False
    assert gelen == [(1100, "sleepy")]


def test_eski_olay_daha_yeni_varlik_bilgisini_ezmez():
    beyin = DavranisBeyni(kesin(), tohum=1)
    beyin.isle(b1(100, [("user_left", 0)]), tik=True)
    beyin.isle(b1(150, [("user_arrived", 120)]), tik=True)  # mt=30: user_left'ten (100) eski
    assert beyin.durum.kullanici_var is False


def test_uyuyan_kedi_20_30_dk_icinde_uyanip_ilgi_ister():
    beyin = DavranisBeyni(kesin(kendi_eylem_aralik_s=(1e9, 1e9)), tohum=3)
    beyin.isle(b1(0, [("user_arrived", 0)], masada=0), tik=True)
    gelen = tiklet(beyin, 1, 2000, masada=5)
    uyku = [sn for sn, k in gelen if k.emotion == "sleepy"]
    ilgi = [sn for sn, k in gelen if k.clip in ("curious2", "playful")]
    assert uyku and uyku[0] == 300
    assert ilgi and 1200 <= ilgi[0] <= 1800


def test_tepkiden_hemen_sonra_kendi_eylemi_olmaz():
    beyin = DavranisBeyni(kesin(kendi_eylem_aralik_s=(60, 60), ilgi_isteme_aralik_s=(1e9, 1e9)), tohum=1)
    beyin.isle(b1(50, [("yawn", 0)]), tik=True)
    gelen = tiklet(beyin, 51, 100, lambda sn: [("yawn", sn - 50)])
    assert gelen == []  # sayaç yawn anından yeniden başladı: ilk eylem ~110. sn


# ---------------------------------------------------------------- köşeye çekilme

# Üç üzgün olayla kediyi köşeye gönderir (0, 30, 60. sn).
def kosede_beyin(**degisiklik):
    beyin = DavranisBeyni(kesin(**degisiklik), tohum=1)
    for sn in (0, 30, 60):
        beyin.isle(b1(sn, [("sad", 0)]))
    assert beyin.durum.basamak == KOSE
    return beyin


def test_kosede_10_dk_hicbir_kendiliginden_davranis_yok_sonra_merakla_cikar():
    # uyku, kendi eylemi ve ilgi isteme normalde bu sürede tetiklenirdi; köşede hepsi susar
    beyin = kosede_beyin(kendi_eylem_aralik_s=(60, 60), ilgi_isteme_aralik_s=(100, 100))
    gelen = tiklet(beyin, 61, 700)
    assert [(sn, k.emotion.value) for sn, k in gelen] == [(660, "curious")]
    assert beyin.durum.basamak == DINLENME


def test_kose_olay_gelince_de_biter_tik_olmasa_bile():
    beyin = kosede_beyin()
    k = beyin.isle(b1(700), tik=False)  # olaysız çağrı, 10 dk dolmuş
    assert k.emotion == "curious" and beyin.durum.basamak == DINLENME


def test_kosedeyken_uzun_bakis_yeniden_meraklandirir():
    beyin = kosede_beyin()
    k = beyin.isle(b1(100, [("looking_at_robot_long", 0)]))
    assert k.emotion == "curious" and k.clip == "curious"
    assert beyin.durum.basamak == ILGILENME and beyin.durum.uzuntu_asama == 0


def test_kosede_uzun_bakis_sessiz_kalma_olsa_bile_tepki_verir():
    ay = replace(VARSAYILAN, sessiz_taban_olasilik=1.0, sessiz_en_fazla=1.0)
    beyin = DavranisBeyni(ay, tohum=1)
    for sn in (0, 30, 60):
        beyin.isle(b1(sn, [("sad", 0)]))
    assert beyin.isle(b1(100, [("looking_at_robot_long", 0)])) is not None


def test_kosedeyken_diger_olaylar_yok_sayilir():
    beyin = kosede_beyin()
    assert beyin.isle(b1(100, [("yawn", 0)])) is None
    assert beyin.isle(b1(110, [("angry", 0)])) is None
    assert beyin.durum.basamak == KOSE


def test_kosedeyken_gulumseme_cikarir():
    beyin = kosede_beyin()
    k = beyin.isle(b1(100, [("smile", 0)]))
    assert k.emotion == "happy" and beyin.durum.basamak == ILGILENME


def test_kose_sonrasi_uzuntu_merdiveni_merakla_baslar():
    beyin = kosede_beyin()
    beyin.isle(b1(100, [("looking_at_robot_long", 0)]))
    k = beyin.isle(b1(200, [("sad", 0)]))
    assert k.emotion == "curious"