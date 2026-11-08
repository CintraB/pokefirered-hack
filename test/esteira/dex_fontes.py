"""Fontes selvagens das espécies, só leitura de fonte: onde cada uma pode ser obtida na natureza.

É a parte "natureza" do levantamento `.superpowers/sdd/levantamento-dex/contar_dex_atual.py` (que é um script solto,
fora do Git, que imprime JSON e não se importa): as tabelas `_FireRed`, a grama por horário (Hack 7, só em mapa com
grama no FireRed), a metade LeafGreen dos slots que `tools/wild_leafgreen/gen_swaps.py` transforma em troca 50/50
(Hack 8) e as evoluções que um jogador consegue fazer sem troca (nível, amizade, pedras, itens à venda). Ficam de fora
os presentes, trocas e ovos da creche, que não dependem das tabelas. Mexeu numa regra de lá, mexa aqui.
"""

import importlib.util
import json
from pathlib import Path

from .evolutions import load_evolution_table

KINDS = ("land_mons", "water_mons", "rock_smash_mons", "fishing_mons")
EVO_SEM_ITEM = {"EVO_LEVEL", "EVO_FRIENDSHIP", "EVO_FRIENDSHIP_DAY", "EVO_FRIENDSHIP_NIGHT",
                "EVO_LEVEL_ATK_GT_DEF", "EVO_LEVEL_ATK_EQ_DEF", "EVO_LEVEL_ATK_LT_DEF",
                "EVO_LEVEL_SILCOON", "EVO_LEVEL_CASCOON", "EVO_LEVEL_NINJASK", "EVO_LEVEL_SHEDINJA",
                "EVO_BEAUTY"}
EVO_COM_ITEM = {"EVO_ITEM", "EVO_LEVEL_HOLD_ITEM", "EVO_LEVEL_UP_HOLD_ITEM"}
ITENS_OK = {"ITEM_FIRE_STONE", "ITEM_WATER_STONE", "ITEM_THUNDER_STONE", "ITEM_LEAF_STONE", "ITEM_MOON_STONE",
            "ITEM_KINGS_ROCK", "ITEM_METAL_COAT", "ITEM_DRAGON_SCALE", "ITEM_UP_GRADE", "ITEM_DEEP_SEA_TOOTH",
            "ITEM_DEEP_SEA_SCALE", "ITEM_PRISM_SCALE", "ITEM_SUN_STONE"}


def _gen_swaps(repo: Path):
    spec = importlib.util.spec_from_file_location("gen_swaps_dex_fontes", repo / "tools" / "wild_leafgreen" / "gen_swaps.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fontes_selvagens(repo: Path) -> dict[str, list[str]]:
    """Espécie (`SPECIES_X`) -> motivos pelos quais ela pode ser obtida só com as tabelas selvagens e evoluções."""
    wild = json.loads((repo / "src" / "data" / "wild_encounters.json").read_text(encoding="utf-8"))
    fontes: dict[str, list[str]] = {}

    def add(especie: str, motivo: str) -> bool:
        novo = especie not in fontes
        fontes.setdefault(especie, []).append(motivo)
        return novo

    mapas_com_grama = set()
    for grupo in wild["wild_encounter_groups"]:
        for enc in grupo["encounters"]:
            if not enc.get("base_label", "").endswith("_FireRed"):
                continue
            for kind in KINDS:
                if kind in enc:
                    if kind == "land_mons":
                        mapas_com_grama.add(enc["map"])
                    for m in enc[kind]["mons"]:
                        add(m["species"], f"selvagem {kind} {enc['map']}")
    for t in json.loads((repo / "src" / "data" / "wild_encounters_time.json").read_text(encoding="utf-8"))["tables"]:
        if t["map"] in mapas_com_grama:
            for periodo in ("morning", "day", "night"):
                for especie in t[periodo]:
                    add(especie, f"grama por horário {periodo} {t['map']}")
    for _, _, mon, _ in _gen_swaps(repo).compute_swaps(wild):
        add(mon["species"], "metade LeafGreen de um slot trocado")

    evolucoes = [(de, metodo, param, para) for de, itens in load_evolution_table(repo).items()
                 for metodo, param, para in itens]
    mudou = True
    while mudou:
        mudou = False
        for de, metodo, param, para in evolucoes:
            if de not in fontes:
                continue
            ok = metodo in EVO_SEM_ITEM or (metodo in EVO_COM_ITEM and param in ITENS_OK)
            if ok and add(para, f"evolução de {de} ({metodo} {param})"):
                mudou = True
    return fontes
