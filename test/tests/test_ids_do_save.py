"""POK-51: os ids de layout e de mapa vao para o save e nao podem andar.

O save guarda `mapLayoutId` (indice em `layouts.json`, de 1 em diante) e o par grupo/mapa (posicao em
`map_groups.json`). Inserir um layout ou um mapa no meio desloca todos os seguintes e um save antigo abre o mapa errado
(no POK-51 a sala de trofeus entrou no meio de `layouts.json` e deslocou 345 layouts). A foto de referencia
`dados/ids_do_save_6fc5229e5.json` e a lista ordenada de ids de 6fc5229e5 (a base do POK-51), versionada junto, sem git
na hora do teste. Para acrescentar, ponha no FIM; nunca edite a foto.
"""

import json
import re
import subprocess

from esteira.constants import _DEFINE, Constants, _strip_comments
from esteira.scenarios import REPO_ROOT

FOTO = json.loads((REPO_ROOT / "test" / "tests" / "dados" / "ids_do_save_6fc5229e5.json").read_text("utf-8"))
LAYOUTS = [l.get("id") for l in json.loads((REPO_ROOT / "data/layouts/layouts.json").read_text("utf-8"))["layouts"]]
GRUPOS = json.loads((REPO_ROOT / "data/maps/map_groups.json").read_text("utf-8"))


def test_layouts_so_acrescentam_no_fim():
    base = FOTO["layouts"]
    assert len(LAYOUTS) >= len(base), "layouts foram removidos"
    for i, antigo in enumerate(base):
        assert LAYOUTS[i] == antigo, (
            f"layout na posicao {i} (id {i + 1} no save) era {antigo} e agora e {LAYOUTS[i]}: "
            "layout novo vai no FIM de layouts.json")
    novos = [x for x in LAYOUTS[len(base):] if x]
    assert len(novos) == len(set(novos)) and not set(novos) & {x for x in base if x}


def test_grupos_de_mapas_so_acrescentam_no_fim():
    assert GRUPOS["group_order"] == FOTO["group_order"], "a ordem dos grupos de mapa mudou"
    for grupo, base in FOTO["grupos"].items():
        atual = GRUPOS[grupo]
        assert len(atual) >= len(base), f"{grupo}: mapas foram removidos"
        for i, antigo in enumerate(base):
            assert atual[i] == antigo, (
                f"{grupo}[{i}] era {antigo} e agora e {atual[i]}: mapa novo vai no FIM do grupo")


# --- POK-54: constantes com id no save ----------------------------------------------------------------------------------
#
# Espécies, golpes, habilidades, itens, flags, vars, gráficos de NPC e gritos também vão para o save (ou para dados que o
# save aponta). A foto `dados/ids_do_save_184573748.json` tem o valor de cada constante dessas famílias em 184573748 (a
# base do POK-54). Foi gerada uma vez, com `git show`, por `gerar_foto("184573748")` (rodar de test/:
# `python3 -c "from tests.test_ids_do_save import gerar_foto; gerar_foto('184573748')"`). Nunca edite a foto.

# família → header de include/constants que a define (CRY_ só em hoenn_cries.h: sound.h tem os CRY_MODE_*).
FAMILIAS = {
    "SPECIES_": "species.h",
    "NATIONAL_DEX_": "pokedex.h",
    "MOVE_": "moves.h",
    "ABILITY_": "abilities.h",
    "ITEM_": "items.h",
    "FLAG_": "flags.h",
    "VAR_": "vars.h",
    "OBJ_EVENT_GFX_": "event_objects.h",
    "CRY_": "hoenn_cries.h",
}
AUXILIARES = ["opponents.h"]  # flags.h usa MAX_TRAINERS_COUNT

# As letras velhas do Unown (espécies 252-276, que o jogo nunca cria) andam +4 na Dex nacional para os 4 extras
# (387-390) ficarem logo depois do Deoxys. Nunca são marcadas no save: nenhum bit da Pokédex muda de dono.
ANDAM_DE_PROPOSITO = re.compile(r"^NATIONAL_DEX_OLD_UNOWN_[A-Z]$")

_ENUM = re.compile(r"\benum\b[^{;]*\{(.*?)\}", re.S)


def _defines_e_enums(textos: dict[str, str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Todas as #define e entradas de enum dos headers; e os nomes que cada header define, na ordem."""
    defines: dict[str, str] = {}
    nomes: dict[str, list[str]] = {}
    for header, texto in textos.items():
        limpo = _strip_comments(texto)
        nomes[header] = []
        for linha in limpo.splitlines():
            m = _DEFINE.match(linha)
            if m:
                defines.setdefault(m.group(1), m.group(2))
                nomes[header].append(m.group(1))
        for corpo in _ENUM.findall(limpo):
            valor = -1
            for item in filter(None, (x.strip() for x in corpo.split(","))):
                nome, _, expr = (p.strip() for p in item.partition("="))
                valor = Constants({**defines, "_X": expr})._eval("_X") if expr else valor + 1
                defines[nome] = str(valor)
                nomes[header].append(nome)
    return defines, nomes


def constantes_do_save(ler) -> dict[str, dict[str, int]]:
    """`ler(header)` devolve o texto de include/constants/<header>. Resultado: família → {nome: valor}."""
    headers = sorted(set(FAMILIAS.values()) | set(AUXILIARES))
    defines, nomes = _defines_e_enums({h: ler(h) for h in headers})
    consts = Constants(defines)
    out: dict[str, dict[str, int]] = {}
    for prefixo, header in FAMILIAS.items():
        out[prefixo] = {n: consts._eval(n) for n in nomes[header] if n.startswith(prefixo)}
    return out


def gerar_foto(commit: str) -> None:
    def ler(header: str) -> str:
        return subprocess.run(["git", "show", f"{commit}:include/constants/{header}"], cwd=REPO_ROOT, check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout

    foto = {"_comentario": f"Constantes com id no save, congeladas em {commit} (base do POK-54). Nome antigo nunca "
                           "muda de valor; constante nova vai no FIM.",
            "familias": constantes_do_save(ler)}
    destino = REPO_ROOT / "test" / "tests" / "dados" / f"ids_do_save_{commit}.json"
    destino.write_text(json.dumps(foto, indent=1, ensure_ascii=False) + "\n", "utf-8")


FOTO_CONSTANTES = json.loads(
    (REPO_ROOT / "test" / "tests" / "dados" / "ids_do_save_184573748.json").read_text("utf-8"))["familias"]


def _constantes_de_hoje() -> dict[str, dict[str, int]]:
    return constantes_do_save(lambda h: (REPO_ROOT / "include" / "constants" / h).read_text("utf-8"))


def test_foto_das_constantes_cobre_as_familias():
    assert set(FOTO_CONSTANTES) == set(FAMILIAS)
    minimos = {"SPECIES_": 440, "NATIONAL_DEX_": 412, "MOVE_": 361, "ABILITY_": 78, "ITEM_": 370, "FLAG_": 1400,
               "VAR_": 270, "OBJ_EVENT_GFX_": 200, "CRY_": 130}
    for prefixo, minimo in minimos.items():
        assert len(FOTO_CONSTANTES[prefixo]) >= minimo, prefixo
    assert FOTO_CONSTANTES["SPECIES_"]["SPECIES_EGG"] == 412
    assert FOTO_CONSTANTES["SPECIES_"]["SPECIES_UNOWN_QMARK"] == 439
    assert FOTO_CONSTANTES["NATIONAL_DEX_"]["NATIONAL_DEX_OLD_UNOWN_B"] == 387
    assert FOTO_CONSTANTES["CRY_"]["CRY_CHIMECHO"] == 387


def test_constantes_so_acrescentam_no_fim():
    hoje = _constantes_de_hoje()
    for prefixo, base in FOTO_CONSTANTES.items():
        atual = hoje[prefixo]
        usados = set(atual.values())
        for nome, valor in base.items():
            if ANDAM_DE_PROPOSITO.match(nome):
                continue
            if nome in atual:
                assert atual[nome] == valor, (
                    f"{nome} era {valor} em 184573748 e hoje é {atual[nome]}: id novo vai no FIM, nunca no meio")
            else:
                # renomear (ou ocupar um id livre com nome próprio) é permitido; sumir com o id, não
                assert valor in usados, f"{nome} ({valor}) sumiu e ninguém ficou com o id"


def test_letras_velhas_do_unown_andam_so_os_4_extras():
    hoje = _constantes_de_hoje()["NATIONAL_DEX_"]
    for nome, valor in FOTO_CONSTANTES["NATIONAL_DEX_"].items():
        if ANDAM_DE_PROPOSITO.match(nome):
            assert hoje[nome] == valor + 4, nome
    assert [hoje[f"NATIONAL_DEX_{n}"] for n in ("GIBLE", "GABITE", "GARCHOMP", "DARKRAI")] == [387, 388, 389, 390]


def test_dex_flags_fixo_52():
    texto = (REPO_ROOT / "include" / "global.h").read_text("utf-8")
    assert re.search(r"^#define DEX_FLAGS_NO 52\s*(//.*)?$", texto, re.M), \
        "DEX_FLAGS_NO é o literal 52: o tamanho da Pokédex no save (416 bits) nunca muda"
    assert re.search(r"^STATIC_ASSERT\(NATIONAL_DEX_TOTAL <= DEX_FLAGS_NO \* 8,\s*\w+\);?", texto, re.M)
    k = Constants.load(str(REPO_ROOT), ["species.h"])
    assert k.species("SPECIES_EGG") == 412  # ROUND_BITS_TO_BYTES(412) = 52: o valor de antes
