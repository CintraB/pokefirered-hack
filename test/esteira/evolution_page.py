"""Hack 4: a página EVOLUTION do resumo do Pokémon (4ª página, depois de KNOWN MOVES).

O jogo monta o texto em `GetEvolutionPageText` (src/pokemon_summary_screen.c) a partir de
`gEvolutionTable`: uma linha por entrada da espécie, na ordem da tabela, ou "Does not evolve.".
Este módulo gera, de forma independente, o texto ESPERADO a partir dos fontes
(src/data/pokemon/evolution.h, src/data/text/species_names.h, src/data/items.json) e o
codifica com o charmap do jogo, para comparar byte a byte com o que a build de teste devolve
(hooks.Mailbox.evolution_text). Também mede a largura de cada linha com a tabela de larguras
da fonte, contra a janela da página.

Formatos (➡ = {RIGHT_ARROW_2}, "Lv" = {LV_2}, os glifos do jogo):
    EVO_LEVEL / EVO_LEVEL_NINJASK   Lv 16 ➡ IVYSAUR
    EVO_ITEM                        FIRE STONE ➡ ARCANINE
    EVO_LEVEL_HOLD_ITEM             Lv 37 + METAL COAT ➡ STEELIX   (nível fixo 37 do Hack 3)
    EVO_FRIENDSHIP                  High friendship ➡ CROBAT
    EVO_LEVEL_UP_HOLD_ITEM          Subir nível + Escama Prisma ➡ MILOTIC   (Hack 7, qualquer nível)
    EVO_FRIENDSHIP_DAY / _NIGHT     Day friendship ➡ ESPEON   (Hack 7: relógio do jogo, sem sufixo)
    EVO_BEAUTY                      High beauty ➡ X (R/S/E only; nenhuma espécie usa mais)
    EVO_LEVEL_ATK_GT/EQ/LT_DEF      Lv 20, ATK > DEF ➡ HITMONLEE
    EVO_LEVEL_SILCOON / _CASCOON    Lv 7 (random) ➡ SILCOON
    EVO_LEVEL_SHEDINJA              Lv 20, free slot ➡ SHEDINJA
    EVO_TRADE / EVO_TRADE_ITEM      Trade ➡ X / Trade + ITEM ➡ X   (não sobrou nenhuma no jogo)
Dia/noite (Hack 7): o relógio do jogo decide (DayNight_IsDayPeriod), então Eevee mostra Espeon e
Umbreon sem sufixo; Feebas evolui com a Escama Prisma. "R/S/E only": nada no FireRed sobe a beleza (sem Pokéblocks;
MON_DATA_BEAUTY só é escrito ao copiar dados de batalha por link), mas um Feebas trazido de
Ruby/Sapphire/Emerald com beleza alta evolui ao subir de nível (o método continua no jogo).
"""

import json
import re
from pathlib import Path

from .charmap import Charmap
from .check_text import _load_widths
from .evolutions import EVOLUTION_TABLE, HOLD_ITEM_LEVEL, load_evolution_table

LV = "{LV_2}"
ARROW = "{RIGHT_ARROW_2}"
NOT_POSSIBLE = " (impossible)"
TRADED_ONLY = " (R/S/E only)"
NO_EVOLUTION = "Does not evolve."
# sufixo das evoluções que o jogo sozinho não dispara
SUFFIXES = {"EVO_BEAUTY": TRADED_ONLY}

# Janela do texto: sWindowTemplates_Evolution[0] (.tilemapLeft = 1, .width = 28 tiles) e o texto
# em x = EVOLUTION_PAGE_TEXT_X = 2 (src/pokemon_summary_screen.c); 13 tiles de altura com 16 px
# por linha (14 da fonte + EVOLUTION_PAGE_LINE_SPACING = 2) a partir de y = 3: cabem 6 linhas.
WINDOW_WIDTH_PX = 28 * 8
TEXT_X = 2
LINE_WIDTH_PX = WINDOW_WIDTH_PX - TEXT_X
MAX_LINES = 6
SOURCE_REF = ("janela sWindowTemplates_Evolution[0] de 28 tiles, texto em x = EVOLUTION_PAGE_TEXT_X = 2, "
              "src/pokemon_summary_screen.c")

SUMMARY_HEADER = Path("include/pokemon_summary_screen.h")
SPECIES_NAMES = Path("src/data/text/species_names.h")
ITEMS_JSON = Path("src/data/items.json")
SOURCE_FILES = (EVOLUTION_TABLE, SPECIES_NAMES, ITEMS_JSON, Path("charmap.txt"), Path("src/text.c"),
                Path("include/constants/species.h"))
POKEMON_NAME_LENGTH = 10          # GetSpeciesName copia no máximo isso (include/constants/global.h)

# Cenário `resumo_evolucao` (scenarios/full_summary_evolution.py): o time de teste, nesta ordem
# nos slots 0-4 (o 5 é um ovo), e a tela da página EVOLUTION de cada um em
# OUT/telas/resumo_evo_<nome>.png (não dependem do inicial: referências em COMUM, refs.py).
SHOWCASE = ("SPECIES_EEVEE", "SPECIES_ONIX", "SPECIES_SLOWPOKE", "SPECIES_BULBASAUR",
            "SPECIES_TAUROS")
SCREEN_POINTS = tuple(f"resumo_evo_{s.removeprefix('SPECIES_').lower()}" for s in SHOWCASE)
# As outras páginas do Eevee, pelos 4 pontos de página novos do cabeçalho (e o título
# "POKéMON SKILLS", que termina a 2 px do 1º ponto)
PAGE_POINTS = ("resumo_pag_skills", "resumo_pag_moves", "resumo_pag_detalhe")

NEWLINE = 0xFE                    # '\n' no charmap
EXTRA_SYMBOL = 0xF9               # {LV_2}, {RIGHT_ARROW_2}: F9 xx, largura = tabela[0x100 | xx]
EOS = 0xFF


def evolution_line(method: str, param: str, target: str, species_names: dict[str, str],
                   item_names: dict[str, str]) -> str | None:
    """Uma linha da página (com os placeholders {LV_2}/{RIGHT_ARROW_2}); None para método vazio."""
    name = species_names[target][:POKEMON_NAME_LENGTH]
    lines = {
        "EVO_LEVEL": lambda: f"{LV} {param} {ARROW} {name}",
        "EVO_LEVEL_NINJASK": lambda: f"{LV} {param} {ARROW} {name}",
        "EVO_ITEM": lambda: f"{item_names[param]} {ARROW} {name}",
        "EVO_LEVEL_HOLD_ITEM": lambda: f"{LV} {HOLD_ITEM_LEVEL} + {item_names[param]} {ARROW} {name}",
        "EVO_LEVEL_UP_HOLD_ITEM": lambda: f"Subir nível + {item_names[param]} {ARROW} {name}",
        "EVO_FRIENDSHIP": lambda: f"High friendship {ARROW} {name}",
        "EVO_FRIENDSHIP_DAY": lambda: f"Day friendship {ARROW} {name}",
        "EVO_FRIENDSHIP_NIGHT": lambda: f"Night friendship {ARROW} {name}",
        "EVO_BEAUTY": lambda: f"High beauty {ARROW} {name}",
        "EVO_LEVEL_ATK_GT_DEF": lambda: f"{LV} {param}, ATK > DEF {ARROW} {name}",
        "EVO_LEVEL_ATK_EQ_DEF": lambda: f"{LV} {param}, ATK = DEF {ARROW} {name}",
        "EVO_LEVEL_ATK_LT_DEF": lambda: f"{LV} {param}, ATK < DEF {ARROW} {name}",
        "EVO_LEVEL_SILCOON": lambda: f"{LV} {param} (random) {ARROW} {name}",
        "EVO_LEVEL_CASCOON": lambda: f"{LV} {param} (random) {ARROW} {name}",
        "EVO_LEVEL_SHEDINJA": lambda: f"{LV} {param}, free slot {ARROW} {name}",
        "EVO_TRADE": lambda: f"Trade {ARROW} {name}",
        "EVO_TRADE_ITEM": lambda: f"Trade + {item_names[param]} {ARROW} {name}",
    }
    if method not in lines:
        return None
    line = lines[method]()
    return line + SUFFIXES.get(method, "")


def page_text(entries: list[tuple[str, str, str]], species_names: dict[str, str],
              item_names: dict[str, str]) -> str:
    """O texto da página para as entradas (método, parâmetro, alvo) de uma espécie."""
    lines = [line for method, param, target in entries
             if (line := evolution_line(method, param, target, species_names, item_names))]
    return "\n".join(lines) if lines else NO_EVOLUTION


def load_species_names(repo: Path) -> dict[str, str]:
    """SPECIES_X -> nome (src/data/text/species_names.h)."""
    text = (repo / SPECIES_NAMES).read_text(encoding="utf-8")
    return {m.group(1): m.group(2).replace('\\"', '"')
            for m in re.finditer(r'\[(SPECIES_\w+)\]\s*=\s*_\("((?:[^"\\]|\\.)*)"\)', text)}


def load_item_names(repo: Path) -> dict[str, str]:
    """ITEM_X -> nome (campo "english" de src/data/items.json)."""
    data = json.loads((repo / ITEMS_JSON).read_text(encoding="utf-8"))
    return {item["itemId"]: item["english"] for item in data["items"]}


def text_size(repo: Path) -> int:
    """SUMMARY_PAGE_TEXT_SIZE (include/pokemon_summary_screen.h), com o terminador."""
    m = re.search(r"#define\s+SUMMARY_PAGE_TEXT_SIZE\s+(\d+)",
                  (repo / SUMMARY_HEADER).read_text(encoding="utf-8"))
    return int(m.group(1))


class EvolutionPage:
    """Textos esperados da página para todas as espécies, já codificados para o jogo."""

    def __init__(self, repo: Path, consts):
        self.repo = Path(repo)
        self.consts = consts
        self.table = load_evolution_table(self.repo)
        self.species_names = load_species_names(self.repo)
        self.item_names = load_item_names(self.repo)
        self.charmap = Charmap.load(str(self.repo))
        self._codes = _charmap_codes(self.repo)
        self._widths = _load_widths(self.repo)

    def valid_species(self) -> list[str]:
        """SPECIES_* de 1 a SPECIES_CHIMECHO, sem as OLD_UNOWN_* (a primeira constante de cada id)."""
        last = self.consts.species("SPECIES_CHIMECHO")
        names = [self.consts.species_name(i) for i in range(1, last + 1)]
        return [n for n in names if not n.startswith("SPECIES_OLD_UNOWN_")]

    def text(self, species: str) -> str:
        return page_text(self.table.get(species, []), self.species_names, self.item_names)

    def encode(self, text: str) -> bytes:
        """Codifica com o charmap, inclusive os placeholders {NOME} (sem terminador)."""
        out = bytearray()
        for token in re.findall(r"\{[A-Z_0-9]+\}|.", text, re.S):
            if token.startswith("{") and len(token) > 1:
                out += self._codes[token[1:-1]]
            else:
                out += self.charmap.encode(token)
        return bytes(out)

    def decode(self, data: bytes) -> str:
        """Leitura do texto do jogo (para mensagens): F9 xx vira {NOME}, \\n vira ' / '."""
        names = {code: name for name, code in self._codes.items() if len(code) == 2}
        out, i = [], 0
        while i < len(data) and data[i] != EOS:
            if data[i] == EXTRA_SYMBOL and i + 1 < len(data):
                out.append("{" + names.get(bytes(data[i:i + 2]), f"F9 {data[i + 1]:02X}") + "}")
                i += 2
                continue
            out.append(" / " if data[i] == NEWLINE else self.charmap.decode(bytes([data[i]])))
            i += 1
        return "".join(out)

    def line_widths(self, data: bytes) -> list[int]:
        """Largura em px de cada linha do texto codificado (FONT_NORMAL, sem espaçamento extra)."""
        widths, width, i = [], 0, 0
        while i < len(data) and data[i] != EOS:
            b = data[i]
            if b == NEWLINE:
                widths.append(width)
                width = 0
            elif b == EXTRA_SYMBOL:
                i += 1
                width += self._widths[0x100 | data[i]]
            else:
                width += self._widths[b]
            i += 1
        widths.append(width)
        return widths


def _charmap_codes(repo: Path) -> dict[str, bytes]:
    """Nomes do charmap (`LV_2 = F9 05`) -> bytes."""
    codes: dict[str, bytes] = {}
    for line in (repo / "charmap.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*((?:[0-9A-Fa-f]{2}\s*)+?)\s*(?:@.*)?$",
                     line.strip())
        if m:
            codes.setdefault(m.group(1), bytes.fromhex(m.group(2).replace(" ", "")))
    return codes


def check_page_widths(repo: Path, consts) -> list[tuple[str, str, int]]:
    """(espécie, linha, px) de toda linha da página mais larga que LINE_WIDTH_PX, de toda espécie."""
    page = EvolutionPage(repo, consts)
    wide = []
    for species in page.valid_species():
        text = page.text(species)
        for line, px in zip(text.split("\n"), page.line_widths(page.encode(text))):
            if px > LINE_WIDTH_PX:
                wide.append((species, line, px))
    return wide


# --- Hack 7 - frente D: linha de amizade, sempre a 6ª da página (y = EVOLUTION_PAGE_TEXT_Y + 5 * 16) ---
# GetFriendshipLineText (src/pokemon_summary_screen.c): "<corações> <n>/255 <frase><marca>"
HEART = "{EMOJI_HEART}"
FRIENDSHIP_PHRASES = ("Odeia você", "Te encara feio", "Ainda desconfia", "Pegando confiança",
                      "Amigável", "Muito feliz", "Ama você!")
FRIENDSHIP_MARK = " (220+)"
FRIENDSHIP_MARK_FROM = 220          # amizade que faz o Eevee evoluir (EVO_FRIENDSHIP_*)
FRIENDSHIP_LINE_SIZE = 48           # FRIENDSHIP_LINE_SIZE do C (buffer na pilha), com o terminador
FRIENDSHIP_SCREEN_POINTS = ("resumo_amizade_eevee",)
# primeira amizade de cada faixa (0-6 corações)
FRIENDSHIP_BAND_STARTS = (0, 1, 50, 100, 150, 200, 255)


def friendship_hearts(friendship: int) -> int:
    return max(i for i, start in enumerate(FRIENDSHIP_BAND_STARTS) if friendship >= start)


def friendship_line(friendship: int) -> str:
    """O texto esperado da linha de amizade (com o placeholder {EMOJI_HEART})."""
    hearts = friendship_hearts(friendship)
    return (HEART * hearts + (" " if hearts else "") + f"{friendship}/255 "
            + FRIENDSHIP_PHRASES[hearts]
            + (FRIENDSHIP_MARK if friendship >= FRIENDSHIP_MARK_FROM else ""))
