# Sahte olay üreteci

Computer Vision ve beyin hazır olmadan, [Arayüz Sözleşmeleri v0.1](https://claude.ai/code/artifact/bf0da636-6bd1-4f66-9efb-c4f3d0124282)'e birebir uyan mesajlar üretir. Kameranın önünde hayali bir kullanıcı oturur: masaya gelir, gülümser, esner, robota bakar, kalkıp gider. Her olay için router'ın beyne göndereceği bağlam ve beynin kararı da üretilir.

| Kanal | Sözleşme | Ne zaman | Kimin işine yarar |
| --- | --- | --- | --- |
| `A1` | Yüz takibi | Saniyede 15 kez | Kaan (refleks katmanı) |
| `A2` | Anlamlı olay | Bir şey olunca | Kaan, Azat |
| `B1` | Router → beyin bağlamı | Her A2'de | Azat |
| `B2` | Beynin kararı | A2'den 0.3–1.5 sn sonra | Kaan, Reşat |

Eşikler sözleşmedekiyle aynı: yüz 2 sn görünürse `user_arrived`, 10 sn yoksa `user_left`, robota 3 sn bakarsa `looking_at_robot_long`. `confidence` hiçbir zaman 0.6'nın altına düşmez. Kararların yaklaşık %10'u test için bilerek eşleme dışı bir duygudur (örneğin gülümsemeye `startled`).

## Komut satırından

Repo kök klasöründen:

```bash
python -m tools.fake_events                      # A2, B1, B2; gerçek zamanlı, Ctrl+C ile dur
python -m tools.fake_events --kanallar A1        # sadece yüz takibi
python -m tools.fake_events --hiz 20 --sure 600  # 10 dakikalık oturum, 20 kat hızlı
python -m tools.fake_events --tohum 42           # her çalıştırmada aynı akış
python -m tools.fake_events --kanallar A2 --ham  # etiketsiz, sadece JSON satırları
```

`--hiz 0` hiç beklemeden üretir. `--tohum` verirsen bir hatayı arkadaşına "42 tohumuyla çalıştır, 3. dakikada bozuluyor" diye tarif edebilirsin.

## Kendi kodundan

```python
import asyncio
from tools.fake_events import SahteOlayUreteci

# Örnek: gelen her A2 olayını ve B2 kararını ekrana yazar.
async def main():
    uretec = SahteOlayUreteci(tohum=42, kanallar=["A2", "B2"])
    async for mesaj in uretec.akis(sure_s=60):
        print(mesaj.kanal, mesaj.veri)      # veri: Pydantic modeli
        print(mesaj.json())                 # sözleşmedeki JSON metni

asyncio.run(main())
```

Router testleri için mesajları doğrudan bir kuyruğa da koyabilirsin:

```python
kuyruk = asyncio.Queue()
asyncio.create_task(SahteOlayUreteci().kuyruga_aktar(kuyruk))
```

Kullanıcının ne sıklıkla güleceğini, esneyeceğini değiştirmek için `KullaniciAyarlari` ver: `SahteOlayUreteci(kullanici_ayarlari=KullaniciAyarlari(esneme_dakikada=5))`.

## Dosyalar

| Dosya | Ne var |
| --- | --- |
| `kullanici.py` | Sahte kullanıcı: A1 ve A2 üretir |
| `beyin_tarafi.py` | B1 bağlamı ve sahte B2 kararı |
| `uretec.py` | Hepsini sanal bir saatle birleştiren `SahteOlayUreteci` |
| `__main__.py` | Komut satırı |
| `test_uretec.py` | Testler: `python -m unittest tools.fake_events.test_uretec -v` |

## Sözleşmelerle bağlantı

Bütün mesajlar `contracts/` içindeki Pydantic modelleriyle (`FaceTrack`, `PerceptionEvent`, `BrainContext`, `Decision`) oluşturulur. Sözleşmede bir alan değişirse üreteç hata verir ve testler bunu hemen yakalar.
