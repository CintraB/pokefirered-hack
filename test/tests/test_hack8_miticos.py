"""Hack 8: Mew, Celebi e Jirachi no endgame (e o Mewtwo voltando pelo Hall da Fama).

Testes estáticos: travam os specials, scripts e flags. O comportamento é conferido no emulador.
"""

import json
import re
import struct

from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


# Task 1 — specials de período do dia, céu limpo e espécie capturada ---------------------------

SPECIALS_T1 = ("GetDayNightPeriodForScript", "IsSkyClear", "IsSpeciesCaught")
# Climas que não são "céu limpo": chuva, tempestade, neblina, neve, areia, granizo (e cinza vulcânica).
CLIMA_RUIM_T1 = re.compile(r"RAIN|THUNDERSTORM|DOWNPOUR|FOG|SNOW|SANDSTORM|HAIL|VOLCANIC_ASH")


def _func_body_t1(name: str) -> str:
    """Corpo da função C `name` em src/field_specials.c (da assinatura até a `}` na coluna 0)."""
    src = _read("src/field_specials.c")
    m = re.search(rf"^\w[\w\s\*]*\b{name}\(void\)\n\{{\n(.*?)^\}}", src, re.M | re.S)
    assert m, f"função {name}(void) não encontrada em src/field_specials.c"
    return m.group(1)


def test_specials_registrados():
    specials = _read("data/specials.inc")
    header = _read("include/field_specials.h")
    for name in SPECIALS_T1:
        assert re.search(rf"^\s*def_special {name}\s*$", specials, re.M), f"{name} fora de data/specials.inc"
        assert re.search(rf"\b{name}\(void\);", header), f"{name} sem protótipo em include/field_specials.h"
        _func_body_t1(name)


def test_get_day_night_period_usa_hack7():
    assert "DayNight_GetPeriod()" in _func_body_t1("GetDayNightPeriodForScript")


def test_is_sky_clear_cobre_climas_ruins():
    weathers = re.findall(r"^#define (WEATHER_\w+)\s", _read("include/constants/weather.h"), re.M)
    ruins = [w for w in weathers if CLIMA_RUIM_T1.search(w)]
    assert ruins, "regex não achou nenhum clima ruim em weather.h"
    body = _func_body_t1("IsSkyClear")
    assert "GetSav1Weather()" in body  # Task 5: ver test_is_sky_clear_le_o_clima_do_mapa_t5
    faltam = [w for w in ruins if not re.search(rf"\b{w}\b", body)]
    assert not faltam, f"IsSkyClear não trata: {faltam}"
    # céu limpo de verdade não pode estar na lista
    for bom in ("WEATHER_NONE", "WEATHER_SUNNY", "WEATHER_SUNNY_CLOUDS", "WEATHER_SHADE"):
        assert not re.search(rf"\b{bom}\b", body), f"IsSkyClear trata {bom} como clima ruim"


def test_is_species_caught_usa_flag_caught():
    body = _func_body_t1("IsSpeciesCaught")
    assert "gSpecialVar_0x8004" in body
    assert "FLAG_GET_CAUGHT" in body
    assert "SpeciesToNationalPokedexNum(" in body
    assert "GetSetPokedexFlag(" in body

# fim da Task 1 ------------------------------------------------------------------------------


# Task 5 — Jirachi como brilho de estrela nas Ruínas de Tanoby ----------------------------------

TANOBY = "data/maps/SevenIsland_TanobyRuins"
TANOBY_PFX = "SevenIsland_TanobyRuins"
STAR_X_T5, STAR_Y_T5 = 66, 3


def _label_body_t5(src: str, label: str) -> str:
    """Texto do rótulo `label::` até o próximo rótulo (ou o fim do arquivo)."""
    m = re.search(rf"^{label}::\n(.*?)(?=^\w+::|\Z)", src, re.M | re.S)
    assert m, f"rótulo {label} não encontrado"
    return m.group(1)


def _tanoby_map_t5() -> dict:
    return json.loads(_read(f"{TANOBY}/map.json"))


def test_jirachi_flags_t5():
    flags = _read("include/constants/flags.h")
    assert re.search(r"^#define FLAG_HIDE_JIRACHI\s+0x305\s*$", flags, re.M)
    assert re.search(r"^#define FLAG_JIRACHI_FLEW_AWAY\s+0x306\s*$", flags, re.M)
    assert not re.search(r"^#define FLAG_0x30[56]\b", flags, re.M), "sobrou o FLAG_0x305/0x306 genérico"
    valores = re.findall(r"^#define (FLAG_\w+)\s+(0x[0-9A-Fa-f]+)\s*$", flags, re.M)
    for nome in ("FLAG_HIDE_JIRACHI", "FLAG_JIRACHI_FLEW_AWAY"):
        valor = int(dict(valores)[nome], 16)
        outros = [n for n, v in valores if n != nome and int(v, 16) == valor]
        assert not outros, f"{nome} colide com {outros}"


def test_is_sky_clear_le_o_clima_do_mapa_t5():
    """O script de mapa (ON_TRANSITION) roda depois de SetSavedWeatherFromCurrMapHeader e antes de
    DoCurrentWeather: o clima sorteado pelo Hack 7 está no save (GetSav1Weather); GetCurrentWeather
    ainda guardaria o clima do mapa anterior."""
    body = _func_body_t1("IsSkyClear")
    assert "GetSav1Weather()" in body
    assert "GetCurrentWeather()" not in body


def test_jirachi_condicoes_t5():
    scripts = _read(f"{TANOBY}/scripts.inc")
    assert re.search(
        rf"map_script MAP_SCRIPT_ON_TRANSITION, {TANOBY_PFX}_OnTransition\b", scripts
    ), "script de mapa ON_TRANSITION não registrado"
    body = _label_body_t5(scripts, f"{TANOBY_PFX}_OnTransition") + _label_body_t5(
        scripts, f"{TANOBY_PFX}_EventScript_TryShowJirachi"
    )
    ordem = [
        "setflag FLAG_HIDE_JIRACHI",  # esconde por padrão a cada entrada
        "FLAG_JIRACHI_FLEW_AWAY",
        "setvar VAR_0x8004, SPECIES_DEOXYS",
        "specialvar VAR_RESULT, IsSpeciesCaught",
        "setvar VAR_0x8004, SPECIES_JIRACHI",
        "specialvar VAR_RESULT, GetDayNightPeriodForScript",
        "TIME_NIGHT",
        "specialvar VAR_RESULT, IsSkyClear",
        "clearflag FLAG_HIDE_JIRACHI",  # só depois de todas as condições
    ]
    pos = -1
    for item in ordem:
        nxt = body.find(item, pos + 1)
        assert nxt > pos, f"'{item}' ausente ou fora de ordem no script de mapa"
        pos = nxt
    assert body.count("clearflag FLAG_HIDE_JIRACHI") == 1
    assert body.count("specialvar VAR_RESULT, IsSpeciesCaught") == 2  # Deoxys e Jirachi


def test_jirachi_batalha_t5():
    scripts = _read(f"{TANOBY}/scripts.inc")
    body = _label_body_t5(scripts, f"{TANOBY_PFX}_EventScript_Jirachi")
    assert "playmoncry SPECIES_JIRACHI" in body
    assert "seteventmon SPECIES_JIRACHI, 30" in body
    assert "special StartLegendaryBattle" in body
    assert re.search(r"B_OUTCOME_WON,\s*" + TANOBY_PFX + "_EventScript_DefeatedJirachi", body)
    assert re.search(r"B_OUTCOME_RAN,\s*" + TANOBY_PFX + "_EventScript_RanFromJirachi", body)
    assert re.search(r"B_OUTCOME_PLAYER_TELEPORTED,\s*" + TANOBY_PFX + "_EventScript_RanFromJirachi", body)
    assert "FLEW_AWAY" not in body, "o caminho do capturado não pode ligar FLEW_AWAY"
    for rotulo in ("DefeatedJirachi", "RanFromJirachi"):
        corpo = _label_body_t5(scripts, f"{TANOBY_PFX}_EventScript_{rotulo}")
        assert "setflag FLAG_JIRACHI_FLEW_AWAY" in corpo
        assert "setvar VAR_0x8004, SPECIES_JIRACHI" in corpo
        assert "goto EventScript_MonFlewAway" in corpo
    # capturado: ON_RESUME tira o objeto (como o Lugia) e a Pokédex impede a volta
    assert "B_OUTCOME_CAUGHT" in _label_body_t5(scripts, f"{TANOBY_PFX}_EventScript_TryRemoveJirachi")
    assert re.search(r"map_script MAP_SCRIPT_ON_RESUME, " + TANOBY_PFX + r"_OnResume\b", scripts)
    # música dos lendários
    setup = _read("src/battle_setup.c")
    grupo = re.search(r"((?:case SPECIES_\w+:\s*)+)CreateBattleStartTask\(B_TRANSITION_BLUR, MUS_VS_LEGEND\)", setup)
    assert grupo and "SPECIES_JIRACHI" in grupo.group(1)


def test_jirachi_hall_da_fama_t5():
    body = _label_body_t5(_read("data/scripts/hall_of_fame.inc"), "EventScript_ResetLegendaries")
    assert "clearflag FLAG_JIRACHI_FLEW_AWAY" in body


def test_jirachi_objeto_de_brilho_t5():
    objs = [o for o in _tanoby_map_t5()["object_events"] if o.get("script") == f"{TANOBY_PFX}_EventScript_Jirachi"]
    assert len(objs) == 1
    o = objs[0]
    assert o["flag"] == "FLAG_HIDE_JIRACHI"
    assert o["local_id"] == "LOCALID_TANOBY_RUINS_JIRACHI"
    assert o["graphics_id"] == "OBJ_EVENT_GFX_JIRACHI_STAR"
    assert (o["x"], o["y"], o["elevation"]) == (STAR_X_T5, STAR_Y_T5, 3)
    assert o["trainer_type"] == "TRAINER_TYPE_NONE"
    # gráfico reaproveitado do brilho de campo (nenhuma arte nova)
    consts = _read("include/constants/event_objects.h")
    num = int(re.search(r"#define NUM_OBJ_EVENT_GFX\s+(\d+)", consts).group(1))
    assert re.search(rf"#define OBJ_EVENT_GFX_JIRACHI_STAR\s+{num - 1}\b", consts)
    pointers = _read("src/data/object_events/object_event_graphics_info_pointers.h")
    assert re.search(r"\[OBJ_EVENT_GFX_JIRACHI_STAR\]\s*=\s*&gObjectEventGraphicsInfo_JirachiStar", pointers)
    info = re.search(
        r"gObjectEventGraphicsInfo_JirachiStar = \{(.*?)\n\};",
        _read("src/data/object_events/object_event_graphics_info.h"),
        re.S,
    ).group(1)
    assert "OBJ_EVENT_PAL_TAG_SMALL_SPARKLE" in info and ".inanimate = TRUE" in info
    pics = _read("src/data/object_events/object_event_pic_tables.h")
    tabela = re.search(r"sPicTable_JirachiStar\[\] = \{(.*?)\};", pics, re.S).group(1)
    assert tabela.count("gFieldEffectObjectPic_SmallSparkle") == 2
    movimento = _read("src/event_object_movement.c")
    assert re.search(r"\{gFieldEffectPal_SmallSparkle,\s*OBJ_EVENT_PAL_TAG_SMALL_SPARKLE\}", movimento)
    assert not list((REPO_ROOT / "graphics/object_events/pics").rglob("*jirachi*")), "arte nova de brilho"


def test_jirachi_brilho_em_terra_firme_sem_bloquear_t5():
    """O brilho fica no pouso vindo do Cânion Sevault (área externa), em chão elevação 3, sem colisão,
    sem tapar o caminho e longe das portas das câmaras."""
    mapa = _tanoby_map_t5()
    data = (REPO_ROOT / "data/layouts/SevenIsland_TanobyRuins/map.bin").read_bytes()
    width = 144

    def celula(x, y):
        v = struct.unpack_from("<H", data, (y * width + x) * 2)[0]
        return (v >> 10) & 3, v >> 12

    assert celula(STAR_X_T5, STAR_Y_T5) == (0, 3)
    livres = [
        (dx, dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if celula(STAR_X_T5 + dx, STAR_Y_T5 + dy) == (0, 3)
    ]
    assert len(livres) >= 3, "o brilho tapa o caminho"
    for w in mapa["warp_events"]:
        assert abs(w["x"] - STAR_X_T5) + abs(w["y"] - STAR_Y_T5) >= 15, "brilho perto da porta de uma câmara"


def test_jirachi_pista_t5():
    mapa = _tanoby_map_t5()
    signs = [
        b for b in mapa["bg_events"] if b["type"] == "sign" and b["script"] == f"{TANOBY_PFX}_EventScript_Inscription"
    ]
    assert len(signs) == 1, "a inscrição precisa ser um bg_event de placa"
    scripts = _read(f"{TANOBY}/scripts.inc")
    assert f"msgbox {TANOBY_PFX}_Text_Inscription, MSGBOX_SIGN" in _label_body_t5(
        scripts, f"{TANOBY_PFX}_EventScript_Inscription"
    )
    texto = _label_body_t5(_read(f"{TANOBY}/text.inc"), f"{TANOBY_PFX}_Text_Inscription")
    bruto = "".join(re.findall(r'\.string "(.*?)"', texto))
    caixas = bruto.split("\\p")
    assert caixas and all(c.count("\\n") <= 1 for c in caixas), "mais de 2 linhas visíveis por caixa"
    plano = re.sub(r"\\[nlp]", " ", bruto).lower()
    assert "estrela" in plano and "noite" in plano
    assert not re.search(r"\b(sozinho|sozinha|amigo|amiga|rapaz|garota|menino|menina|escolhido|escolhida)\b", plano)
    assert not re.search(r"\b(the|you|star|night)\b", plano), "texto em inglês"


# fim da Task 5 ------------------------------------------------------------------------------
