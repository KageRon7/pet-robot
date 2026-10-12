"""
Komut satırından sahte olay üreteci.

Repo kök klasöründen çalıştır:
    python -m tools.fake_events                     # A2, B1, B2 mesajları, gerçek zamanlı
    python -m tools.fake_events --kanallar A1       # sadece yüz takibi (saniyede 15 satır)
    python -m tools.fake_events --hiz 20 --sure 600 # 10 dakikalık oturum, 20 kat hızlı
    python -m tools.fake_events --tohum 42          # her seferinde aynı akış
    python -m tools.fake_events --kanallar A2 --ham # sadece JSON, başka programa aktarmak için
"""

import argparse
import asyncio
import os
import sys

from .uretec import TUM_KANALLAR, SahteOlayUreteci


# Komut satırı seçeneklerini tanımlar ve okur.
def argumanlari_oku() -> argparse.Namespace:
    ayrac = argparse.ArgumentParser(description="Sözleşmelere uyan sahte A1/A2/B1/B2 mesajları üretir.")
    ayrac.add_argument("--kanallar", default="A2,B1,B2", help="virgülle ayrılmış: A1,A2,B1,B2 (varsayılan: A2,B1,B2)")
    ayrac.add_argument("--sure", type=float, default=None, help="kaç saniyelik oturum (varsayılan: Ctrl+C'ye kadar)")
    ayrac.add_argument("--hiz", type=float, default=1.0, help="zaman çarpanı: 1 gerçek zaman, 0 beklemeden")
    ayrac.add_argument("--tohum", type=int, default=None, help="rastgelelik tohumu; aynı tohum aynı akışı verir")
    ayrac.add_argument("--ham", action="store_true", help="kanal etiketi olmadan sadece JSON yaz")
    argumanlar = ayrac.parse_args()

    kanallar = [k.strip().upper() for k in argumanlar.kanallar.split(",") if k.strip()]
    hatali = [k for k in kanallar if k not in TUM_KANALLAR]
    if hatali:
        ayrac.error(f"bilinmeyen kanal: {', '.join(hatali)}")
    argumanlar.kanallar = kanallar
    return argumanlar


# Üreteci çalıştırır ve her mesajı bir satır olarak ekrana yazar.
async def calistir(argumanlar: argparse.Namespace) -> None:
    uretec = SahteOlayUreteci(tohum=argumanlar.tohum, hiz=argumanlar.hiz, kanallar=argumanlar.kanallar)
    async for mesaj in uretec.akis(argumanlar.sure):
        print(mesaj.json() if argumanlar.ham else f"{mesaj.kanal}  {mesaj.json()}", flush=True)


# Programın giriş noktası; Ctrl+C ile veya çıktı `head` gibi bir programa verilip kapanınca sessizce biter.
def main() -> None:
    try:
        asyncio.run(calistir(argumanlari_oku()))
    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        # Okuyan program kapandı; Python'un çıkışta tekrar yazmaya çalışıp hata basmasını önle.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())


if __name__ == "__main__":
    main()
