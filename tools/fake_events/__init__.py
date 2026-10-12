"""
Sahte olay üreteci: Computer Vision ve beyin hazır olmadan, sözleşmelere
(A1, A2, B1, B2) birebir uyan mesajlar üretir. Ayrıntılar README.md içinde.
"""

from .kullanici import KullaniciAyarlari
from .uretec import TUM_KANALLAR, Kanal, Mesaj, SahteOlayUreteci

__all__ = ["SahteOlayUreteci", "Mesaj", "Kanal", "TUM_KANALLAR", "KullaniciAyarlari"]
