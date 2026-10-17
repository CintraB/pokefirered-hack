"""Hack 6, breeding genético: as regras do filhote como modelo exato e a estatística da esteira.

As regras (docs/superpowers/specs/2026-10-17-breeding-genetico-design.md) estão aqui em forma de
distribuição de probabilidade EXATA: dado o par de pais (IVs, natureza, posição da habilidade,
golpes e item segurado), `iv_distribution`, `nature_distribution`, `ability_one_probability` e
`egg_move_probability` dizem quanto vale cada resultado do filhote, incluindo o viés mínimo do
`Random() % n` do jogo (65536 não é múltiplo de n). O cenário `creche`
(scenarios/full_breeding.py) gera milhares de ovos pelo caminho real da creche na build de teste
e compara a contagem com este modelo; os números das regras (SPEC) são conferidos contra
include/constants/daycare.h pelo pytest (tests/test_breeding_estatico.py), então o C não pode
mudar uma probabilidade sem a esteira perceber.

Estatística:
- proporções (taxa de golpe de ovo, habilidade, gênero, "natureza igual à do pai"...): faixa de
  ±Z_SIGMAS desvios-padrão da binomial;
- distribuições inteiras (os 32 valores de IV, as 25 naturezas): qui-quadrado de aderência, com
  as classes de esperado < 5 agrupadas, reprovando se p < CHI2_MIN_P;
- a taxa de shiny dos ovos usa ±3σ, como o teste de shiny existente (full_shiny.py).
"""

import math
import struct
from dataclasses import dataclass, field
from pathlib import Path

# --- as regras (percentuais), iguais às de include/constants/daycare.h ----------------------
SPEC = {
    "BREED_IV_POWER_ITEM_CHANCE": 90,
    "BREED_IV_MUTATION_CHANCE": 5,
    "BREED_IV_ONE_PARENT_CHANCE": 25,
    "BREED_IV_ONE_PARENT_SPREAD": 2,
    "BREED_IV_AVERAGE_SPREAD": 3,
    "BREED_IV_AVERAGE_SPREAD_KNOT": 1,
    "BREED_NATURE_EVERSTONE_CHANCE": 70,
    "BREED_NATURE_MUTATION_CHANCE": 10,
    "BREED_ABILITY_MUTATION_CHANCE": 10,
    "BREED_ABILITY_FATHER_CHANCE": 60,
    "BREED_EGG_MOVE_FATHER_CHANCE": 60,
    "BREED_EGG_MOVE_MOTHER_CHANCE": 40,
    "POWER_ITEM_EV_BONUS": 8,
}
PRICES = {"ITEM_EVERSTONE": 7000, "ITEM_DESTINY_KNOT": 10000, "ITEM_POWER_WEIGHT": 8000,
          "ITEM_POWER_BRACER": 8000, "ITEM_POWER_BELT": 8000, "ITEM_POWER_LENS": 8000,
          "ITEM_POWER_BAND": 8000, "ITEM_POWER_ANKLET": 8000}
NEW_ITEMS = {  # constante -> (slot, nome no jogo)
    "ITEM_DESTINY_KNOT": (53, "DESTINY KNOT"), "ITEM_POWER_WEIGHT": (54, "POWER WEIGHT"),
    "ITEM_POWER_BRACER": (55, "POWER BRACER"), "ITEM_POWER_BELT": (56, "POWER BELT"),
    "ITEM_POWER_LENS": (57, "POWER LENS"), "ITEM_POWER_BAND": (58, "POWER BAND"),
    "ITEM_POWER_ANKLET": (59, "POWER ANKLET"),
}
STATS = ("HP", "ATK", "DEF", "SPE", "SPA", "SPD")            # ordem do jogo (STAT_*)
POWER_ITEMS = {"ITEM_POWER_WEIGHT": 0, "ITEM_POWER_BRACER": 1, "ITEM_POWER_BELT": 2,
               "ITEM_POWER_ANKLET": 3, "ITEM_POWER_LENS": 4, "ITEM_POWER_BAND": 5}
SHOP_SCRIPT = "data/maps/FourIsland_Mart/scripts.inc"

NATURES = ("HARDY", "LONELY", "BRAVE", "ADAMANT", "NAUGHTY", "BOLD", "DOCILE", "RELAXED",
           "IMPISH", "LAX", "TIMID", "HASTY", "SERIOUS", "JOLLY", "NAIVE", "MODEST", "MILD",
           "QUIET", "BASHFUL", "RASH", "CALM", "GENTLE", "SASSY", "CAREFUL", "QUIRKY")
NUM_NATURES, NATURE_STATS, MAX_IV = 25, 5, 31
MON_MALE, MON_FEMALE, MON_GENDERLESS = 0x00, 0xFE, 0xFF

Z_SIGMAS = 4.0          # proporções: muitas checagens, 4σ mantém o falso vermelho < 0,5% no total
CHI2_MIN_P = 1e-5       # qui-quadrado
SHINY_SIGMAS = 3.0      # taxa de shiny dos ovos, como full_shiny.py
U16 = 65536


# --- o RNG do jogo: Random() é um u16 uniforme ------------------------------------------------
def mod_dist(n: int) -> list[float]:
    """Distribuição exata de Random() % n."""
    q, r = divmod(U16, n)
    return [(q + (1 if k < r else 0)) / U16 for k in range(n)]


def percent(p: int) -> float:
    """P(Random() % 100 < p), exato."""
    return sum(mod_dist(100)[:p])


def spread(width: int) -> list[tuple[int, float]]:
    """RandomSpread(width): Random() % (2w+1) - w."""
    return [(k - width, w) for k, w in enumerate(mod_dist(2 * width + 1))]


def _rules(spec: dict[str, int] = SPEC) -> dict[str, float]:
    return {
        "power": percent(spec["BREED_IV_POWER_ITEM_CHANCE"]),
        "iv_mut": percent(spec["BREED_IV_MUTATION_CHANCE"]),
        "one": percent(spec["BREED_IV_ONE_PARENT_CHANCE"]),
        "stone": percent(spec["BREED_NATURE_EVERSTONE_CHANCE"]),
        "nat_mut": percent(spec["BREED_NATURE_MUTATION_CHANCE"]),
        "ab_mut": percent(spec["BREED_ABILITY_MUTATION_CHANCE"]),
        "ab_father": percent(spec["BREED_ABILITY_FATHER_CHANCE"]),
        "move_father": percent(spec["BREED_EGG_MOVE_FATHER_CHANCE"]),
        "move_mother": percent(spec["BREED_EGG_MOVE_MOTHER_CHANCE"]),
    }


P = _rules()


# --- o modelo -------------------------------------------------------------------------------
def iv_distribution(father: int, mother: int, knot: bool = False, father_power: bool = False,
                    mother_power: bool = False) -> list[float]:
    """P(IV do filhote = v), v = 0..31, para um atributo (InheritIV em src/daycare.c)."""
    dist = [0.0] * (MAX_IV + 1)

    def add(center: int, width: int, weight: float) -> None:
        for delta, w in spread(width):
            dist[min(max(center + delta, 0), MAX_IV)] += weight * w

    for v, w in enumerate(mod_dist(MAX_IV + 1)):
        dist[v] += P["iv_mut"] * w
    one = (1 - P["iv_mut"]) * P["one"]
    if knot:
        add(max(father, mother), SPEC["BREED_IV_ONE_PARENT_SPREAD"], one)
    else:
        add(father, SPEC["BREED_IV_ONE_PARENT_SPREAD"], one / 2)
        add(mother, SPEC["BREED_IV_ONE_PARENT_SPREAD"], one / 2)
    width = SPEC["BREED_IV_AVERAGE_SPREAD_KNOT" if knot else "BREED_IV_AVERAGE_SPREAD"]
    add((father + mother + 1) // 2, width, (1 - P["iv_mut"]) * (1 - P["one"]))
    if father_power or mother_power:
        dist = [(1 - P["power"]) * w for w in dist]
        if father_power and mother_power:
            dist[father] += P["power"] / 2
            dist[mother] += P["power"] / 2
        else:
            dist[father if father_power else mother] += P["power"]
    return dist


def _raised(nature: int) -> int:
    return nature // NATURE_STATS


def _lowered(nature: int) -> int:
    return nature % NATURE_STATS


def nature_distribution(father: int, mother: int, father_stone: bool = False,
                        mother_stone: bool = False) -> list[float]:
    """P(natureza do filhote = n), n = 0..24 (InheritNature em src/daycare.c)."""
    dist = [P["nat_mut"] * w for w in mod_dist(NUM_NATURES)]
    neutral = mod_dist(NATURE_STATS)
    for up in (_raised(father), _raised(mother)):
        for down in (_lowered(father), _lowered(mother)):
            weight = (1 - P["nat_mut"]) / 4
            if up == down:
                for k, w in enumerate(neutral):
                    dist[k * (NATURE_STATS + 1)] += weight * w
            else:
                dist[up * NATURE_STATS + down] += weight
    if father_stone or mother_stone:
        dist = [(1 - P["stone"]) * w for w in dist]
        if father_stone and mother_stone:
            dist[father] += P["stone"] / 2
            dist[mother] += P["stone"] / 2
        else:
            dist[father if father_stone else mother] += P["stone"]
    return dist


def ability_one_probability(child_two_abilities: bool, father_slot: int | None,
                            mother_slot: int | None) -> float | None:
    """P(posição da habilidade do filhote = 1). `*_slot` None = pai de espécie com uma
    habilidade só (inclui o Ditto: "sem informação"). None se o filhote só tem uma."""
    if not child_two_abilities:
        return None
    if father_slot is None and mother_slot is None:
        return 0.5
    if father_slot is not None and mother_slot is not None:
        inherited = P["ab_father"] * father_slot + (1 - P["ab_father"]) * mother_slot
    else:
        inherited = father_slot if father_slot is not None else mother_slot
    return P["ab_mut"] * 0.5 + (1 - P["ab_mut"]) * inherited


def egg_move_probability(father_knows: bool, mother_knows: bool) -> float:
    """Chance de um golpe de ovo da espécie passar (60% do pai, 40% da mãe, independentes)."""
    miss = (1 - P["move_father"] if father_knows else 1) * (1 - P["move_mother"] if mother_knows else 1)
    return 1 - miss


def female_probability(gender_ratio: int, ability_slot: int | None) -> float:
    """P(fêmea) de um ovo de espécie com gênero, dada a posição da habilidade quando ela foi
    exigida (personality & 1, o mesmo bit do byte do gênero): personalidade uniforme entre as
    que cumprem natureza + habilidade, como no selvagem."""
    lows = range(256) if ability_slot is None else range(ability_slot, 256, 2)
    lows = list(lows)
    return sum(1 for low in lows if low < gender_ratio) / len(lows)


def mean_and_std(dist: list[float]) -> tuple[float, float]:
    mean = sum(v * w for v, w in enumerate(dist))
    var = sum((v - mean) ** 2 * w for v, w in enumerate(dist))
    return mean, math.sqrt(var)


# --- estatística ----------------------------------------------------------------------------
def z_score(hits: int, n: int, p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0 if hits == round(n * p) else math.inf
    return (hits - n * p) / math.sqrt(n * p * (1 - p))


def proportion_interval(n: int, p: float, sigmas: float = Z_SIGMAS) -> tuple[float, float]:
    mean, sigma = n * p, math.sqrt(n * p * (1 - p))
    return mean - sigmas * sigma, mean + sigmas * sigma


def _gammq(a: float, x: float) -> float:
    """Função gama incompleta regularizada superior Q(a, x) (Numerical Recipes)."""
    if x <= 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1:          # série para P(a, x)
        term = total = 1 / a
        ap = a
        for _ in range(10_000):
            ap += 1
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-15:
                break
        return 1 - total * math.exp(-x + a * math.log(x) - gln)
    b = x + 1 - a          # fração contínua para Q(a, x)
    c, d = 1 / 1e-300, 1 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_sf(stat: float, dof: int) -> float:
    """P(X² >= stat) com `dof` graus de liberdade."""
    return _gammq(dof / 2, stat / 2) if dof > 0 else 1.0


def chi_square(observed: list[int], probs: list[float]) -> tuple[float, int, float]:
    """Aderência de `observed` (contagens) a `probs`; classes de esperado < 5 são somadas
    (em ordem crescente de esperado) até passarem de 5. Resultado com esperado 0 que aparece
    vira p = 0. Devolve (X², graus de liberdade, p)."""
    n = sum(observed)
    if any(o > 0 and p == 0 for o, p in zip(observed, probs)):
        return math.inf, 0, 0.0
    cells = sorted(((p * n, o) for o, p in zip(observed, probs) if p > 0), key=lambda c: c[0])
    merged: list[list[float]] = []
    acc = [0.0, 0.0]
    for exp, obs in cells:
        acc[0] += exp
        acc[1] += obs
        if acc[0] >= 5:
            merged.append(acc)
            acc = [0.0, 0.0]
    if acc[0] > 0:
        if merged:
            merged[-1][0] += acc[0]
            merged[-1][1] += acc[1]
        else:
            merged.append(acc)
    stat = sum((obs - exp) ** 2 / exp for exp, obs in merged)
    dof = len(merged) - 1
    return stat, dof, chi2_sf(stat, dof)


# --- o lado C: struct TestBreedSetup e o registro de cada ovo (include/test_hooks.h) ---------
PARENT_FORMAT = "<HH4H6B3B3x"      # species, heldItem, moves[4], ivs[6], gender, nature, ability, padding[3]
PROBES_FORMAT = "<4H"
PARENT_SIZE = struct.calcsize(PARENT_FORMAT)
SETUP_SIZE = 2 * PARENT_SIZE + struct.calcsize(PROBES_FORMAT)
BATCH = 64                          # TEST_BREED_BATCH
RECORD_SIZE = 8


@dataclass(frozen=True)
class Record:
    ivs: tuple[int, ...]
    ability: int
    shiny: bool
    nature: int
    gender: str        # "M", "F", "-"
    is_egg: bool
    probes: tuple[bool, bool, bool, bool]
    species: int


def unpack_record(word0: int, word1: int) -> Record:
    return Record(
        ivs=tuple((word0 >> (5 * i)) & 31 for i in range(6)),
        ability=(word0 >> 30) & 1,
        shiny=bool(word0 >> 31),
        nature=word1 & 31,
        gender="MF-"[(word1 >> 5) & 3],
        is_egg=bool((word1 >> 7) & 1),
        probes=tuple(bool((word1 >> (8 + i)) & 1) for i in range(4)),
        species=word1 >> 16,
    )


def unpack_records(raw: bytes, count: int) -> list[Record]:
    words = struct.unpack_from(f"<{2 * count}I", raw)
    return [unpack_record(words[2 * i], words[2 * i + 1]) for i in range(count)]


# --- os pares de pais testados ------------------------------------------------------------
@dataclass(frozen=True)
class Parent:
    species: str
    gender: str                       # "M", "F" ou "-" (Ditto, sem gênero)
    nature: int
    ability: int = 0                  # posição (0/1); ignorada em espécie de uma habilidade
    ivs: tuple[int, ...] = (15,) * 6
    moves: tuple[str, ...] = ()
    item: str | None = None


@dataclass(frozen=True)
class Config:
    name: str
    what: str
    father: Parent
    mother: Parent
    eggs: int
    probes: tuple[str, ...] = ()
    child: str = "SPECIES_RATTATA"


def _n(name: str) -> int:
    return NATURES.index(name)


RATTATA, DITTO = "SPECIES_RATTATA", "SPECIES_DITTO"
HIGH, LOW = (28,) * 6, (4,) * 6
CONFIGS = (
    Config("base", "Rattata x Rattata sem item (IVs 28 x 4, Adamant x Bold)",
           Parent(RATTATA, "M", _n("ADAMANT"), 0, HIGH, ("MOVE_BITE", "MOVE_REVERSAL")),
           Parent(RATTATA, "F", _n("BOLD"), 1, LOW, ("MOVE_BITE", "MOVE_FLAME_WHEEL")),
           eggs=4096, probes=("MOVE_BITE", "MOVE_REVERSAL", "MOVE_FLAME_WHEEL")),
    Config("everstone_knot", "pai com Everstone, mãe com Destiny Knot (IVs cruzados 28/4)",
           Parent(RATTATA, "M", _n("LONELY"), 1, (28, 4, 28, 4, 28, 4), ("MOVE_SCREECH",),
                  "ITEM_EVERSTONE"),
           Parent(RATTATA, "F", _n("TIMID"), 0, (4, 28, 4, 28, 4, 28), ("MOVE_UPROAR",),
                  "ITEM_DESTINY_KNOT"),
           eggs=3072, probes=("MOVE_SCREECH", "MOVE_UPROAR")),
    Config("power_diff", "pai com Power Weight (HP), mãe com Power Anklet (Velocidade)",
           Parent(RATTATA, "M", _n("HARDY"), 1, (30,) * 6, item="ITEM_POWER_WEIGHT"),
           Parent(RATTATA, "F", _n("SERIOUS"), 1, (2,) * 6, item="ITEM_POWER_ANKLET"),
           eggs=3072),
    Config("power_same", "os dois com Power Belt (Defesa 25 x 9)",
           Parent(RATTATA, "M", _n("JOLLY"), 0, (25,) * 6, item="ITEM_POWER_BELT"),
           Parent(RATTATA, "F", _n("CALM"), 0, (9,) * 6, item="ITEM_POWER_BELT"),
           eggs=2048),
    Config("two_everstones", "os dois com Everstone (Modest x Jolly)",
           Parent(RATTATA, "M", _n("MODEST"), 0, HIGH, item="ITEM_EVERSTONE"),
           Parent(RATTATA, "F", _n("JOLLY"), 1, LOW, item="ITEM_EVERSTONE"),
           eggs=2048),
    Config("ditto_mother", "Rattata macho x Ditto (o Ditto é a mãe)",
           Parent(RATTATA, "M", _n("NAUGHTY"), 1, (31,) * 6, ("MOVE_COUNTER",)),
           Parent(DITTO, "-", _n("CALM"), 0, (0,) * 6, ("MOVE_TRANSFORM",)),
           eggs=2048, probes=("MOVE_COUNTER",)),
    Config("ditto_father", "Ditto x Rattata fêmea (o Ditto é o pai)",
           Parent(DITTO, "-", _n("QUIRKY"), 0, (20,) * 6, ("MOVE_TRANSFORM",)),
           Parent(RATTATA, "F", _n("RASH"), 0, (10,) * 6, ("MOVE_FURY_SWIPES",)),
           eggs=2048, probes=("MOVE_FURY_SWIPES",)),
    Config("single_ability_father", "Meowth macho (uma habilidade) x Rattata fêmea",
           Parent("SPECIES_MEOWTH", "M", _n("BRAVE"), 0, (16,) * 6, ("MOVE_BITE",)),
           Parent(RATTATA, "F", _n("MILD"), 1, (8,) * 6),
           eggs=2048, probes=("MOVE_BITE",)),
    Config("genderless_ditto", "Magnemite (sem gênero) x Ditto",
           Parent("SPECIES_MAGNEMITE", "-", _n("SASSY"), 1, (24,) * 6),
           Parent(DITTO, "-", _n("HASTY"), 0, (6,) * 6),
           eggs=1024, child="SPECIES_MAGNEMITE"),
)

EGG_SHINY_SAMPLES = 400_000
EGG_PERSONALITY_TRIALS = 256


# --- dados das espécies e golpes lidos do repo (para o modelo e o teste estático) -----------
def header_defines(repo: Path, *headers: str) -> dict[str, int]:
    """#define NOME número (decimal/hex) dos headers de include/constants."""
    import re
    out: dict[str, int] = {}
    for header in headers:
        text = (repo / "include" / "constants" / header).read_text(encoding="utf-8")
        for m in re.finditer(r"^#define\s+(\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", text, re.M):
            out.setdefault(m.group(1), int(m.group(2), 0))
    return out


@dataclass
class SpeciesInfo:
    gender_ratio: int
    abilities: tuple[str, str]
    ev_yield: tuple[int, ...] = field(default=(0,) * 6)

    @property
    def two_abilities(self) -> bool:
        return self.abilities[1] != "ABILITY_NONE"


def species_info(repo: Path, name: str) -> SpeciesInfo:
    import re
    text = (repo / "src" / "data" / "pokemon" / "species_info.h").read_text(encoding="utf-8")
    m = re.search(rf"\[{name}\]\s*=\s*\{{(.*?)\n    \}},", text, re.S)
    if m is None:
        raise KeyError(name)
    body = m.group(1)
    ratio = re.search(r"\.genderRatio\s*=\s*([^,\n]+),", body).group(1).strip()
    pf = re.fullmatch(r"PERCENT_FEMALE\((\d+(?:\.\d+)?)\)", ratio)
    if pf:
        gender_ratio = min(254, int(float(pf.group(1)) * 255 / 100))
    else:
        gender_ratio = {"MON_MALE": MON_MALE, "MON_FEMALE": MON_FEMALE,
                        "MON_GENDERLESS": MON_GENDERLESS}[ratio]
    abilities = tuple(a.strip() for a in
                      re.search(r"\.abilities\s*=\s*\{([^}]*)\}", body).group(1).split(","))
    keys = ("HP", "Attack", "Defense", "Speed", "SpAttack", "SpDefense")
    ev = tuple(int(re.search(rf"\.evYield_{k}\s*=\s*(\d+)", body).group(1)) for k in keys)
    return SpeciesInfo(gender_ratio, (abilities + ("ABILITY_NONE",))[:2], ev)


def egg_moves(repo: Path, species: str) -> list[str]:
    import re
    text = (repo / "src" / "data" / "pokemon" / "egg_moves.h").read_text(encoding="utf-8")
    m = re.search(rf"egg_moves\({species.removeprefix('SPECIES_')},\s*(.*?)\)", text, re.S)
    return [] if m is None else [mv.strip() for mv in m.group(1).split(",") if mv.strip()]

# telas da loja de Four Island (cenário `ovo`), com referência em test/referencias/COMUM/: a
# lista com o cursor no Destiny Knot (preço de 5 dígitos) e a janela de quantidade dele
SHOP_SCREEN_POINTS = ("loja_four_island", "loja_four_island_quantidade")
SHOP_MONEY = 50_000
