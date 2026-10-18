"""Hack 7 sem emulador: os consertos de neve, areia e neblina no C batem com o cenário `clima_visual`.

O cenário (esteira/scenarios/full_weather_gfx.py) espelha a intensidade da neblina (externa e a
original da Pokémon Tower) e os offsets de struct Weather; aqui o espelho é conferido contra o
código, sem ROM.
"""

import re

from esteira.scenarios import REPO_ROOT
from esteira.scenarios import full_weather_gfx as fw

EFFECTS_C = (REPO_ROOT / "src" / "field_weather_effects.c").read_text(encoding="utf-8")
WEATHER_H = (REPO_ROOT / "include" / "field_weather.h").read_text(encoding="utf-8")


def _function(name: str) -> str:
    m = re.search(r"^\w[\w\s\*]*\b" + name + r"\(void\)\n\{\n(.*?)^\}", EFFECTS_C, re.M | re.S)
    assert m, f"{name} não encontrada em field_weather_effects.c"
    return m.group(1)


def test_neblina_externa_e_interna_espelhadas():
    body = _function("FogHorizontal_Main")
    blends = re.findall(r"Weather_SetTargetBlendCoeffs\((\d+), (\d+), \d+\)", body)
    pairs = [fw.bldalpha(int(a), int(b)) for a, b in blends]
    assert "IsMapTypeOutdoors(gMapHeader.mapType)" in body
    assert pairs[0] == fw.FOG_OUTDOOR_BLEND, "a primeira intensidade é a externa (Hack 7)"
    assert pairs[1] == fw.FOG_INDOOR_BLEND == fw.bldalpha(12, 8), "interior = a do RSE"


def test_neve_libera_os_flocos_e_areia_devolve_a_paleta():
    assert "gWeatherPtr->snowflakeTimer++" in _function("Snow_Main")
    assert "RestoreDefaultWeatherSpritePalette();" in _function("DestroySandstormSprites")
    assert "RestoreDefaultWeatherSpritePalette();" in _function("DestroyCloudSprites")


def test_offsets_de_struct_weather():
    """Campos que o cenário escreve/lê, em sequência no header (finishStep u16 e depois quatro u8):
    se a ordem mudar, os offsets do espelho ficam errados."""
    block = re.search(r"u16 finishStep;(.*?)bool8 weatherChangeComplete;", WEATHER_H, re.S).group(1)
    assert block.split() == ["u8", "currWeather;", "u8", "nextWeather;", "u8", "weatherGfxLoaded;"]
    assert (fw.W_CURR, fw.W_NEXT, fw.W_GFX_LOADED, fw.W_CHANGE_COMPLETE) == tuple(
        fw.W_FINISH_STEP + 2 + i for i in range(4))
    assert "struct Sprite *snowflakeSprites[101];" in WEATHER_H
