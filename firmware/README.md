# firmware/ · Robotun içindeki kod

**Sorumlu:** Eda (yüz ekranı, animasyon) · Onur (mesajlar, animasyon aracı)

ESP32'nin Arduino kodu. Fiziksel parçalar gelene kadar **Wokwi** simülatöründe çalışır; yazılan kod gerçek karta yüklenecek kodun aynısıdır.

## Tek resmi program: `animasyon_oynatma/`

Kartın tek programı budur (12 Kasım kararı). Kafa ve gövde aynı karttadır:

- Sözleşme C2 mesajları: `ping`, `neutral`, `move`, `anim` (klibi adıyla oynatır). Hatalı mesaja `bad_json` / `bad_cmd` / `out_of_range`, doğru mesaja `ack`.
- 5 servo `millis()` ile yumuşak hareket eder; servo pinleri 13, 12, 14, 27, 26.
- 2.4" ILI9341 yüz ekranı: CS 5, DC 2, RST 4.
- 3 saniye mesaj gelmezse nötre döner; 256 karakterden uzun mesajı reddeder.

Onur'un eski `src/` programı kaldırıldı; yaptığı her şey bu programda var.

## Araçlar

- `animasyon_aktar.py`: `motion/clips/` içindeki klipleri `animasyon_oynatma/include/animasyonlar.h` dosyasına çevirir. Klip ekleyince/değiştirince çalıştır: `python firmware/animasyon_aktar.py`
- `demo.py`: Wokwi açıkken karta sırayla komut gönderip cevapları gösterir: `python firmware/demo.py`

## Wokwi'de çalıştırma

VS Code'da PlatformIO eklentisiyle `firmware/animasyon_oynatma` klasörünü aç, **Build** de, sonra Wokwi simülatörünü başlat. Bilgisayardaki Python kodu karta `rfc2217://localhost:4000` adresinden bağlanır.

`serial_deneme/` ve ana klasördeki `test/` eski alıştırmalardır, robotta kullanılmaz.

**Kural:** Robot karar vermez; sadece verilen hareketi düzgün ve güvenli uygular.
