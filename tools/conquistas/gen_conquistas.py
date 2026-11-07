#!/usr/bin/env python3
"""Conquistas e diário de batalhas (POK-44): gera os headers a partir do conquistas.json.

Uso (o make chama sozinho): python3 tools/conquistas/gen_conquistas.py <conquistas.json> <ids.h> <tabela.h>
Para o Cintra:             python3 tools/conquistas/gen_conquistas.py --tabela <conquistas.json>

O JSON tem `abas[]`, `conquistas[]` (num, id, aba, nome, tipo, param, param2, lista, degraus, premios,
perdivel, ativa, slot, ...) e `diario[]` (id, nome, local, tipo, lider, rival, especie, treinadores), com os
mesmos nomes dos campos de `struct Conquista`/`struct DiarioEvento` (include/conquistas.h). As constantes
(FLAG_*, GAME_STAT_*, SPECIES_*, ITEM_*, TRAINER_*, CONQ_EVT_*) são conferidas contra os headers do repo:
constante que não existe é erro.

`ids.h` traz CONQ_<ID> = num, CONQ_COUNT, CONQ_ABA_<ID>, CONQ_ABAS_COUNT, DIARIO_EVT_<ID> (posição no
array `diario`) e DIARIO_EVT_COUNT. `tabela.h` traz as tabelas (só `const`, nenhum EWRAM_DATA), incluída
por src/conquistas_data.c. O `{N}` do nome vira {STR_VAR_1}. Cada saída é determinística.
"""

import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
IDENT = re.compile(r"[a-z][a-z0-9_]*")
CONST_HEADERS = ("flags", "game_stat", "species", "items", "opponents", "conquistas")
TIPOS = ("FLAG", "FLAGS_TODAS", "DEX_TODOS", "DEX_KANTO", "DEX_NACIONAL", "NIVEL", "AMIZADE_MAX",
         "GAME_STAT", "DINHEIRO", "HORAS", "VITORIAS", "SHINIES", "EVENTO")
TIPOS_DIARIO = ("treinador", "lendario", "chefe")
CONQ_MAX = 64
CONQ_MAX_DEGRAUS = 8
DIARIO_MAX = 48
TEXTO_RE = re.compile(r"[^\"\\]+")
CONSTANTE_RE = re.compile(r"[A-Z][A-Z0-9_]+")

_constantes_cache: set[str] | None = None


def constantes() -> set[str]:
    """Todo `#define NOME` dos headers de constantes usados pelas tabelas."""
    global _constantes_cache
    if _constantes_cache is None:
        nomes: set[str] = set()
        for nome in CONST_HEADERS:
            texto = (REPO / "include" / "constants" / f"{nome}.h").read_text(encoding="utf-8")
            nomes.update(re.findall(r"^#define\s+([A-Z][A-Z0-9_]*)\b", texto, re.M))
        _constantes_cache = nomes
    return _constantes_cache


def _constante(valor, onde: str, prefixo: str | None = None) -> str:
    if not isinstance(valor, str) or not CONSTANTE_RE.fullmatch(valor):
        raise ValueError(f"{onde}: '{valor}' não é um nome de constante")
    if prefixo and not valor.startswith(prefixo):
        raise ValueError(f"{onde}: '{valor}' deveria começar com {prefixo}")
    if valor not in constantes():
        raise ValueError(f"{onde}: constante '{valor}' não existe nos headers do repo")
    return valor


def _texto(texto, onde: str) -> str:
    if not isinstance(texto, str) or not texto or not TEXTO_RE.fullmatch(texto):
        raise ValueError(f"{onde}: texto vazio ou com aspas/barra invertida")
    return texto.replace("{N}", "{STR_VAR_1}")


def _inteiro(valor, onde: str, minimo: int, maximo: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or not minimo <= valor <= maximo:
        raise ValueError(f"{onde}: {valor!r} fora de {minimo}-{maximo}")
    return valor


def carregar(json_path) -> dict:
    return json.loads(Path(json_path).read_text(encoding="utf-8"))


def validar(data: dict) -> None:
    """Confere o esquema inteiro (a mesma regra que o test_conquistas_tabela repete sobre o JSON)."""
    abas = [a["id"] for a in data["abas"]]
    if len(set(abas)) != len(abas) or not all(IDENT.fullmatch(a) for a in abas):
        raise ValueError("ids de aba inválidos ou repetidos")
    nums, ids, slots, com_degraus = set(), set(), set(), 0
    for c in data["conquistas"]:
        cid = c.get("id", "?")
        if not IDENT.fullmatch(str(cid)) or cid in ids:
            raise ValueError(f"id de conquista inválido ou repetido: {cid!r}")
        ids.add(cid)
        num = _inteiro(c.get("num"), f"{cid}: num", 0, CONQ_MAX - 1)
        if num in nums:
            raise ValueError(f"{cid}: num {num} repetido")
        nums.add(num)
        if c.get("aba") not in abas:
            raise ValueError(f"{cid}: aba '{c.get('aba')}' não está em `abas`")
        tipo = c.get("tipo")
        if tipo not in TIPOS:
            raise ValueError(f"{cid}: tipo '{tipo}' desconhecido")
        degraus = c.get("degraus", [])
        premios = c.get("premios", [])
        _texto(c.get("nome"), f"{cid}: nome")
        if ("{N}" in c["nome"]) != bool(degraus):
            raise ValueError(f"{cid}: o nome tem {{N}} se e só se a conquista tem degraus")
        if degraus:
            com_degraus += 1
            for d in degraus:
                _inteiro(d, f"{cid}: degrau", 1, 65535)
            if any(a >= b for a, b in zip(degraus, degraus[1:])):
                raise ValueError(f"{cid}: degraus precisam ser estritamente crescentes")
            if tipo not in ("VITORIAS", "SHINIES", "HORAS"):
                raise ValueError(f"{cid}: só VITORIAS, SHINIES e HORAS têm degraus")
            # o slot é a posição do progresso no save (degrauEntregue[slot]): explícito, para não mudar
            # quando outra conquista com degraus entrar na tabela
            if "slot" not in c:
                raise ValueError(f"{cid}: conquista com degraus precisa do campo `slot`")
            slot = _inteiro(c["slot"], f"{cid}: slot", 0, CONQ_MAX_DEGRAUS - 1)
            if slot in slots:
                raise ValueError(f"{cid}: slot {slot} repetido")
            slots.add(slot)
        elif tipo in ("VITORIAS", "SHINIES", "HORAS"):
            raise ValueError(f"{cid}: o tipo {tipo} exige degraus")
        elif "slot" in c:
            raise ValueError(f"{cid}: `slot` só existe em conquista com degraus")
        if not premios or len(premios) not in {1, len(degraus)}:
            raise ValueError(f"{cid}: `premios` tem 1 ou len(degraus) entradas")
        for p in premios:
            _constante(p.get("item"), f"{cid}: item de prêmio", "ITEM_")
            _inteiro(p.get("qtd"), f"{cid}: qtd do prêmio", 1, 99)
        _validar_param(c, cid, tipo)
        if not isinstance(c.get("perdivel", False), bool) or not isinstance(c.get("ativa", True), bool):
            raise ValueError(f"{cid}: perdivel/ativa são booleanos")
    if com_degraus > CONQ_MAX_DEGRAUS:
        raise ValueError(f"no máximo {CONQ_MAX_DEGRAUS} conquistas com degraus (há {com_degraus})")
    if len(data["diario"]) > DIARIO_MAX:
        raise ValueError(f"o diário passa de {DIARIO_MAX} eventos")
    dids = set()
    for e in data["diario"]:
        did = e.get("id", "?")
        if not IDENT.fullmatch(str(did)) or did in dids:
            raise ValueError(f"id de evento do diário inválido ou repetido: {did!r}")
        dids.add(did)
        _texto(e.get("nome"), f"{did}: nome")
        _texto(e.get("local"), f"{did}: local")
        if e.get("tipo") not in TIPOS_DIARIO:
            raise ValueError(f"{did}: tipo '{e.get('tipo')}' desconhecido")
        if e["tipo"] in ("lendario", "chefe"):
            _constante(e.get("especie"), f"{did}: especie", "SPECIES_")
        else:
            if not e.get("treinadores"):
                raise ValueError(f"{did}: evento de treinador sem `treinadores`")
            for t in e["treinadores"]:
                _constante(t, f"{did}: treinador", "TRAINER_")


def _validar_param(c: dict, cid: str, tipo: str) -> None:
    p, p2 = c.get("param"), c.get("param2")
    if tipo == "FLAG":
        _constante(p, f"{cid}: param", "FLAG_")
    elif tipo == "FLAGS_TODAS":
        _constante(p, f"{cid}: param", "FLAG_")
        _constante(c.get("paramFim"), f"{cid}: paramFim", "FLAG_")
        _inteiro(p2, f"{cid}: param2", 2, 255)
    elif tipo == "DEX_TODOS":
        if not c.get("lista"):
            raise ValueError(f"{cid}: DEX_TODOS sem `lista`")
        for s in c["lista"]:
            _constante(s, f"{cid}: lista", "SPECIES_")
    elif tipo in ("DEX_KANTO", "DEX_NACIONAL", "NIVEL", "AMIZADE_MAX", "DINHEIRO"):
        _inteiro(p, f"{cid}: param", 1, 4294967295)
    elif tipo == "GAME_STAT":
        _constante(p, f"{cid}: param", "GAME_STAT_")
        _inteiro(p2, f"{cid}: param2", 1, 65535)
    elif tipo == "EVENTO":
        _constante(p, f"{cid}: param", "CONQ_EVT_")


def _valor(v) -> str:
    return str(v) if isinstance(v, int) else v


def render_ids(data: dict) -> str:
    validar(data)
    out = ["//",
           "// DO NOT MODIFY THIS FILE! It is auto-generated by tools/conquistas/gen_conquistas.py",
           "// from src/data/conquistas/conquistas.json (conquistas e diário de batalhas, POK-44).",
           "//", ""]
    for c in sorted(data["conquistas"], key=lambda c: c["num"]):
        out.append(f"#define CONQ_{c['id'].upper()} {c['num']}")
    out.append(f"#define CONQ_COUNT {max(c['num'] for c in data['conquistas']) + 1}")
    out.append("")
    for i, a in enumerate(data["abas"]):
        out.append(f"#define CONQ_ABA_{a['id'].upper()} {i}")
    out += [f"#define CONQ_ABAS_COUNT {len(data['abas'])}", ""]
    for i, e in enumerate(data["diario"]):
        out.append(f"#define DIARIO_EVT_{e['id'].upper()} {i}")
    out += [f"#define DIARIO_EVT_COUNT {len(data['diario'])}", ""]
    return "\n".join(out)


def render_tabela(data: dict) -> str:
    validar(data)
    abas = {a["id"]: i for i, a in enumerate(data["abas"])}
    out = ["//",
           "// DO NOT MODIFY THIS FILE! It is auto-generated by tools/conquistas/gen_conquistas.py",
           "// from src/data/conquistas/conquistas.json (conquistas e diário de batalhas, POK-44).",
           "//", ""]
    for a in data["abas"]:
        out.append(f"static const u8 sConqAbaNome_{a['id']}[] = _(\"{_texto(a['nome'], a['id'])}\");")
    out += ["", "const u8 *const gConquistasAbaNomes[CONQ_ABAS_COUNT] =", "{"]
    out += [f"    [CONQ_ABA_{a['id'].upper()}] = sConqAbaNome_{a['id']}," for a in data["abas"]]
    out += ["};", ""]

    ordenadas = sorted(data["conquistas"], key=lambda c: c["num"])
    slots = {c["id"]: c["slot"] for c in ordenadas if c.get("degraus")}
    for c in ordenadas:
        cid = c["id"]
        out.append(f"static const u8 sConqNome_{cid}[] = _(\"{_texto(c['nome'], cid)}\");")
        if c.get("lista"):
            out.append(f"static const u16 sConqLista_{cid}[] = {{ {', '.join(c['lista'])}, 0xFFFF }};")
        if c.get("degraus"):
            out.append(f"static const u16 sConqDegraus_{cid}[] = {{ {', '.join(map(str, c['degraus']))} }};")
        n = max(1, len(c.get("degraus", [])))
        premios = c["premios"] * n if len(c["premios"]) == 1 else c["premios"]
        out.append(f"static const struct ConquistaPremio sConqPremios_{cid}[] =")
        out.append("{")
        out += [f"    {{ {p['item']}, {p['qtd']} }}," for p in premios]
        out += ["};", ""]

    out += ["const struct Conquista gConquistas[CONQ_COUNT] =", "{"]
    for c in ordenadas:
        cid = c["id"]
        campos = OrderedDict()
        campos["nome"] = f"sConqNome_{cid}"
        campos["aba"] = f"CONQ_ABA_{c['aba'].upper()}"
        campos["tipo"] = f"CONQ_TIPO_{c['tipo']}"
        campos["numDegraus"] = str(len(c.get("degraus", [])))
        campos["slotDegrau"] = str(slots[cid]) if cid in slots else "0xFF"
        campos["perdivel"] = "TRUE" if c.get("perdivel") else "FALSE"
        campos["ativa"] = "TRUE" if c.get("ativa", True) else "FALSE"
        if "param2" in c:
            campos["param2"] = _valor(c["param2"])
        if "param" in c:
            campos["param"] = _valor(c["param"])
        if c.get("lista"):
            campos["lista"] = f"sConqLista_{cid}"
        if c.get("degraus"):
            campos["degraus"] = f"sConqDegraus_{cid}"
        campos["premios"] = f"sConqPremios_{cid}"
        out.append(f"    [CONQ_{cid.upper()}] =")
        out.append("    {")
        out += [f"        .{k} = {v}," for k, v in campos.items()]
        out.append("    },")
    out += ["};", ""]

    for e in data["diario"]:
        did = e["id"]
        out.append(f"static const u8 sDiarioNome_{did}[] = _(\"{_texto(e['nome'], did)}\");")
        out.append(f"static const u8 sDiarioLocal_{did}[] = _(\"{_texto(e['local'], did)}\");")
        if e["tipo"] == "treinador":
            out.append(f"static const u16 sDiarioTreinadores_{did}[] = {{ {', '.join(e['treinadores'])}, 0xFFFF }};")
    out += ["", "const struct DiarioEvento gDiarioEventos[DIARIO_EVT_COUNT] =", "{"]
    for e in data["diario"]:
        did = e["id"]
        out += [f"    [DIARIO_EVT_{did.upper()}] =", "    {",
                f"        .nome = sDiarioNome_{did},",
                f"        .local = sDiarioLocal_{did},",
                f"        .tipo = DIARIO_TIPO_{e['tipo'].upper()},",
                f"        .lider = {'TRUE' if e.get('lider') else 'FALSE'},",
                f"        .rival = {'TRUE' if e.get('rival') else 'FALSE'},"]
        if e["tipo"] in ("lendario", "chefe"):
            out.append(f"        .especie = {e['especie']},")
        else:
            out.append(f"        .treinadores = sDiarioTreinadores_{did},")
        out.append("    },")
    out += ["};", ""]

    out += ["STATIC_ASSERT(CONQ_COUNT <= CONQ_MAX, ConquistasCountPassaDoMaximo);",
            "STATIC_ASSERT(DIARIO_EVT_COUNT <= DIARIO_MAX, DiarioCountPassaDoMaximo);"]
    for c in ordenadas:
        if c["tipo"] == "FLAGS_TODAS":
            out.append(f"STATIC_ASSERT({c['paramFim']} - {c['param']} + 1 == {c['param2']}, "
                       f"Conquista_{c['id']}_QuantidadeDeFlags);")
    out.append("")
    return "\n".join(out)


# ---- tabela em Markdown para o Cintra aprovar ------------------------------------------------

def _nomes_itens() -> dict[str, str]:
    """ITEM_* -> nome em PT-BR do jogo (campo `english` do items.json, já traduzido)."""
    itens = json.loads((REPO / "src" / "data" / "items.json").read_text(encoding="utf-8"))["items"]
    return {i["itemId"]: i["english"] for i in itens}


def _premio(p: dict, nomes: dict[str, str]) -> str:
    nome = nomes.get(p["item"], p["item"])
    return f"{p['qtd']}× {nome}"


def _premios_por_degrau(c: dict, nomes: dict[str, str]) -> str:
    degraus = c.get("degraus", [])
    if not degraus:
        return "; ".join(_premio(p, nomes) for p in c["premios"])
    premios = c["premios"] * len(degraus) if len(c["premios"]) == 1 else c["premios"]
    grupos: list[tuple[list[int], str]] = []
    for d, p in zip(degraus, premios):
        texto = _premio(p, nomes)
        if grupos and grupos[-1][1] == texto:
            grupos[-1][0].append(d)
        else:
            grupos.append(([d], texto))
    return "; ".join(f"{', '.join(map(str, ds))}: {t}" for ds, t in grupos)


def render_tabela_md(data: dict) -> str:
    validar(data)
    nomes = _nomes_itens()
    out = ["## Conquistas", ""]
    for aba in data["abas"]:
        itens = [c for c in data["conquistas"] if c["aba"] == aba["id"]]
        out += [f"### {aba['nome']} ({sum(1 for c in itens if c.get('ativa', True))} ativas)", "",
                "| Nome | Condição | Prêmio |", "|---|---|---|"]
        for c in itens:
            nome = c["nome"]
            marca = ""
            if not c.get("ativa", True):
                marca = " _(inativa)_"
            elif c.get("perdivel"):
                marca = " _(pode ser perdida)_"
            out.append(f"| {nome}{marca} | {c['condicao']} | {_premios_por_degrau(c, nomes)} |")
        out.append("")
    faixa_de = {item: f for f, itens in data["faixas"].items() for item in itens}
    por_faixa: dict[str, dict[str, list[str]]] = {f: {} for f in data["faixas"]}
    for c in data["conquistas"]:
        if not c.get("ativa", True):
            continue
        degraus = max(1, len(c.get("degraus", [])))
        premios = c["premios"] * degraus if len(c["premios"]) == 1 else c["premios"]
        for p in premios:
            item = p["item"][len("ITEM_"):]
            if item not in faixa_de:
                raise ValueError(f"{c['id']}: item {item} não está em nenhuma faixa")
            por_faixa[faixa_de[item]].setdefault(item, []).append(c["id"])
    out += ["## Prêmios por faixa (conquistas ativas)", "",
            "| Faixa | Item | Vezes que cai | Total entregue |", "|---|---|---:|---:|"]
    total_qtd: dict[str, int] = {}
    for c in data["conquistas"]:
        if not c.get("ativa", True):
            continue
        degraus = max(1, len(c.get("degraus", [])))
        for p in (c["premios"] * degraus if len(c["premios"]) == 1 else c["premios"]):
            total_qtd[p["item"][5:]] = total_qtd.get(p["item"][5:], 0) + p["qtd"]
    for faixa, itens in por_faixa.items():
        for item, quem in itens.items():
            out.append(f"| {faixa} | {nomes.get('ITEM_' + item, item)} | {len(quem)} | {total_qtd[item]} |")
    out.append("")
    out += ["## Diário de batalhas marcantes", "", "| Tipo | Nome | Local |", "|---|---|---|"]
    for e in data["diario"]:
        tipo = "líder" if e.get("lider") else "rival" if e.get("rival") else e["tipo"]
        out.append(f"| {tipo} | {e['nome']} | {e['local']} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    if len(argv) == 3 and argv[1] == "--tabela":
        sys.stdout.reconfigure(encoding="utf-8")
        print(render_tabela_md(carregar(argv[2])))
        return 0
    if len(argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    data = carregar(argv[1])
    Path(argv[2]).write_text(render_ids(data), encoding="utf-8")
    Path(argv[3]).write_text(render_tabela(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
