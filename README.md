# Pet Robot · Kutu Kafalı Kedi

Bilgisayar başındaki insana arkadaşlık eden, masaüstünde duran küçük bir kedi robot. Konuşmaz; duygularını gövdesi, başı ve kulaklarıyla gösterir.

Robot bir "aptal terminal"dir: hiçbir karar vermez, sadece bilgisayardan gelen hareketi düzgün ve güvenli uygular. Görme, düşünme ve hareket hesabı bilgisayardaki Python kodunda yapılır.

## Kim nerede çalışıyor

| Klasör | Ne var | Sorumlu |
| --- | --- | --- |
| `contracts/` | Modüller arası mesajların tanımları | Ferhat |
| `computer_vision/` | Kameradan gülümseme, esneme, gelip gitme tespiti | Mustafa |
| `motion/` | Duygu → hareket pozları, animasyonlar, ekran simülatörü | Reşat (tasarım: Tuğra) |
| `brain/` | Duygu seçen beyin: önce kurallar, sonra yapay zekâ | Azat |
| `router/` | Bütün parçaları birbirine bağlayan merkez ve HAL | Kaan |
| `firmware/` | ESP32 kodu (şimdilik Wokwi'de) | Onur, Eda |
| `tools/` | Sahte veri üreteçleri ve test araçları | Herkes |

Her klasörün içinde ne yapacağını anlatan kısa bir README var.

## Kurulum

1. **Python 3.11** kur. Ekipte herkes aynı sürümü kullanıyor.
2. **VS Code** ve içinden **Python** eklentisini kur.
3. Repoyu indir:
   ```bash
   git clone <repo-linki>
   cd pet-robot
   ```
4. Sanal ortam oluştur ve etkinleştir:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate
   ```
5. Paketleri kur:
   ```bash
   pip install -r requirements.txt
   ```
6. `.env.example` dosyasını kopyalayıp adını `.env` yap. Bu dosya asla GitHub'a gönderilmez.

Gövde takımı (Onur, Eda) ayrıca **Arduino IDE** veya VS Code için **Wokwi** eklentisini kurar; ayrıntılar `firmware/README.md` içinde.

## Çalışma kuralları

- **Kimse doğrudan `main` dalına yazmaz.** Her iş kendi dalında yapılır (`motion/ilk-pencere`, `computer_vision/smile-detection` gibi), Pull Request açılır, ikili partner inceler ve onaylar.
- **Mesaj formatları Arayüz Sözleşmeleri dokümanındadır.** Değişiklik gerekiyorsa önce dokümana yorum yaz; kodda kendi başına değiştirme.
- **Her akşam 21.00:** gruba üç satır: bugün ne yaptım, yarın ne yapacağım, nerede takıldım.
- **2 saat kuralı:** Bir sorunda 2 saattir ilerlemiyorsan yardım iste.
- **Anlamadığın kodu commit etme.** Yapay zekâdan kod alabilirsin, ama satır satır açıklayabilmelisin.

## Dokümanlar

- [Arayüz Sözleşmeleri](https://claude.ai/code/artifact/bf0da636-6bd1-4f66-9efb-c4f3d0124282): modüllerin birbirine gönderdiği mesajlar. Kod yazarken açık tut.
- [Yol Haritası](https://claude.ai/code/artifact/11e42fea-e990-47c1-b08e-d989c3d6eeb9): fazlar, kapılar ve kişi kişi görevler.
- [Teknik Resim](https://claude.ai/artifact/JNkUQR4CiUBz5FAC9yZ1tA): robotun ölçüleri ve servo yerleşimi.
- [Yüz Atölyesi](https://claude.ai/artifact/7tgRi9gK8AVZMqchB9Hv9t): Tuğra'nın ifade tasarım aracı.


## Takvim

| Tarih | Faz | Kapı |
| --- | --- | --- |
| 12–14 Ekim | Faz 0 · öğrenme | Kapı 0: herkes alıştırmasını gösterir |
| 15–18 Ekim | Faz 1 · tek başına çalışan parçalar | Kapı 1: her modül sahte veriyle çalışır |
| 19–21 Ekim | Faz 2 · yürüyen iskelet | Kapı 2: gülümse → ekrandaki kedi mutlu |
| 22–25 Ekim | Faz 3 · yapay zekâ ve sanal ESP32 | Demo: 25 Ekim |

## İsimler 
-Onur