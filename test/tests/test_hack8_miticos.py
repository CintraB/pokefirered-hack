"""Hack 8: Mew, Celebi e Jirachi no endgame (e o Mewtwo voltando pelo Hall da Fama).

Testes estáticos: travam os specials, scripts e flags. O comportamento é conferido no emulador.
"""

import json
import re
import struct

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


def _block(src: str, label: str) -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global."""
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    return src[start:start + len(label) + 2 + (m.start() if m else len(src))]


# Task 2: Mewtwo volta pelo Hall da Fama

CERULEAN = "data/maps/CeruleanCave_B1F/scripts.inc"


def _cerulean(label: str) -> str:
    return _block(_read(CERULEAN), f"CeruleanCave_B1F_{label}")


def test_mewtwo_flag_existe_sem_colisao():
    flags = _read("include/constants/flags.h")
    defs = re.findall(r"^#define (FLAG_\w+)\s+(0x[0-9A-Fa-f]+)\s*$", flags, re.M)
    valor = {n: int(v, 16) for n, v in defs}
    assert valor["FLAG_MEWTWO_FLEW_AWAY"] == 0x300
    iguais = [n for n, v in valor.items() if v == 0x300]
    assert iguais == ["FLAG_MEWTWO_FLEW_AWAY"], iguais


def test_mewtwo_volta_pelo_hall():
    hall = _block(_read("data/scripts/hall_of_fame.inc"), "EventScript_ResetLegendaries")
    assert "clearflag FLAG_MEWTWO_FLEW_AWAY" in hall


def test_mewtwo_derrotado_ou_fuga_ligam_flew_away():
    for label in ("EventScript_DefeatedMewtwo", "EventScript_RanFromMewtwo"):
        assert "setflag FLAG_MEWTWO_FLEW_AWAY" in _cerulean(label), label
    luta = _cerulean("EventScript_Mewtwo")
    assert "B_OUTCOME_WON, CeruleanCave_B1F_EventScript_DefeatedMewtwo" in luta
    assert "B_OUTCOME_RAN, CeruleanCave_B1F_EventScript_RanFromMewtwo" in luta
    assert "B_OUTCOME_PLAYER_TELEPORTED, CeruleanCave_B1F_EventScript_RanFromMewtwo" in luta


def test_mewtwo_derrotado_ou_fuga_nao_ligam_fought():
    # FOUGHT_MEWTWO passa a significar "capturado" (some para sempre).
    for label in ("EventScript_DefeatedMewtwo", "EventScript_RanFromMewtwo"):
        assert "FLAG_FOUGHT_MEWTWO" not in _cerulean(label), label


def test_mewtwo_capturado_liga_fought_e_nao_flew_away():
    luta = _cerulean("EventScript_Mewtwo")
    depois = luta[luta.index("B_OUTCOME_PLAYER_TELEPORTED"):]
    assert "setflag FLAG_FOUGHT_MEWTWO" in depois
    assert "FLAG_MEWTWO_FLEW_AWAY" not in depois


def test_mewtwo_mapa_esconde_e_mostra_como_o_lugia():
    trans = _cerulean("OnTransition")
    assert "call_if_set FLAG_FOUGHT_MEWTWO, CeruleanCave_B1F_EventScript_HideMewtwo" in trans
    assert "call_if_unset FLAG_FOUGHT_MEWTWO, CeruleanCave_B1F_EventScript_TryShowMewtwo" in trans
    assert "setflag FLAG_HIDE_MEWTWO" in _cerulean("EventScript_HideMewtwo")
    tenta = _cerulean("EventScript_TryShowMewtwo")
    assert tenta.index("goto_if_set FLAG_MEWTWO_FLEW_AWAY") < tenta.index("clearflag FLAG_HIDE_MEWTWO")


def test_hall_migra_save_antigo_em_que_o_mewtwo_foi_so_derrotado():
    # Save antigo: FOUGHT_MEWTWO ligada sem captura -> o Hall a desliga para ele voltar.
    c = _read("src/post_battle_event_funcs.c")
    corpo = c[c.index("bool8 EnterHallOfFame"):c.index("bool8 SetCB2WhiteOut")]
    assert "FlagGet(FLAG_FOUGHT_MEWTWO)" in corpo
    assert "FlagClear(FLAG_FOUGHT_MEWTWO)" in corpo
    assert "GetSetPokedexFlag(SpeciesToNationalPokedexNum(SPECIES_MEWTWO), FLAG_GET_CAUGHT)" in corpo
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
    assert "setflag FLAG_CELEBI_FLEW_AWAY" not in celebi
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


# Task 3 — Mew no porão da Mansão Pokémon ------------------------------------------------------

MANSION_MAP_T3 = "data/maps/PokemonMansion_B1F"
MANSION_W_T3, MANSION_H_T3 = 38, 35
# a passagem copia o corte de 3 colunas que o B1F já tem em x=5..7 (y=13..17), deslocado 15 colunas
GAP_SHIFT_T3 = 15
GAP_BLOCK_T3 = [(x, y) for y in range(13, 17) for x in range(4, 9)] + [(x, 17) for x in range(5, 8)]


def _flag_defs_t3() -> dict[str, int]:
    return {m.group(1): int(m.group(2), 16)
            for m in re.finditer(r"^#define (FLAG_\w+)\s+(0x[0-9A-Fa-f]+)\b", _read("include/constants/flags.h"), re.M)}


def _script_t3(label: str) -> str:
    src = _read(f"{MANSION_MAP_T3}/scripts.inc")
    m = re.search(rf"^{label}::\n(.*?)(?=^\w+::|\Z)", src, re.M | re.S)
    assert m, f"script {label} não encontrado"
    return m.group(1)


def _reachable_t3(label: str, seen: set[str] | None = None) -> str:
    """Texto do script `label` mais o de tudo que ele chama/desvia no mesmo arquivo."""
    seen = seen if seen is not None else set()
    if label in seen:
        return ""
    seen.add(label)
    body = _script_t3(label)
    out = body
    for ref in re.findall(r"\b(PokemonMansion_B1F_\w+)\b", body):
        if re.search(rf"^{ref}::", _read(f"{MANSION_MAP_T3}/scripts.inc"), re.M):
            out += _reachable_t3(ref, seen)
    return out


def _bloco_t3(x: int, y: int) -> int:
    """Valor de 16 bits (metatile | colisão << 10 | elevação << 12) do tile (x, y) do layout do B1F."""
    mapbin = (REPO_ROOT / "data/layouts/PokemonMansion_B1F/map.bin").read_bytes()
    i = (y * MANSION_W_T3 + x) * 2
    return int.from_bytes(mapbin[i:i + 2], "little")


def _metatile_labels_t3() -> dict[str, int]:
    return {m.group(1): int(m.group(2), 16)
            for m in re.finditer(r"^#define (METATILE_\w+)\s+(0x[0-9A-Fa-f]+)\b",
                                 _read("include/constants/metatile_labels.h"), re.M)}


def _setmetatiles_t3(body: str) -> dict[tuple[int, int], tuple[int, int]]:
    """(x, y) -> (metatile, impassável) dos `setmetatile` do script."""
    labels = _metatile_labels_t3()
    out = {}
    for m in re.finditer(r"^\s*setmetatile\s+(\d+),\s*(\d+),\s*(\w+),\s*(\d)\s*$", body, re.M):
        ident = m.group(3)
        out[(int(m.group(1)), int(m.group(2)))] = (
            int(ident, 16) if ident.lower().startswith("0x") else labels[ident], int(m.group(4)))
    return out


def test_mew_flags_reservadas():
    flags = _flag_defs_t3()
    assert flags.get("FLAG_HIDE_MEW") == 0x301
    assert flags.get("FLAG_MEW_FLEW_AWAY") == 0x302
    for nome in ("FLAG_HIDE_MEW", "FLAG_MEW_FLEW_AWAY"):
        iguais = [n for n, v in flags.items() if v == flags[nome]]
        assert iguais == [nome], f"{nome} colide com {iguais}"
    assert "FLAG_0x301" not in flags and "FLAG_0x302" not in flags


def test_mew_condicoes():
    scripts = _read(f"{MANSION_MAP_T3}/scripts.inc")
    assert "MAP_SCRIPT_ON_TRANSITION, PokemonMansion_B1F_OnTransition" in scripts
    assert "TryShowMew" in _script_t3("PokemonMansion_B1F_OnTransition")
    mostrar = _reachable_t3("PokemonMansion_B1F_EventScript_TryShowMew")
    # esconde por padrão e só mostra depois de todas as condições
    assert "setflag FLAG_HIDE_MEW" in mostrar
    assert mostrar.index("setflag FLAG_HIDE_MEW") < mostrar.index("clearflag FLAG_HIDE_MEW")
    antes = mostrar[:mostrar.index("clearflag FLAG_HIDE_MEW")]
    assert re.search(r"goto_if_set FLAG_MEW_FLEW_AWAY\b", antes)
    # Mewtwo capturado (Pokédex, não flag nova) liga; Mew já capturado desliga
    i_mewtwo = antes.index("setvar VAR_0x8004, SPECIES_MEWTWO")
    assert "specialvar VAR_RESULT, IsSpeciesCaught" in antes[i_mewtwo:]
    assert re.search(r"goto_if_eq VAR_RESULT, FALSE\b", antes[i_mewtwo:])
    i_mew = antes.index("setvar VAR_0x8004, SPECIES_MEW\n")
    assert "specialvar VAR_RESULT, IsSpeciesCaught" in antes[i_mew:]
    assert re.search(r"goto_if_eq VAR_RESULT, TRUE\b", antes[i_mew:])
    assert i_mewtwo < i_mew


def test_mew_batalha_e_fuga():
    mew = _script_t3("PokemonMansion_B1F_EventScript_Mew")
    assert re.search(r"setwildbattle SPECIES_MEW, 30\b", mew)
    assert "playmoncry SPECIES_MEW" in mew
    assert "special StartLegendaryBattle" in mew
    assert "goto_if_questlog EventScript_ReleaseEnd" in mew
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_WON, \w*Mew\w*", mew)
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_RAN, \w*Mew\w*", mew)
    assert re.search(r"goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, \w*Mew\w*", mew)
    # derrotado e fuga: some (FLEW_AWAY); capturado (o que sobra) nunca liga o FLEW_AWAY
    derrotado = _script_t3("PokemonMansion_B1F_EventScript_DefeatedMew")
    fuga = _script_t3("PokemonMansion_B1F_EventScript_RanFromMew")
    for caso in (derrotado, fuga):
        assert "setflag FLAG_MEW_FLEW_AWAY" in caso and "EventScript_MonFlewAway" in caso
        assert "setvar VAR_0x8004, SPECIES_MEW" in caso
    assert "setflag FLAG_MEW_FLEW_AWAY" not in mew
    # capturado: ao voltar da batalha o objeto some na hora
    assert "MAP_SCRIPT_ON_RESUME, PokemonMansion_B1F_OnResume" in _read(f"{MANSION_MAP_T3}/scripts.inc")
    remover = _reachable_t3("PokemonMansion_B1F_OnResume")
    assert "FLAG_SYS_SPECIAL_WILD_BATTLE" in remover
    assert re.search(r"goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT\b", remover)
    assert "removeobject LOCALID_POKEMON_MANSION_B1F_MEW" in remover


def test_mew_volta_pelo_hall():
    reset = re.search(r"^EventScript_ResetLegendaries::\n(.*?)^\treturn", _read("data/scripts/hall_of_fame.inc"),
                      re.M | re.S)
    assert reset and "clearflag FLAG_MEW_FLEW_AWAY" in reset.group(1)


def test_mew_musica_de_lendario():
    body = re.search(r"void StartLegendaryBattle\(void\)\n\{(.*?)^\}", _read("src/battle_setup.c"), re.M | re.S)
    assert body and re.search(
        r"case SPECIES_MEW:(\s*case \w+:)*\s*CreateBattleStartTask\(B_TRANSITION_BLUR, MUS_VS_LEGEND\)",
        body.group(1))


def test_mew_passagem_fechada_antes_da_condicao():
    """O layout (map.bin) segue com a parede original; só o script de carga abre a passagem, e só
    com o Mewtwo capturado."""
    on_load = _reachable_t3("PokemonMansion_B1F_OnLoad")
    assert "TryOpenMewPassage" in on_load
    abrir = _reachable_t3("PokemonMansion_B1F_EventScript_TryOpenMewPassage")
    assert "setvar VAR_0x8004, SPECIES_MEWTWO" in abrir
    assert "specialvar VAR_RESULT, IsSpeciesCaught" in abrir
    assert abrir.index("IsSpeciesCaught") < abrir.index("setmetatile")
    assert re.search(r"goto_if_eq VAR_RESULT, FALSE\b", abrir[:abrir.index("setmetatile")])
    # a passagem fica aberta depois do Mewtwo: não depende de FLEW_AWAY nem da captura do Mew
    assert "FLAG_MEW_FLEW_AWAY" not in abrir
    assert _setmetatiles_t3(abrir), "a passagem não troca nenhum metatile"
    # no layout, o corte (x=20..22, y=14..16) é parede (colisão)
    for x in range(20, 23):
        for y in (14, 15, 16):
            assert (_bloco_t3(x, y) >> 10) & 3 == 1, f"({x},{y}) deveria ser parede no layout"


def test_mew_passagem_copia_o_corte_existente():
    """Os metatiles da passagem são exatamente os do corte de x=5..7 que o B1F já tem (visual provado)."""
    abrir = _reachable_t3("PokemonMansion_B1F_EventScript_TryOpenMewPassage")
    novos = _setmetatiles_t3(abrir)
    esperados = {}
    for (x, y) in GAP_BLOCK_T3:
        bloco = _bloco_t3(x, y)
        esperados[(x + GAP_SHIFT_T3, y)] = (bloco & 0x3FF, (bloco >> 10) & 3)
    assert novos == esperados


def test_mew_passagem_nao_bloqueia_caminho_existente():
    abrir = _reachable_t3("PokemonMansion_B1F_EventScript_TryOpenMewPassage")
    novos = _setmetatiles_t3(abrir)
    for (x, y), (_, imp) in novos.items():
        assert 0 <= x < MANSION_W_T3 and 0 <= y < MANSION_H_T3
        if (_bloco_t3(x, y) >> 10) & 3 == 0:  # tile que já era andável continua andável
            assert imp == 0, f"({x},{y}) andável no original viraria parede"
    # o corte abre mesmo: as 3 colunas do meio ficam andáveis de y=13 a y=17 (norte e sul ligados)
    for x in range(20, 23):
        for y in range(13, 18):
            passavel = (novos[(x, y)][1] == 0) if (x, y) in novos else ((_bloco_t3(x, y) >> 10) & 3 == 0)
            assert passavel, f"({x},{y}) fechado na passagem"


def test_mew_objeto_na_passagem():
    mapa = json.loads(_read(f"{MANSION_MAP_T3}/map.json"))
    mews = [o for o in mapa["object_events"] if o["graphics_id"] == "OBJ_EVENT_GFX_MEW"]
    assert len(mews) == 1
    m = mews[0]
    assert m["local_id"] == "LOCALID_POKEMON_MANSION_B1F_MEW"
    assert m["flag"] == "FLAG_HIDE_MEW"
    assert m["script"] == "PokemonMansion_B1F_EventScript_Mew"
    assert m["movement_type"] == "MOVEMENT_TYPE_FACE_DOWN"
    assert m["elevation"] == 3
    pos = (m["x"], m["y"])
    # no meio do corte (x=21), a meia altura, com uma coluna andável de cada lado (dá para contornar)
    assert pos == (21, 15)
    outros = [(e["x"], e["y"]) for k in ("object_events", "bg_events", "warp_events", "coord_events")
              for e in mapa[k] if e is not m]
    assert pos not in outros
    abrir = _setmetatiles_t3(_reachable_t3("PokemonMansion_B1F_EventScript_TryOpenMewPassage"))
    assert abrir[(20, 15)][1] == 0 and abrir[(22, 15)][1] == 0 and abrir[pos][1] == 0


def test_mew_pista():
    mapa = json.loads(_read(f"{MANSION_MAP_T3}/map.json"))
    placas = [b for b in mapa["bg_events"] if b["type"] == "sign" and "DiaryMew" in b["script"]]
    assert len(placas) == 1, "um diário novo"
    p = placas[0]
    roteiro = _script_t3(p["script"])
    assert "msgbox PokemonMansion_B1F_Text_DiaryMewHint, MSGBOX_SIGN" in roteiro
    assert "goto_if" not in roteiro and "call_if" not in roteiro, "legível a qualquer momento"
    texto = _read(f"{MANSION_MAP_T3}/text.inc")
    m = re.search(r'^PokemonMansion_B1F_Text_DiaryMewHint::\n((?:    \.string ".*"\n)+)', texto, re.M)
    assert m, "rótulo da pista não encontrado"
    cru = "".join(re.findall(r'\.string "(.*)"', m.group(1)))
    assert cru.endswith("$")
    assert ct.box_lines(cru) <= 2
    plano = re.sub(r"\\[nlp]", " ", cru)
    assert not re.search(r"\{PLAYER\}|\{RIVAL\}", plano)
    assert not re.search(r"\b(o|a)\s+(jogador|treinador)", plano, re.I)
    assert plano.startswith("Diário:")
    assert re.search(r"\bporão\b", plano), "a pista aponta para o porão"
    # o diário usa o metatile de diário, como o diário original do B1F, e fica sobre mesa (colisão)
    original = next(b for b in mapa["bg_events"] if b["script"] == "PokemonMansion_B1F_EventScript_DiarySep1st")
    assert _bloco_t3(p["x"], p["y"]) & 0x3FF == _bloco_t3(original["x"], original["y"]) & 0x3FF
    assert (_bloco_t3(p["x"], p["y"]) >> 10) & 3 == 1

# fim da Task 3 ------------------------------------------------------------------------------


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
    ret = "EventScript_Return"
    ordem = [  # linhas inteiras: travam também o sentido de cada comparação
        "setflag FLAG_HIDE_JIRACHI",  # esconde por padrão a cada entrada
        f"goto_if_set FLAG_JIRACHI_FLEW_AWAY, {ret}",
        "setvar VAR_0x8004, SPECIES_DEOXYS",
        "specialvar VAR_RESULT, IsSpeciesCaught",
        f"goto_if_eq VAR_RESULT, FALSE, {ret}",  # Deoxys não capturado: some
        "setvar VAR_0x8004, SPECIES_JIRACHI",
        "specialvar VAR_RESULT, IsSpeciesCaught",
        f"goto_if_eq VAR_RESULT, TRUE, {ret}",  # Jirachi já capturado: some
        "specialvar VAR_RESULT, GetDayNightPeriodForScript",
        f"goto_if_ne VAR_RESULT, TIME_NIGHT, {ret}",
        "specialvar VAR_RESULT, IsSkyClear",
        f"goto_if_eq VAR_RESULT, FALSE, {ret}",
        "clearflag FLAG_HIDE_JIRACHI",  # só depois de todas as condições
    ]
    linhas = [ln.strip() for ln in body.splitlines()]
    pos = -1
    for item in ordem:
        assert item in linhas[pos + 1:], f"'{item}' ausente ou fora de ordem no script de mapa"
        pos = linhas.index(item, pos + 1)
    assert body.count("clearflag FLAG_HIDE_JIRACHI") == 1
    assert body.count("specialvar VAR_RESULT, IsSpeciesCaught") == 2  # Deoxys e Jirachi


def test_jirachi_batalha_t5():
    scripts = _read(f"{TANOBY}/scripts.inc")
    body = _label_body_t5(scripts, f"{TANOBY_PFX}_EventScript_Jirachi")
    assert "playmoncry SPECIES_JIRACHI" in body
    assert "seteventmon SPECIES_JIRACHI, 30" in body
    assert "special StartLegendaryBattle" in body
    for saida in ("B_OUTCOME_WON", "B_OUTCOME_RAN", "B_OUTCOME_PLAYER_TELEPORTED"):
        assert re.search(rf"goto_if_eq VAR_RESULT, {saida},\s*{TANOBY_PFX}_EventScript_JirachiFlewAway\b", body)
    assert "setflag FLAG_JIRACHI_FLEW_AWAY" not in body, "o caminho do capturado não pode ligar FLEW_AWAY"
    corpo = _label_body_t5(scripts, f"{TANOBY_PFX}_EventScript_JirachiFlewAway")
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
    # FACE_DOWN pausaria a animação (FaceDirection liga animPaused): o brilho só cintila com NONE
    assert o["movement_type"] == "MOVEMENT_TYPE_NONE"
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


# Task 6 — reconferência das condições na conversa (save antigo gravado dentro do mapa) -----------
# Um save da ROM anterior ao Hack 8 gravado dentro do mapa traz um template velho no índice do
# mítico; o CONTINUAR põe nele o script do mítico ("fantasma"). O script reconfere, ao ser falado,
# as condições que não dependem de horário/clima e encerra calado se alguma falhar.

GUARDAS_T6 = {
    "mew": (f"{MANSION_MAP_T3}/scripts.inc", "PokemonMansion_B1F_EventScript_Mew",
            "FLAG_MEW_FLEW_AWAY", ("setvar VAR_0x8004, SPECIES_MEWTWO\n", "FALSE"), "SPECIES_MEW\n"),
    "celebi": (f"{BERRY_MAP_T4}/scripts.inc", "ThreeIsland_BerryForest_EventScript_Celebi",
               "FLAG_CELEBI_FLEW_AWAY", ("goto_if_unset FLAG_SYS_CAN_LINK_WITH_RS, EventScript_ReleaseEnd", None),
               "SPECIES_CELEBI\n"),
    "jirachi": (f"{TANOBY}/scripts.inc", f"{TANOBY_PFX}_EventScript_Jirachi",
                "FLAG_JIRACHI_FLEW_AWAY", ("setvar VAR_0x8004, SPECIES_DEOXYS\n", "FALSE"), "SPECIES_JIRACHI\n"),
}


def _guarda_t6(nome: str) -> tuple[str, str]:
    arq, rotulo, *_ = GUARDAS_T6[nome]
    body = _label_body_t5(_read(arq), rotulo)
    # a guarda vem antes de qualquer reação visível (virar, grito, texto) e da batalha
    fim = min(body.index(k) for k in ("faceplayer", "playmoncry", "msgbox", "message ") if k in body)
    return body, body[:fim]


def test_miticos_reconferem_condicoes_na_conversa_t6():
    for nome, (_arq, _rot, flew, desbloqueio, proprio) in GUARDAS_T6.items():
        body, guarda = _guarda_t6(nome)
        i_flew = guarda.index(f"goto_if_set {flew}, EventScript_ReleaseEnd")
        assert guarda.index("goto_if_questlog EventScript_ReleaseEnd") < i_flew, nome
        marcador, falso = desbloqueio
        i_desb = guarda.index(marcador)
        if falso:
            depois = guarda[i_desb:]
            assert re.match(r"setvar VAR_0x8004, SPECIES_\w+\n\s*specialvar VAR_RESULT, IsSpeciesCaught\n"
                            r"\s*goto_if_eq VAR_RESULT, FALSE, EventScript_ReleaseEnd", depois), nome
        i_prop = guarda.index(f"setvar VAR_0x8004, {proprio}")
        assert re.match(r"setvar VAR_0x8004, SPECIES_\w+\n\s*specialvar VAR_RESULT, IsSpeciesCaught\n"
                        r"\s*goto_if_eq VAR_RESULT, TRUE, EventScript_ReleaseEnd", guarda[i_prop:]), nome
        assert i_flew < i_desb < i_prop, f"{nome}: ordem FLEW_AWAY → desbloqueio → já capturado"


def test_miticos_nao_reconferem_hora_nem_clima_na_conversa_t6():
    # Review Focus 1/2: o mítico que já está no mapa ainda batalha depois da janela
    for nome in GUARDAS_T6:
        body, _guarda = _guarda_t6(nome)
        assert "GetDayNightPeriodForScript" not in body and "IsSkyClear" not in body, nome


def test_miticos_saem_calados_t6():
    # as saídas da guarda vão direto para release/end (sem texto, sem grito)
    for nome in GUARDAS_T6:
        _body, guarda = _guarda_t6(nome)
        alvos = re.findall(r"goto_if_\w+ [^\n]*?(\w+)\n", guarda)
        assert alvos and set(alvos) == {"EventScript_ReleaseEnd"}, (nome, alvos)
