import os
import json
from pathlib import Path

# Proje ana dizinini otomatik bul
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "firmware" else SCRIPT_DIR

# Hedef C++ başlık dosyası
HEDEF_H = REPO_ROOT / "firmware" / "animasyon_oynatma" / "include" / "animasyonlar.h"

def animasyon_klasorunu_bul():
    # Projede içinde C3-taslak formatlı JSON'lar olan klasörü otomatik bulur
    for root, dirs, files in os.walk(REPO_ROOT):
        if any(ign in root for ign in [".git", ".pio", ".venv", ".vscode"]):
            continue
        json_files = [f for f in files if f.endswith(".json") and f != "diagram.json"]
        if len(json_files) >= 5:
            return Path(root)
    return None

def main():
    kaynak_klasor = animasyon_klasorunu_bul()
    if not kaynak_klasor:
        print("HATA: Animasyon JSON klasörü bulunamadı!")
        return

    print(f"Animasyon klasörü bulundu: {kaynak_klasor.relative_to(REPO_ROOT)}")
    json_dosyalari = sorted(kaynak_klasor.glob("*.json"))

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

        klip_adi = dosya.stem.lower() # örn: happy.json -> "happy"
        degisken_adi = f"{dosya.stem.upper().replace('-', '_').replace(' ', '_')}_JSON"

        satirlar.append(f'const char {degisken_adi}[] = R"json({icerik})json";\n')
        klip_listesi.append((klip_adi, degisken_adi))

    satirlar.append("// klip listesi, yeni klip eklenirse otomatik güncellenir")
    satirlar.append("const Klip klipler[] = {")
    for i, (ad, degisken) in enumerate(klip_listesi):
        virgul = "," if i < len(klip_listesi) - 1 else ""
        satirlar.append(f'    {{"{ad}", {degisken}}}{virgul}')
    satirlar.append("};\n")
    satirlar.append("const int KLIP_SAYISI = sizeof(klipler) / sizeof(klipler[0]);\n")

    HEDEF_H.write_text("\n".join(satirlar), encoding="utf-8")
    print(f"BAŞARILI: Toplam {len(klip_listesi)} animasyon '{HEDEF_H.name}' dosyasına aktarıldı!")

if __name__ == "__main__":
    main()