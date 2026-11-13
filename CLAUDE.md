# Pet Robot — Kutu Kafalı Kedi

Masaüstünde duran, bilgisayar başındaki kullanıcıya arkadaşlık eden "pet" robot. 7 kişilik öğrenci ekibi, tech lead: Ferhat.
Repo: github.com/KageRon7/pet-robot · Python 3.11 (venv) · Sözleşmeler: `contracts/`

## Mimari (tek cümle)
Robot **aptal terminal**: ESP32 sadece gelen açıları uygular. Görme, düşünme, hareket hesabı bilgisayarda Python'da.

```
Kamera → computer_vision/ ──A1/A2──► router/ (asyncio) ──B1──► brain/ (kurallar.py | claude_beyin.py)
                                         ▲  ◄──B2──┘
                                         └──C1/C3──► router/hal.py ──► motion/ simülatör (Tkinter)
                                                                   └──C2──► firmware/ ESP32 (Wokwi: rfc2217://localhost:4000)
```
HAL sayesinde router simülatöre mi robota mı gittiğini bilmez.

## Klasörler ve giriş noktaları
| Klasör | Önemli dosyalar | Sahip |
|---|---|---|
| `contracts/` | Pydantic modelleri: `perception.py` (A), `brain.py` (B), `motion.py` (C1/C2/C3, kulak kalibrasyonu), `common.py` (`ContractModel`) | Ferhat |
| `computer_vision/` | `faz1.py` (canlı olay tespiti, MediaPipe Face Landmarker — `mp.solutions` YOK, kullanma), `veri_kaydet.py` | Mustafa |
| `router/` | `canli.py` (canlı mod girişi), `hal.py` (C1→C2, `SimulatorHAL`), `animasyon.py` (klip oynatma), `beyin_istemcisi.py` | Kaan |
| `brain/` | `kurallar.py` (`decide(b1)`), `claude_beyin.py` (model `claude-haiku-5-5`, hata → kural beyni) | Azat (+Ferhat) |
| `motion/` | `simulator.py`, `klip.py` (`Klip`, `Enterpolator`), `yuz.py` (yüz çizimi), `clips/*.json` (C3 klipleri) | Reşat, tasarım Tuğra |
| `firmware/` | **Tek resmi program `animasyon_oynatma/`** (`src/main.cpp`). Pinler: servo 13,12,14,27,26 · ekran CS 5, DC 2, RST 4. `serial_deneme/` ve kökteki `test/` eski alıştırma, dokunma | Eda, Onur |
| `tools/fake_events/` | Sahte olay üreteci (`python -m tools.fake_events`) | herkes |
| `docs/TEAM_GUIDE.md` | Ekip kuralları ve takvim (sadece gerektiğinde oku) | — |

Çalıştırma: `python computer_vision/faz1.py | python -m router.canli` · kamerasız: `python -m tools.fake_events` · test: `python -m pytest`
Beyin seçimi `.env` içinde `BEYIN=claude|sahte` (boşsa kural beyni). Simülatör/robot geçişi `ROBOT_PORT` ile.

## Sözleşmeler (özet — ayrıntı `contracts/`)
- **A1 face_track** (~15 Hz, sadece refleks): `{type:"face_track", t, present, x, y (0–1, sol üst 0,0), looking_at_robot}`
- **A2 event**: `{type:"event", t, event, confidence (≥0.6), duration_s}` · event ∈ `user_arrived, user_left, smile, yawn, drowsy, looking_at_robot_long`
- **B1** router → beyin: `{now, current_mood{emotion,intensity}, session{user_present_minutes,last_break_minutes_ago}, recent_events[{event,ago_s}], memories[≤5]}`
- **B2** beyin → router: `{emotion, intensity 0–1, duration_s, memory_note|null, reason}` · emotion ∈ `idle, happy, curious, sleepy, sad, playful, startled`
  - Bozuk JSON / liste dışı duygu / >5 sn gecikme → router sessizce `idle`'a düşer ve loglar. Sistem LLM yüzünden asla durmaz; kurallı beyin yedekte kalır.
- **C1** mantıksal poz (router → HAL): `{body_yaw, head_pan, head_tilt, ear_left, ear_right, ms}`
- **C2** kablo (HAL → ESP32, 115200 baud, tek satır JSON + `\n`): `{v:1, seq, cmd: move|ping|neutral|anim, deg:[S0..S4], ms, name}` → `{ack:seq, ok}` / hata: `bad_json, bad_cmd, out_of_range`
  - ESP32: millis() ile yumuşak geçiş, sınır dışı açıyı reddeder, 3 sn mesaj yoksa nötre döner. Python her 1 sn `ping` atar. `anim` ESP32'ye gömülü klibi adıyla oynatır (bilinmeyen ad → `bad_cmd`); 256 karakterden uzun mesaj reddedilir.
- **C3** animasyon klibi (Yüz Atölyesi → `motion/clips/*.json`): `{format:"C3", name, emotion, loop, duration_ms, keys:[{t_ms, ease, face{...}, pose{C1}}]}`
  - ease ∈ `smooth, stop, linear, snap, bounce` · ≥2 kare, ilk `t_ms`=0 · pose C1 aralıklarını aşmaz.
  - Router 25 adım/sn oynatır: her 40 ms'de ara pozu (Yüz Atölyesi'yle aynı ease hesabı) `ms:40` ile C1 olarak yollar. Bir duyguya birden çok klip → router rastgele seçer. Beyin klip seçmez, sadece duygu (B2).
- Sabit listeler kapalıdır: listede olmayan değer gönderilmez, alıcı yok sayar.

## Servo eşlemesi (beta, 5 servo)
| Kanal | Eklem | Mantıksal aralık | Parça |
|---|---|---|---|
| S0 | body_yaw (gövde, Ø75 rulman) | −45° … +45° | MG996R |
| S1 | head_pan | −90° … +90° (0 = gövdeyle aynı yön) | MG90S |
| S2 | head_tilt | −10° … +45° | MG90S |
| S3 | ear_left (3 parçalı, ipli) | 0 (yatık) … 1 (dik) | MG90S |
| S4 | ear_right | 0 … 1 (servo ayna takılı, kalibrasyonda "ters") | MG90S |

Kulak → derece: 1 = 150°, 0 = 60°, nötr 0.8 ≈ 132° (sağ kulak ters: 1 = 30°, 0 = 120°). Kodda `contracts/motion.py`: `EAR_UP_DEG, EAR_DOWN_DEG, EAR_NEUTRAL, ear_to_deg()`.
Güç: 5V 5A harici, ESP32 ile ortak GND; servolar ESP32'den beslenmez. Yüz ekranı: 2.4" ILI9341 SPI 320×240.
Kuyruk ve patiler vize sonrası (yeni sözleşme sürümüyle girer). Ölçü değişirse önce teknik resim, sonra sözleşme güncellenir.

Not: Yüz ekranı ESP32'de; klipler `firmware/animasyon_aktar.py` ile karta gömülür ve `anim` ile oynatılır.

## Kurallar
- Gizlilik: kamera görüntüsü router'a, LLM'e veya diske **asla** gitmez. Hafızaya sadece `memory_note` yazılır.
- API anahtarı `.env`'de, `.env` `.gitignore`'da. Anahtarı koda, loga, commit'e yazma.
- `main`'e doğrudan push yok; dal adı `takim/is` (örn. `cv/smile-detection`), PR + ikili partner onayı.
- Kod stili: temiz OOP, hata toleranslı, asyncio uyumlu (bloklayan çağrı yok). Fonksiyonların üstüne **yeni başlayanlar için Türkçe yorum**.
- Önce simülatör, sonra donanım. Önce kurallı beyin, sonra LLM.
- RAG hafızası şimdilik dondurulmuş (vize sonrası).

## Claude için çalışma notları (token tasarrufu)
- **`firmware/animasyon_oynatma/include/animasyonlar.h` otomatik üretilir (~4300 satır): kullanıcı açıkça istemedikçe okuma, elle de düzenleme.** Klip değişince `python firmware/animasyon_aktar.py` ile yeniden üretilir.
- `motion/clips/*.json` dosyalarının hepsini okuma; gerekirse bir tanesine bak, format zaten yukarıda.
- Kodda bir şey ararken önce `graphify-out/GRAPH_REPORT.md` dosyasına bak (hangi sınıf/fonksiyon nerede, kim kimi çağırıyor), sonra sadece ilgili dosyaları aç. `graphify-out/graph.json` ve `graph.html` büyük dosyalar, okuma; bağlantı sorusu için `graphify explain "SınıfAdı"` veya `graphify path "A" "B"` komutunu kullan.
- Kod değişikliğinden sonra grafiği tazelemek için: `graphify update .` (token harcamaz).
- Görev hangi klasördeyse orada kal; ilgisiz modülleri okuma. venv, `.pio/`, `veri/`, `*.task` dosyalarını okuma.
