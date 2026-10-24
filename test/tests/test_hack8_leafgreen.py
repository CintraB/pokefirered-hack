"""Hack 8: exclusivos do LeafGreen nos mesmos lugares do LeafGreen (sem emulador).

Quando o encontro sorteia um slot cujo equivalente nas tabelas `_LeafGreen` (mesmo mapa, mesmo
tipo de encontro, mesmo índice) é uma espécie que as tabelas `_FireRed` não têm, o jogo sorteia
50%: a espécie do FireRed do slot ou a do LeafGreen, com os níveis do slot no LeafGreen.

A tabela "onde e qual" sai de tools/wild_leafgreen/gen_swaps.py (rodado pelo make) a partir do
wild_encounters.json. Aqui o teste refaz a conta sozinho e confere o header gerado, o C e a
cobertura das 18 espécies que o levantamento da Dex marcou como exclusivas do LeafGreen.
"""

import importlib.util
import json
import re
import subprocess
import sys

from esteira.scenarios import REPO_ROOT

WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
GEN_SCRIPT = REPO_ROOT / "tools" / "wild_leafgreen" / "gen_swaps.py"
WILD_C = (REPO_ROOT / "src" / "wild_encounter.c").read_text(encoding="utf-8")
WILD_H = (REPO_ROOT / "include" / "wild_encounter.h").read_text(encoding="utf-8")
AREA_C = (REPO_ROOT / "src" / "wild_pokemon_area.c").read_text(encoding="utf-8")
EVO_H = (REPO_ROOT / "src" / "data" / "pokemon" / "evolution.h").read_text(encoding="utf-8")

KINDS = {"land_mons": "LandMonsInfo", "water_mons": "WaterMonsInfo",
         "rock_smash_mons": "RockSmashMonsInfo", "fishing_mons": "FishingMonsInfo"}
# As 18 do levantamento da Dex (.superpowers/sdd/levantamento-dex/relatorio.md)
ALVOS = {"VULPIX", "NINETALES", "SLOWPOKE", "SLOWBRO", "SLOWKING", "STARYU", "STARMIE", "MAGMAR",
         "MAGBY", "PINSIR", "MARILL", "AZUMARILL", "AZURILL", "MISDREAVUS", "SNEASEL", "REMORAID",
         "OCTILLERY", "MANTINE"}
_ENTRY = re.compile(r"\{\s*&(\w+),\s*(\d+),\s*\{\s*(\d+),\s*(\d+),\s*(SPECIES_\w+)\s*\}\s*\}")


def _encounters():
    data = json.loads(WILD_JSON.read_text(encoding="utf-8"))
    return [e for g in data["wild_encounter_groups"] for e in g["encounters"]]


def _species_of(encs, version):
    return {m["species"] for e in encs if version in e["base_label"]
            for k in KINDS if k in e for m in e[k]["mons"]}


def _esperado():
    """(símbolo da tabela FR, slot, nível mín, nível máx, espécie LG) refeito do JSON."""
    encs = _encounters()
    fr_species = _species_of(encs, "FireRed")
    by_label = {e["base_label"]: e for e in encs}
    out = []
    for fr in encs:
        if "FireRed" not in fr["base_label"]:
            continue
        lg = by_label[fr["base_label"].replace("FireRed", "LeafGreen")]
        for kind, suffix in KINDS.items():
            if kind not in fr:
                continue
            for slot, (a, b) in enumerate(zip(fr[kind]["mons"], lg[kind]["mons"])):
                if a["species"] != b["species"] and b["species"] not in fr_species:
                    out.append((f"{fr['base_label']}_{suffix}", slot, b["min_level"],
                                b["max_level"], b["species"]))
    return out


def _gen_module():
    spec = importlib.util.spec_from_file_location("gen_swaps", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gerado():
    text = _gen_module().render(WILD_JSON)
    return text, [(m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5))
                  for m in _ENTRY.finditer(text)]


def _function_body(text: str, signature: str) -> str:
    start = re.search(re.escape(signature) + r"[^;{]*\)\s*\{", text).start()
    brace = text.index("{", start)
    depth, i = 0, brace
    while True:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[brace:i + 1]
        i += 1


# --- a tabela gerada ---------------------------------------------------------------------------

def test_tabela_gerada_bate_com_o_json():
    _, entries = _gerado()
    esperado = _esperado()
    assert len(entries) == len(set(entries)), "slot repetido na tabela gerada"
    assert sorted(entries) == sorted(esperado)
    assert len(esperado) > 300  # ~360 slots: se cair muito, o JSON ou a regra mudou


def test_tabela_gerada_e_const_e_so_firered():
    text, _ = _gerado()
    assert "const struct WildLeafGreenSwap gWildLeafGreenSwaps[]" in text
    assert "#ifdef FIRERED" in text
    assert "EWRAM_DATA" not in text


def test_so_especies_ausentes_das_tabelas_firered():
    encs = _encounters()
    fr = _species_of(encs, "FireRed")
    _, entries = _gerado()
    trocadas = {e[4] for e in entries}
    assert not trocadas & fr
    # toda espécie que só existe no LG entra em algum slot
    assert trocadas == _species_of(encs, "LeafGreen") - fr


def test_pares_conhecidos():
    _, entries = _gerado()
    idx = {(e[0], e[4]) for e in entries}
    assert ("sRoute4_FireRed_LandMonsInfo", "SPECIES_SANDSHREW") in idx
    assert ("sSafariZoneCenter_FireRed_LandMonsInfo", "SPECIES_PINSIR") in idx
    assert ("sSeafoamIslandsB3F_FireRed_WaterMonsInfo", "SPECIES_SLOWPOKE") in idx
    assert ("sCinnabarIsland_FireRed_FishingMonsInfo", "SPECIES_STARYU") in idx
    # Mt. Ember: o Magmar do LG vem com o nível do LG (38/40), não com o do Spearow do FR (30)
    magmar = sorted(e[1:4] for e in entries
                    if e[0] == "sMtEmberExterior_FireRed_LandMonsInfo" and e[4] == "SPECIES_MAGMAR")
    assert magmar == [(8, 38, 38), (10, 40, 40)]


def test_cli_gera_o_mesmo_header(tmp_path):
    out = tmp_path / "wild_encounters_leafgreen.h"
    subprocess.run([sys.executable, "-I", str(GEN_SCRIPT), str(WILD_JSON), str(out)], check=True)
    assert out.read_text(encoding="utf-8") == _gen_module().render(WILD_JSON)


def test_nenhum_mapa_perde_exclusivo_do_fr():
    """A troca é 50/50: cada espécie do FR continua no mapa com pelo menos metade da chance."""
    encs = _encounters()
    data = json.loads(WILD_JSON.read_text(encoding="utf-8"))
    rates = {f["type"]: f["encounter_rates"] for f in data["wild_encounter_groups"][0]["fields"]}
    trocados = {(e[0], e[1]) for e in _gerado()[1]}
    for fr in encs:
        if "FireRed" not in fr["base_label"]:
            continue
        for kind, suffix in KINDS.items():
            if kind not in fr:
                continue
            label = f"{fr['base_label']}_{suffix}"
            antes, depois = {}, {}
            for slot, m in enumerate(fr[kind]["mons"]):
                r = rates[kind][slot]
                antes[m["species"]] = antes.get(m["species"], 0) + r
                depois[m["species"]] = depois.get(m["species"], 0) + (r / 2 if (label, slot) in trocados else r)
            for sp, r in antes.items():
                assert depois[sp] >= r / 2 and depois[sp] > 0, (label, sp)


def _evolucoes():
    evos = []
    heads = list(re.finditer(r"\[(SPECIES_\w+)\]\s*=", EVO_H))
    for i, h in enumerate(heads):
        chunk = EVO_H[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(EVO_H)]
        for e in re.finditer(r"\{(EVO_\w+),\s*(\w+),\s*(SPECIES_\w+)\}", chunk):
            evos.append((h.group(1), e.group(1), e.group(2), e.group(3)))
    return evos


def _slots_vivos(entries):
    """Tira os slots de grama em que a tabela por horário (Hack 7) troca a espécie do FR nos 3
    períodos: lá o horário vem primeiro e a metade LG nunca sai."""
    time = json.loads((REPO_ROOT / "src" / "data" / "wild_encounters_time.json").read_text(encoding="utf-8"))
    by_map = {t["map"]: t for t in time["tables"]}
    encs = {e["base_label"]: e for e in _encounters()}
    vivos = []
    for e in entries:
        label = e[0].removesuffix("_LandMonsInfo")
        if label != e[0] and encs[label]["map"] in by_map:
            fr = encs[label]["land_mons"]["mons"][e[1]]["species"]
            t = by_map[encs[label]["map"]]
            if all(t[p][e[1]] != fr for p in ("morning", "day", "night")):
                continue
        vivos.append(e)
    return vivos


def test_slots_mortos_pelo_horario():
    _, entries = _gerado()
    vivos = _slots_vivos(entries)
    mortos = {(e[0], e[1]) for e in entries} - {(e[0], e[1]) for e in vivos}
    assert ("sRoute4_FireRed_LandMonsInfo", 2) in mortos
    assert ("sRoute23_FireRed_LandMonsInfo", 2) not in mortos  # Rota 23 não tem tabela por horário
    assert len(vivos) > 250


def test_especies_alvo_cobertas():
    """As 18 saem de um slot trocado que sai de verdade, de evolução (sem troca) ou da creche."""
    _, entries = _gerado()
    obt = {e[4] for e in _slots_vivos(entries)}
    evos = [e for e in _evolucoes() if e[1] not in ("EVO_TRADE", "EVO_TRADE_ITEM")]
    pre = {to: frm for frm, _, _, to in _evolucoes()}
    changed = True
    while changed:
        changed = False
        for frm, _, _, to in evos:
            if frm in obt and to not in obt:
                obt.add(to)
                changed = True
        for sp in list(obt):  # creche (Ditto é selvagem no FR): o bebê da linha
            if sp in pre and pre[sp] not in obt:
                obt.add(pre[sp])
                changed = True
    faltam = sorted(a for a in ALVOS if f"SPECIES_{a}" not in obt)
    assert not faltam, faltam


# --- o C ---------------------------------------------------------------------------------------

def test_header_declara_a_struct():
    assert "struct WildLeafGreenSwap" in WILD_H
    assert re.search(r"const struct WildPokemonInfo \*info;", WILD_H)
    assert re.search(r"struct WildPokemon mon;", WILD_H)


def test_c_inclui_o_header_gerado():
    assert '#include "data/wild_encounters_leafgreen.h"' in WILD_C
    assert WILD_C.count("EWRAM_DATA") == 2  # nenhum buffer novo


def test_sorteio_50_por_cento():
    body = _function_body(WILD_C, "static const struct WildPokemon *GetLeafGreenSlotMon(")
    assert "gWildLeafGreenSwaps" in body
    assert "Random() % 2" in body


def test_terra_agua_e_pedra_usam_a_troca_depois_do_horario():
    body = _function_body(WILD_C, "static bool8 TryGenerateWildMon(")
    i_time = body.index("GetTimeOfDayLandSpecies(")
    i_swap = body.index("GetLeafGreenSlotMon(")
    i_repel = body.index("IsWildLevelAllowedByRepel(")
    levels = [m.start() for m in re.finditer(r"ChooseWildMonLevel\(", body)]
    # Ordem do FRLG preservada fora dos slots trocados: nível da linha FR, depois o horário (o
    # RNG dos mapas sem troca fica igual ao de antes). Horário primeiro; a troca LG só quando o
    # horário manteve a espécie do slot; se sair a metade LG, o nível é sorteado de novo na linha
    # do LG. O Repel olha o nível final.
    assert len(levels) == 2
    assert levels[0] < i_time < i_swap < levels[1] < i_repel
    assert re.search(r"if \(lg != mon\)", body)
    assert re.search(r"level = ChooseWildMonLevel\(lg\)", body)


def test_pesca_usa_a_troca():
    body = _function_body(WILD_C, "static u16 GenerateFishingEncounter(")
    assert body.index("GetLeafGreenSlotMon(") < body.index("ChooseWildMonLevel(")
    assert re.search(r"ChooseWildMonLevel\(mon\)", body)


def test_pokedex_area_ve_a_troca():
    body = _function_body(AREA_C, "static bool32 IsSpeciesOnMap(")
    assert "IsLeafGreenSlotSpeciesOnMap(" in body


def test_pokedex_area_ignora_slot_que_o_horario_sempre_troca():
    """Na grama de um mapa com tabela por horário, a metade LG só vale se algum período mantém a
    espécie do FR no slot (Rota 4: o horário tira o Ekans nos 3 períodos, o Sandshrew nunca sai)."""
    body = _function_body(WILD_C, "bool8 IsLeafGreenSlotSpeciesOnMap(")
    assert "TimeTableKeepsLandSlot(" in body
    keeps = _function_body(WILD_C, "static bool8 TimeTableKeepsLandSlot(")
    assert "gWildMonTimeTables" in keeps


def test_makefile_gera_o_header():
    rules = (REPO_ROOT / "json_data_rules.mk").read_text(encoding="utf-8")
    assert "wild_encounters_leafgreen.h" in rules
    assert "tools/wild_leafgreen/gen_swaps.py" in rules
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "src/data/wild_encounters_leafgreen.h" in gitignore
