"""ESP32HAL'ın bildiği klip adları, ESP32'ye gömülen adlarla aynı olmalı."""

from router.hal import ESP32HAL, KLIP_KLASORU


# Türkçe harfli klipler de (derın_uyku -> derin_uyku) ESP32'deki adıyla bilinmeli.
def test_turkce_harfli_klipler_esp32_adiyla_bilinir():
    adlar = ESP32HAL._firmware_kliplerini_oku()
    assert len(adlar) == len(list(KLIP_KLASORU.glob("*.json")))
    for ad in adlar:
        assert ad.isascii() and ad == ad.lower()
    if (KLIP_KLASORU / "derın_uyku.json").exists():
        assert "derin_uyku" in adlar
