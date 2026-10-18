"""Glossário de máquina da tradução PT-BR e a busca da regra `glossario` da checagem de texto.

`glossario.json` (ao lado deste arquivo) vem do glossário aprovado
(docs/superpowers/specs/2026-10-18-traducao-glossario.md, fora do Git, com as decisões da §6):

  termos     [{en, pt, fonte, categoria, detectar, obs?, completo?, tela?}]: termo como o jogo
             inglês escreve -> termo PT-BR do glossário. `detectar` = o termo inglês é procurado
             nos textos traduzidos (só os escritos como no jogo, em maiúsculas: "POKé BALL",
             "PALLET TOWN"; palavras comuns como "move" colidem com português e ficam de fora).
  proibidos  [{variante, use, motivo}]: grafias que não podem aparecer em texto traduzido.

A busca (`Glossary.problems`) roda só em texto que mudou em relação à base inglesa (check_text):
o inglês que ainda não foi traduzido é assunto da regra `ingles`.

Termo novo criado por uma frente entra em `termos` com fonte "criado" (bloco da frente, só
acréscimo). Regenerar do Markdown (`python3 -m esteira.glossario gerar <md>`) descarta esses
acréscimos: só a Task 1/integração regenera.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

GLOSSARY_PATH = Path(__file__).with_name("glossario.json")

_LETTER = "0-9A-Za-zÀ-ÖØ-öø-ÿ"
_PLACEHOLDER = re.compile(r"\{[^}]*\}")
_BREAK = re.compile(r"\\[nlp]")


def _pattern(term: str, plural: bool = False) -> re.Pattern:
    tail = "s?" if plural else ""
    return re.compile(rf"(?<![{_LETTER}]){re.escape(term)}{tail}(?![{_LETTER}])")


@dataclass
class _Check:
    pattern: re.Pattern
    what: str          # "termo proibido" ou "termo do glossário em inglês"
    use: str           # o que usar no lugar

    def message(self, found: str) -> str:
        return f"{self.what} '{found}' (use '{self.use}')"


class Glossary:
    def __init__(self, data: dict):
        self.data = data
        forbidden = sorted(data.get("proibidos", []), key=lambda p: -len(p["variante"]))
        self._forbidden = [_Check(_pattern(p["variante"], plural=True), "termo proibido", p["use"])
                           for p in forbidden]
        by_en: dict[str, list[str]] = {}
        for t in data.get("termos", []):
            if not t.get("detectar"):
                continue
            en = _PLACEHOLDER.sub("", t["en"]).strip()
            # a grafia do jogo ("PALLET TOWN") e, nos termos de mais de uma palavra, a mista
            # ("Pallet Town"), quando ela não é a própria tradução ("S.S. Anne", "Silph Co.")
            title = en.title()
            for variant in (en, title) if " " in en and title not in (en, t["pt"]) else (en,):
                pts = by_en.setdefault(variant, [])
                if t["pt"] not in pts:
                    pts.append(t["pt"])
        self._english = [_Check(_pattern(en), "termo do glossário em inglês", "' ou '".join(pts))
                         for en, pts in sorted(by_en.items(), key=lambda kv: -len(kv[0]))]

    def problems(self, text: str) -> list[str]:
        """Variantes proibidas e termos ingleses do glossário presentes no texto cru."""
        plain = _BREAK.sub(" ", _PLACEHOLDER.sub(" ", text))
        taken: list[tuple[int, int]] = []
        found: list[str] = []
        for check in self._forbidden + self._english:
            for m in check.pattern.finditer(plain):
                if any(m.start() < end and start < m.end() for start, end in taken):
                    continue
                taken.append((m.start(), m.end()))
                message = check.message(m.group(0))
                if message not in found:
                    found.append(message)
        return found


@lru_cache(maxsize=4)
def _load_cached(path: str, mtime: float) -> Glossary:
    return Glossary(json.loads(Path(path).read_text(encoding="utf-8")))


def load(path: Path = GLOSSARY_PATH) -> Glossary:
    return _load_cached(str(path), Path(path).stat().st_mtime)


# ---- gerador a partir do glossário aprovado (Markdown) -------------------------------------

_SECTIONS = {"2.1": "tipo", "2.2": "status", "2.3": "natureza", "2.4": "batalha", "2.5": "habilidade",
             "2.6": "golpe", "2.7": "item", "2.8": "lugar", "2.9": "personagem", "2.10": "interface"}

# Frutas da 3ª geração na ordem do jogo; "demais frutas (Figy … Enigma)" = da FIGY em diante,
# menos as 5 que o GO traduziu (linhas próprias)
_BERRIES = ("CHERI CHESTO PECHA RAWST ASPEAR LEPPA ORAN PERSIM LUM SITRUS FIGY WIKI MAGO AGUAV IAPAPA "
            "RAZZ BLUK NANAB WEPEAR PINAP POMEG KELPSY QUALOT HONDEW GREPA TAMATO CORNN MAGOST RABUTA "
            "NOMEL SPELON PAMTRE WATMEL DURIN BELUE LIECHI GANLON SALAC PETAYA APICOT LANSAT STARF ENIGMA").split()
_GO_BERRIES = {"RAZZ", "BLUK", "NANAB", "WEPEAR", "PINAP"}
_NUMBERS_PT = ("Um", "Dois", "Três", "Quatro", "Cinco", "Seis", "Sete")
_NUMBERS_EN = ("ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN")


def _zip(*pairs: str) -> list[tuple[str, str]]:
    return [(pairs[i], pairs[i + 1]) for i in range(0, len(pairs), 2)]


def _fruits(names: list[str]) -> list[tuple[str, str]]:
    return [(f"{n} BERRY", f"Fruta {n.title()}") for n in names]


# Linhas agrupadas do Markdown -> termos (en, pt). Chave: a célula inglesa como está no .md.
_MANUAL: dict[str, list[tuple[str, str]]] = {
    "paralysis / paralyzed (PAR)": _zip("paralysis", "paralisia", "paralyzed", "paralisado"),
    "sleep / asleep (SLP)": _zip("sleep", "sono", "asleep", "adormecido"),
    "poison / poisoned (PSN)": _zip("poison", "envenenamento", "poisoned", "envenenado"),
    "burn / burned (BRN)": _zip("burn", "queimadura", "burned", "queimado"),
    "freeze / frozen (FRZ)": _zip("freeze", "congelamento", "frozen", "congelado"),
    "confusion / confused": _zip("confusion", "confusão", "confused", "confuso"),
    "attraction / in love": _zip("attraction", "paixão", "in love", "apaixonado"),
    "fainted (FNT)": _zip("fainted", "desmaiado"),
    "(friendship, hack)": _zip("friendship", "Amizade"),
    "Lv. / level": _zip("Lv.", "Nv.", "level", "nível"),
    "weakness / resistance": _zip("weakness", "fraqueza", "resistance", "resistência"),
    "FIGHT / BAG / POKéMON / RUN": _zip("FIGHT", "Lutar", "BAG", "Bolsa", "POKéMON", "Pokémon", "RUN", "Fugir"),
    "weather (rain/sun/sand/hail)": _zip("weather", "clima", "rain", "chuva", "sun", "sol forte",
                                         "sand", "tempestade de areia", "hail", "granizo"),
    "EXP. POINTS": _zip("EXP. POINTS", "PE"),
    "BLUE / YELLOW / RED FLUTE": _zip("BLUE FLUTE", "Flauta Azul", "YELLOW FLUTE", "Flauta Amar.",
                                      "RED FLUTE", "Flauta Verm."),
    "BLACK / WHITE FLUTE": _zip("BLACK FLUTE", "Flauta Preta", "WHITE FLUTE", "Flauta Branca"),
    "PEARL / BIG PEARL": _zip("PEARL", "Pérola", "BIG PEARL", "Pérola Grande"),
    "MENTAL HERB / WHITE HERB": _zip("MENTAL HERB", "Erva Mental", "WHITE HERB", "Erva Branca"),
    "SOFT SAND / HARD STONE": _zip("SOFT SAND", "Areia Macia", "HARD STONE", "Pedra Dura"),
    "CHERI / CHESTO / PECHA / RAWST / ASPEAR BERRY": _fruits(["CHERI", "CHESTO", "PECHA", "RAWST", "ASPEAR"]),
    "LEPPA / ORAN / PERSIM BERRY": _fruits(["LEPPA", "ORAN", "PERSIM"]),
    "demais frutas (Figy … Enigma)": _fruits([b for b in _BERRIES[_BERRIES.index("FIGY"):]
                                              if b not in _GO_BERRIES]),
    "OLD ROD / GOOD ROD": _zip("OLD ROD", "Vara Velha", "GOOD ROD", "Vara Boa"),
    "RUBY / SAPPHIRE": _zip("RUBY", "Rubi", "SAPPHIRE", "Safira"),
    "MYSTICTICKET / AURORATICKET": _zip("MYSTICTICKET", "Bilhete Míst.", "AURORATICKET", "Bilh. Aurora"),
    "ACRO BIKE / MACH BIKE": _zip("ACRO BIKE", "Bicic. Acro", "MACH BIKE", "Bicic. Mach"),
    "ROUTE 1 … ROUTE 25": [(f"ROUTE {n}", f"Rota {n}") for n in range(1, 26)],
    "ONE … SEVEN ISLAND": [(f"{en} ISLAND", f"Ilha {pt}") for en, pt in zip(_NUMBERS_EN, _NUMBERS_PT)],
    "SEVII ISLE 6 … 24": [(f"SEVII ISLE {n}", f"Ilhas Sevii {n}") for n in range(6, 25)],
    "MONEAN / LIPTOO / WEEPTH / DILFORD / SCUFIB / RIXY / VIAPOIS CHAMBER":
        [(f"{n} CHAMBER", f"Câmara {n.title()}")
         for n in ("MONEAN", "LIPTOO", "WEEPTH", "DILFORD", "SCUFIB", "RIXY", "VIAPOIS")],
    "PROF. OAK / OAK": _zip("PROF. OAK", "Prof. Carvalho", "OAK", "Carvalho"),
    "BROCK, MISTY, ERIKA, KOGA, SABRINA, BLAINE":
        [(n, n.title()) for n in ("BROCK", "MISTY", "ERIKA", "KOGA", "SABRINA", "BLAINE")],
    "LORELEI, BRUNO, AGATHA, LANCE": [(n, n.title()) for n in ("LORELEI", "BRUNO", "AGATHA", "LANCE")],
    "BILL, DAISY, CELIO, LOSTELLE": [(n, n.title()) for n in ("BILL", "DAISY", "CELIO", "LOSTELLE")],
    "CAMPER / PICNICKER": _zip("CAMPER", "Campista", "PICNICKER", "Campista"),
    "SWIMMER♂ / SWIMMER♀": _zip("SWIMMER♂", "Nadador", "SWIMMER♀", "Nadadora"),
    "YOUNG COUPLE / COOL COUPLE": _zip("YOUNG COUPLE", "Casal Jovem", "COOL COUPLE", "Casal Ás"),
    "CRUSH GIRL / CRUSH KIN": _zip("CRUSH GIRL", "Lutadora", "CRUSH KIN", "Família Luta"),
    "ITEMS / KEY ITEMS / POKé BALLS": _zip("ITEMS", "Itens", "KEY ITEMS", "Itens-chave", "POKé BALLS", "Poké Bolas"),
    "USE / GIVE / TOSS / REGISTER / CHECK": _zip("USE", "Usar", "GIVE", "Dar", "TOSS", "Descartar",
                                                 "REGISTER", "Registrar", "CHECK", "Ver"),
    "BILL'S PC / SOMEONE'S PC": _zip("BILL'S PC", "PC do Bill", "SOMEONE'S PC", "PC de alguém"),
    "WITHDRAW / DEPOSIT / MOVE POKéMON": _zip("WITHDRAW", "Retirar", "DEPOSIT", "Guardar",
                                              "MOVE POKéMON", "Mover Pokémon"),
    "BOX / ITEM STORAGE": _zip("BOX", "Caixa", "ITEM STORAGE", "Depósito de Itens"),
    "SEEN / OWNED": _zip("SEEN", "Vistos", "OWNED", "Pegos"),
    "HT / WT": _zip("HT", "Alt.", "WT", "Peso"),
    "AREA / CRY / SIZE": _zip("AREA", "Área", "CRY", "Grito", "SIZE", "Tamanho"),
    "EVOLUTION / IVs/EVs (hack)": _zip("EVOLUTION", "Evolução", "IVs/EVs", "IVs/EVs"),
    "OT / ID No.": _zip("OT", "TO", "ID No.", "Nº ID"),
    "TYPE / ITEM / ABILITY": _zip("TYPE", "Tipo", "ITEM", "Item", "ABILITY", "Habilidade"),
    "EXP. POINTS / NEXT LV.": _zip("EXP. POINTS", "PE", "NEXT LV.", "Próx. Nv."),
    "male / female": _zip("male", "macho", "female", "fêmea"),
    "PP / TYPE/": _zip("PP", "PP", "TYPE/", "Tipo/"),
    "SUMMARY / SWITCH / ITEM / CANCEL": _zip("SUMMARY", "Resumo", "SWITCH", "Trocar", "ITEM", "Item",
                                             "CANCEL", "Cancelar"),
    "GIVE / TAKE / MAIL": _zip("GIVE", "Dar", "TAKE", "Pegar", "MAIL", "Carta"),
    "TEXT SPEED (SLOW/MID/FAST)": _zip("TEXT SPEED", "Vel. texto", "SLOW", "Lenta", "MID", "Média",
                                       "FAST", "Rápida"),
    "BATTLE SCENE (ON/OFF)": _zip("BATTLE SCENE", "Animação", "ON", "Sim", "OFF", "Não"),
    "BATTLE STYLE (SHIFT/SET)": _zip("BATTLE STYLE", "Estilo", "SHIFT", "Troca", "SET", "Fixo"),
    "SOUND (MONO/STEREO)": _zip("SOUND", "Áudio", "MONO", "Mono", "STEREO", "Estéreo"),
    "BUY / SELL / SEE YA!": _zip("BUY", "Comprar", "SELL", "Vender", "SEE YA!", "Tchau!"),
    "MONEY / IN BAG": _zip("MONEY", "Dinheiro", "IN BAG", "Na bolsa"),
    "NEW GAME / CONTINUE": _zip("NEW GAME", "Novo jogo", "CONTINUE", "Continuar"),
    "YES / NO": _zip("YES", "Sim", "NO", "Não"),
    # no jogo inglês as insígnias são uma palavra só: "BOULDERBADGE" (PewterCity_Gym/text.inc)
    "BOULDER / CASCADE / THUNDER / RAINBOW / SOUL / MARSH / VOLCANO / EARTH BADGE":
        [(f"{en}BADGE", f"Insígnia {pt}") for en, pt in zip(
            ("BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"),
            ("Rocha", "Cascata", "Trovão", "Arco-íris", "Alma", "Pântano", "Vulcão", "Terra"))],
    "Morning / Day / Evening / Night (hack)": _zip("Morning", "Manhã", "Day", "Tarde", "Evening", "Entardecer",
                                                   "Night", "Noite"),
}

# Palavras inglesas curtas demais para procurar sem colidir com português em maiúsculas
_AMBIGUOUS = {"NO", "ON", "PC", "OK"}

PROIBIDOS = [
    *[{"variante": v, "use": "Poké Bola", "motivo": "glossário §2.7: Poké Bola (GO+TCG), caixa mista (§6.3)"}
      for v in ("Pokébola", "Pokebola", "Poké bola", "Poke Bola", "PokéBola", "Poké-bola", "Poké Ball")],
    *[{"variante": v, "use": "Prof. Carvalho", "motivo": "glossário §2.9 e Global Constraints: Prof. Carvalho"}
      for v in ("Professor Oak", "Prof. Oak")],
    {"variante": "Oak", "use": "Carvalho", "motivo": "glossário §2.9: Carvalho"},
    {"variante": "HP", "use": "PS", "motivo": "decisão §6.2: PS e PE"},
    {"variante": "EXP", "use": "PE", "motivo": "decisão §6.2: PS e PE"},
    *[{"variante": v, "use": "Equipe Rocket", "motivo": "glossário §2.9: Equipe Rocket"}
      for v in ("Team Rocket", "Time Rocket")],
    {"variante": "Pokemon", "use": "Pokémon", "motivo": "glossário: Pokémon (com acento, caixa mista)"},
    {"variante": "Pokedex", "use": "Pokédex", "motivo": "glossário §2.10: Pokédex"},
    {"variante": "Pokémon Center", "use": "Centro Pokémon", "motivo": "glossário §2.8: Centro Pokémon"},
    {"variante": "Lv.", "use": "Nv.", "motivo": "glossário §2.4: Nv. / nível"},
    {"variante": "Gym", "use": "Ginásio", "motivo": "glossário §2.8: Ginásio (GO)"},
]


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _detectar(en: str, pt: str) -> bool:
    if "{" in en and not en.startswith("{PKMN} "):
        return False      # frase montada ou "{PLAYER}'S PC": o pedaço solto não é termo
    plain = _PLACEHOLDER.sub("", en).strip()
    upper = sum(ch.isascii() and ch.isupper() for ch in plain)
    lower = sum(ch.isascii() and ch.islower() for ch in plain)
    return upper >= 2 and lower == 0 and plain != pt and plain not in _AMBIGUOUS


def _clean_en(en: str) -> str:
    return re.sub(r"\s+\((hack|classe|Joy|Safári)\)$", "", en).strip()


def build(markdown: str) -> dict:
    """Glossário de máquina a partir do Markdown aprovado (tabelas das seções 2.1 a 2.10)."""
    terms: list[dict] = []
    seen: dict[tuple[str, str], dict] = {}
    unknown: list[str] = []
    section = None
    header: list[str] | None = None

    def add(en: str, pt: str, fonte: str, categoria: str, extra: dict) -> None:
        key = (en, categoria)
        if key in seen:
            if seen[key]["pt"] != pt:
                raise ValueError(f"{en} ({categoria}) com duas traduções: {seen[key]['pt']} / {pt}")
            return
        term = {"en": en, "pt": pt, "fonte": fonte, "categoria": categoria, "detectar": _detectar(en, pt)}
        term.update({k: v for k, v in extra.items() if v})
        seen[key] = term
        terms.append(term)

    for line in markdown.splitlines():
        m = re.match(r"^### (2\.\d+) ", line)
        if m:
            section, header = _SECTIONS.get(m.group(1)), None
            continue
        if line.startswith("## ") or line.startswith("### "):
            section, header = None, None
            continue
        if section is None or not line.startswith("|"):
            header = None if not line.startswith("|") else header
            continue
        cells = _cells(line)
        if header is None:
            header = cells
            continue
        if all(re.fullmatch(r":?-+:?", c) or not c for c in cells):
            continue
        groups = [(header, cells)]
        if section == "natureza":   # duas tabelas lado a lado
            groups = [(header[:3], cells[:3]), (header[4:7], cells[4:7])]
        for head, row in groups:
            col = {name.split(" ")[0]: i for i, name in enumerate(head) if name}
            en_cell = row[col["Inglês"]]
            if not en_cell:
                continue
            pt_cell = row[col["Na"]] if "Na" in col else row[col["PT-BR"]]
            fonte = row[col["Fonte"]] if "Fonte" in col else ""
            extra = {"obs": row[col["Obs."]] if "Obs." in col else "",
                     "completo": row[col["PT-BR"]] if "Na" in col and row[col["PT-BR"]] != pt_cell else "",
                     "tela": row[col["Tela"]] if "Tela" in col else ""}
            if en_cell in _MANUAL:
                for en, pt in _MANUAL[en_cell]:
                    add(en, pt, fonte, section, extra)
                continue
            if en_cell.startswith("(") and en_cell.endswith(")"):
                add(en_cell[1:-1], pt_cell, fonte, section, extra)   # sem grafia no jogo
                continue
            en = _clean_en(en_cell)
            if " / " in en or " … " in en or ", " in en or " / " in pt_cell:
                unknown.append(f"{section}: {en_cell} | {pt_cell}")
                continue
            pm = re.fullmatch(r"(.+?) \((.+)\)", pt_cell)
            if pm:
                pt_cell, extra = pm.group(1), {**extra, "completo": pm.group(2)}
            add(en, pt_cell, fonte, section, extra)
    if unknown:
        raise ValueError("linhas agrupadas sem expansão em _MANUAL:\n" + "\n".join(unknown))
    return {
        "_formato": ("termos[]: en = termo como o jogo inglês escreve; pt = termo do glossário (como vai "
                     "na tela); fonte = GO/TCG/TCG antigo/anime/jogo/criado; categoria = tipo, status, "
                     "natureza, batalha, habilidade, golpe, item, lugar, personagem ou interface; detectar "
                     "= o en é procurado nos textos traduzidos (regra glossario); obs/completo/tela = "
                     "colunas do glossário. proibidos[]: variante que não pode aparecer em texto "
                     "traduzido, com o termo a usar. Termo novo de uma frente: acrescentar em termos com "
                     "fonte \"criado\" e \"frente\": \"<nome>\"."),
        "_fonte": ("docs/superpowers/specs/2026-10-18-traducao-glossario.md (aprovado em 18/10; decisões "
                   "da §6: GO -> TCG -> criado, PS/PE, caixa mista, golpe longo abreviado com ponto, GARY) "
                   "via python3 -m esteira.glossario gerar"),
        "termos": terms,
        "proibidos": PROIBIDOS,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m esteira.glossario")
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("gerar", help="gera o glossario.json a partir do Markdown aprovado")
    gen.add_argument("markdown")
    gen.add_argument("--saida", default=str(GLOSSARY_PATH))
    check = sub.add_parser("checar", help="mostra os problemas de glossário de um texto")
    check.add_argument("texto")
    args = parser.parse_args(argv)
    if args.cmd == "gerar":
        data = build(Path(args.markdown).read_text(encoding="utf-8"))
        Path(args.saida).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        counts: dict[str, int] = {}
        for t in data["termos"]:
            counts[t["categoria"]] = counts.get(t["categoria"], 0) + 1
        print(f"{len(data['termos'])} termos ({counts}), {len(data['proibidos'])} variantes proibidas -> {args.saida}")
    else:
        for p in load().problems(args.texto):
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
