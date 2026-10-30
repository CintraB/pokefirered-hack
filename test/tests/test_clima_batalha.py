"""POK-15 (clima visível na batalha): checagens estáticas do módulo battle_weather_visual."""
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MODULO = RAIZ / "src/battle_weather_visual.c"


def _ler(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


def _funcao(texto, nome):
    m = re.search(r"^(?:static )?[\w ]+?\b" + nome + r"\([^;\n]*\)\n\{.*?\n\}\n", texto, re.M | re.S)
    assert m, nome
    return m.group(0)


def _corpo(funcao):
    """Corpo sem comentários, sem as linhas de declaração."""
    corpo = re.sub(r"//[^\n]*|/\*.*?\*/", "", funcao, flags=re.S)
    return corpo[corpo.index("{") + 1:]


def test_update_roda_em_todo_quadro_da_batalha():
    cb2 = _corpo(_funcao(_ler("src/battle_main.c"), "BattleMainCB2"))
    assert "BattleWeatherVisual_Update();" in cb2
    assert cb2.index("RunTasks();") < cb2.index("BattleWeatherVisual_Update();")


def test_reset_no_inicio_e_na_volta_dos_menus():
    assert "BattleWeatherVisual_Reset();" in _corpo(_funcao(_ler("src/battle_main.c"), "CB2_InitBattleInternal"))
    reshow = _corpo(_funcao(_ler("src/reshow_battle_screen.c"), "ReshowBattleScreenAfterMenu"))
    assert reshow.strip().startswith("BattleWeatherVisual_Reset();")


def test_animacao_suspende_o_clima_antes_de_tudo():
    launch = _corpo(_funcao(_ler("src/battle_anim.c"), "LaunchBattleAnimation"))
    primeira = [l.strip() for l in launch.splitlines() if l.strip() and not l.strip().startswith("s32 ")][0]
    assert primeira == "BattleWeatherVisual_Suspend();"


def test_get_wanted_nao_tem_efeito_colateral():
    c = MODULO.read_text(encoding="utf-8")
    # GetWanted e os dois ajudantes que ela chama
    wanted = "".join(_corpo(_funcao(c, f)) for f in
                     ("BattleWeatherVisual_GetWanted", "IsWeatherNegatedOnField", "IsBattleAnimRunning",
                      "IsBrightnessFade"))
    assert "IsWeatherNegatedOnField()" in c and "IsBattleAnimRunning()" in c
    # AbilityBattleEffects e WEATHER_HAS_EFFECT gravam gLastUsedAbility
    assert "AbilityBattleEffects" not in wanted and "WEATHER_HAS_EFFECT" not in wanted
    assert "ABILITY_CLOUD_NINE" in wanted and "ABILITY_AIR_LOCK" in wanted
    assert re.search(r"gBattleMons\[\w+\]\.hp != 0", wanted)
    for campo in ("optionsBattleSceneOff", "gAnimScriptActive", "gBattleOutcome", "gPaletteFade.active"):
        assert campo in wanted, campo


def test_interface_publica():
    h = _ler("include/battle_weather_visual.h")
    assert re.search(r"enum\s*\{\s*BWV_NONE,\s*BWV_RAIN,\s*BWV_HAIL,\s*BWV_SAND,\s*BWV_SUN,?\s*\};", h)
    assert "extern struct BattleWeatherVisual gBattleWeatherVisual;" in h
    for f in ("void BattleWeatherVisual_Reset(void);", "void BattleWeatherVisual_Suspend(void);",
              "void BattleWeatherVisual_Update(void);", "u8 BattleWeatherVisual_GetWanted(void);"):
        assert f in h, f


def test_granizo_e_areia_sao_particulas():
    c = MODULO.read_text(encoding="utf-8")
    assert "#define BWV_HAIL_COUNT 8" in c and "#define BWV_SAND_COUNT 10" in c
    assert "ANIM_TAG_HAIL" in c and "ANIM_TAG_FLYING_DIRT" in c
    # a areia não usa a camada de fundo da animação do golpe
    assert "AnimTask_LoadSandstormBackground" not in c
    assert not re.search(r"\bBG[12]\b|REG_OFFSET_BG[12]", c)
    wanted = _corpo(_funcao(c, "BattleWeatherVisual_GetWanted"))
    for bit, bwv in (("B_WEATHER_HAIL", "BWV_HAIL"), ("B_WEATHER_SANDSTORM", "BWV_SAND")):
        assert re.search(r"gBattleWeather & " + bit + r"\)\s*return " + bwv + ";", wanted), bwv


def test_sol_e_chuva_tingem_so_fundo_e_pokemon():
    c = MODULO.read_text(encoding="utf-8")
    tinge = _corpo(_funcao(c, "ApplySceneTint"))
    assert "GetBattleMonSpritePalettesMask(1, 1, 1, 1)" in tinge
    assert "BlendPalettes(" in tinge
    desfaz = _corpo(_funcao(c, "RemoveSceneTint"))
    assert "RestorePalettes(gBattleWeatherVisual.tintMask);" in desfaz
    restaura = _corpo(_funcao(c, "RestorePalettes"))
    assert "gPlttBufferUnfaded" in restaura and "gPlttBufferFaded" in restaura
    assert "RemoveSceneTint();" in _corpo(_funcao(c, "BattleWeatherVisual_Suspend"))
    wanted = _corpo(_funcao(c, "BattleWeatherVisual_GetWanted"))
    assert re.search(r"gBattleWeather & B_WEATHER_SUN\)\s*return BWV_SUN;", wanted)
    assert "#define BWV_SUN_TINT RGB(31, 28, 16)" in c
    assert "u32 tintMask;" in _ler("include/battle_weather_visual.h")


def test_revisao_fora_da_tela_da_batalha_nada_aparece():
    """Achado 1: a página da Pokédex da captura roda dentro do BattleMainCB2 com o VBlank dela."""
    c = MODULO.read_text(encoding="utf-8")
    wanted = _corpo(_funcao(c, "BattleWeatherVisual_GetWanted"))
    assert "gMain.vblankCallback != VBlankCB_Battle" in wanted


def test_revisao_suspend_so_destroi_particulas_vivas_do_modulo():
    """Achado 1: depois de um ResetSpriteData que o módulo não viu, os ids velhos são de outros."""
    suspend = _corpo(_funcao(MODULO.read_text(encoding="utf-8"), "BattleWeatherVisual_Suspend"))
    assert "IsWeatherParticle(" in suspend
    particula = _corpo(_funcao(MODULO.read_text(encoding="utf-8"), "IsWeatherParticle"))
    assert "->inUse" in particula
    for cb in ("SpriteCB_RainDrop", "SpriteCB_Hail", "SpriteCB_Sand"):
        assert cb in particula, cb


def test_revisao_tela_apagada_e_fade_sem_brilho():
    """Achados 2 e 3: tela apagada (fade para preto terminado) = nada; fade 0→0 do menu de golpes
    não derruba as partículas."""
    c = MODULO.read_text(encoding="utf-8")
    wanted = _corpo(_funcao(c, "BattleWeatherVisual_GetWanted"))
    assert "gPaletteFade.y != 0" in wanted
    assert "IsBrightnessFade()" in wanted
    fade = _corpo(_funcao(c, "IsBrightnessFade"))
    assert "gPaletteFade.active" in fade and "gPaletteFade.targetY" in fade


def test_revisao_tom_reaplicado_e_so_no_terreno():
    """Achados 3, 5 e 6: o tom volta depois de um fade e pega o Pokémon que entrou; só as
    paletas 2-3 do terreno (a 1 é a das molduras dos menus)."""
    c = MODULO.read_text(encoding="utf-8")
    assert "#define BWV_TERRAIN_PALETTES ((1 << 2) | (1 << 3))" in c
    tinge = _corpo(_funcao(c, "ApplySceneTint"))
    assert "BWV_TERRAIN_PALETTES" in tinge and "GetBattlePalettesMask" not in tinge
    update = _corpo(_funcao(c, "BattleWeatherVisual_Update"))
    assert "RefreshSceneTint();" in update
    refresh = _corpo(_funcao(c, "RefreshSceneTint"))
    assert "BWV_SUN" in refresh and "BWV_RAIN" in refresh and "ApplySceneTint(" in refresh
    tinge_corpo = _corpo(_funcao(c, "ApplySceneTint"))
    # o Pokémon que saiu de campo volta a Unfaded; o que entrou é tingido
    assert "RestorePalettes(gBattleWeatherVisual.tintMask & ~mask);" in tinge_corpo


def test_chuva_tem_dez_gotas_atras_das_caixas_de_ps():
    c = MODULO.read_text(encoding="utf-8")
    assert "#define BWV_RAIN_COUNT 10" in c
    assert "ANIM_TAG_RAIN_DROPS" in c
    assert "#define BWV_SUBPRIORITY 2" in c   # caixas de PS: prioridade 1, subprioridade 0-1
