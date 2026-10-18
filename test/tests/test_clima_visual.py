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


def test_neblina_clareia_sprites_pela_intensidade():
    """Item 1 dos ajustes do Hack 7: o clareamento dos sprites na neblina sai da intensidade em uso
    (EVA), não do 12 fixo do RSE, e não pega gente nem a paleta do clima; o espelho do cenário
    (W_WEATHER_PAL, OBJ_PALSLOT_COUNT) bate com o C."""
    weather_c = (REPO_ROOT / "src" / "field_weather.c").read_text(encoding="utf-8")
    assert "BlendPalette(paletteIndex, 16, 12, RGB(28, 31, 28))" not in weather_c
    assert "* 3) >> 2;" not in weather_c, "ApplyFogBlend ainda clareia 3/4 fixo"
    coeff = re.search(r"static u8 GetFogSpriteLightenCoeff\(u8 spritePaletteIndex\)\n\{(.*?)^\}",
                      weather_c, re.M | re.S).group(1)
    for part in ("OBJ_PALSLOT_COUNT", "weatherPicSpritePalIndex", "targetBlendEVA"):
        assert part in coeff, part
    assert "UpdateSpritePalettesForFog();" in _function("FogHorizontal_Main")
    assert "UpdateSpritePalettesForFog();" in re.search(
        r"bool8 FogHorizontal_Finish\(void\)\n\{(.*?)^\}", EFFECTS_C, re.M | re.S).group(1)
    block = re.search(r"bool8 weatherChangeComplete;\s*u8 (\w+);", WEATHER_H).group(1)
    assert block == "weatherPicSpritePalIndex" and fw.W_WEATHER_PAL == fw.W_CHANGE_COMPLETE + 1
    header = (REPO_ROOT / "include" / "event_object_movement.h").read_text(encoding="utf-8")
    slots = re.search(r"enum \{\n(.*?)OBJ_PALSLOT_COUNT", header, re.S).group(1)
    assert len(re.findall(r"PALSLOT_\w+,", slots)) == fw.OBJ_PALSLOT_COUNT


def test_neblina_reaplicada_depois_de_reescrever_as_paletas():
    """Ajustes do Hack 7 (revisão): a gamma da troca de clima (chuva -> neblina) e o retingimento
    dia/noite reescrevem as paletas OBJ do Unfaded; os dois chamam UpdateSpritePalettesForFog no
    fim, e ela só refaz as paletas que passaram por UpdateSpritePaletteWithWeather (não um loadpal)."""
    weather_c = (REPO_ROOT / "src" / "field_weather.c").read_text(encoding="utf-8")
    day_night_c = (REPO_ROOT / "src" / "day_night.c").read_text(encoding="utf-8")
    gamma = re.search(r"static void UpdateWeatherGammaShift\(void\)\n\{(.*?)^\}", weather_c, re.M | re.S).group(1)
    assert gamma.index("UpdateSpritePalettesForFog();") < gamma.index("WEATHER_PAL_STATE_IDLE;")
    retint = re.search(r"static void TryRetintField\(void\)\n\{(.*?)^\}", day_night_c, re.M | re.S).group(1)
    assert retint.index("RestoreDefaultWeatherSpritePalette();") < retint.index("UpdateSpritePalettesForFog();")
    refresh = re.search(r"void UpdateSpritePalettesForFog\(void\)\n\{(.*?)^\}", weather_c, re.M | re.S).group(1)
    assert "fogSpritePalTags[i - OBJ_PALSLOT_COUNT]" in refresh
    update = re.search(r"void UpdateSpritePaletteWithWeather\(u8 spritePaletteIndex\)\n\{(.*?)^\}",
                       weather_c, re.M | re.S).group(1)
    assert "fogSpritePalTags[spritePaletteIndex - OBJ_PALSLOT_COUNT] = " in update
    # a lista de tags ocupa o filler antigo: o resto de struct Weather não muda de lugar
    assert re.search(r"s16 droughtState;\s*u16 fogSpritePalTags\[4\];[^\n]*\n\s*u8 filler_74C\[1\];"
                     r"\s*s8 loadDroughtPalsIndex;", WEATHER_H)
