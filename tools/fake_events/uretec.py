"""
SahteOlayUreteci: sahte kullanıcıyı ve sahte beyni bir araya getiren akış.

Kendi sanal saatini tutar ve her adımda (varsayılan 1/15 sn, A1 hızı)
sırasıyla şunları üretir:
  A1  yüz takibi (her adımda bir tane)
  A2  anlamlı olay (sadece bir şey olduğunda)
  B1  o olay için router'ın beyne göndereceği bağlam
  B2  beynin kararı (gerçek bir LLM gibi 0.3-1.5 sn gecikmeyle)

Kullanım (asyncio içinde):
    uretec = SahteOlayUreteci(tohum=42)
    async for mesaj in uretec.akis(sure_s=60):
        print(mesaj.kanal, mesaj.json())
"""

import asyncio
import random
import time
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from typing import Literal

from .beyin_tarafi import SahteBeyinAkisi
from .kullanici import KullaniciAyarlari, SahteKullanici
from contracts import ContractModel

Kanal = Literal["A1", "A2", "B1", "B2"]
TUM_KANALLAR: tuple[Kanal, ...] = ("A1", "A2", "B1", "B2")


@dataclass(frozen=True)
class Mesaj:
    """Üretecin verdiği tek bir mesaj: hangi sözleşmeye ait olduğu ve içeriği."""

    kanal: Kanal
    veri: ContractModel

    # Mesajı sözleşmedeki JSON formatında tek satırlık metne çevirir.
    def json(self) -> str:
        return self.veri.to_json()


class SahteOlayUreteci:
    """Sözleşmelere uyan A1, A2, B1 ve B2 mesajlarını sırayla üreten sahte kaynak."""

    # Ayarları alır. hiz=1 gerçek zaman, hiz=10 on kat hızlı, hiz=0 hiç beklemeden üretir.
    def __init__(
        self,
        tohum: int | None = None,
        hiz: float = 1.0,
        kanallar: Iterable[Kanal] = TUM_KANALLAR,
        adim_s: float = 1 / 15,
        kullanici_ayarlari: KullaniciAyarlari | None = None,
        baslangic_zamani: float | None = None,
    ):
        if hiz < 0:
            raise ValueError("hiz negatif olamaz")
        self._rnd = random.Random(tohum)  # aynı tohum her seferinde aynı akışı verir
        self._hiz = hiz
        self._kanallar = set(kanallar)
        self._adim_s = adim_s
        self._kullanici = SahteKullanici(self._rnd, kullanici_ayarlari)
        self._beyin = SahteBeyinAkisi(self._rnd)
        self._simdi = time.time() if baslangic_zamani is None else baslangic_zamani
        self._bekleyen_kararlar: list[tuple[float, Mesaj]] = []

    # Mesajları sırayla verir. sure_s verilmezse sonsuza kadar (Ctrl+C'ye kadar) sürer.
    async def akis(self, sure_s: float | None = None) -> AsyncIterator[Mesaj]:
        # Saati adım sayısından hesaplıyoruz; 0.0666... gibi sayıları üst üste
        # toplamak küçük yuvarlama hataları biriktirir.
        baslangic = self._simdi
        gercek_baslangic = time.monotonic()
        adim_sayisi = 0
        while sure_s is None or adim_sayisi * self._adim_s < sure_s - 1e-9:
            for mesaj in self._adim():
                if mesaj.kanal in self._kanallar:
                    yield mesaj
            adim_sayisi += 1
            self._simdi = baslangic + adim_sayisi * self._adim_s
            # Bir sonraki adımın gerçek saatteki zamanına kadar bekle. Her seferinde sabit
            # süre beklemek yerine hedefe göre beklersek akış zamanla geride kalmaz.
            # hiz=0 olsa bile sleep(0) diğer görevlere sıra verir; kimse bekletilmez.
            bekleme = 0.0
            if self._hiz > 0:
                hedef = gercek_baslangic + adim_sayisi * self._adim_s / self._hiz
                bekleme = max(0.0, hedef - time.monotonic())
            await asyncio.sleep(bekleme)

    # Mesajları bir asyncio.Queue'ya koyar; router testleri için hazır kaynak.
    async def kuyruga_aktar(self, kuyruk: asyncio.Queue, sure_s: float | None = None) -> None:
        async for mesaj in self.akis(sure_s):
            await kuyruk.put(mesaj)

    # Sanal saatte bir adım ilerler ve bu adımda oluşan bütün mesajları döndürür.
    def _adim(self) -> list[Mesaj]:
        yuz, olaylar = self._kullanici.adim(self._simdi, self._adim_s)
        mesajlar = [Mesaj("A1", yuz)]

        for olay in olaylar:
            mesajlar.append(Mesaj("A2", olay))
            mesajlar.append(Mesaj("B1", self._beyin.baglam_olustur(olay, self._simdi)))
            karar = self._beyin.karar_ver(olay, self._simdi)
            gecikme = self._rnd.uniform(0.3, 1.5)  # LLM cevabı anında gelmez
            self._bekleyen_kararlar.append((self._simdi + gecikme, Mesaj("B2", karar)))

        hazir = [m for z, m in self._bekleyen_kararlar if z <= self._simdi]
        self._bekleyen_kararlar = [(z, m) for z, m in self._bekleyen_kararlar if z > self._simdi]
        return mesajlar + hazir
