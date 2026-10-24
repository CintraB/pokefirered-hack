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
    assert "FLAG_MEW_FLEW_AWAY" not in mew
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
