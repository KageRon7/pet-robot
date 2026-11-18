Import("env")
import os
import re

proje = env["PROJECT_DIR"]
klip_klasoru = os.path.normpath(os.path.join(proje, "..", "..", "motion", "clips"))
cikti = os.path.join(proje, "include", "gomulu_klipler.h")

if not os.path.isdir(klip_klasoru):
    raise Exception("motion/clips klasoru bulunamadi: " + klip_klasoru)

# Turkce harfleri ASCII'ye cevir
TR = str.maketrans({
    "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i",
    "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
})

satirlar = [
    "#pragma once",
    "// Bu dosya klipleri_hazirla.py tarafindan otomatik uretilir. Elle duzenleme.",
    '#include "animasyon_tanimlari.h"',
    "",
    "const Klip klipler[] = {",
]

adlar = []
atlananlar = []

for dosya in sorted(os.listdir(klip_klasoru)):
    if not dosya.lower().endswith(".json"):
        continue

    ad = dosya[:-5].translate(TR).lower()

    if not re.fullmatch(r"[a-z0-9_]+", ad) or ad in adlar:
        atlananlar.append(dosya)
        continue

    with open(os.path.join(klip_klasoru, dosya), encoding="utf-8-sig") as f:
        icerik = f.read()

    satirlar.append('    {"%s", R"KLIP(%s)KLIP"},' % (ad, icerik))
    adlar.append(ad)

satirlar.append("};")
satirlar.append("")
satirlar.append("const int KLIP_SAYISI = sizeof(klipler) / sizeof(klipler[0]);")

yeni = "\n".join(satirlar) + "\n"

eski = ""
if os.path.exists(cikti):
    with open(cikti, encoding="utf-8") as f:
        eski = f.read()

if yeni != eski:
    os.makedirs(os.path.dirname(cikti), exist_ok=True)
    with open(cikti, "w", encoding="utf-8", newline="\n") as f:
        f.write(yeni)

print("Klipler hazir: " + ", ".join(adlar))
if atlananlar:
    print("Atlanan dosyalar: " + ", ".join(atlananlar))