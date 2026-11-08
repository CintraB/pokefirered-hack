"""POK-54 (Task 9): o dossiê da Família Sombra em tela cheia (src/dossie.c, src/data/dossie_textos.h, include/dossie.h).

Leitura estática das páginas, dos textos e dos gráficos de `tools/familia_sombra/dossie.py`. A navegação e os
carimbos no jogo ficam no cenário `familia` (grupo `dossie/*`).
"""

import os
import re
import subprocess
import sys

from PIL import Image

from esteira import check_text
from esteira.scenarios import REPO_ROOT

TEXTOS_H = REPO_ROOT / "src" / "data" / "dossie_textos.h"
DOSSIE_C = REPO_ROOT / "src" / "dossie.c"
DOSSIE_H = REPO_ROOT / "include" / "dossie.h"
GRAFICOS = REPO_ROOT / "graphics" / "dossie"
CHEFES = ("Dom", "Cobrador", "Mercenario", "Pesadelo")
TITULOS = ("GENGAR, O DOM", "TYRANITAR, O COBRADOR", "GARCHOMP, O MERCENÁRIO", "DARKRAI, O PESADELO")
ESPECIES = ("GENGAR", "TYRANITAR", "GARCHOMP", "DARKRAI")
CAPA, DEPOIS = 0, 5


def _textos() -> dict[str, str]:
    """rótulo -> texto cru (as partes "..." de cada _( ) juntas, com os escapes como no fonte)."""
    fonte = TEXTOS_H.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"static const u8 (\w+)\[\] = _\((.*?)\);", fonte, re.S):
        out[m.group(1)] = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2)))
    return out


def _paginas() -> list[tuple[int, int, int, str, str]]:
    fonte = TEXTOS_H.read_text(encoding="utf-8")
    corpo = re.search(r"sDossiePaginas\[\] = \{(.*?)\n\};", fonte, re.S).group(1)
    consts = {"DOSSIE_CAPA": CAPA, "DOSSIE_DEPOIS": DEPOIS}
    paginas = []
    for m in re.finditer(r"\{(\w+), (\d+), (\d+), (\w+), (\w+)\}", corpo):
        chefe = consts.get(m.group(1)) if m.group(1) in consts else int(m.group(1))
        paginas.append((chefe, int(m.group(2)), int(m.group(3)), m.group(4), m.group(5)))
    return paginas


def _medidas() -> dict[str, int]:
    return {k: int(v) for k, v in re.findall(r"^#define DOSSIE_(\w+)\s+(\d+)\b", DOSSIE_H.read_text("utf-8"), re.M)}


def test_ordem_das_paginas():
    paginas = _paginas()
    assert paginas[0][0] == CAPA and paginas[-1][0] == DEPOIS, paginas
    chefes = [p[0] for p in paginas[1:-1]]
    assert chefes == sorted(chefes) and set(chefes) == {1, 2, 3, 4}, chefes
    for n in range(1, 5):
        da_ficha = [p for p in paginas if p[0] == n]
        assert 2 <= len(da_ficha) <= 3, (n, da_ficha)
        assert [p[1] for p in da_ficha] == list(range(1, len(da_ficha) + 1)), da_ficha
        assert {p[2] for p in da_ficha} == {len(da_ficha)}, da_ficha
        assert all(p[3] == f"sDossieTitulo_{CHEFES[n - 1]}" for p in da_ficha), da_ficha
        assert all(p[4].startswith(f"sDossieTexto_{CHEFES[n - 1]}") for p in da_ficha), da_ficha
    assert paginas[0][3] == "NULL" and paginas[-1][4] == "sDossieTexto_Depois"


def test_titulos():
    textos = _textos()
    assert [textos[f"sDossieTitulo_{c}"] for c in CHEFES] == list(TITULOS)
    # na lore, a espécie aparece sempre com o título, em vermelho
    for rotulo, texto in textos.items():
        for especie, titulo in zip(ESPECIES, TITULOS):
            if rotulo.startswith("sDossieTitulo_"):
                continue
            assert texto.count(especie) == texto.count("{COLOR RED}" + titulo + "{COLOR DARK_GRAY}"), (rotulo, texto)
    # cada ficha cita o título do chefe na 1ª página
    for c, titulo in zip(CHEFES, TITULOS):
        assert titulo in textos[f"sDossieTexto_{c}1"], c
    assert textos["sDossieGemeos_Dom"] == "Gêmeos: 2 Machamp"
    assert [textos[f"sDossieRosa_{c}"] for c in CHEFES] == ["Rosa vermelha", "Rosa dourada", "Rosa azul", "Rosa negra"]


def test_sem_travessao():
    for arq in (TEXTOS_H, DOSSIE_C, DOSSIE_H):
        assert "—" not in arq.read_text(encoding="utf-8"), arq


def test_textos_cabem():
    env = check_text._load_env(REPO_ROOT)
    medidas = _medidas()
    rel = "src/data/dossie_textos.h"

    def largura(s: str) -> int:
        return check_text.measure(s + "$", env).widest

    textos = _textos()
    for rotulo, texto in textos.items():
        regra = check_text.rule_for(rel, rotulo)
        assert regra is not None and regra.px is not None, f"{rotulo} sem regra de largura"
        m = check_text.measure(texto + "$", env)
        assert m.widest <= regra.px, (rotulo, m.widest, regra.px)
        assert m.lines <= regra.lines, (rotulo, m.lines, regra.lines)
        if rotulo.startswith("sDossieTexto_") and rotulo != "sDossieTexto_Depois":
            topo = texto.split("\\n")[0]
            assert largura(topo) <= medidas["LORE_TOPO_PX"], (rotulo, topo, largura(topo))
    # linhas montadas na tela: "FOLHA 3/3" no fim da aba e o rodapé "13/13 ►"
    total = len(_paginas())
    assert largura(textos["sDossieFolha_Prefixo"] + "3/3") <= medidas["FOLHA_PX"]
    rodape = f"{total}/{total} {{RIGHT_ARROW}}"
    assert 12 + largura(textos["sDossieCapa_Arquivo"]) + 6 <= 228 - largura(rodape)
    # a aba da ficha: "FICHA 1 DE 4" e "FOLHA 3/3" sem encostar (a aba vai de x = 12 a 156)
    assert 12 + largura(textos["sDossieAba_Ficha1"]) + 8 <= 156 - medidas["FOLHA_PX"]


def test_regras_da_checagem_de_texto():
    """A checagem da esteira (make firered_switch) mede os textos do dossiê com as medidas de include/dossie.h."""
    medidas = _medidas()
    rel = "src/data/dossie_textos.h"
    assert check_text.rule_for(rel, "sDossieTexto_Dom1").px == medidas["LORE_PX"]
    assert check_text.rule_for(rel, "sDossieTexto_Dom1").lines == medidas["LORE_LINHAS"]
    assert check_text.rule_for(rel, "sDossieTexto_Depois").lines == medidas["DEPOIS_LINHAS"]
    assert check_text.rule_for(rel, "sDossieTitulo_Mercenario").px == medidas["TITULO_PX"]


def test_gerador_confere():
    env = {k: v for k, v in os.environ.items() if k not in ("GIT_DIR", "GIT_WORK_TREE")}
    r = subprocess.run([sys.executable, "-I", str(REPO_ROOT / "tools/familia_sombra/dossie.py"), "--conferir"],
                       capture_output=True, text=True, env=env, cwd=REPO_ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_foto_tres_tons():
    for nome in ("dom", "cobrador", "mercenario", "pesadelo"):
        im = Image.open(GRAFICOS / f"foto_{nome}.png")
        assert im.size == (64, 64) and im.mode == "P", (nome, im.size, im.mode)
        px = list(im.tobytes())
        assert set(px) <= {1, 2, 3}, (nome, sorted(set(px)))
        for tom in (1, 2, 3):
            assert px.count(tom) >= 0.10 * len(px), (nome, tom, px.count(tom) / len(px))


def test_carimbo_dois_quadros():
    im = Image.open(GRAFICOS / "carimbo.png")
    assert im.size == (64, 64)
    px = im.load()
    for q in range(2):
        tinta = sum(1 for y in range(q * 32, q * 32 + 32) for x in range(64) if px[x, y])
        assert tinta > 100, (q, tinta)


def test_special_no_fim():
    specials = [s for s in re.findall(r"^\s*def_special (\w+)", (REPO_ROOT / "data/specials.inc").read_text("utf-8"), re.M)
                if "ElmEgg" not in s]   # os ovos do Elm (POK-28) vêm depois
    # o dossiê é o último special da Task 9; só os 2 da entrega da Jenny (Task 10) vêm depois dele
    assert specials[specials.index("Dossie_Abrir") + 1:] == ["FamiliaSombra_ApreendidoPendente",
                                                             "FamiliaSombra_EntregarApreendido"], specials[-4:]


def test_saida_continua_o_script_e_desliga_a_ajuda():
    fonte = DOSSIE_C.read_text(encoding="utf-8")
    assert "SetMainCallback2(CB2_ReturnToFieldContinueScriptPlayMapMusic)" in fonte
    assert "gHelpSystemEnabled = FALSE" in fonte
    assert re.search(r"#define DOSSIE_MUSICA MUS_POKE_TOWER\b", fonte)
    assert "AllocZeroed" in fonte and len(re.findall(r"^static EWRAM_DATA", fonte, re.M)) == 1
