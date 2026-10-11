# router/ · Kedinin sinir sistemi

**Sorumlu:** Kaan

Bütün parçalar arasında mesajları taşıyan merkez. Computer Vision'dan olayları alır, refleksleri kendisi halleder, anlamlı olayları beyne sorar, kararı poza çevirip HAL üzerinden simülatöre veya ESP32'ye gönderir. Hiçbir parçanın diğerini bekletmemesi bu klasörün asıl işi.

**Başlangıç (Faz 0):** asyncio ile birbirini bekletmeden çalışan iki görev ve aralarında bir `asyncio.Queue`.

HAL de burada: router'ın gönderdiği C1 pozunu, kalibrasyon dosyasıyla C2 kablo mesajına çeviren katman. Router simülatöre mi gerçek robota mı konuştuğunu bilmez; bunu `.env` içindeki `ROBOT_PORT` belirler.
