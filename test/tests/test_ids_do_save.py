"""POK-51: os ids de layout e de mapa vao para o save e nao podem andar.

O save guarda `mapLayoutId` (indice em `layouts.json`, de 1 em diante) e o par grupo/mapa (posicao em
`map_groups.json`). Inserir um layout ou um mapa no meio desloca todos os seguintes e um save antigo abre o mapa errado
(no POK-51 a sala de trofeus entrou no meio de `layouts.json` e deslocou 345 layouts). A foto de referencia
`dados/ids_do_save_6fc5229e5.json` e a lista ordenada de ids de 6fc5229e5 (a base do POK-51), versionada junto, sem git
na hora do teste. Para acrescentar, ponha no FIM; nunca edite a foto.
"""

import json

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
