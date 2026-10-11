# computer_vision/ · Kedinin gözleri

**Sorumlu:** Mustafa

Kameradan kullanıcının geldiğini, gittiğini, gülümsediğini ve esnediğini anlayan kod. Çıktısı Sözleşme A formatındadır: sürekli yüz takibi (A1) ve anlamlı olaylar (A2).

**Başlangıç (Faz 0):** OpenCV ile webcam'i aç, MediaPipe Face Landmarker ile yüz noktalarını ekrana çiz. Sonra ağız açıklığını ekrana sayı olarak yazdır.

**Gizlilik kuralı:** Kamera görüntüsü hiçbir zaman diske kaydedilmez veya başka modüle gönderilmez. Dışarı sadece olaylar çıkar.
