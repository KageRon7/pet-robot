# brain/ · Kedinin aklı

**Sorumlu:** Azat

Kedinin hangi duyguyu yaşayacağına karar veren kısım. Girdisi Sözleşme B1 (bağlam), çıktısı Sözleşme B2 (karar) formatındadır.

**Nasıl çalışıyoruz:** Bütün geliştirme **sahte beyin** üzerinde yapılır. Sahte beyin, gerçek yapay zekâyla aynı formatta hazır cevaplar döndüren bir sınıftır; böylece API anahtarı olmadan bütün kodu, prompt'u ve cevap kontrolünü yazıp test edebilirsin. Gerçek Claude API, Faz 3'te entegrasyon bilgisayarında bağlanır ve senin kodun hiç değişmez: sadece sahte sınıf yerine gerçek sınıf seçilir. Profesyonel ekipler de dış servislere bağlı kodu böyle geliştirir.

**Başlangıç (Faz 0):** B2 formatında rastgele ama geçerli bir duygu döndüren `SahteBeyin` sınıfı. Ardından kurallı beyin: `smile → happy`, `yawn → sleepy`, `user_left → sad`.

**Kural:** Beyin bozuk veya liste dışı bir cevap üretirse sistem `idle` duygusuna düşer; asla çökmez.


## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `kurallar.py` | Kurallı beyin. `decide(b1)` fonksiyonu B1 alır, `Decision` döner. |
| `tests/fake_brain.py` | Faz 0 sahte beyni. Girdiye bakmadan rastgele bir duygu seçer. |


Repo kökünde, Python 3.11 ile:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`contracts/` güncel olmalı. Emin olmak için `git pull origin main` yap.

## Çalıştırma

Repo kökünden çalıştır (`brain` klasörünün içinden değil):

```powershell
python -m brain.kurallar
```

Bu komut sahte bağlamlarla 13 test satırı basar. Terminal paneli küçükse Maximize Panel Size ile büyüt. Her satırda test adı, seçilen duygu, şiddet ve gerekçe görünür. Örnek:

```
gülümseme                    -> happy    0.8  (Kullanıcı gülümsedi)
kalktı, 60 sn sonra          -> idle     0.0  (Kural eşleşmedi ya da süre doldu)
```

Sahte beyin için:

```powershell
python -m brain.tests.fake_brain
```

Başka bir dosyadan kullanmak için:

```python
from brain.kurallar import decide

karar = decide(b1)   # b1: BrainContext, karar: Decision
```

## Kurallar

`decide`, B1'deki `recent_events` listesinin **son** elemanına (en yeni olay) bakar.

| Olay | Duygu | Şiddet | Süre (sn) |
|---|---|---|---|
| `smile` | happy | 0.8 | 5 |
| `yawn` | sleepy | 0.6 | 8 |
| `drowsy` | sleepy | 0.6 | 8 |
| `user_left` | sad | 0.7 | 6 |
| `sad` | sad | 0.7 | 6 |
| `angry` | startled | 0.6 | 5 |
| `surprised` | curious | 0.6 | 5 |
| `user_arrived` | curious | 0.6 | 5 |
| `looking_at_robot_long` | playful | 0.6 | 5 |

Durumsal kısımlar:

- **Süre dolunca idle:** Olayın `ago_s` değeri duygunun süresinden büyükse beyin tekrar tepki vermez ve `idle` döner. Böylece kullanıcı kalkınca kedi 6 saniye üzülür, sonra sakinleşir.
- **Uzun süre kimse yoksa uyku:** Son 5 dakikada hiç olay yoksa ve `user_present_minutes` 0 ise kedi `sleepy` olur (şiddet 0.6, süre 8).
- **Eşleşme yoksa:** Tabloda olmayan bir olay gelirse `Decision.idle()` döner.
- **Hata olursa:** Beyin hata verirse çökmez, `Decision.idle("Hata, bekleme durumu")` döner (Sözleşme B hata kuralı).

## Bilinen sorunlar

- Şiddet ve süre sayıları tahminidir, sözleşmede verilmemiştir. Animasyonlar netleşince ince ayar gerekebilir.
- Sözleşmede "sinirli" diye bir duygu yok. `angry` olayı `startled` duygusuna, `surprised` olayı `curious` duygusuna eşlenir (sahte olay üretecindeki eşlemeyle aynı).
- Aynı anda birden fazla olay varsa sadece en yenisine bakılır, öncelik sırası yoktur.
- Kod hata yakalayıp sessizce `idle` döndüğü için, kodda yazım hatası olursa kedi hata göstermeden `idle` kalır. Testte "Hata, bekleme durumu" yazısı görürsen sebebi budur.
- `tests/fake_brain.py` henüz `Decision` değil düz sözlük döndürür.
- LLM beyni henüz yok. İlk sürümde API kullanılmıyor, anahtar gerekmiyor.
- Sahte olay üreteci (`tools/fake_events`) her olayda bağlam kurduğu için "olay yok" durumunu üretmez. O durumu denemek için `kurallar.py`'nin test bloğuna bak.