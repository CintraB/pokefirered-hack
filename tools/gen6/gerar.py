"""Snapshot da Gen 6 (X/Y) a partir dos CSVs da PokéAPI, e aplicação da categoria nos golpes.

    python3 -I tools/gen6/gerar.py            # baixa os CSVs e regrava tools/gen6/gen6.json
    python3 -I tools/gen6/gerar.py --aplicar  # acrescenta .category em src/data/battle_moves.h

Os CSVs vão para uma pasta temporária própria (fora do repo) e não são versionados.
Só a biblioteca padrão é usada; os CSVs são tratados como dado, nunca como código.
"""

import argparse
import csv
import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SAIDA = Path(__file__).resolve().parent / "gen6.json"
URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/{}.csv"
CSVS = ("moves", "pokemon_moves", "pokemon_types", "pokemon", "types",
        "version_groups", "move_damage_classes", "pokemon_move_methods")

VERSION_GROUP_XY = 15          # conferido em version_groups.csv (identifier "x-y")
METODO_NIVEL, METODO_OVO = 1, 2  # conferido em pokemon_move_methods.csv
CLASSES = {1: "STATUS", 2: "PHYSICAL", 3: "SPECIAL"}  # conferido em move_damage_classes.csv
CLASSES_NOME = {1: "status", 2: "physical", 3: "special"}
ESPECIE_MAX = 386

# Golpes novos da hack (fim da tabela; os ids da PokéAPI são outros, o mapeamento é pelo nome).
GOLPES_NOVOS = {
    "moonblast": ("MOVE_MOONBLAST", 355),
    "play-rough": ("MOVE_PLAY_ROUGH", 356),
    "dazzling-gleam": ("MOVE_DAZZLING_GLEAM", 357),
    "draining-kiss": ("MOVE_DRAINING_KISS", 358),
    "fairy-wind": ("MOVE_FAIRY_WIND", 359),
    "disarming-voice": ("MOVE_DISARMING_VOICE", 360),
}

# Nome PokéAPI -> constante do repo, quando a regra (maiúsculas, "-" -> "_") não bate.
EXCECOES_GOLPES = {
    "vise-grip": "MOVE_VICE_GRIP",
    "high-jump-kick": "MOVE_HI_JUMP_KICK",
    "smelling-salts": "MOVE_SMELLING_SALT",
    "feint-attack": "MOVE_FAINT_ATTACK",
}

# As 18 espécies que trocam de tipo na Gen 6 (spec, POK-45).
ESPECIES_TIPO = (
    "SPECIES_CLEFAIRY", "SPECIES_CLEFABLE", "SPECIES_CLEFFA",
    "SPECIES_JIGGLYPUFF", "SPECIES_WIGGLYTUFF", "SPECIES_IGGLYBUFF",
    "SPECIES_MR_MIME", "SPECIES_TOGEPI", "SPECIES_TOGETIC",
    "SPECIES_SNUBBULL", "SPECIES_GRANBULL",
    "SPECIES_MARILL", "SPECIES_AZUMARILL", "SPECIES_AZURILL",
    "SPECIES_RALTS", "SPECIES_KIRLIA", "SPECIES_GARDEVOIR", "SPECIES_MAWILE",
)


def falha(msg: str) -> None:
    sys.exit(f"gerar.py: {msg}")


def baixar(pasta: Path) -> dict[str, list[dict[str, str]]]:
    tabelas = {}
    for nome in CSVS:
        destino = pasta / f"{nome}.csv"
        with urllib.request.urlopen(URL.format(nome), timeout=120) as resp:
            destino.write_bytes(resp.read())
        with destino.open(encoding="utf-8", newline="") as f:
            tabelas[nome] = list(csv.DictReader(f))
    return tabelas


def golpes_do_repo() -> dict[str, int]:
    texto = (REPO / "include" / "constants" / "moves.h").read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"^#define\s+(MOVE_\w+)\s+(\d+)\b", texto, re.M)
            if m.group(1) not in ("MOVE_NONE", "MOVES_COUNT")}


def especies_por_dex() -> dict[int, str]:
    """Número da Dex Nacional -> SPECIES_* (pelo enum de include/constants/pokedex.h)."""
    texto = (REPO / "include" / "constants" / "pokedex.h").read_text(encoding="utf-8")
    corpo = texto[texto.index("enum {"):]
    corpo = corpo[:corpo.index("}")]
    nomes = re.findall(r"\bNATIONAL_DEX_(\w+)", corpo)
    if nomes[0] != "NONE":
        falha("pokedex.h: o enum não começa em NATIONAL_DEX_NONE")
    return {i: f"SPECIES_{n}" for i, n in enumerate(nomes) if 0 < i <= ESPECIE_MAX}


def conferir_ids(t: dict) -> None:
    vg = {int(r["id"]): r["identifier"] for r in t["version_groups"]}
    if vg.get(VERSION_GROUP_XY) != "x-y":
        falha(f"version_group {VERSION_GROUP_XY} é {vg.get(VERSION_GROUP_XY)!r}, esperado 'x-y'")
    met = {int(r["id"]): r["identifier"] for r in t["pokemon_move_methods"]}
    if met.get(METODO_NIVEL) != "level-up" or met.get(METODO_OVO) != "egg":
        falha(f"métodos de aprendizado inesperados: {met}")
    dc = {int(r["id"]): r["identifier"] for r in t["move_damage_classes"]}
    if any(dc.get(k) != v for k, v in CLASSES_NOME.items()):
        falha(f"classes de dano inesperadas: {dc}")


def nome_golpe(ident: str) -> str:
    return EXCECOES_GOLPES.get(ident, "MOVE_" + ident.upper().replace("-", "_"))


def gerar() -> dict:
    with tempfile.TemporaryDirectory(prefix="pkfr-gen6-") as tmp:
        t = baixar(Path(tmp))
    conferir_ids(t)

    repo = golpes_do_repo()
    tipos = {int(r["id"]): "TYPE_" + r["identifier"].upper() for r in t["types"]}

    # PokéAPI id -> (MOVE_*, id na hack)
    mapa: dict[int, tuple[str, int]] = {}
    for r in t["moves"]:
        pid, ident = int(r["id"]), r["identifier"]
        if ident in GOLPES_NOVOS:
            mapa[pid] = GOLPES_NOVOS[ident]
        elif pid <= 354:
            nome = nome_golpe(ident)
            if repo.get(nome) != pid:
                falha(f"golpe {pid} {ident!r} -> {nome}, que não está em moves.h com o id {pid};"
                      " acrescente em EXCECOES_GOLPES")
            mapa[pid] = (nome, pid)
    if sorted(h for _, h in mapa.values()) != list(range(1, 361)):
        falha("o snapshot não cobre os golpes 1–360")

    categorias, tipos_golpe = {}, {}
    por_hack = {}
    for r in t["moves"]:
        pid = int(r["id"])
        if pid not in mapa:
            continue
        nome, hid = mapa[pid]
        classe = int(r["damage_class_id"]) if r["damage_class_id"] else 0
        if classe not in CLASSES:
            falha(f"{nome}: damage_class_id desconhecido {r['damage_class_id']!r}")
        por_hack[hid] = (nome, CLASSES[classe], tipos[int(r["type_id"])])
    for hid in sorted(por_hack):
        nome, cat, tipo = por_hack[hid]
        categorias[nome] = cat
        tipos_golpe[nome] = tipo

    dex = especies_por_dex()
    padrao = {int(r["id"]): int(r["species_id"]) for r in t["pokemon"]
              if r["is_default"] == "1" and int(r["species_id"]) <= ESPECIE_MAX}

    tipos_mon: dict[int, dict[int, str]] = {}
    for r in t["pokemon_types"]:
        pk = int(r["pokemon_id"])
        if pk in padrao:
            tipos_mon.setdefault(padrao[pk], {})[int(r["slot"])] = tipos[int(r["type_id"])]
    especie_tipos = {}
    num_por_nome = {v: k for k, v in dex.items()}
    for esp in ESPECIES_TIPO:
        if esp not in num_por_nome:
            falha(f"{esp} não está em pokedex.h")
        sl = tipos_mon[num_por_nome[esp]]
        especie_tipos[esp] = [sl[1], sl.get(2, sl[1])]

    novos = {pid for pid, (_, hid) in mapa.items() if hid >= 355}
    nivel: dict[str, set] = {}
    ovo: dict[str, set] = {}
    for r in t["pokemon_moves"]:
        if int(r["version_group_id"]) != VERSION_GROUP_XY or int(r["move_id"]) not in novos:
            continue
        pk = int(r["pokemon_id"])
        if pk not in padrao:
            continue
        esp = dex[padrao[pk]]
        golpe = mapa[int(r["move_id"])][0]
        metodo = int(r["pokemon_move_method_id"])
        if metodo == METODO_NIVEL:
            nivel.setdefault(esp, set()).add((int(r["level"]), golpe))
        elif metodo == METODO_OVO:
            ovo.setdefault(esp, set()).add(golpe)

    ordem = {v: k for k, v in dex.items()}          # SPECIES_* -> número da Dex
    id_novo = dict(GOLPES_NOVOS.values())           # MOVE_* novo -> id na hack
    return {
        "categories": categorias,
        "types": tipos_golpe,
        "species_types": especie_tipos,
        "levelup": {e: [list(x) for x in sorted(nivel[e])] for e in sorted(nivel, key=ordem.get)},
        "egg": {e: sorted(ovo[e], key=id_novo.get) for e in sorted(ovo, key=ordem.get)},
    }


def aplicar() -> None:
    dados = json.loads(SAIDA.read_text(encoding="utf-8"))["categories"]
    arq = REPO / "src" / "data" / "battle_moves.h"
    texto = arq.read_text(encoding="utf-8")
    entrada = re.compile(r"(\[(MOVE_\w+)\] =\s*\{.*?)(\n(\s*)\.flags = [^\n]*\n)(\s*\},)", re.S)
    vistos = []

    def troca(m: re.Match) -> str:
        nome = m.group(2)
        if ".category" in m.group(1):
            falha(f"{nome} já tem .category")
        cat = "PHYSICAL" if nome == "MOVE_NONE" else dados.get(nome)
        if cat is None:
            falha(f"{nome} não está no snapshot")
        vistos.append(nome)
        return f"{m.group(1)}{m.group(3)}{m.group(4)}.category = MOVE_CATEGORY_{cat},\n{m.group(5)}"

    novo = entrada.sub(troca, texto)
    total = len(re.findall(r"^    \[MOVE_\w+\] =", texto, re.M))
    if len(vistos) != total:
        falha(f"só {len(vistos)} de {total} entradas receberam .category")
    arq.write_text(novo, encoding="utf-8", newline="\n")
    print(f"battle_moves.h: .category em {len(vistos)} entradas")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--aplicar", action="store_true",
                    help="acrescenta .category em src/data/battle_moves.h a partir do gen6.json")
    args = ap.parse_args()
    if args.aplicar:
        aplicar()
        return
    dados = gerar()
    SAIDA.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"{SAIDA.relative_to(REPO)}: {len(dados['categories'])} golpes, "
          f"{len(dados['levelup'])} espécies (nível), {len(dados['egg'])} (ovo)")


if __name__ == "__main__":
    main()
