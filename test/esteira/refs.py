"""Screenshots de referência por inicial: comparação pixel a pixel e aprovação.

As referências ficam em `test/referencias/<INICIAL>/<ponto>.png`, versionadas no Git. Diferença
de tela nunca reprova sozinha (é `aviso`): quem decide se a mudança é boa é o Cintra, que roda
`python3 -m esteira aprovar <pasta da execução>` para promover as telas novas a referência.
"""

import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops

from esteira.result import Result

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFS_DIR = "test/referencias"
# Nomes dos arquivos em OUT/telas/<ponto>.png gravados pelos cenários nos pontos-chave: os do
# modo rápido e os do tour de telas do modo completo (scenarios/full_screen_tour.py).
TOUR_POINTS = ("bolsa", "resumo", "pokedex", "opcoes", "cartao", "pc", "loja", "mapa")
KEY_POINTS = ("nome", "inicial", "batalha_rival", "captura", "save_continue") + TOUR_POINTS
DIFF_RED = (255, 0, 0)


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
    with Image.open(img_path) as shot_img, Image.open(ref_path) as ref_img:
        shot, ref = shot_img.convert("RGB"), ref_img.convert("RGB")
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

    O inicial vem de `starter` ou de `run_dir/meta.json` ("inicial"). Devolve os caminhos copiados.
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
    target = _refs_root(refs_dir) / starter
    copied: list[str] = []
    for point in KEY_POINTS:
        src = run / "telas" / f"{point}.png"
        if src.is_file():
            target.mkdir(parents=True, exist_ok=True)
            dst = target / f"{point}.png"
            shutil.copyfile(src, dst)
            copied.append(str(dst))
    return copied
