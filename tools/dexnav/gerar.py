"""DexNav (POK-47): a lista dos mapas com encontro e o espelho das chances de src/wild_encounter.c.

    python3 -I tools/dexnav/gerar.py             # grava src/data/dexnav_mapas.h
    python3 -I tools/dexnav/gerar.py --conferir  # sai com 1 se o header commitado divergir
    python3 -I tools/dexnav/gerar.py --listar    # imprime os mapas (índice, região, nome) em Markdown

Lê `src/data/wild_encounters.json` (só os cabeçalhos `_FireRed`, os que o FireRed compila: 132 cabeçalhos para
124 mapas, porque a Caverna Mutante tem 9 tabelas no mesmo mapa), `data/maps/map_groups.json` + `map.json` de cada
mapa (seção do mapa), `src/data/region_map/region_map_sections.json` (nomes PT-BR e ordem das seções: a partir de
MAPSEC_ONE_ISLAND é Sevii) e a ordem da Pokédex AREA em `src/wild_pokemon_area.c`.

Nome de cada linha: o nome da seção do mapa (já traduzido) e, quando a seção tem mais de um mapa com encontro, o
andar tirado da constante do mapa (`MAP_MT_MOON_B1F` -> "Monte Lua B1F"; o `floor_number` dos map.json é 0 em
todos). Os casos que não têm andar na constante (Rota 21 Norte/Sul, Zona Safári, Monte Brasa, Caverna Gélida,
Caverna Perdida) estão em NOMES_FIXOS.

O espelho das chances (`enumerar`) segue as mesmas regras que `DexNav_GetMapEntries` (src/wild_encounter.c): chance
por slot do FRLG, tabela por horário do Hack 7 só na grama (a tarde-noite, TIME_EVENING, é a média da tarde e da
noite e não tem coluna própria), metade LeafGreen do Hack 8 só quando a espécie do horário é a do FireRed (níveis do
LeafGreen), conjunto da Caverna Mutante (fora da faixa vale 0) e câmaras de Tanoby sem encontro antes de
FLAG_SYS_UNLOCKED_TANOBY_RUINS. Chances em por mil (‰), uma entrada por (espécie, método).
Só a biblioteca padrão é usada.
"""

import argparse
import functools
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HEADER = REPO / "src" / "data" / "dexnav_mapas.h"
WILD_JSON = REPO / "src" / "data" / "wild_encounters.json"
TIME_JSON = REPO / "src" / "data" / "wild_encounters_time.json"
GEN_SWAPS = REPO / "tools" / "wild_leafgreen" / "gen_swaps.py"
MAP_GROUPS = REPO / "data" / "maps" / "map_groups.json"
SECOES = REPO / "src" / "data" / "region_map" / "region_map_sections.json"
AREA_C = REPO / "src" / "wild_pokemon_area.c"

# Métodos (DEXNAV_METHOD_* de include/dexnav.h), na ordem da enumeração
LAND, WATER, OLD_ROD, GOOD_ROD, SUPER_ROD, ROCK = range(6)
METODOS = 6
PERIODOS = ("morning", "day", "night")  # rateX10[0..2]: manhã, tarde (TIME_AFTERNOON), noite
REGIAO_KANTO, REGIAO_SEVII = 0, 1

MUTANTE = "MAP_SIX_ISLAND_ALTERING_CAVE"
NUM_CONJUNTOS_MUTANTE = 9  # NUM_ALTERING_CAVE_TABLES
CAMARAS_TANOBY = {f"MAP_SEVEN_ISLAND_TANOBY_RUINS_{c}_CHAMBER"
                  for c in ("MONEAN", "LIPTOO", "WEEPTH", "DILFORD", "SCUFIB", "RIXY", "VIAPOIS")}

# Nomes que o andar da constante não resolve (cabem em DEXNAV_NAME_WIDTH = 120 px, FONT_NORMAL). Os lugares cujo nome
# de mapa é a forma curta do glossário (sem a preposição: "Cidade Vermilion") usam aqui a forma cheia ("Cidade de
# Vermilion"), como "Cidade de Pallet" ao lado (revisão R5); a Caverna Cerulean fica curta porque "Caverna de Cerulean
# B1F" passa dos 120 px.
NOMES_FIXOS = {
    "MAP_VERMILION_CITY": "Cidade de Vermilion",
    "MAP_VIRIDIAN_FOREST": "Floresta de Viridian",
    "MAP_FIVE_ISLAND_MEADOW": "Prado da Ilha Cinco",
    "MAP_ROUTE21_NORTH": "Rota 21 Norte",
    "MAP_ROUTE21_SOUTH": "Rota 21 Sul",
    "MAP_SAFARI_ZONE_CENTER": "Zona Safári Centro",
    "MAP_SAFARI_ZONE_EAST": "Zona Safári Leste",
    "MAP_SAFARI_ZONE_NORTH": "Zona Safári Norte",
    "MAP_SAFARI_ZONE_WEST": "Zona Safári Oeste",
    "MAP_MT_EMBER_EXTERIOR": "Monte Brasa",
    "MAP_MT_EMBER_SUMMIT_PATH_1F": "M. Brasa Cume 1F",
    "MAP_MT_EMBER_SUMMIT_PATH_2F": "M. Brasa Cume 2F",
    "MAP_MT_EMBER_SUMMIT_PATH_3F": "M. Brasa Cume 3F",
    "MAP_MT_EMBER_RUBY_PATH_1F": "M. Brasa Rubi 1F",
    "MAP_MT_EMBER_RUBY_PATH_B1F": "M. Brasa Rubi B1F",
    "MAP_MT_EMBER_RUBY_PATH_B2F": "M. Brasa Rubi B2F",
    "MAP_MT_EMBER_RUBY_PATH_B3F": "M. Brasa Rubi B3F",
    "MAP_MT_EMBER_RUBY_PATH_B1F_STAIRS": "M. Brasa Escada B1F",
    "MAP_MT_EMBER_RUBY_PATH_B2F_STAIRS": "M. Brasa Escada B2F",
    "MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE": "Caverna Gélida Entr.",
    "MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK": "Caverna Gélida Fundo",
    **{f"MAP_FIVE_ISLAND_LOST_CAVE_ROOM{n}": f"Caverna Perdida {n}" for n in range(1, 15)},
}
_ANDAR = re.compile(r"_(B?\d+F)$")


def falha(msg: str):
    print(f"gerar.py: {msg}", file=sys.stderr)
    sys.exit(1)


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=None)
def _wild() -> dict:
    return _json(WILD_JSON)


def cabecalhos_firered() -> list[dict]:
    """Os encontros `_FireRed` na ordem do JSON (= a ordem de gWildMonHeaders no FireRed)."""
    return [e for g in _wild()["wild_encounter_groups"] if g["label"] == "gWildMonHeaders"
            for e in g["encounters"] if "FireRed" in e["base_label"]]


@functools.lru_cache(maxsize=None)
def _chances_por_slot() -> dict[int, list[tuple[int, int]]]:
    """Método -> [(slot, chance em %)] dos campos do JSON (a soma de cada método é 100)."""
    campos = {f["type"]: f for g in _wild()["wild_encounter_groups"] if g["label"] == "gWildMonHeaders"
              for f in g.get("fields", [])}
    out = {LAND: list(enumerate(campos["land_mons"]["encounter_rates"])),
           WATER: list(enumerate(campos["water_mons"]["encounter_rates"])),
           ROCK: list(enumerate(campos["rock_smash_mons"]["encounter_rates"]))}
    pesca = campos["fishing_mons"]
    for metodo, grupo in ((OLD_ROD, "old_rod"), (GOOD_ROD, "good_rod"), (SUPER_ROD, "super_rod")):
        out[metodo] = [(s, pesca["encounter_rates"][s]) for s in pesca["groups"][grupo]]
    for metodo, slots in out.items():
        if sum(c for _, c in slots) != 100:
            falha(f"as chances do método {metodo} não somam 100: {slots}")
    return out


@functools.lru_cache(maxsize=None)
def _tabelas_horario() -> dict[str, dict]:
    """Mapa -> tabela por horário (a primeira do mapa, como GetTimeOfDayLandSpecies)."""
    out: dict[str, dict] = {}
    for t in _json(TIME_JSON)["tables"]:
        out.setdefault(t["map"], t)
    return out


@functools.lru_cache(maxsize=None)
def _gemeos_leafgreen() -> dict[tuple[str, str, int], dict]:
    """(base_label FR, tipo de encontro, slot) -> linha do LeafGreen (gen_swaps.compute_swaps, o mesmo do make)."""
    spec = importlib.util.spec_from_file_location("dexnav_gen_swaps", GEN_SWAPS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sufixos = {suf: tipo for tipo, suf in mod.KINDS}
    out = {}
    for simbolo, slot, mon, _ in mod.compute_swaps(_wild()):
        base, suf = simbolo.rsplit("_", 1)
        out[(base, sufixos[suf], slot)] = mon
    return out


def _cabecalho(mapa: str, conjunto_mutante: int) -> dict | None:
    """GetCurrentMapWildMonHeaderId para um mapa qualquer (sem a trava de Tanoby)."""
    hs = cabecalhos_firered()
    for i, h in enumerate(hs):
        if h["map"] == mapa:
            if mapa == MUTANTE:
                i += conjunto_mutante if 0 <= conjunto_mutante < NUM_CONJUNTOS_MUTANTE else 0
            return hs[i]
    return None


def enumerar(mapa: str, conjunto_mutante: int = 0, tanoby_liberado: bool = True) -> list[dict]:
    """Os resultados possíveis do mapa: [{especie, metodo, min, max, periodos, chances: [manhã, tarde, noite] ‰}],
    uma entrada por (espécie, método), na ordem da função C."""
    h = _cabecalho(mapa, conjunto_mutante)
    if h is None or (mapa in CAMARAS_TANOBY and not tanoby_liberado):
        return []
    entradas: list[dict] = []
    por_chave: dict[tuple[str, int], dict] = {}

    def soma(especie: str, metodo: int, linha: dict, periodos: int, chance: int):
        e = por_chave.get((especie, metodo))
        if e is None:
            e = {"especie": especie, "metodo": metodo, "min": 255, "max": 0, "periodos": 0, "chances": [0, 0, 0]}
            por_chave[(especie, metodo)] = e
            entradas.append(e)
        lo, hi = sorted((linha["min_level"], linha["max_level"]))
        e["min"], e["max"] = min(e["min"], lo), max(e["max"], hi)
        e["periodos"] |= periodos
        for p in range(3):
            if periodos & (1 << p):
                e["chances"][p] += chance

    def slot(tipo: str, metodo: int, s: int, pct: int, especie: str, periodos: int):
        fr = h[tipo]["mons"][s]
        lg = _gemeos_leafgreen().get((h["base_label"], tipo, s))
        if especie == fr["species"] and lg is not None:
            soma(fr["species"], metodo, fr, periodos, pct * 5)
            soma(lg["species"], metodo, lg, periodos, pct * 5)
        else:
            soma(especie, metodo, fr, periodos, pct * 10)

    for metodo, tipo in ((LAND, "land_mons"), (WATER, "water_mons"), (OLD_ROD, "fishing_mons"),
                         (GOOD_ROD, "fishing_mons"), (SUPER_ROD, "fishing_mons"), (ROCK, "rock_smash_mons")):
        if tipo not in h:
            continue
        if metodo == LAND:
            tabela = _tabelas_horario().get(mapa)
            for p, periodo in enumerate(PERIODOS):
                for s, pct in _chances_por_slot()[LAND]:
                    especie = tabela[periodo][s] if tabela else h[tipo]["mons"][s]["species"]
                    slot(tipo, LAND, s, pct, especie, 1 << p)
        else:
            for s, pct in _chances_por_slot()[metodo]:
                slot(tipo, metodo, s, pct, h[tipo]["mons"][s]["species"], 0b111)
    return entradas


# --- mapas e nomes ---------------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def _mapas_do_jogo() -> dict[str, dict]:
    """MAP_* -> {grupo, num, ordem, secao} a partir de map_groups.json e de cada map.json."""
    grupos = _json(MAP_GROUPS)
    out, ordem = {}, 0
    for gi, grupo in enumerate(grupos["group_order"]):
        for ni, nome in enumerate(grupos[grupo]):
            m = _json(REPO / "data" / "maps" / nome / "map.json")
            out[m["id"]] = {"grupo": gi, "num": ni, "ordem": ordem, "secao": m["region_map_section"]}
            ordem += 1
    return out


@functools.lru_cache(maxsize=None)
def _secoes() -> tuple[dict[str, str], dict[str, int]]:
    """(nome PT-BR de cada MAPSEC_*, região de cada MAPSEC_*) na ordem do enum."""
    lista = _json(SECOES)["map_sections"]
    ids = [s["id"] for s in lista]
    sevii = ids.index("MAPSEC_ONE_ISLAND")  # SEVII_MAPSEC_START
    return ({s["id"]: s.get("name", "") for s in lista},
            {sid: REGIAO_SEVII if i >= sevii else REGIAO_KANTO for i, sid in enumerate(ids)})


@functools.lru_cache(maxsize=None)
def _ordem_area() -> list[str]:
    """As seções na ordem das tabelas sDexAreas_* da Pokédex AREA (Kanto, depois Sevii 1..7)."""
    fonte = AREA_C.read_text(encoding="utf-8")
    out: list[str] = []
    for sec in re.findall(r"\{\s*(MAPSEC_\w+),\s*DEX_AREA_\w+\s*\}", fonte):
        if sec not in out:
            out.append(sec)
    return out


def mapas() -> list[dict]:
    """Os mapas com encontro, um por mapa: [{id, nome, regiao, grupo, num, secao}] na ordem da tabela."""
    jogo = _mapas_do_jogo()
    nomes_secao, regiao_secao = _secoes()
    area = _ordem_area()
    ids: list[str] = []
    for h in cabecalhos_firered():
        if h["map"] not in ids:
            ids.append(h["map"])
    por_secao: dict[str, int] = {}
    for mid in ids:
        por_secao[jogo[mid]["secao"]] = por_secao.get(jogo[mid]["secao"], 0) + 1
    out = []
    for mid in ids:
        secao = jogo[mid]["secao"]
        if secao not in area:
            falha(f"{mid}: a seção {secao} não está na Pokédex AREA (src/wild_pokemon_area.c)")
        if mid in NOMES_FIXOS:
            nome = NOMES_FIXOS[mid]
        elif por_secao[secao] > 1:
            andar = _ANDAR.search(mid)
            if not andar:
                falha(f"{mid}: {secao} tem {por_secao[secao]} mapas e a constante não tem andar; ponha em NOMES_FIXOS")
            nome = f"{nomes_secao[secao]} {andar.group(1)}"
        else:
            nome = nomes_secao[secao]
        out.append({"id": mid, "nome": nome, "regiao": regiao_secao[secao], "grupo": jogo[mid]["grupo"],
                    "num": jogo[mid]["num"], "secao": secao})
    out.sort(key=lambda m: (m["regiao"], area.index(m["secao"]), jogo[m["id"]]["ordem"]))
    nomes = [m["nome"] for m in out]
    repetidos = sorted({n for n in nomes if nomes.count(n) > 1})
    if repetidos:
        falha(f"nomes repetidos: {repetidos}")
    return out


def header() -> str:
    ms = mapas()
    linhas = [
        "// GERADO por tools/dexnav/gerar.py; não editar (python3 -I tools/dexnav/gerar.py; o teste roda --conferir)",
        "// DexNav (POK-47): os mapas com encontro do FireRed (um por mapa: a Caverna Mutante tem 9 tabelas e 1 linha),",
        "// nome PT-BR \"lugar + andar\" e região, na ordem da Pokédex AREA (Kanto, depois Sevii). O índice é o bit de",
        "// \"visitado\" em gSaveBlock1Ptr->dexNav.visitedMaps: mapa novo no meio da ordem desloca os bits dos saves.",
        "",
        f"#define DEXNAV_MAPAS_GERADOS {len(ms)}",
        "",
    ]
    for i, m in enumerate(ms):
        linhas.append(f'static const u8 sDexNavNome_{i}[] = _("{m["nome"]}");')
    linhas += ["", "const struct DexNavMap gDexNavMaps[DEXNAV_MAP_COUNT] =", "{"]
    for i, m in enumerate(ms):
        regiao = "DEXNAV_REGION_SEVII" if m["regiao"] == REGIAO_SEVII else "DEXNAV_REGION_KANTO"
        linhas.append(f"    {{ MAP_GROUP({m['id']}), MAP_NUM({m['id']}), {regiao}, sDexNavNome_{i} }}, // {i}")
    linhas += ["};", ""]
    return "\n".join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--conferir", action="store_true", help="sai com 1 se o header commitado divergir")
    ap.add_argument("--listar", action="store_true", help="imprime os mapas em Markdown")
    args = ap.parse_args()
    if args.listar:
        print("| # | região | mapa | nome |\n|---|---|---|---|")
        for i, m in enumerate(mapas()):
            print(f"| {i} | {'Sevii' if m['regiao'] else 'Kanto'} | {m['id']} | {m['nome']} |")
        return
    novo = header()
    if args.conferir:
        atual = HEADER.read_text(encoding="utf-8", newline="") if HEADER.exists() else None
        if atual != novo:
            falha(f"{HEADER.relative_to(REPO)} está fora de dia; rode python3 -I tools/dexnav/gerar.py")
        return
    HEADER.write_text(novo, encoding="utf-8", newline="\n")
    print(f"gravado {HEADER.relative_to(REPO)} ({len(mapas())} mapas)")


if __name__ == "__main__":
    main()
