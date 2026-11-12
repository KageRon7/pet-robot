"""Göz modeli için veri toplama aracı (kendi yapay zekâmız, 1. adım).

Ne yapar?
    Kameraya bakarsın, bir tuşa basıp bir ifade yaparsın (gülme, üzgün, şaşkın...).
    Araç o birkaç saniyedeki yüzün 52 SAYISINI (MediaPipe blendshape skorları: kaş ne kadar
    kalkık, ağız ne kadar açık gibi) ve baş açısını, ifadenin adıyla birlikte bir CSV
    dosyasına yazar. Bu dosyalarla sonra küçük bir model eğiteceğiz.

Gizlilik:
    Görüntü (kare) ASLA diske yazılmaz. Dosyada sadece sayılar ve senin verdiğin takma ad olur.
    Dosyalar veri/ifade/ klasörüne gider; bu klasör .gitignore'da, GitHub'a kendiliğinden gitmez.

Çalıştırma (repo kökünden):
    python computer_vision/veri_kaydet.py --kisi ferhat

Tuşlar:
    0 normal   1 gülüyor   2 üzgün   3 sinirli   4 şaşkın   5 esniyor
    -> 1 sn hazırlan, sonra 3 sn o ifadeyi yap ve tut. Bir "çekim" böyle biter.
    g        son çekimi geri al (yanlış ifade yaptıysan)
    q / ESC  kaydet ve çık

Hedef: her ifade için en az 10 çekim (ekranda sayaç var). Farklı ışıkta, gözlükle/gözlüksüz,
hafif ve abartılı hâllerini karışık yap; model ne kadar çeşit görürse o kadar iyi öğrenir.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime

# Tuş -> etiket. Etiket adları A2 olay adlarıyla aynı (normal hariç), modeli sonra
# doğrudan A2'ye bağlayabilelim diye.
ETIKETLER = {
    ord("0"): "normal",
    ord("1"): "smile",
    ord("2"): "sad",
    ord("3"): "angry",
    ord("4"): "surprised",
    ord("5"): "yawn",
}
EKRAN_ADI = {
    "normal": "normal", "smile": "guluyor", "sad": "uzgun",
    "angry": "sinirli", "surprised": "saskin", "yawn": "esniyor",
}

HAZIRLIK_SN = 1.0      # tuşa bastıktan sonra ifadeyi kurmak için süre (kayıt yok)
CEKIM_SN = 3.0         # ifadeyi tutma ve kaydetme süresi
ORNEK_HZ = 10          # saniyede en fazla kaç satır (art arda neredeyse aynı kareler olmasın)
HEDEF_CEKIM = 10       # ifade başına önerilen çekim sayısı

VERI_KLASORU = os.path.join("veri", "ifade")
SABIT_SUTUNLAR = ["kisi", "oturum", "cekim", "etiket", "t_ms", "yaw", "pitch"]


# Takma adı dosya adına uygun hâle getirir (harf, rakam, alt çizgi dışını atar).
def temiz_ad(ad):
    temiz = "".join(c for c in ad.strip().lower() if c.isalnum() or c == "_")
    if not temiz:
        raise ValueError("Takma ad boş olamaz (örn. --kisi ferhat)")
    return temiz


class VeriDefteri:
    """Bir oturumdaki çekimleri bellekte tutar ve CSV dosyasına yazar.

    Bir defter gibi düşün: her çekim bir sayfa. "Geri al" son sayfayı yırtar.
    Her çekim bitince dosya baştan yazılır, böylece program çökse bile veri kaybolmaz.
    """

    # Defteri kişi ve oturum bilgisiyle açar; dosya yolunu belirler.
    def __init__(self, kisi, klasor=VERI_KLASORU, oturum=None):
        self.kisi = temiz_ad(kisi)
        self.oturum = oturum or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.klasor = klasor
        self.yol = os.path.join(klasor, f"{self.kisi}_{self.oturum}.csv")
        self.cekimler = []          # her eleman: (etiket, [satır sözlükleri])
        self.ozellik_adlari = None  # blendshape adları, ilk satırdan sabitlenir

    # Bir çekimi (etiket + satırlar) deftere ekler ve dosyayı günceller. Boş çekimi yok sayar.
    def cekim_ekle(self, etiket, satirlar):
        if etiket not in EKRAN_ADI:
            raise ValueError(f"Bilinmeyen etiket: {etiket}")
        if not satirlar:
            return False
        if self.ozellik_adlari is None:
            self.ozellik_adlari = sorted(satirlar[0]["ozellikler"])
        self.cekimler.append((etiket, satirlar))
        self.kaydet()
        return True

    # Son çekimi siler ve dosyayı günceller. Silinen etiketi döner (yoksa None).
    def geri_al(self):
        if not self.cekimler:
            return None
        etiket, _ = self.cekimler.pop()
        self.kaydet()
        return etiket

    # Her etiketten kaç çekim yapıldığını sayar (ekrandaki sayaç için).
    def sayac(self):
        s = {e: 0 for e in EKRAN_ADI}
        for etiket, _ in self.cekimler:
            s[etiket] += 1
        return s

    # Tüm çekimleri CSV'ye yazar. Önce geçici dosyaya yazıp sonra yerine koyar (yarım dosya kalmaz).
    def kaydet(self):
        os.makedirs(self.klasor, exist_ok=True)
        if not self.cekimler:
            if os.path.exists(self.yol):
                os.remove(self.yol)
            return
        gecici = self.yol + ".tmp"
        with open(gecici, "w", newline="", encoding="utf-8") as f:
            yazici = csv.writer(f)
            yazici.writerow(SABIT_SUTUNLAR + self.ozellik_adlari)
            for no, (etiket, satirlar) in enumerate(self.cekimler, start=1):
                for s in satirlar:
                    oz = s["ozellikler"]
                    yazici.writerow(
                        [self.kisi, self.oturum, no, etiket, s["t_ms"],
                         round(s["yaw"], 2), round(s["pitch"], 2)]
                        + [round(oz.get(ad, 0.0), 4) for ad in self.ozellik_adlari]
                    )
        os.replace(gecici, self.yol)


class Cekim:
    """Tek bir çekimin zamanlamasını yönetir: önce hazırlık, sonra kayıt, sonra bitiş.

    Fotoğrafçının "3, 2, 1, çek" demesi gibi: hazırlıkta kayıt yok, kayıtta saniyede
    en fazla ORNEK_HZ satır alınır.
    """

    # Çekimi başlatır; hazırlık ve kayıt bitiş zamanlarını hesaplar.
    def __init__(self, etiket, simdi):
        self.etiket = etiket
        self.kayit_basi = simdi + HAZIRLIK_SN
        self.bitis = self.kayit_basi + CEKIM_SN
        self.satirlar = []
        self._son_ornek = -1.0

    # Şu an hangi aşamada olduğunu söyler: "hazirlik", "kayit" ya da "bitti".
    def asama(self, simdi):
        if simdi < self.kayit_basi:
            return "hazirlik"
        if simdi < self.bitis:
            return "kayit"
        return "bitti"

    # Kayıt aşamasındaysa ve sıklık sınırı izin veriyorsa bir satır ekler.
    def ornek_ekle(self, simdi, ozellikler, yaw, pitch):
        if self.asama(simdi) != "kayit":
            return
        if simdi - self._son_ornek < 1.0 / ORNEK_HZ:
            return
        self._son_ornek = simdi
        self.satirlar.append({
            "t_ms": int((simdi - self.kayit_basi) * 1000),
            "yaw": yaw, "pitch": pitch,
            # "_neutral" gibi alt çizgiyle başlayan yardımcı skorlar özellik değil
            "ozellikler": {k: v for k, v in ozellikler.items() if not k.startswith("_")},
        })


# Kamera döngüsü: yüzü okur, tuşları dinler, çekimleri deftere yazar. Kare hiçbir yere kaydedilmez.
def main():
    ap = argparse.ArgumentParser(description="Göz modeli için ifade verisi toplar (sadece sayılar).")
    ap.add_argument("--kisi", required=True, help="takma ad, örn. ferhat (dosya adında görünür)")
    args = ap.parse_args()

    # Kamera kütüphaneleri sadece burada yüklenir; böylece testler kamerasız çalışır.
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    import faz1  # aynı klasördeki Mustafa'nın kodu: model indirme, blendshape, baş açısı

    defter = VeriDefteri(args.kisi)
    faz1.modeli_indir()
    secenekler = vision.FaceLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=faz1.MODEL_PATH),
        running_mode=vision.RunningMode.VIDEO,
        num_faces=1,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
    )
    kamera = cv2.VideoCapture(0)
    if not kamera.isOpened():
        raise RuntimeError("Webcam açılamadı (indeks 0). Başka uygulama kullanıyor olabilir.")

    cekim = None
    mesaj, mesaj_bitis = "", 0.0
    baslangic = time.monotonic()
    son_ts = -1

    with vision.FaceLandmarker.create_from_options(secenekler) as landmarker:
        while True:
            ok, kare = kamera.read()
            if not ok:
                break
            rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
            ts = max(int((time.monotonic() - baslangic) * 1000), son_ts + 1)
            son_ts = ts
            sonuc = landmarker.detect_for_video(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ts)
            simdi = time.time()
            yuz_var = bool(sonuc.face_landmarks)

            if cekim is not None:
                if yuz_var:
                    yaw, pitch = faz1.bas_acisi(sonuc)
                    cekim.ornek_ekle(simdi, faz1.blendshape_sozlugu(sonuc), yaw, pitch)
                if cekim.asama(simdi) == "bitti":
                    if defter.cekim_ekle(cekim.etiket, cekim.satirlar):
                        mesaj = f"kaydedildi: {EKRAN_ADI[cekim.etiket]} ({len(cekim.satirlar)} satir)"
                    else:
                        mesaj = "yuz gorunmedi, cekim kaydedilmedi"
                    mesaj_bitis = simdi + 2.0
                    cekim = None

            # --- Ekran (sadece sana yol göstermek için, kaydedilmez) ---
            ekran = cv2.flip(kare, 1)
            renk = (0, 255, 255) if yuz_var else (0, 0, 255)
            if cekim is None:
                ust = "tus: 0 normal 1 gulme 2 uzgun 3 sinirli 4 saskin 5 esneme | g geri al | q cik"
            elif cekim.asama(simdi) == "hazirlik":
                ust = f"HAZIRLAN: {EKRAN_ADI[cekim.etiket]}"
            else:
                kalan = cekim.bitis - simdi
                ust = f"KAYIT: {EKRAN_ADI[cekim.etiket]} yap ve tut ({kalan:.1f} sn)"
                renk = (0, 0, 255)
            if not yuz_var:
                ust += "  [yuz yok]"
            cv2.putText(ekran, ust, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, renk, 2)
            sayac = defter.sayac()
            for i, (etiket, n) in enumerate(sayac.items()):
                r = (0, 255, 0) if n >= HEDEF_CEKIM else (255, 255, 255)
                cv2.putText(ekran, f"{EKRAN_ADI[etiket]}: {n}/{HEDEF_CEKIM}", (10, 60 + 24 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, r, 1)
            if simdi < mesaj_bitis:
                cv2.putText(ekran, mesaj, (10, ekran.shape[0] - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.imshow("Veri kaydi", ekran)

            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            if cekim is None and tus in ETIKETLER:
                cekim = Cekim(ETIKETLER[tus], simdi)
            elif cekim is None and tus == ord("g"):
                silinen = defter.geri_al()
                mesaj = f"geri alindi: {EKRAN_ADI[silinen]}" if silinen else "geri alinacak cekim yok"
                mesaj_bitis = simdi + 2.0

    kamera.release()
    cv2.destroyAllWindows()
    if defter.cekimler:
        print(f"Kaydedildi: {defter.yol}", file=sys.stderr)
    else:
        print("Hiç çekim yapılmadı, dosya oluşmadı.", file=sys.stderr)


if __name__ == "__main__":
    main()
