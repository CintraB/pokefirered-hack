"""Hack 3 sem emulador: tabela de evoluções, método novo no C e a loja de Celadon 4F.

Confere os arquivos do repo contra a tabela única de esteira/evolutions.py (as regras pedidas
pelo Cintra): os 11 Pokémon que evoluíam por troca agora evoluem no nível 37 (alguns segurando
um item), nenhum evolui mais por troca, e os 6 itens estão à venda no 4F por 2100.
"""

import json
import re

import pytest

from esteira.evolutions import (EVOLUTION_TABLE, HOLD_ITEM_LEVEL, RULES, SHOP_NEW_ITEMS,
                                SHOP_PRICE, SHOP_SCRIPT, SHOP_STONES, SPECIES,
                                load_evolution_table, parse_evolution_table, parse_shop)
from esteira.scenarios import REPO_ROOT

TABLE = load_evolution_table(REPO_ROOT)
POKEMON_H = (REPO_ROOT / "include" / "constants" / "pokemon.h").read_text(encoding="utf-8")
POKEMON_C = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")


def _defines() -> dict[str, int]:
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"^#define\s+(EVO_\w+)\s+(\d+)\b", POKEMON_H, re.M)}


# --- leitura da tabela (o parser também é testado, para o resto não passar à toa) -------------

def test_parser_le_linhas_simples_e_multiplas_na_ordem():
    text = """
    const struct Evolution gEvolutionTable[NUM_SPECIES][EVOS_PER_MON] =
    {
        [SPECIES_A] = {{EVO_LEVEL, 16, SPECIES_B}},
        [SPECIES_C] = {{EVO_LEVEL, 37, SPECIES_D},  // comentário
                       {EVO_LEVEL_HOLD_ITEM, ITEM_X, SPECIES_E}},
    };
    """
    assert parse_evolution_table(text) == {
        "SPECIES_A": [("EVO_LEVEL", "16", "SPECIES_B")],
        "SPECIES_C": [("EVO_LEVEL", "37", "SPECIES_D"),
                      ("EVO_LEVEL_HOLD_ITEM", "ITEM_X", "SPECIES_E")],
    }


def test_tabela_real_lida_inteira():
    raw = (REPO_ROOT / EVOLUTION_TABLE).read_text(encoding="utf-8")
    assert len(TABLE) == raw.count("[SPECIES_") > 150
    assert TABLE["SPECIES_BULBASAUR"] == [("EVO_LEVEL", "16", "SPECIES_IVYSAUR")]


# --- as regras do Cintra -------------------------------------------------------------------------

@pytest.mark.parametrize("rule", RULES, ids=lambda r: f"{r.species}->{r.target}")
def test_regra_na_tabela(rule):
    assert (rule.method, rule.param, rule.target) in TABLE[rule.species]


@pytest.mark.parametrize("species", SPECIES)
def test_nenhum_dos_11_evolui_por_troca(species):
    methods = [method for method, _param, _target in TABLE[species]]
    assert not [m for m in methods if m.startswith("EVO_TRADE")], TABLE[species]


def test_nenhuma_evolucao_por_troca_sobrou_no_jogo():
    left = {s: e for s, e in TABLE.items() if any(m.startswith("EVO_TRADE") for m, _, _ in e)}
    assert left == {}


def test_entradas_exatas_dos_que_mudaram():
    """Nada além das regras: os 4 sem item só têm o nível 37, os de item só a entrada nova
    (Slowpoke e Poliwhirl mantêm Slowbro e Poliwrath)."""
    assert TABLE["SPECIES_KADABRA"] == [("EVO_LEVEL", "37", "SPECIES_ALAKAZAM")]
    assert TABLE["SPECIES_HAUNTER"] == [("EVO_LEVEL", "37", "SPECIES_GENGAR")]
    assert TABLE["SPECIES_MACHOKE"] == [("EVO_LEVEL", "37", "SPECIES_MACHAMP")]
    assert TABLE["SPECIES_GRAVELER"] == [("EVO_LEVEL", "37", "SPECIES_GOLEM")]
    assert TABLE["SPECIES_ONIX"] == [("EVO_LEVEL_HOLD_ITEM", "ITEM_METAL_COAT", "SPECIES_STEELIX")]
    assert TABLE["SPECIES_SCYTHER"] == [("EVO_LEVEL_HOLD_ITEM", "ITEM_METAL_COAT", "SPECIES_SCIZOR")]
    assert TABLE["SPECIES_SEADRA"] == [("EVO_LEVEL_HOLD_ITEM", "ITEM_DRAGON_SCALE", "SPECIES_KINGDRA")]
    assert TABLE["SPECIES_PORYGON"] == [("EVO_LEVEL_HOLD_ITEM", "ITEM_UP_GRADE", "SPECIES_PORYGON2")]
    assert TABLE["SPECIES_CLAMPERL"] == [
        ("EVO_LEVEL_HOLD_ITEM", "ITEM_DEEP_SEA_TOOTH", "SPECIES_HUNTAIL"),
        ("EVO_LEVEL_HOLD_ITEM", "ITEM_DEEP_SEA_SCALE", "SPECIES_GOREBYSS")]
    assert TABLE["SPECIES_POLIWHIRL"] == [
        ("EVO_ITEM", "ITEM_WATER_STONE", "SPECIES_POLIWRATH"),
        ("EVO_LEVEL_HOLD_ITEM", "ITEM_KINGS_ROCK", "SPECIES_POLITOED")]


def test_slowpoke_entrada_com_item_vem_depois_da_de_nivel():
    """No modo normal o laço não para na 1ª: a última que casa vence. Com King's Rock no 37
    as duas casam e tem que dar Slowking; sem item só a de nível (Slowbro)."""
    assert TABLE["SPECIES_SLOWPOKE"] == [
        ("EVO_LEVEL", "37", "SPECIES_SLOWBRO"),
        ("EVO_LEVEL_HOLD_ITEM", "ITEM_KINGS_ROCK", "SPECIES_SLOWKING")]


# --- método novo no C ----------------------------------------------------------------------------

def test_metodo_novo_definido_com_numero_livre_e_nivel_37():
    defines = _defines()
    methods = {k: v for k, v in defines.items()
               if not k.startswith(("EVO_MODE_", "EVOS_")) and k != "EVO_HOLD_ITEM_LEVEL"}
    assert "EVO_LEVEL_HOLD_ITEM" in methods
    assert len(set(methods.values())) == len(methods), methods      # nenhum número repetido
    assert methods["EVO_LEVEL_HOLD_ITEM"] == max(methods.values())  # o próximo livre
    assert defines["EVO_HOLD_ITEM_LEVEL"] == HOLD_ITEM_LEVEL == 37


def test_metodo_novo_tratado_no_modo_normal():
    body = POKEMON_C[POKEMON_C.index("u16 GetEvolutionTargetSpecies("):]
    normal = body[body.index("case EVO_MODE_NORMAL:"):body.index("case EVO_MODE_TRADE:")]
    case = normal[normal.index("case EVO_LEVEL_HOLD_ITEM:"):]
    case = case[:case.index("break;")]
    assert "EVO_HOLD_ITEM_LEVEL <= level" in case
    assert "param == heldItem" in case
    assert "SetMonData" not in case          # o item segurado não é consumido


# --- loja do 4F e preços -------------------------------------------------------------------------

def test_loja_do_4f_vende_os_6_itens_depois_das_pedras():
    items = parse_shop((REPO_ROOT / SHOP_SCRIPT).read_text(encoding="utf-8"))
    stones = items.index(SHOP_STONES[0])
    assert items[stones:stones + 4] == list(SHOP_STONES)
    assert items[stones + 4:] == list(SHOP_NEW_ITEMS)
    assert items[:stones] == ["ITEM_POKE_DOLL", "ITEM_RETRO_MAIL"]


def test_parser_da_loja_exige_terminador():
    with pytest.raises(ValueError):
        parse_shop("X_Items::\n\t.2byte ITEM_POKE_DOLL\n\trelease\n", "X_Items")


def test_precos_dos_6_itens_iguais_aos_das_pedras():
    data = json.loads((REPO_ROOT / "src" / "data" / "items.json").read_text(encoding="utf-8"))
    price = {i["itemId"]: i["price"] for i in data["items"]}
    assert {i: price[i] for i in SHOP_NEW_ITEMS} == {i: SHOP_PRICE for i in SHOP_NEW_ITEMS}
    assert {price[s] for s in SHOP_STONES} == {SHOP_PRICE}


# --- sem a trava da Dex Nacional (decisão do Cintra) --------------------------------------------

EVOLUTION_SCENE_C = (REPO_ROOT / "src" / "evolution_scene.c").read_text(encoding="utf-8")
PARTY_MENU_C = (REPO_ROOT / "src" / "party_menu.c").read_text(encoding="utf-8")


def _function(source: str, signature: str) -> str:
    """Corpo de uma função C (da assinatura até a `}` na coluna 0)."""
    start = source.index(signature + "\n{")   # a definição, não o protótipo
    return source[start:source.index("\n}\n", start)]


@pytest.mark.parametrize("task", ["static void Task_EvolutionScene(u8 taskId)",
                                  "static void Task_TradeEvolutionScene(u8 taskId)"])
def test_cena_de_evolucao_nao_cancela_especie_de_fora_de_kanto(task):
    body = _function(EVOLUTION_SCENE_C, task)
    assert "IsNationalPokedexEnabled" not in body
    assert "SPECIES_MEW" not in body


def test_pedra_de_evolucao_nao_e_recusada_sem_a_dex_nacional():
    body = _function(PARTY_MENU_C, "static void CB2_DoUseItemAnim(void)")
    assert "StartUseItemAnim_CantEvolve" not in body
    assert "MonCanEvolve" not in PARTY_MENU_C
    assert "KANTO_DEX_COUNT" not in PARTY_MENU_C


def test_registro_na_pokedex_ao_evoluir_continua_pelo_numero_nacional():
    """A cena marca vista/capturada pelo número nacional (cabe nas flags da Dex mesmo antes da
    Dex Nacional: o vetor tem o tamanho da Nacional)."""
    for task in ("static void Task_EvolutionScene(u8 taskId)",
                 "static void Task_TradeEvolutionScene(u8 taskId)"):
        body = _function(EVOLUTION_SCENE_C, task)
        for flag in ("FLAG_SET_SEEN", "FLAG_SET_CAUGHT"):
            assert (f"GetSetPokedexFlag(SpeciesToNationalPokedexNum(gTasks[taskId]."
                    f"tPostEvoSpecies), {flag})") in body


def test_modo_troca_sem_a_trava_da_dex_nacional():
    """Hack 4 (achado da revisão do Hack 3): o ramo EVO_MODE_TRADE de
    GetEvolutionTargetSpecies também não tem mais a trava (Scizor, Steelix... só com a Dex
    Nacional); hoje é código morto (nenhuma evolução por troca sobrou), mas não volta."""
    body = POKEMON_C[POKEMON_C.index("u16 GetEvolutionTargetSpecies("):]
    trade = body[body.index("case EVO_MODE_TRADE:"):body.index("case EVO_MODE_ITEM_USE:")]
    assert "IsNationalPokedexEnabled" not in trade
    assert "KANTO_SPECIES_END" not in trade
    item = trade[trade.index("case EVO_TRADE_ITEM:"):]
    assert "SetMonData(mon, MON_DATA_HELD_ITEM, &heldItem)" in item[:item.index("break;")]
