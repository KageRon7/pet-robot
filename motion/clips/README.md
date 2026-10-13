# motion/clips/ · Tuğra'nın animasyon klipleri

**Sorumlu:** Tuğra · **Kullanan:** Reşat'ın simülatörü (ve ileride gerçek robot)

Bu klasöre Yüz Atölyesi'nden dışa aktarılan animasyon klipleri konur. Her duygu için bir dosya: `happy.json`, `sad.json`, `startled.json` ... Simülatör bu klasördeki dosyaları okuyup kareleri sırayla oynatır.

## Tuğra: klip nasıl yüklenir?

1. [Yüz Atölyesi](https://claude.ai/artifact/7tgRi9gK8AVZMqchB9Hv9t)'nde animasyonu yap, dışa aktar ve `.json` dosyasını indir.
2. Dosyanın adını duygunun İngilizce adıyla ver: `idle`, `happy`, `curious`, `sleepy`, `sad`, `playful`, `startled`. Aynı duygunun ikinci versiyonu için `happy_2.json` gibi bir ad kullan.
3. GitHub'da bu klasörü aç (`motion/clips`), sağ üstten **Add file → Upload files** seç ve dosyayı sürükle.
4. Alttaki kutuya kısa bir not yaz (örnek: "mutlu klibi ilk versiyon") ve **Commit changes**'e bas.

Aynı adla tekrar yüklersen eski dosyanın yerine geçer; eski hali GitHub geçmişinde kalır, kaybolmaz.

## Dosya formatı (C3, taslak)

Format henüz kesinleşmedi; çarşamba (14 Ekim) diğer sözleşmelerle birlikte dondurulacak. Yüz Atölyesi'nin dışa aktardığı dosya zaten bu formattadır, elle düzenlemeye gerek yok.

Her karedeki `pose` kısmı Sözleşme C1'in aynısıdır (gövde, baş, kulaklar ve `ms`), bu yüzden Reşat'ın simülatörü bu kareleri doğrudan oynatabilir.
