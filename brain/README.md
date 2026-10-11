# brain/ · Kedinin aklı

**Sorumlu:** Azat

Kedinin hangi duyguyu yaşayacağına karar veren kısım. Girdisi Sözleşme B1 (bağlam), çıktısı Sözleşme B2 (karar) formatındadır.

**Nasıl çalışıyoruz:** Bütün geliştirme **sahte beyin** üzerinde yapılır. Sahte beyin, gerçek yapay zekâyla aynı formatta hazır cevaplar döndüren bir sınıftır; böylece API anahtarı olmadan bütün kodu, prompt'u ve cevap kontrolünü yazıp test edebilirsin. Gerçek Claude API, Faz 3'te entegrasyon bilgisayarında bağlanır ve senin kodun hiç değişmez: sadece sahte sınıf yerine gerçek sınıf seçilir. Profesyonel ekipler de dış servislere bağlı kodu böyle geliştirir.

**Başlangıç (Faz 0):** B2 formatında rastgele ama geçerli bir duygu döndüren `SahteBeyin` sınıfı. Ardından kurallı beyin: `smile → happy`, `yawn → sleepy`, `user_left → sad`.

**Kural:** Beyin bozuk veya liste dışı bir cevap üretirse sistem `idle` duygusuna düşer; asla çökmez.
