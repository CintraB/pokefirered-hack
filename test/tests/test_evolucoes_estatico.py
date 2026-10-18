"""Hack 3 sem emulador: tabela de evoluções, método novo no C e a loja de Celadon 4F.

Confere os arquivos do repo contra a tabela única de esteira/evolutions.py (as regras pedidas
pelo Cintra): os 11 Pokémon que evoluíam por troca agora evoluem no nível 37 (alguns segurando
um item), nenhum evolui mais por troca, e os 6 itens estão à venda no 4F por 2100.
"""

import json
import re
import struct

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
    assert methods["EVO_LEVEL_HOLD_ITEM"] == 16
    assert methods["EVO_LEVEL_UP_HOLD_ITEM"] == max(methods.values())  # o próximo livre (17)
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


# --- Hack 7 frente D: Espeon/Umbreon por horário e Milotic pela Escama Prisma --------------------

def _normal_mode() -> str:
    body = POKEMON_C[POKEMON_C.index("u16 GetEvolutionTargetSpecies("):]
    return body[body.index("case EVO_MODE_NORMAL:"):body.index("case EVO_MODE_TRADE:")]


def _case(normal: str, method: str) -> str:
    case = normal[normal.index(f"case {method}:"):]
    return case[:case.index("break;")]


def test_feebas_prism_scale():
    assert TABLE["SPECIES_FEEBAS"] == [("EVO_LEVEL_UP_HOLD_ITEM", "ITEM_PRISM_SCALE", "SPECIES_MILOTIC")]


def test_metodo_17_unico_e_maior():
    defines = _defines()
    methods = {k: v for k, v in defines.items()
               if not k.startswith(("EVO_MODE_", "EVOS_")) and k != "EVO_HOLD_ITEM_LEVEL"}
    assert methods["EVO_LEVEL_UP_HOLD_ITEM"] == 17 == max(methods.values())
    assert list(methods.values()).count(17) == 1
    case = _case(_normal_mode(), "EVO_LEVEL_UP_HOLD_ITEM")
    assert "param == heldItem" in case
    assert "EVO_HOLD_ITEM_LEVEL" not in case      # qualquer nível
    assert "SetMonData" not in case               # o item segurado não é consumido


def test_amizade_dia_e_noite_usam_o_relogio_novo():
    normal = _normal_mode()
    for method, neg in (("EVO_FRIENDSHIP_DAY", ""), ("EVO_FRIENDSHIP_NIGHT", "!")):
        case = _case(normal, method)
        assert f"friendship >= 220 && {neg}DayNight_IsDayPeriod(DayNight_GetPeriod())" in case
        assert "/*" not in case and "RtcCalcLocalTime" not in case


def test_prism_scale_item():
    items = json.loads((REPO_ROOT / "src" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
    it = items[60]
    assert it["itemId"] == "ITEM_PRISM_SCALE"
    assert it["english"] == "Escama Prisma" and len(it["english"]) < 14   # ITEM_NAME_LENGTH 14
    assert it["price"] == 7000
    assert (it["holdEffect"], it["holdEffectParam"]) == ("HOLD_EFFECT_NONE", 0)
    assert it["pocket"] == "POCKET_ITEMS" and it["importance"] == 0
    assert it["description_english"] == ("Uma escama misteriosa que\\nfaz certo Pokémon evoluir.\\n"
                                         "Brilha com as cores do arco-íris.")
    items_h = (REPO_ROOT / "include" / "constants" / "items.h").read_text(encoding="utf-8")
    assert re.search(r"#define ITEM_PRISM_SCALE 60\b", items_h) and "ITEM_03C" not in items_h
    table = (REPO_ROOT / "src" / "data" / "item_icon_table.h").read_text(encoding="utf-8")
    m = re.search(r"\[ITEM_PRISM_SCALE\]\s*=\s*\{(\w+), (\w+)\}", table)
    assert m and "QuestionMark" not in m.group(0)
    gfx = (REPO_ROOT / "src" / "data" / "graphics" / "items.h").read_text(encoding="utf-8")
    assert 'INCBIN_U32("graphics/items/icons/prism_scale.4bpp.lz")' in gfx
    assert 'INCBIN_U32("graphics/items/icon_palettes/prism_scale.gbapal.lz")' in gfx
    raw = (REPO_ROOT / "graphics/items/icons/prism_scale.png").read_bytes()
    assert struct.unpack(">IIBB", raw[16:26]) == (24, 24, 4, 3)
    pal = (REPO_ROOT / "graphics/items/icon_palettes/prism_scale.pal").read_bytes()
    assert pal.startswith(b"JASC-PAL\r\n0100\r\n16\r\n") and pal.count(b"\r\n") == 19
    shop = parse_shop((REPO_ROOT / "data/maps/FourIsland_Mart/scripts.inc").read_text(encoding="utf-8"),
                      "FourIsland_Mart_Items")
    assert "ITEM_PRISM_SCALE" in shop
    assert shop.index("ITEM_PRISM_SCALE") < shop.index("ITEM_EVERSTONE")  # os 8 do breeding ficam no fim


def test_eevee_sem_impossible():
    strings = (REPO_ROOT / "src" / "strings.c").read_text(encoding="utf-8")
    summary = (REPO_ROOT / "src" / "pokemon_summary_screen.c").read_text(encoding="utf-8")
    day_night = summary[summary.index("case EVO_FRIENDSHIP_DAY:"):summary.index("case EVO_BEAUTY:")]
    assert "EvoNotPossible" not in day_night
    assert ('gText_PokeSum_EvoLevelUpHoldItem[] = _("Subir nível + {STR_VAR_2} '
            '{RIGHT_ARROW_2} {STR_VAR_3}");') in strings


def test_loja_comporta_o_nome_da_escama_prisma():
    """Os nomes da lista da loja moram em buffers de 13 bytes na base: 'Escama Prisma' (13 letras +
    fim) estourava no nome da linha seguinte; o buffer agora é do tamanho do nome de item."""
    shop = (REPO_ROOT / "src" / "shop.c").read_text(encoding="utf-8")
    assert "(*sShopMenuItemStrings)[ITEM_NAME_LENGTH]" in shop
