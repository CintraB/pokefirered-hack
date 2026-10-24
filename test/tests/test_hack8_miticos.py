"""Hack 8: Mew, Celebi e Jirachi no endgame (e o Mewtwo voltando pelo Hall da Fama).

Testes estáticos: travam os specials, scripts e flags. O comportamento é conferido no emulador.
"""

import json
import re

from esteira import check_text as ct
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
    assert "GetCurrentWeather()" in body
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


# Task 4 — Celebi ao amanhecer no Bosque das Frutas ---------------------------------------------

BERRY_MAP_T4 = "data/maps/ThreeIsland_BerryForest"


def _flag_defs_t4() -> dict[str, int]:
    return {m.group(1): int(m.group(2), 16)
            for m in re.finditer(r"^#define (FLAG_\w+)\s+(0x[0-9A-Fa-f]+)\b", _read("include/constants/flags.h"), re.M)}


def _script_t4(label: str) -> str:
    """Corpo do script `label::` em scripts.inc do Bosque das Frutas (até o próximo rótulo `::`)."""
    src = _read(f"{BERRY_MAP_T4}/scripts.inc")
    m = re.search(rf"^{label}::\n(.*?)(?=^\w+::|\Z)", src, re.M | re.S)
    assert m, f"script {label} não encontrado"
    return m.group(1)


def _reachable_t4(label: str, seen: set[str] | None = None) -> str:
    """Texto do script `label` mais o de tudo que ele chama/desvia no mesmo arquivo."""
    seen = seen if seen is not None else set()
    if label in seen:
        return ""
    seen.add(label)
    body = _script_t4(label)
    out = body
    for ref in re.findall(r"\b(ThreeIsland_BerryForest_\w+)\b", body):
        if re.search(rf"^{ref}::", _read(f"{BERRY_MAP_T4}/scripts.inc"), re.M):
            out += _reachable_t4(ref, seen)
    return out


def _bloco_t4(x: int, y: int) -> int:
    """Valor de 16 bits (metatile | colisão << 10 | elevação << 12) do tile (x, y) do layout do Bosque."""
    w = 57
    mapbin = (REPO_ROOT / "data/layouts/ThreeIsland_BerryForest/map.bin").read_bytes()
    return int.from_bytes(mapbin[(y * w + x) * 2:(y * w + x) * 2 + 2], "little")


def test_celebi_flags_reservadas():
    flags = _flag_defs_t4()
    assert flags.get("FLAG_HIDE_CELEBI") == 0x303
    assert flags.get("FLAG_CELEBI_FLEW_AWAY") == 0x304
    for nome in ("FLAG_HIDE_CELEBI", "FLAG_CELEBI_FLEW_AWAY"):
        iguais = [n for n, v in flags.items() if v == flags[nome]]
        assert iguais == [nome], f"{nome} colide com {iguais}"
    assert "FLAG_0x303" not in flags and "FLAG_0x304" not in flags


def test_celebi_condicoes():
    on_transition = _script_t4("ThreeIsland_BerryForest_OnTransition")
    assert "TryShowCelebi" in on_transition, "a entrada no mapa precisa avaliar o Celebi"
    mostrar = _reachable_t4("ThreeIsland_BerryForest_EventScript_TryShowCelebi")
    # esconde por padrão e só mostra depois de todas as condições
    assert "setflag FLAG_HIDE_CELEBI" in mostrar
    assert mostrar.index("setflag FLAG_HIDE_CELEBI") < mostrar.index("clearflag FLAG_HIDE_CELEBI")
    antes = mostrar[:mostrar.index("clearflag FLAG_HIDE_CELEBI")]
    assert re.search(r"goto_if_unset FLAG_SYS_CAN_LINK_WITH_RS\b", antes)
    assert re.search(r"goto_if_set FLAG_CELEBI_FLEW_AWAY\b", antes)
    assert "specialvar VAR_RESULT, GetDayNightPeriodForScript" in antes
    assert re.search(r"goto_if_ne VAR_RESULT, TIME_MORNING\b", antes)
    assert "setvar VAR_0x8004, SPECIES_CELEBI" in antes
    assert "specialvar VAR_RESULT, IsSpeciesCaught" in antes
    assert "goto_if_eq VAR_RESULT, TRUE" in antes
    # o clima do Bosque é fixo (WEATHER_SHADE): o Celebi só depende do horário
    assert "IsSkyClear" not in mostrar
    # os scripts enxergam TIME_MORNING
    assert '#include "constants/day_night.h"' in _read("data/event_scripts.s")


def test_celebi_batalha_e_fuga():
    celebi = _script_t4("ThreeIsland_BerryForest_EventScript_Celebi")
    assert re.search(r"setwildbattle SPECIES_CELEBI, 30\b", celebi)
    assert "playmoncry SPECIES_CELEBI" in celebi
    assert "special StartLegendaryBattle" in celebi
    assert "goto_if_questlog EventScript_ReleaseEnd" in celebi
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_WON, \w*Celebi\w*", celebi)
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_RAN, \w*Celebi\w*", celebi)
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, \w*Celebi\w*", celebi)
    # derrotado e fuga: some (FLEW_AWAY); capturado (o que sobra) nunca liga o FLEW_AWAY
    derrotado = _script_t4("ThreeIsland_BerryForest_EventScript_DefeatedCelebi")
    fuga = _script_t4("ThreeIsland_BerryForest_EventScript_RanFromCelebi")
    for caso in (derrotado, fuga):
        assert "setflag FLAG_CELEBI_FLEW_AWAY" in caso and "EventScript_MonFlewAway" in caso
        assert "setvar VAR_0x8004, SPECIES_CELEBI" in caso
    assert "FLAG_CELEBI_FLEW_AWAY" not in celebi
    # capturado: ao voltar da batalha o objeto some na hora
    scripts = _read(f"{BERRY_MAP_T4}/scripts.inc")
    assert "MAP_SCRIPT_ON_RESUME, ThreeIsland_BerryForest_OnResume" in scripts
    remover = _reachable_t4("ThreeIsland_BerryForest_OnResume")
    assert "FLAG_SYS_SPECIAL_WILD_BATTLE" in remover
    assert re.search(r"goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT\b", remover)
    assert "removeobject LOCALID_BERRY_FOREST_CELEBI" in remover


def test_celebi_volta_pelo_hall():
    reset = re.search(r"^EventScript_ResetLegendaries::\n(.*?)^\treturn", _read("data/scripts/hall_of_fame.inc"),
                      re.M | re.S)
    assert reset and "clearflag FLAG_CELEBI_FLEW_AWAY" in reset.group(1)


def test_celebi_musica_de_lendario():
    body = re.search(r"void StartLegendaryBattle\(void\)\n\{(.*?)^\}", _read("src/battle_setup.c"), re.M | re.S)
    assert body and re.search(
        r"case SPECIES_CELEBI:(\s*case \w+:)*\s*CreateBattleStartTask\(B_TRANSITION_BLUR, MUS_VS_LEGEND\)",
        body.group(1))


def test_celebi_objeto_no_fundo_sem_bloquear():
    mapa = json.loads(_read(f"{BERRY_MAP_T4}/map.json"))
    celebis = [o for o in mapa["object_events"] if o["graphics_id"] == "OBJ_EVENT_GFX_CELEBI"]
    assert len(celebis) == 1
    c = celebis[0]
    assert c["local_id"] == "LOCALID_BERRY_FOREST_CELEBI"
    assert c["flag"] == "FLAG_HIDE_CELEBI"
    assert c["script"] == "ThreeIsland_BerryForest_EventScript_Celebi"
    assert c["movement_type"] == "MOVEMENT_TYPE_FACE_DOWN"
    pos = (c["x"], c["y"])
    # não pisa em nenhum outro evento do mapa (NPCs, árvores, itens, placas, avisos, warps)
    outros = [(e["x"], e["y"]) for k in ("object_events", "bg_events", "warp_events", "coord_events")
              for e in mapa[k] if e is not c]
    assert pos not in outros
    # Lostelle (LOOK_AROUND, raio 1) não pode andar para cima dele
    lostelle = next(o for o in mapa["object_events"] if o.get("local_id") == "LOCALID_BERRY_FOREST_LOSTELLE")
    assert (abs(lostelle["x"] - c["x"]) > lostelle["movement_range_x"]
            or abs(lostelle["y"] - c["y"]) > lostelle["movement_range_y"])
    # fundo do bosque: bem longe da entrada (warps do sul)
    entrada = mapa["warp_events"][0]
    assert abs(c["x"] - entrada["x"]) + abs(c["y"] - entrada["y"]) >= 60

    def livre(x, y):
        return (_bloco_t4(x, y) >> 10) & 3 == 0

    assert livre(*pos)
    # o jogador alcança e fica à frente dele (olhando para baixo, a casa do sul é a de aproximação)
    assert livre(pos[0], pos[1] + 1)


def test_celebi_pista():
    texto = _read(f"{BERRY_MAP_T4}/text.inc")
    mapa = json.loads(_read(f"{BERRY_MAP_T4}/map.json"))
    # placa nova no Bosque, legível a qualquer hora (sem condição de flag/horário)
    placas = [b for b in mapa["bg_events"] if b["type"] == "sign" and "Sun" in b["script"]]
    assert len(placas) == 1, "uma placa de pista"
    roteiro = _script_t4(placas[0]["script"])
    assert "msgbox ThreeIsland_BerryForest_Text_ForestWakesWithSun, MSGBOX_SIGN" in roteiro
    assert "goto_if" not in roteiro and "call_if" not in roteiro
    m = re.search(r'^ThreeIsland_BerryForest_Text_ForestWakesWithSun::\n((?:    \.string ".*"\n)+)', texto, re.M)
    assert m, "rótulo da pista não encontrado"
    cru = "".join(re.findall(r'\.string "(.*)"', m.group(1)))
    assert cru.endswith("$")
    assert ct.box_lines(cru) <= 2
    plano = re.sub(r"\\[nlp]", " ", cru)
    assert not re.search(r"\{PLAYER\}|\{RIVAL\}", plano)
    assert not re.search(r"\b(o|a)\s+(jogador|treinador)", plano, re.I)
    assert re.search(r"\bsol\b", plano) and re.search(r"\bfundo\b", plano)
    assert "Celebi" not in plano, "a pista não entrega o nome"
    # a placa fica sobre um tile de placa no layout (mesmo valor das placas originais)
    originais = [_bloco_t4(b["x"], b["y"]) for b in mapa["bg_events"]
                 if b["type"] == "sign" and "Sun" not in b["script"]]
    assert originais and all(_bloco_t4(placas[0]["x"], placas[0]["y"]) == o for o in originais)

# fim da Task 4 ------------------------------------------------------------------------------
