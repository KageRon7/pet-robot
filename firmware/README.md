# firmware/ · Robotun içindeki kod

**Sorumlu:** Onur (iletişim) · Eda (hareket)

ESP32'nin Arduino kodu. Fiziksel parçalar gelene kadar **Wokwi** simülatöründe çalışır; yazılan kod gerçek karta yüklenecek kodun aynısıdır.

- **Onur:** Sözleşme C2 mesajlarını (`move`, `ping`, `neutral`) okur, hatalı mesajı yakalar, `ack` gönderir.
- **Eda:** Beş servoyu `ms` süresinde yumuşakça hedefe götürür; açı sınırlarını ve 3 saniyelik güvenlik sigortasını uygular. Zamanlama `delay()` ile değil `millis()` ile yapılır.

**Başlangıç (Faz 0):** Hiçbir şey kurma; tarayıcıda [wokwi.com](https://wokwi.com) aç, ücretsiz hesapla giriş yap, ana sayfadan **ESP32** ve **Arduino** şablonunu seç. Kod solda, devre sağda; yeşil ▶ düğmesi derleyip çalıştırır. Parça eklemek için devre alanındaki **+** düğmesi (servo için "Servo" ara). Servo kütüphanesi için `ESP32Servo` kullan: soldaki **Library Manager** sekmesinden ekle.

- **Onur:** Serial'den gelen satırı geri yazdır. Wokwi'nin altındaki Serial Monitor'e yazıp Enter'a bas.
- **Eda:** Sanal bir servoyu 0–180° süpür; `delay()` değil `millis()` kullan.

Bitince **Save** ile projeyi kaydet ve linkini gruba at; Kapı 0'da bu linki açıp göstereceksin. Kodu ayrıca `firmware/alistirmalar/` altına `.ino` dosyası olarak ekle.

**Faz 3'te:** Bilgisayardaki Python kodunun sanal ESP32'ye bağlanması için VS Code Wokwi eklentisine geçeceğiz. O eklenti kodu kendisi derlemiyor, derleme aracı ve ayar dosyaları gerekiyor; o zaman birlikte kuracağız. Şimdi uğraşma.

**Kural:** Robot karar vermez; sadece verilen hareketi düzgün ve güvenli uygular.
