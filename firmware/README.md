# firmware/ · Robotun içindeki kod

**Sorumlu:** Onur (iletişim) · Eda (hareket)

ESP32'nin Arduino kodu. Fiziksel parçalar gelene kadar **Wokwi** simülatöründe çalışır; yazılan kod gerçek karta yüklenecek kodun aynısıdır.

- **Onur:** Sözleşme C2 mesajlarını (`move`, `ping`, `neutral`) okur, hatalı mesajı yakalar, `ack` gönderir.
- **Eda:** Beş servoyu `ms` süresinde yumuşakça hedefe götürür; açı sınırlarını ve 3 saniyelik güvenlik sigortasını uygular. Zamanlama `delay()` ile değil `millis()` ile yapılır.

**Başlangıç (Faz 0):** VS Code'a Wokwi eklentisini kur. Onur: Serial'den gelen satırı geri yazdır. Eda: sanal bir servoyu 0–180° süpür.

**Kural:** Robot karar vermez; sadece verilen hareketi düzgün ve güvenli uygular.
