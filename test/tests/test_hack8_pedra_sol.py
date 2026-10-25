"""Hack 8: a Pedra Solar à venda na Loja de Departamento de Celadon (4º andar), mais cara que as outras pedras."""

import json
import re

from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _celadon_4f_items() -> list[str]:
    src = _read("data/maps/CeladonCity_DepartmentStore_4F/scripts.inc")
    block = src.split("CeladonCity_DepartmentStore_4F_Items::", 1)[1].split("ITEM_NONE", 1)[0]
    return re.findall(r"\.2byte (ITEM_\w+)", block)


def _price(item: str) -> int:
    items = json.loads(_read("src/data/items.json"))["items"]
    return next(i["price"] for i in items if i["itemId"] == item)


def test_pedra_solar_a_venda_em_celadon_4f():
    itens = _celadon_4f_items()
    assert "ITEM_SUN_STONE" in itens
    # as outras pedras continuam lá
    for pedra in ("ITEM_FIRE_STONE", "ITEM_THUNDER_STONE", "ITEM_WATER_STONE", "ITEM_LEAF_STONE"):
        assert pedra in itens, pedra


def test_pedra_solar_custa_5000_mais_que_as_outras():
    assert _price("ITEM_SUN_STONE") == 5000
    for pedra in ("ITEM_FIRE_STONE", "ITEM_THUNDER_STONE", "ITEM_WATER_STONE", "ITEM_LEAF_STONE"):
        assert _price(pedra) < _price("ITEM_SUN_STONE"), pedra
