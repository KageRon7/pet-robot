# sim/ · Robotun dijital ikizi

Parçaları basmadan önce kediyi bilgisayarda kurup **deneme sürüşü** yaptığımız yer.
Pilotların uçuş simülatörü gibi: hataları burada yaparız, gerçek robotta değil.

Fizik motoru olarak [MuJoCo](https://mujoco.org) kullanır (ücretsiz). Ana kodu değiştirmez;
sadece `motion/clips/` içindeki klipleri okur ve router'ın yaptığı gibi 40 ms'de bir komut gönderir.

## Kurulum (bir kere)

```
pip install -r sim/requirements.txt
```

## Kullanım

```
python -m sim.calistir                 # bütün klipleri + zorlama testlerini dener, rapor yazar
python -m sim.calistir --pencere       # kediyi 3B pencerede izle (fare ile çevir)
python -m sim.calistir --pencere --klip curious
python -m sim.calistir --karsilastir   # bugünkü tasarım ile önerileri yan yana koyar
python -m sim.calistir --s0 MG90S --surtunme 0.8   # "ya şöyle olsaydı" denemesi
```

Pencerede bir parça başka bir parçaya 3 mm'den fazla yaklaşırsa **kırmızıya** döner.

## Neye bakıyor?

| # | Sorun | Gerçek hayattaki karşılığı |
|---|---|---|
| 1 | Çarpışma / çok yakın geçiş | Kafa gövdeye sürtüyor, kabuk çiziliyor, motor takılıyor |
| 2 | Motor takılıyor | Servo uzun süre tam güçte: ısınır, vızıldar, bozulur |
| 3 | Motor yetişemiyor | Klip "130 ms'de dön" diyor ama servo o kadar hızlı değil |
| 4 | Devrilme / kayma / dönme | Hızlı harekette robot masada kayıyor ya da devriliyor |
| 5 | Akım | Motorlar aynı anda çalışınca 5 A adaptör yetmiyor |

🔴 gerçek robotta sorun çıkar · 🟡 dikkat · 🟢 sorun yok

## Sayıları nereden değiştiririm?

Bütün ölçüler, ağırlıklar ve motor bilgileri tek dosyada: [`parcalar.py`](parcalar.py)
(kaynak: Teknik Resim v0.2 + İç Mimari v0.3). Montajda bir parçayı tartınca ya da ölçünce
sadece oradaki sayıyı düzeltin.

## Dosyalar

- `parcalar.py`: ölçüler, ağırlıklar, servo bilgileri
- `model.py`: bu sayılardan 3B fizik modelini üretir
- `ikiz.py`: sanal ESP32 + gerçekçi servo (hız ve güç sınırı) + ölçümler
- `kontrol.py`: senaryolar, gözlemci, rapor
- `calistir.py`: komut satırı

## Bilinen sınırlar (dürüst olalım)

- Ağırlıklar ve servo değerleri **tahmin** (satıcı bilgisi). Sonuçlar "kesin şu olur" değil,
  "burada risk var, montajda ilk buna bak" demektir.
- Parçalar kutu olarak modellendi; kafa derinliği (60 mm) çizimde olmadığı için tahmin.
- Henüz yok: kabloların burulması, kulak ipinin gerilmesi, kabuğun **içindeki** parça sığması,
  ESP32'nin belleği ve ekran çizim hızı. Bunlar sıradaki adımlar.
