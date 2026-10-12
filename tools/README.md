# tools/ · Yardımcı araçlar

**Sorumlu:** Herkes

Herkesin ortak kullandığı küçük araçlar: sahte veri üreteçleri ve test betikleri. Karşı taraf hazır olmadan kendi kodunu denemek için buradaki sahte verileri kullan. Örneğin router, Computer Vision hazır olmadan buradaki sahte olay üreteciyle test edilir.

Yeni bir araç eklediğinde dosyanın en üstüne ne işe yaradığını ve nasıl çalıştırıldığını yaz.

## Araçlar

- [`fake_events/`](fake_events/README.md): Sözleşme A1, A2, B1 ve B2'ye uyan sahte mesajlar üretir. `python -m tools.fake_events`
