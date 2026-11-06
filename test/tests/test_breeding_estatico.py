"""Hack 6 sem emulador: regras, itens, ícones, loja e o modelo estatístico do breeding.

As probabilidades do C (include/constants/daycare.h) têm de ser as do design (esteira/breeding.py
SPEC); os 7 itens novos ocupam os slots vazios depois do Shiny Charm, com ícone próprio e preço;
a loja de Four Island vende os 8 itens de empurrão; e o modelo exato que o cenário `creche` usa
é conferido contra uma simulação independente das regras.
"""

import json
import random
import re
import struct

import pytest

from esteira import breeding as br
from esteira.check_text import ITEM_NAME_MAX_CHARS
from esteira.scenarios import REPO_ROOT
from esteira.scenarios.full_breeding import expected_evs

ITEMS = json.loads((REPO_ROOT / "src" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
BY_ID = {it["itemId"]: (slot, it) for slot, it in enumerate(ITEMS)}
DAYCARE_C = (REPO_ROOT / "src" / "daycare.c").read_text(encoding="utf-8")


def _defines(header: str) -> dict[str, int]:
    return br.header_defines(REPO_ROOT, header)


# --- as regras no C ---------------------------------------------------------------------------

def test_probabilidades_do_c_iguais_as_do_design():
    defines = _defines("daycare.h")
    assert {k: defines.get(k) for k in br.SPEC} == br.SPEC


def test_codificacao_das_naturezas_sobe_vezes_5_mais_desce():
    """InheritNature monta a natureza como sobe * 5 + desce: confere com sNatureStatTable."""
    text = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
    rows = re.findall(r"\[NATURE_(\w+)\]\s*=\s*\{([^}]*)\}", text)
    assert [name for name, _ in rows] == list(br.NATURES)
    for n, (_, row) in enumerate(rows):
        values = [int(v) for v in row.replace("+", "").split(",")]
        up, down = n // 5, n % 5
        if up == down:
            assert values == [0] * 5
        else:
            assert values[up] == 1 and values[down] == -1 and values.count(0) == 3


def test_ovo_usa_a_personalidade_com_rerolls_e_os_dois_pais():
    assert "SetInitialEggData(&egg, species, GetEggPersonality(species, father, mother));" in DAYCARE_C
    assert "return GetPlayerMonPersonality(nature, abilityNum);" in DAYCARE_C
    assert "offspringPersonality | (Random() << 16)" not in DAYCARE_C
    pokemon_c = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
    body = re.search(r"u32 GetPlayerMonPersonality\(u8 nature, u8 abilityNum\)\n\{(.*?)\n\}", pokemon_c, re.S).group(1)
    assert "GetShinyRerolls()" in body and "SHINY_ODDS" in body


def test_power_items_na_batalha():
    battle = (REPO_ROOT / "src" / "battle_main.c").read_text(encoding="utf-8")
    assert battle.count("holdEffect == HOLD_EFFECT_MACHO_BRACE || holdEffect == HOLD_EFFECT_POWER_ITEM") == 2
    pokemon_c = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
    assert "evIncrease += POWER_ITEM_EV_BONUS;" in pokemon_c


# --- itens -------------------------------------------------------------------------------------

@pytest.mark.parametrize("item", sorted(br.NEW_ITEMS))
def test_item_novo_no_slot_vazio_com_preco_e_efeito(item):
    want_slot, name = br.NEW_ITEMS[item]
    slot, it = BY_ID[item]
    assert slot == want_slot == _defines("items.h")[item]
    assert it["english"] == name and len(name) <= ITEM_NAME_MAX_CHARS
    assert it["price"] == br.PRICES[item]
    assert it["pocket"] == "POCKET_ITEMS" and it["importance"] == 0
    assert it["description_english"].count("\\n") == 2
    if item == "ITEM_DESTINY_KNOT":
        assert (it["holdEffect"], it["holdEffectParam"]) == ("HOLD_EFFECT_DESTINY_KNOT", 0)
    else:
        assert it["holdEffect"] == "HOLD_EFFECT_POWER_ITEM"
        assert it["holdEffectParam"] == br.POWER_ITEMS[item]


def test_param_dos_power_items_e_o_stat_do_jogo():
    stats = _defines("pokemon.h")
    assert [stats[f"STAT_{s}"] for s in ("HP", "ATK", "DEF", "SPEED", "SPATK", "SPDEF")] == list(range(6))


def test_everstone_reprecificada():
    _, it = BY_ID["ITEM_EVERSTONE"]
    assert it["price"] == br.PRICES["ITEM_EVERSTONE"] == 7000
    assert it["holdEffect"] == "HOLD_EFFECT_PREVENT_EVOLVE"


def test_quinze_dos_67_slots_vazios_usados():
    # 7 do Hack 6 + a Escama Prisma do Hack 7 (slot 60) + PC Portátil e Incubadora (61, 62) + DexNav (72, POK-47)
    # + as 4 rosas da Família Sombra (87 a 90, POK-51)
    assert sum(it["english"] == "????????" for it in ITEMS) == 67 - 15


@pytest.mark.parametrize("item", sorted(br.NEW_ITEMS))
def test_icone_proprio(item):
    table = (REPO_ROOT / "src" / "data" / "item_icon_table.h").read_text(encoding="utf-8")
    m = re.search(rf"\[{item}\]\s*=\s*\{{(\w+), (\w+)\}}", table)
    assert m and "QuestionMark" not in m.group(0)
    gfx = (REPO_ROOT / "src" / "data" / "graphics" / "items.h").read_text(encoding="utf-8")
    for symbol in m.groups():
        path = re.search(rf"const u32 {symbol}\[\] = INCBIN_U32\(\"([^\"]+)\"\);", gfx).group(1)
        source = REPO_ROOT / path.replace(".4bpp.lz", ".png").replace(".gbapal.lz", ".pal")
        assert source.is_file(), source
        raw = source.read_bytes()
        if source.suffix == ".png":
            width, height, depth, color = struct.unpack(">IIBB", raw[16:26])
            assert (width, height, depth, color) == (24, 24, 4, 3)   # 24x24, 4bpp indexado
        else:
            lines = raw.split(b"\r\n")
            assert lines[:3] == [b"JASC-PAL", b"0100", b"16"] and len(lines) == 20   # CRLF
            assert b"\n" not in raw.replace(b"\r\n", b"")


def test_loja_de_four_island_vende_os_itens_de_empurrao():
    text = (REPO_ROOT / br.SHOP_SCRIPT).read_text(encoding="utf-8")
    items = re.search(r"FourIsland_Mart_Items::\n(.*?)\.2byte ITEM_NONE", text, re.S).group(1)
    sold = re.findall(r"\.2byte (ITEM_\w+)", items)
    assert set(br.PRICES) <= set(sold)
    assert sold[:8] == ["ITEM_ULTRA_BALL", "ITEM_FULL_RESTORE", "ITEM_MAX_POTION", "ITEM_REVIVE",
                        "ITEM_ICE_HEAL", "ITEM_FULL_HEAL", "ITEM_ESCAPE_ROPE", "ITEM_MAX_REPEL"]


def test_precos_entre_7000_e_10000():
    assert all(7000 <= p <= 10000 for p in br.PRICES.values())


# --- configurações do cenário ----------------------------------------------------------------

def _tm_moves() -> set[str]:
    return {it.get("moveId") for it in ITEMS if it["pocket"] == "POCKET_TM_CASE"}


def _level_up_moves(species: str) -> set[str]:
    text = (REPO_ROOT / "src" / "data" / "pokemon" / "level_up_learnsets.h").read_text(encoding="utf-8")
    name = species.removeprefix("SPECIES_").title().replace("_", "")
    body = re.search(rf"s{name}LevelUpLearnset\[\] = \{{(.*?)\}};", text, re.S).group(1)
    return set(re.findall(r"LEVEL_UP_MOVE\(\s*\d+,\s*(MOVE_\w+)\)", body))


@pytest.mark.parametrize("config", br.CONFIGS, ids=lambda c: c.name)
def test_golpes_sondados_so_vem_pela_regra_dos_golpes_de_ovo(config):
    """Os golpes medidos são de ovo da espécie e não chegam por outro caminho (TM do pai ou golpe
    de nível que os dois sabem), senão a taxa de 60/40% não estaria sendo medida."""
    egg = set(br.egg_moves(REPO_ROOT, config.child))
    for move in config.probes:
        assert move in egg
        assert move not in _tm_moves()
        assert move not in _level_up_moves(config.child)
    # cabem: golpes do filhote no nível 5 + golpes de ovo sondados <= 4 + 1 (o 1º sai)
    assert len(config.probes) <= 3


@pytest.mark.parametrize("config", br.CONFIGS, ids=lambda c: c.name)
def test_pais_compativeis_e_papeis(config):
    f, m = config.father, config.mother
    assert f.gender in "M-" and m.gender in "F-"
    assert "SPECIES_DITTO" in (f.species, m.species) or (f.gender, m.gender) == ("M", "F")
    assert len(f.ivs) == len(m.ivs) == 6 and all(0 <= v <= 31 for v in f.ivs + m.ivs)
    assert len(struct.pack(br.PARENT_FORMAT, 1, 2, 3, 4, 5, 6, *f.ivs, 0, 0, 0)) == br.PARENT_SIZE == 24


def test_layout_da_struct_do_c():
    header = (REPO_ROOT / "include" / "test_hooks.h").read_text(encoding="utf-8")
    body = re.search(r"struct TestBreedParent\s*\{(.*?)\};", header, re.S).group(1)
    fields = re.findall(r"(u8|u16)\s+(\w+)(?:\[(\w+)\])?;", body)
    assert fields == [("u16", "species", ""), ("u16", "heldItem", ""), ("u16", "moves", "MAX_MON_MOVES"),
                      ("u8", "ivs", "NUM_STATS"), ("u8", "gender", ""), ("u8", "nature", ""),
                      ("u8", "abilityNum", ""), ("u8", "padding", "3")]
    assert re.search(r"#define TEST_BREED_BATCH (\d+)", header).group(1) == str(br.BATCH)
    assert br.BATCH * br.RECORD_SIZE <= 6 * 100        # cabe em gEnemyParty


# --- o modelo ---------------------------------------------------------------------------------

def test_distribuicoes_somam_1():
    for args in ((28, 4), (28, 4, True), (30, 2, False, True), (25, 9, False, True, True), (0, 31)):
        assert abs(sum(br.iv_distribution(*args)) - 1) < 1e-12
    for args in ((3, 5), (3, 5, True), (15, 13, True, True), (0, 24)):
        assert abs(sum(br.nature_distribution(*args)) - 1) < 1e-12


def test_numeros_do_design():
    """Os exemplos do documento: golpe de ovo 60/40/76%, habilidade 60/40, Everstone 70%."""
    assert br.egg_move_probability(True, False) == pytest.approx(0.60, abs=1e-3)
    assert br.egg_move_probability(False, True) == pytest.approx(0.40, abs=1e-3)
    assert br.egg_move_probability(True, True) == pytest.approx(0.76, abs=1e-3)
    assert br.ability_one_probability(True, 1, 0) == pytest.approx(0.05 + 0.9 * 0.6, abs=1e-3)
    assert br.ability_one_probability(True, None, 1) == pytest.approx(0.95, abs=1e-3)
    assert br.ability_one_probability(True, None, None) == 0.5
    assert br.ability_one_probability(False, 1, 1) is None
    nat = br.nature_distribution(3, 5, father_stone=True)
    assert nat[3] == pytest.approx(0.7 + 0.3 * (0.1 / 25 + 0.9 / 4), abs=1e-3)
    power = br.iv_distribution(30, 2, father_power=True)
    assert power[30] > 0.9


def _simulate_iv(rng, f, m, knot, fp, mp):
    """As regras de novo, escritas direto do design (sem o modelo): sorteio por sorteio."""
    if (fp or mp) and rng.random() < 0.9:
        return rng.choice([f, m]) if fp and mp else (f if fp else m)
    if rng.random() < 0.05:
        return rng.randrange(32)
    if rng.random() < 0.25:
        iv = (max(f, m) if knot else rng.choice([f, m])) + rng.randint(-2, 2)
    else:
        s = 1 if knot else 3
        iv = (f + m + 1) // 2 + rng.randint(-s, s)
    return min(max(iv, 0), 31)


def _simulate_nature(rng, f, m, fs, ms):
    if (fs or ms) and rng.random() < 0.7:
        return rng.choice([f, m]) if fs and ms else (f if fs else m)
    if rng.random() < 0.1:
        return rng.randrange(25)
    up, down = rng.choice([f, m]) // 5, rng.choice([f, m]) % 5
    return rng.randrange(5) * 6 if up == down else up * 5 + down


@pytest.mark.parametrize("args", [(28, 4, False, False, False), (28, 4, True, False, False),
                                  (30, 2, False, True, False), (25, 9, False, True, True),
                                  (31, 0, True, False, True)])
def test_modelo_de_iv_bate_com_simulacao(args):
    rng = random.Random(1234)
    n = 200_000
    counts = [0] * 32
    for _ in range(n):
        counts[_simulate_iv(rng, *args)] += 1
    _, _, p = br.chi_square(counts, br.iv_distribution(*args))
    assert p > 1e-4


@pytest.mark.parametrize("args", [(3, 5, False, False), (1, 10, True, False), (15, 13, True, True),
                                  (0, 12, False, False)])
def test_modelo_de_natureza_bate_com_simulacao(args):
    rng = random.Random(99)
    n = 200_000
    counts = [0] * 25
    for _ in range(n):
        counts[_simulate_nature(rng, *args)] += 1
    _, _, p = br.chi_square(counts, br.nature_distribution(*args))
    assert p > 1e-4


def test_qui_quadrado_reprova_distribuicao_errada():
    """O teste tem poder: 5% de mutação a mais ou o ±3 virando ±2 reprovam com o N do cenário."""
    rng = random.Random(7)
    n = 4096 * 6
    wrong = [0] * 32
    for _ in range(n):
        if rng.random() < 0.10:
            wrong[rng.randrange(32)] += 1
        else:
            wrong[_simulate_iv(rng, 28, 4, False, False, False)] += 1
    assert br.chi_square(wrong, br.iv_distribution(28, 4))[2] < br.CHI2_MIN_P
    narrow = [0] * 32
    for _ in range(n):
        if rng.random() < 0.05:
            narrow[rng.randrange(32)] += 1
        elif rng.random() < 0.25:
            narrow[min(max(rng.choice([28, 4]) + rng.randint(-2, 2), 0), 31)] += 1
        else:
            narrow[16 + rng.randint(-2, 2)] += 1
    assert br.chi_square(narrow, br.iv_distribution(28, 4))[2] < br.CHI2_MIN_P


def test_chi2_sf_valores_conhecidos():
    assert br.chi2_sf(3.841, 1) == pytest.approx(0.05, abs=1e-3)
    assert br.chi2_sf(18.307, 10) == pytest.approx(0.05, abs=1e-3)
    assert br.chi2_sf(52.191, 31) == pytest.approx(0.01, abs=1e-3)


def test_genero_natural_condicionado_ao_bit_da_habilidade():
    assert br.female_probability(127, None) == 127 / 256
    assert br.female_probability(127, 0) == 64 / 128
    assert br.female_probability(127, 1) == 63 / 128


def test_registro_do_ovo():
    word0 = 31 | 2 << 5 | 3 << 10 | 4 << 15 | 5 << 20 | 6 << 25 | 1 << 30 | 1 << 31
    word1 = 17 | 1 << 5 | 1 << 7 | 0b0101 << 8 | 19 << 16
    r = br.unpack_record(word0, word1)
    assert (r.ivs, r.ability, r.shiny, r.nature, r.gender, r.is_egg, r.probes, r.species) == (
        (31, 2, 3, 4, 5, 6), 1, True, 17, "F", True, (True, False, True, False), 19)


def test_evs_esperados_respeitam_os_limites():
    pidgey = (0, 0, 0, 1, 0, 0)
    assert expected_evs([0] * 6, pidgey, 1) == [0, 8, 0, 1, 0, 0]
    assert expected_evs([250, 0, 0, 0, 0, 0], pidgey, 0) == [255, 0, 0, 1, 0, 0]
    assert expected_evs([100, 100, 100, 100, 10, 100], pidgey, 4) == [100, 100, 100, 100, 10, 100]
    assert expected_evs([100, 100, 100, 100, 100, 5], pidgey, 5) == [100, 100, 100, 101, 100, 9]
    assert expected_evs([0] * 6, pidgey, None) == [0, 0, 0, 1, 0, 0]


# --- o sorteio da personalidade (RandomPersonalityWithNature em src/pokemon.c) ----------------

def _personality(nature: int, ability: int | None, low: int, k: int) -> int | None:
    """O sorteio do C, com os dois Random() dados: None quando o par (low, k) é redesenhado."""
    if ability is not None:
        low = (low & ~1) | ability
    first = ((nature + 25 - low % 25) * 16) % 25
    if k >= 2622 or first + 25 * k > 0xFFFF:
        return None
    return (first + 25 * k) << 16 | low


def test_sorteio_da_personalidade_no_c():
    text = (REPO_ROOT / "src" / "pokemon.c").read_text(encoding="utf-8")
    body = re.search(r"static u32 RandomPersonalityWithNature\(u8 nature, u8 abilityNum\)\n\{(.*?)\n\}", text, re.S).group(1)
    assert "first = ((nature + NUM_NATURES - low % NUM_NATURES) * 16) % NUM_NATURES;" in body
    assert "k = Random() & 0xFFF;" in body
    assert "while (k >= PERSONALITY_HIGH_SLOTS || first + NUM_NATURES * k > 0xFFFF);" in body
    assert "#define PERSONALITY_HIGH_SLOTS 2622" in text


@pytest.mark.parametrize("ability", [None, 0, 1])
def test_sorteio_acerta_natureza_e_habilidade_e_e_uniforme(ability):
    """Toda personalidade aceita tem a natureza e o bit pedidos, e cada personalidade com eles
    sai de exatamente um par (low, k): o sorteio (que redesenha o par inteiro) é uniforme."""
    rng = random.Random(5)
    for _ in range(20_000):
        nature = rng.randrange(25)
        pid = _personality(nature, ability, rng.randrange(65536), rng.randrange(4096))
        if pid is not None:
            assert pid % 25 == nature and (ability is None or pid & 1 == ability)
    # bijeção para uma natureza: nº de pares aceitos = nº de personalidades de 32 bits com ela
    nature = 7
    lows = range(65536) if ability is None else range(ability, 65536, 2)
    pairs = sum((0xFFFF - ((nature + 25 - low % 25) * 16) % 25) // 25 + 1 for low in lows)
    if ability is None:
        want = (2**32 - 1 - nature) // 25 + 1
    else:
        c = next(c for c in range(50) if c % 25 == nature and c % 2 == ability)
        want = (2**32 - 1 - c) // 50 + 1
    assert pairs == want


# --- preços de 5 dígitos na loja ------------------------------------------------------------

def test_lista_da_loja_mostra_precos_de_5_digitos():
    """BuyMenuPrintPriceInList convertia com 4 dígitos: 10000 virava "?0000". A lista agora
    usa SHOP_PRICE_DIGITS dígitos, e todo item à venda cabe; a janela de quantidade e a caixa
    de dinheiro (PrintMoneyAmount, 6 dígitos) cabem o total máximo (o dinheiro, até 999999)."""
    shop = (REPO_ROOT / "src" / "shop.c").read_text(encoding="utf-8")
    digits = int(re.search(r"#define SHOP_PRICE_DIGITS (\d+)", shop).group(1))
    body = re.search(r"static void BuyMenuPrintPriceInList\([^;]*?\)\n\{.*?\n\}", shop, re.S).group(0)
    assert "ConvertIntToDecimalStringN(gStringVar1, ItemId_GetPrice(item), STR_CONV_MODE_LEFT_ALIGN, SHOP_PRICE_DIGITS);" in body
    assert "padding = SHOP_PRICE_DIGITS - 1 - StringLength(gStringVar1);" in body
    assert max(it["price"] for it in ITEMS) < 10 ** digits
    money = (REPO_ROOT / "src" / "money.c").read_text(encoding="utf-8")
    assert "ConvertIntToDecimalStringN(gStringVar1, amount, STR_CONV_MODE_LEFT_ALIGN, 6);" in money
    assert "#define MAX_MONEY 999999" in money
