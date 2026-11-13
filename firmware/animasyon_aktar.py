import json
import re
from pathlib import Path

# Proje ana dizinini otomatik bul
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "firmware" else SCRIPT_DIR

# Hedef C++ başlık dosyası
HEDEF_H = REPO_ROOT / "firmware" / "animasyon_oynatma" / "include" / "animasyonlar.h"

# Tuğra'nın animasyonlarının durduğu klasör (aramak yerine doğrudan yazıldı, yanlış klasörü bulmasın)
KAYNAK_KLASOR = REPO_ROOT / "motion" / "clips"


# Dosya adını C++'ın kabul ettiği bir ada çevirir: harf, rakam ve _ dışındaki her şey _ olur.
# Örnek: "Head_Explosion(BuUM)" -> "Head_Explosion_BuUM"
def guvenli_ad(ad):
    temiz = re.sub(r"[^A-Za-z0-9_]", "_", ad)
    temiz = re.sub(r"_+", "_", temiz).strip("_")
    if not temiz or temiz[0].isdigit():
        temiz = "klip_" + temiz
    return temiz


def main():
    kaynak_klasor = KAYNAK_KLASOR
    if not kaynak_klasor.is_dir():
        print(f"HATA: Animasyon klasörü bulunamadı: {kaynak_klasor}")
        return

    # Her bilgisayarda aynı sıra çıksın diye küçük harfe göre sıralanır
    json_dosyalari = sorted(kaynak_klasor.glob("*.json"), key=lambda d: d.name.lower())

    satirlar = [
        "#pragma once",
        '// BU DOSYA animasyon_aktar.py TARAFINDAN OTOMATIK OLUSTURULMUSTUR.',
        '#include "animasyon_tanimlari.h"',
        ""
    ]

    klip_listesi = []

    for dosya in json_dosyalari:
        icerik = dosya.read_text(encoding="utf-8").strip()
        
        # JSON geçerli mi kontrol et (bozuk dosyaları yakalar)
        try:
             json.loads(icerik)
        except Exception as e:
            print(f"UYARI: {dosya.name} bozuk JSON içeriyor, atlandı! ({e})")
            continue

        klip_adi = guvenli_ad(dosya.stem).lower()  # örn: happy.json -> "happy"
        degisken_adi = f"{guvenli_ad(dosya.stem).upper()}_JSON"

        satirlar.append(f'const char {degisken_adi}[] = R"json({icerik})json";\n')
        klip_listesi.append((klip_adi, degisken_adi))

    satirlar.append("// klip listesi, yeni klip eklenirse otomatik güncellenir")
    satirlar.append("const Klip klipler[] = {")
    for i, (ad, degisken) in enumerate(klip_listesi):
        virgul = "," if i < len(klip_listesi) - 1 else ""
        satirlar.append(f'    {{"{ad}", {degisken}}}{virgul}')
    satirlar.append("};\n")
    satirlar.append("const int KLIP_SAYISI = sizeof(klipler) / sizeof(klipler[0]);\n")

    # Windows satır sonu (CRLF) her bilgisayarda aynı olsun, dosya gereksiz yere değişmesin
    HEDEF_H.write_text("\n".join(satirlar), encoding="utf-8", newline="\r\n")
    print(f"BAŞARILI: Toplam {len(klip_listesi)} animasyon '{HEDEF_H.name}' dosyasına aktarıldı!")

if __name__ == "__main__":
    main()