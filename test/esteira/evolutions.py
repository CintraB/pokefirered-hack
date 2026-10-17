"""Hack 3: as evoluções por troca viram evoluções por nível (37), algumas segurando um item.

Tabela única das regras pedidas pelo Cintra, usada pelo teste estático
(tests/test_evolucoes_estatico.py), pelo cenário do modo completo
(scenarios/full_evolutions.py) e pelas referências de tela (refs.py). Só dados e leitura de
fonte: nada aqui fala com o emulador.

No jogo: `EVO_LEVEL, 37` para os 4 sem item e `EVO_LEVEL_HOLD_ITEM, <item>` (nível fixo
`EVO_HOLD_ITEM_LEVEL` = 37, include/constants/pokemon.h) para os outros; o item segurado não é
consumido. Os 6 itens são vendidos na Celadon Dept. Store 4F por 2100 (como as pedras).
"""

import re
from dataclasses import dataclass
from pathlib import Path

HOLD_ITEM_LEVEL = 37


@dataclass(frozen=True)
class EvoRule:
    species: str          # SPECIES_*
    target: str           # SPECIES_*
    item: str | None      # ITEM_* que precisa estar segurado (None: só o nível)

    @property
    def method(self) -> str:
        return "EVO_LEVEL_HOLD_ITEM" if self.item else "EVO_LEVEL"

    @property
    def param(self) -> str:
        return self.item or str(HOLD_ITEM_LEVEL)

    @property
    def slug(self) -> str:
        """Nome curto do alvo para arquivos (ex.: 'porygon2')."""
        return self.target.removeprefix("SPECIES_").lower()


RULES: tuple[EvoRule, ...] = (
    EvoRule("SPECIES_KADABRA", "SPECIES_ALAKAZAM", None),
    EvoRule("SPECIES_HAUNTER", "SPECIES_GENGAR", None),
    EvoRule("SPECIES_MACHOKE", "SPECIES_MACHAMP", None),
    EvoRule("SPECIES_GRAVELER", "SPECIES_GOLEM", None),
    EvoRule("SPECIES_SLOWPOKE", "SPECIES_SLOWKING", "ITEM_KINGS_ROCK"),
    EvoRule("SPECIES_POLIWHIRL", "SPECIES_POLITOED", "ITEM_KINGS_ROCK"),
    EvoRule("SPECIES_ONIX", "SPECIES_STEELIX", "ITEM_METAL_COAT"),
    EvoRule("SPECIES_SCYTHER", "SPECIES_SCIZOR", "ITEM_METAL_COAT"),
    EvoRule("SPECIES_SEADRA", "SPECIES_KINGDRA", "ITEM_DRAGON_SCALE"),
    EvoRule("SPECIES_PORYGON", "SPECIES_PORYGON2", "ITEM_UP_GRADE"),
    EvoRule("SPECIES_CLAMPERL", "SPECIES_HUNTAIL", "ITEM_DEEP_SEA_TOOTH"),
    EvoRule("SPECIES_CLAMPERL", "SPECIES_GOREBYSS", "ITEM_DEEP_SEA_SCALE"),
)
SPECIES = tuple(dict.fromkeys(r.species for r in RULES))    # os 11, sem repetir o Clamperl
# itens que um desses Pokémon segurava para evoluir na troca (para conferir que a troca não
# evolui mais nem com eles)
OLD_TRADE_ITEMS: dict[str, tuple[str, ...]] = {
    s: tuple(r.item for r in RULES if r.species == s and r.item) for s in SPECIES}

# Telas da cena de evolução gravadas pelo cenário `evolucoes` (OUT/telas/<nome>_antes.png e
# _depois.png): uma por evolução das regras, mais o Slowbro (Slowpoke sem item), o Bellossom
# (Sun Stone), o Crobat (amizade) e o Steelix do "passou do 37 sem item" (nível 41). Não dependem
# do inicial: as referências ficam em test/referencias/COMUM/ (refs.py).
EVO_SHOTS = tuple(f"evo_{r.slug}" for r in RULES) + (
    "evo_slowbro", "evo_bellossom", "evo_crobat", "evo_steelix_nivel41")
SCREEN_POINTS = tuple(f"{name}_{when}" for name in EVO_SHOTS for when in ("antes", "depois"))

SHOP_LABEL = "CeladonCity_DepartmentStore_4F_Items"
SHOP_SCRIPT = Path("data/maps/CeladonCity_DepartmentStore_4F/scripts.inc")
SHOP_STONES = ("ITEM_FIRE_STONE", "ITEM_THUNDER_STONE", "ITEM_WATER_STONE", "ITEM_LEAF_STONE")
SHOP_NEW_ITEMS = ("ITEM_KINGS_ROCK", "ITEM_METAL_COAT", "ITEM_DRAGON_SCALE", "ITEM_UP_GRADE",
                  "ITEM_DEEP_SEA_TOOTH", "ITEM_DEEP_SEA_SCALE")
SHOP_PRICE = 2100

EVOLUTION_TABLE = Path("src/data/pokemon/evolution.h")
_ENTRY = re.compile(r"\{\s*(EVO_\w+)\s*,\s*(\w+)\s*,\s*(SPECIES_\w+)\s*\}")
_SPECIES_ROW = re.compile(r"\[(SPECIES_\w+)\]\s*=\s*\{(.*?)\}\s*\}\s*,", re.S)


def parse_evolution_table(text: str) -> dict[str, list[tuple[str, str, str]]]:
    """`gEvolutionTable` de src/data/pokemon/evolution.h: espécie -> [(método, parâmetro,
    alvo)] na ordem do arquivo (a ordem importa: no modo normal a última que casa vence)."""
    text = re.sub(r"//[^\n]*", "", text)
    table: dict[str, list[tuple[str, str, str]]] = {}
    for m in _SPECIES_ROW.finditer(text):
        table[m.group(1)] = _ENTRY.findall(m.group(2) + "}")
    return table


def load_evolution_table(repo: Path) -> dict[str, list[tuple[str, str, str]]]:
    return parse_evolution_table((repo / EVOLUTION_TABLE).read_text(encoding="utf-8"))


def parse_shop(text: str, label: str = SHOP_LABEL) -> list[str]:
    """Itens (`.2byte ITEM_*`) da lista `label` de um scripts.inc, sem o ITEM_NONE final."""
    m = re.search(rf"^{label}::\s*\n((?:\s*\.2byte\s+\w+\s*\n)+)", text, re.M)
    if m is None:
        raise ValueError(f"lista {label} não encontrada")
    items = re.findall(r"\.2byte\s+(\w+)", m.group(1))
    if not items or items[-1] != "ITEM_NONE":
        raise ValueError(f"lista {label} sem ITEM_NONE no fim: {items}")
    return items[:-1]
