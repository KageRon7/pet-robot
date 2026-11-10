"""
sim/panel_olustur.py  --  "Kedi Deneme Tezgâhı" web sayfasını üretir.

Simülasyonu çalıştırır (sim/disa_aktar.py), sonucu sim/panel/sablon.html içine
gömer ve tek bir HTML dosyası yazar. Dosya tarayıcıda çift tıklayınca açılır
(3B kütüphane internetten yüklenir).

Kullanım:
    python -m sim.panel_olustur                     # sim/panel/kedi_tezgahi.html
    python -m sim.panel_olustur --cikti tezgah.html
"""

import argparse
import json
from pathlib import Path

from .disa_aktar import veri_uret

KLASOR = Path(__file__).resolve().parent / "panel"
SABLON = KLASOR / "sablon.html"
VARSAYILAN_CIKTI = KLASOR / "kedi_tezgahi.html"


# Şablona veriyi gömer; "</" dizisi kaçırılır ki script etiketi erken kapanmasın.
def sayfa_uret(veri: dict) -> str:
    metin = json.dumps(veri, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return SABLON.read_text(encoding="utf-8").replace("__VERI__", metin, 1)


# Komut satırı: simülasyonu çalıştırır ve sayfayı yazar.
def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Kedi Deneme Tezgâhı sayfasını üretir")
    p.add_argument("--cikti", type=Path, default=VARSAYILAN_CIKTI)
    arg = p.parse_args(argv)
    print("Simülasyon çalışıyor (yaklaşık 20 saniye)...")
    arg.cikti.write_text(sayfa_uret(veri_uret()), encoding="utf-8")
    print(f"Sayfa hazır: {arg.cikti}  (tarayıcıda açmak için çift tıkla)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
