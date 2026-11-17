# Her testten önce küresel davranış beynini temiz ve rastgelelikten arındırılmış kurar.
# Böylece eski testler (örneğin test_claude_beyin.py) bir önceki testin durumundan
# ve "bazen tepki vermeme" olasılığından etkilenmez.

from dataclasses import replace

import pytest

from brain import davranis
from brain.ayarlar import VARSAYILAN


@pytest.fixture(autouse=True)
def temiz_beyin():
    ayar = replace(VARSAYILAN, sessiz_taban_olasilik=0.0, sessiz_alisma_katsayisi=0.0)
    davranis.sifirla(ayar, tohum=1)
    yield
    davranis.sifirla()
