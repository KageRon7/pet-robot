"""Claude beyni: kedinin duygusunu Claude yapay zekasına sorarak seçer.

Kısaca nasıl çalışır:
    1. Router B1 bağlamını (saat, son olaylar, masada geçen süre) verir.
    2. Bu bağlam Claude'a kısa bir mesaj olarak gider, Claude B2 kararı (JSON) döndürür.
    3. Cevap sözleşmeye uymazsa, geç kalırsa ya da internet yoksa kural beyni
       (brain/kurallar.py) devreye girer. Yani kedi Claude yüzünden asla donmaz.

İki "istemci" var (istemci = Claude'a soruyu taşıyan postacı):
    - GercekClaudeIstemci: gerçek Claude API'si. ANTHROPIC_API_KEY gerekir.
    - SahteClaudeIstemci: anahtar gerektirmez, hazır cevaplar döndürür. Test için.

Elle deneme (repo kökünden):
    python -m brain.claude_beyin            # sahte Claude ile
    python -m brain.claude_beyin --gercek   # gerçek Claude ile (.env içinde anahtar olmalı)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from typing import Protocol

from pydantic import ValidationError

from brain.kurallar import decide as kural_beyni
from contracts import BrainContext, Decision, Emotion

logger = logging.getLogger(__name__)

# Hızlı ve ucuz model: kedi her olayda soru sorduğu için hız önemli.
VARSAYILAN_MODEL = "claude-haiku-5-5"
# Router beyni 5 sn bekliyor; biz daha erken vazgeçip kural beynine dönüyoruz.
VARSAYILAN_ZAMAN_ASIMI_S = 3.5

# Claude'a kedinin kim olduğunu anlatan sabit metin (sistem mesajı).
# Bu metin hiç değişmez, sadece altındaki bağlam her olayda değişir.
SISTEM_METNI = """\
Sen "Kutu Kafalı Kedi" adında 15 cm'lik bir masaüstü robot kedinin duygu beynisin.
Konuşamazsın; duygunu kafa, gövde ve kulak hareketleri ve yüz ekranınla gösterirsin.

Görevin: bilgisayar başında uzun saatler çalışan bir insana arkadaşlık etmek.
Bir evcil hayvan gibi yanında olursun. Kullanıcıyı taklit ETMEZSİN, ona TEPKİ verirsin:
- Kullanıcı üzgünse sen de üzülmek yerine yanında olduğunu hissettir (curious veya
  hafif playful ile ilgilen, ya da düşük şiddette sad ile empati kur).
- Kullanıcı sinirliyse ürkebilirsin (startled) ama abartma.
- Kullanıcı gülümserse sevinirsin (happy).
- Kullanıcı uzun süredir molasız çalışıyor ya da esniyorsa sleepy ile "biraz dinlen" hissi ver.
- Kullanıcı gelince merakla karşıla (curious), gidince hafifçe üzül (sad).
- Kullanıcı sana uzun süre bakarsa oyuncu ol (playful).
- Olaylar eskiyse ya da bir şey olmuyorsa sakin dur (idle).
Her seferinde aynı tepkiyi verme; bağlama ve saate bak, canlı bir hayvan gibi davran.

Seçebileceğin duygular SADECE şunlar:
idle, happy, curious, sleepy, sad, playful, startled

Cevabın tek bir JSON nesnesi olsun:
- emotion: yukarıdaki listeden biri
- intensity: 0 ile 1 arası (hareketin büyüklüğü)
- duration_s: 0 ile 15 arası saniye (sonra kedi idle'a döner)
- reason: Türkçe, en fazla bir kısa cümle, neden bu duyguyu seçtiğin
"""

# Claude'un cevabının kalıbı (JSON şeması). API cevabı bu kalıba uydurur.
CEVAP_SEMASI = {
    "type": "object",
    "properties": {
        "emotion": {"type": "string", "enum": [e.value for e in Emotion]},
        "intensity": {"type": "number"},
        "duration_s": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["emotion", "intensity", "duration_s", "reason"],
    "additionalProperties": False,
}


class ClaudeIstemcisi(Protocol):
    """Claude'a soru taşıyan her postacının uyması gereken kalıp."""

    # Sistem metnini ve bağlam mesajını gönderir, Claude'un ham metin cevabını döner.
    async def sor(self, sistem: str, mesaj: str) -> str: ...


class GercekClaudeIstemci:
    """Gerçek Claude API'sine bağlanan postacı. Anahtarı ortamdan (.env) okur."""

    # İstemciyi kurar; anahtar yoksa burada hata verir ki sorun hemen görülsün.
    def __init__(self, model: str = VARSAYILAN_MODEL) -> None:
        import anthropic  # sadece gerçek modda gerekli

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY bulunamadı. Repo kökündeki .env dosyasına ekle.")
        self.model = model
        # max_retries=0: tekrar denemeyi biz yapmıyoruz, geç kalırsa kural beyni devreye girer.
        self._istemci = anthropic.AsyncAnthropic(max_retries=0)

    # Claude'a tek bir soru sorar ve cevabın metnini döner.
    async def sor(self, sistem: str, mesaj: str) -> str:
        cevap = await self._istemci.messages.create(
            model=self.model,
            max_tokens=300,
            system=sistem,
            messages=[{"role": "user", "content": mesaj}],
            # Düşünmeyi kapatıp en hızlı ayarda çalışıyoruz: kedi beklememeli.
            thinking={"type": "disabled"},
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": CEVAP_SEMASI},
            },
        )
        if cevap.stop_reason == "refusal":
            raise RuntimeError("Claude cevap vermeyi reddetti")
        return next(b.text for b in cevap.content if b.type == "text")


class SahteClaudeIstemci:
    """Anahtar gerektirmeyen sahte postacı. Sırayla hazır cevapları döndürür.

    cevaplar listesindeki her öğe şunlardan biri olabilir:
      - str: Claude'un döndürdüğü metin (bozuk JSON da olabilir, test için)
      - Exception: o soruda hata fırlatılır (internet kopması gibi)
    gecikme_s ile Claude'un yavaş cevap vermesi taklit edilir.
    """

    # Hazır cevapları ve yapay gecikmeyi kaydeder.
    def __init__(self, cevaplar: list | None = None, gecikme_s: float = 0.0) -> None:
        self.cevaplar = list(cevaplar) if cevaplar else []
        self.gecikme_s = gecikme_s
        self.sorulanlar: list[str] = []  # testlerde neyin sorulduğunu görmek için

    # Sıradaki hazır cevabı döner; liste bittiyse son olaya bakıp basit bir cevap üretir.
    async def sor(self, sistem: str, mesaj: str) -> str:
        self.sorulanlar.append(mesaj)
        if self.gecikme_s:
            await asyncio.sleep(self.gecikme_s)
        if self.cevaplar:
            cevap = self.cevaplar.pop(0)
            if isinstance(cevap, Exception):
                raise cevap
            return cevap
        return json.dumps({
            "emotion": "curious", "intensity": 0.5, "duration_s": 5,
            "reason": "Sahte Claude: ne olduğunu merak ettim",
        })


# B1 bağlamını Claude'un kolay okuyacağı kısa bir Türkçe metne çevirir.
def baglami_metne_cevir(b1: BrainContext) -> str:
    satirlar = [
        f"Saat: {b1.now.strftime('%H:%M')}",
        f"Kedinin şu anki duygusu: {b1.current_mood.emotion.value} (şiddet {b1.current_mood.intensity})",
        f"Kullanıcı masada: {b1.session.user_present_minutes} dakikadır",
        f"Son moladan beri: {b1.session.last_break_minutes_ago} dakika",
    ]
    if b1.recent_events:
        satirlar.append("Son 5 dakikadaki olaylar (en yeni en altta):")
        satirlar += [f"- {o.event.value}, {o.ago_s} sn önce" for o in b1.recent_events]
    else:
        satirlar.append("Son 5 dakikada hiç olay yok.")
    if b1.memories:
        satirlar.append("Hatırladıkların:")
        satirlar += [f"- {anı}" for anı in b1.memories]
    satirlar.append("Kedi şimdi ne hissetsin?")
    return "\n".join(satirlar)


class ClaudeBeyin:
    """Claude'a sorarak karar veren beyin. Sorun olursa kural beynine döner."""

    # Postacıyı ve bekleme süresini ayarlar.
    def __init__(self, istemci: ClaudeIstemcisi, zaman_asimi_s: float = VARSAYILAN_ZAMAN_ASIMI_S) -> None:
        self.istemci = istemci
        self.zaman_asimi_s = zaman_asimi_s

    # B1'i alır, B2 döner. Asla hata fırlatmaz: her sorunda kural beyni cevap verir.
    async def karar_ver(self, b1: BrainContext) -> Decision:
        try:
            metin = await asyncio.wait_for(
                self.istemci.sor(SISTEM_METNI, baglami_metne_cevir(b1)),
                timeout=self.zaman_asimi_s,
            )
            # Sözleşme B2 kontrolü: liste dışı duygu, 0-1 dışı şiddet vb. burada yakalanır.
            karar = Decision.model_validate_json(metin)
            return karar.model_copy(update={"reason": f"[claude] {karar.reason}"})
        except asyncio.TimeoutError:
            sebep = "zaman aşımı"
        except ValidationError:
            sebep = "geçersiz cevap"
        except Exception as hata:  # internet yok, anahtar yanlış, kota doldu...
            sebep = f"hata: {type(hata).__name__}"
        logger.warning("Claude beyni cevap veremedi (%s), kural beynine dönülüyor", sebep)
        yedek = await asyncio.to_thread(kural_beyni, b1)
        return yedek.model_copy(update={"reason": f"[kural, {sebep}] {yedek.reason}"})


# Elle deneme: kural beyninin test bağlamlarını Claude beyniyle çalıştırır.
async def _elle_dene(gercek: bool) -> None:
    from datetime import datetime

    def ctx(olaylar, masada=30):
        return BrainContext.model_validate({
            "now": datetime.now().replace(microsecond=0).isoformat(),
            "current_mood": {"emotion": "idle", "intensity": 0.3},
            "session": {"user_present_minutes": masada, "last_break_minutes_ago": masada},
            "recent_events": olaylar,
        })

    denemeler = [
        ("gülümseme", ctx([{"event": "smile", "ago_s": 0}])),
        ("esneme, 3 saattir masada", ctx([{"event": "yawn", "ago_s": 0}], masada=180)),
        ("kullanıcı üzgün", ctx([{"event": "sad", "ago_s": 1}])),
        ("kullanıcı sinirli", ctx([{"event": "angry", "ago_s": 0}])),
        ("kullanıcı geldi", ctx([{"event": "user_arrived", "ago_s": 0}], masada=0)),
        ("uzun süre robota baktı", ctx([{"event": "looking_at_robot_long", "ago_s": 0}])),
        ("kullanıcı kalktı", ctx([{"event": "user_left", "ago_s": 2}])),
        ("olay yok, masada kimse yok", ctx([], masada=0)),
    ]
    if gercek:
        from dotenv import load_dotenv

        load_dotenv()
        istemci = GercekClaudeIstemci()
    else:
        # Sahte modda bir bozuk cevap ve bir hata da koyuyoruz: yedek beyin görünsün.
        istemci = SahteClaudeIstemci([
            '{"emotion": "happy", "intensity": 0.8, "duration_s": 5, "reason": "Gülümsedi, sevindim"}',
            '{"emotion": "angry", "intensity": 0.9, "duration_s": 5, "reason": "liste dışı duygu"}',
            ConnectionError("internet yok"),
        ])
    beyin = ClaudeBeyin(istemci)
    for ad, b1 in denemeler:
        k = await beyin.karar_ver(b1)
        print(f"{ad:28} -> {k.emotion.value:8} {k.intensity:<4} ({k.reason})")


if __name__ == "__main__":
    asyncio.run(_elle_dene(gercek="--gercek" in sys.argv))
