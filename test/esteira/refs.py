"""Screenshots de referência por inicial: comparação pixel a pixel e aprovação.

As referências ficam em `test/referencias/<INICIAL>/<ponto>.png`, versionadas no Git. Diferença
de tela nunca reprova sozinha (é `aviso`): quem decide se a mudança é boa é o Cintra, que roda
`python3 -m esteira aprovar <pasta da execução>` para promover as telas novas a referência.
"""

import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops

from esteira.evolution_page import PAGE_POINTS as SUMMARY_PAGE_POINTS
from esteira.evolution_page import SCREEN_POINTS as EVOLUTION_PAGE_POINTS
from esteira.evolutions import SCREEN_POINTS as EVOLUTION_POINTS
from esteira.ivev_page import SCREEN_POINTS as IVEV_PAGE_POINTS
from esteira.breeding import SHOP_SCREEN_POINTS   # Hack 6
from esteira.evolution_page import FRIENDSHIP_SCREEN_POINTS   # Hack 7 - frente D
from esteira.scenarios.full_novidades import SCREEN_POINTS as NOVIDADES_POINTS   # tela de novidades
from esteira.scenarios.full_fisico_fada import SCREEN_POINTS as FISICO_FADA_POINTS   # POK-43, 45
from esteira.result import Result

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFS_DIR = "test/referencias"
# Nomes dos arquivos em OUT/telas/<ponto>.png gravados pelos cenários nos pontos-chave: os do
# modo rápido e os do tour de telas do modo completo (scenarios/full_screen_tour.py).
TOUR_POINTS = ("bolsa", "resumo", "pokedex", "opcoes", "cartao", "pc", "loja", "mapa")
# Hack 7: telas de cenários da ROM de teste que mudam com o inicial (ou com a execução): NPC que
# anda no Centro Pokémon (relogio_*), contagem da Pokédex (pokedex_nacional), Poké Balls que
# sobraram na mesa do Oak (pos_liga_*). Por isso referência por inicial, não COMUM.
STARTER_DEPENDENT_POINTS = ("relogio_menu", "relogio_aviso_noite",   # Hack 7 — frente A
                            "pokedex_nacional",                       # Hack 7 — frente C
                            "pos_liga_ovo", "pos_liga_dinheiro", "pos_liga_objetivo",
                            # POK-15: partículas e selvagem saem do sorteio, que muda com o save
                            "batalha_clima_chuva", "batalha_clima_granizo", "batalha_clima_areia", "batalha_clima_sol")
KEY_POINTS = (("nome", "inicial", "batalha_rival", "captura", "save_continue") + TOUR_POINTS
              + STARTER_DEPENDENT_POINTS)
# POK-44, Task 7: a tela de conquistas (aba História e a Batalha com a perdida riscada) e o cartão com a dica do SELECT
CONQUISTAS_TELA_POINTS = ("conquistas_historia", "conquistas_batalha", "cartao_dica")
# Pontos cuja tela não depende do inicial (cena de evolução do cenário `evolucoes`, página
# EVOLUTION do resumo do cenário `resumo_evolucao`): uma referência só, em
# test/referencias/COMUM/<ponto>.png, vale para os três.
SHARED_REFS = "COMUM"
SHARED_POINTS = (EVOLUTION_POINTS + EVOLUTION_PAGE_POINTS + SUMMARY_PAGE_POINTS + IVEV_PAGE_POINTS
                 + SHOP_SCREEN_POINTS
                 + FRIENDSHIP_SCREEN_POINTS  # Hack 7 - frente D
                 + NOVIDADES_POINTS  # tela de novidades do Carvalho
                 + FISICO_FADA_POINTS  # POK-43, 45: resumo com FADA e ícones de categoria
                 + CONQUISTAS_TELA_POINTS)  # POK-44: tela de conquistas e a dica no cartão (cenário `conquistas`)
DIFF_RED = (255, 0, 0)
# O Pillow acusa PNG quebrado com OSError (UnidentifiedImageError é subclasse, "image file is
# truncated"), SyntaxError ("broken PNG file") ou ValueError, conforme onde o arquivo está estragado.
_UNREADABLE = (OSError, SyntaxError, ValueError)


def _refs_root(refs_dir: str) -> Path:
    """`refs_dir` relativo é relativo à raiz do repo (não ao diretório atual)."""
    path = Path(refs_dir)
    return path if path.is_absolute() else REPO_ROOT / path


def compare_ref(name: str, starter: str, img_path: str, refs_dir: str = DEFAULT_REFS_DIR) -> Result:
    """Compara `img_path` com `<refs_dir>/<starter>/<name>.png`.

    Sem referência -> `aviso`; pixels diferentes -> `aviso` com imagem de diff (pixels diferentes
    em vermelho sobre a tela escurecida) gravada ao lado de `img_path`; igual -> `ok`.
    """
    label = f"tela/{name}"
    ref_path = _refs_root(refs_dir) / starter / f"{name}.png"
    if not ref_path.is_file():
        return Result(label, "aviso",
                      f"sem referência para {starter}/{name} (aprove com `esteira aprovar`)",
                      [img_path])
    try:
        return _compare(label, starter, img_path, ref_path)
    except _UNREADABLE as exc:   # PNG corrompido/truncado (ou disco): aviso, nunca derruba a esteira
        return Result(label, "aviso", f"não consegui comparar com a referência de {starter}: {exc}",
                      [img_path, str(ref_path)])


def _open_rgb(path: str | Path, what: str) -> Image.Image:
    try:
        with Image.open(path) as img:
            return img.convert("RGB")
    except _UNREADABLE as exc:
        raise OSError(f"{what} ilegível ({path}): {type(exc).__name__}: {exc}") from exc


def _compare(label: str, starter: str, img_path: str, ref_path: Path) -> Result:
    shot = _open_rgb(img_path, "tela")
    ref = _open_rgb(ref_path, "referência")
    if shot.size != ref.size:
        return Result(label, "aviso",
                      f"tamanho diferente: tela {shot.size}, referência {ref.size}",
                      [img_path, str(ref_path)])
    diff = ImageChops.difference(shot, ref)
    box = diff.getbbox()
    if box is None:
        return Result(label, "ok", f"igual à referência de {starter}")
    mask = diff.convert("L").point(lambda v: 255 if v else 0)
    count = mask.histogram()[255]
    out = shot.point(lambda v: v // 3)
    out.paste(Image.new("RGB", shot.size, DIFF_RED), mask=mask)
    diff_path = Path(img_path).with_name(f"{Path(img_path).stem}.diff.png")
    out.save(diff_path)
    noun = "pixel diferente" if count == 1 else "pixels diferentes"
    return Result(label, "aviso", f"{count} {noun} da referência de {starter}",
                  [img_path, str(ref_path), str(diff_path)])


def approve_refs(run_dir: str, starter: str | None = None,
                 refs_dir: str = DEFAULT_REFS_DIR) -> list[str]:
    """Copia os screenshots de pontos-chave de `run_dir/telas/` para as referências do inicial.

    O inicial vem de `starter` ou de `run_dir/meta.json` ("inicial"). Os pontos de
    SHARED_POINTS vão para `<refs_dir>/COMUM/`. Devolve os caminhos copiados.
    """
    run = Path(run_dir)
    if starter is None:
        try:
            starter = json.loads((run / "meta.json").read_text(encoding="utf-8")).get("inicial")
        except (OSError, ValueError):
            starter = None
    if not starter:
        raise ValueError(f"inicial desconhecido para {run}: sem meta.json com 'inicial' "
                         f"(passe o inicial explicitamente)")
    copied: list[str] = []
    for points, folder in ((KEY_POINTS, starter), (SHARED_POINTS, SHARED_REFS)):
        target = _refs_root(refs_dir) / folder
        for point in points:
            src = run / "telas" / f"{point}.png"
            if src.is_file():
                target.mkdir(parents=True, exist_ok=True)
                dst = target / f"{point}.png"
                shutil.copyfile(src, dst)
                copied.append(str(dst))
    return copied
