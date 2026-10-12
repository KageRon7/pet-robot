# computer_vision/ · Kedinin gözleri

**Sorumlu:** Mustafa

Kameradan kullanıcının geldiğini, gittiğini, gülümsediğini ve esnediğini anlayan kod. Çıktısı Sözleşme A formatındadır: sürekli yüz takibi (A1) ve anlamlı olaylar (A2).

**Başlangıç (Faz 0):** OpenCV ile webcam'i aç, MediaPipe Face Landmarker ile yüz noktalarını ekrana çiz. Sonra ağız açıklığını ekrana sayı olarak yazdır.

Hazır örnek: `python -m computer_vision.ornek_yuz_noktalari`. Önce çalıştır, sonra satır satır okuyup anla; kendi kodunu bunun üzerine kur.

**Dikkat:** İnternetteki örneklerin çoğu `mp.solutions.face_mesh` ve `mp.solutions.drawing_utils` kullanır. Kurulan MediaPipe sürümünde `mp.solutions` yok, o kod hata verir. Yeni yol `mediapipe.tasks.python.vision.FaceLandmarker`; örnek dosya bunu kullanıyor. Yapay zekâdan kod isterken de "MediaPipe Tasks FaceLandmarker kullan, mp.solutions kullanma" de.

**Gizlilik kuralı:** Kamera görüntüsü hiçbir zaman diske kaydedilmez veya başka modüle gönderilmez. Dışarı sadece olaylar çıkar.
