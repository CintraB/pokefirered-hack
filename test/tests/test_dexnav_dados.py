"""DexNav (POK-47), Task 1: os mapas com encontro, as chances enumeradas e os mapas visitados (sem emulador).

`tools/dexnav/gerar.py` lê os cabeçalhos `_FireRed` de `src/data/wild_encounters.json` (132 cabeçalhos, 124 mapas:
a Caverna Mutante tem 9 tabelas para 1 mapa) e grava `src/data/dexnav_mapas.h` (commitado): um mapa por linha,
com o nome PT-BR "lugar + andar" e a região (Kanto ou Sevii), na ordem da Pokédex AREA. O mesmo arquivo tem o
espelho Python das regras de chance de `src/wild_encounter.c` (slots do FRLG, tabelas por horário do Hack 7,
metade LeafGreen do Hack 8, Caverna Mutante, Tanoby trancada), que a função C `DexNav_GetMapEntries` segue sem
sortear nada. O confronto com o sorteio real fica no emulador (`esteira/dexnav.py`, `dexnav/chances_reais`).
"""

import importlib.util
import re
import subprocess
import sys

import pytest

from esteira import check_text as ct
from esteira import hooks
from esteira.scenarios import REPO_ROOT

GERAR = REPO_ROOT / "tools" / "dexnav" / "gerar.py"
HEADER_MAPAS = REPO_ROOT / "src" / "data" / "dexnav_mapas.h"
DEXNAV_H = REPO_ROOT / "include" / "dexnav.h"
DEXNAV_C = REPO_ROOT / "src" / "dexnav_data.c"
WILD_C = REPO_ROOT / "src" / "wild_encounter.c"
GLOBAL_H = REPO_ROOT / "include" / "global.h"
OVERWORLD_C = REPO_ROOT / "src" / "overworld.c"
NEW_GAME_C = REPO_ROOT / "src" / "new_game.c"
FIELDMAP_C = REPO_ROOT / "src" / "fieldmap.c"
BASE_SHA = "0b2bb078e"  # hack-switch antes do POK-47


@pytest.fixture(scope="module")
def g():
    spec = importlib.util.spec_from_file_location("dexnav_gerar_t1", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _define(fonte: str, nome: str) -> int:
    m = re.search(rf"^#define {nome}\s+\(?(0x[0-9A-Fa-f]+|\d+)", fonte, re.M)
    assert m, nome
    return int(m.group(1), 0)


# --- mapas ---------------------------------------------------------------------------------------------------------

def test_124_mapas(g):
    assert len(g.cabecalhos_firered()) == 132
    mapas = g.mapas()
    ids = [m["id"] for m in mapas]
    assert len(ids) == len(set(ids)) == 124
    assert ids.count("MAP_SIX_ISLAND_ALTERING_CAVE") == 1
    assert _define(_ler(DEXNAV_H), "DEXNAV_MAP_COUNT") == 124
    assert re.search(r"^#define DEXNAV_MAPAS_GERADOS 124$", _ler(HEADER_MAPAS), re.M)
    # Kanto primeiro, depois Sevii; a região sai da seção do mapa
    regioes = [m["regiao"] for m in mapas]
    assert regioes == sorted(regioes) and set(regioes) == {0, 1}
    por_id = {m["id"]: m for m in mapas}
    for kanto in ("MAP_ROUTE1", "MAP_MT_MOON_B2F", "MAP_SAFARI_ZONE_WEST", "MAP_CERULEAN_CAVE_B1F", "MAP_PALLET_TOWN"):
        assert por_id[kanto]["regiao"] == 0, kanto
    for sevii in ("MAP_ONE_ISLAND_KINDLE_ROAD", "MAP_MT_EMBER_RUBY_PATH_B3F", "MAP_SIX_ISLAND_ALTERING_CAVE",
                  "MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER", "MAP_FIVE_ISLAND_LOST_CAVE_ROOM14"):
        assert por_id[sevii]["regiao"] == 1, sevii
    # ordem da Pokédex AREA: a Rota 1 vem antes da Rota 2, que vem antes do Monte Lua
    assert ids.index("MAP_ROUTE1") < ids.index("MAP_ROUTE2") < ids.index("MAP_MT_MOON_1F")
    assert ids.index("MAP_MT_MOON_1F") < ids.index("MAP_MT_MOON_B1F") < ids.index("MAP_MT_MOON_B2F")


def test_tabela_no_header(g):
    texto = _ler(HEADER_MAPAS)
    assert texto.startswith("// GERADO por tools/dexnav/gerar.py; não editar")
    linhas = re.findall(r"\{ MAP_GROUP\((MAP_\w+)\), MAP_NUM\(\1\), (DEXNAV_REGION_KANTO|DEXNAV_REGION_SEVII), "
                        r"sDexNavNome_(\d+) \},", texto)
    assert [m for m, _, _ in linhas] == [m["id"] for m in g.mapas()]
    assert [int(i) for _, _, i in linhas] == list(range(124))
    assert "const struct DexNavMap gDexNavMaps[DEXNAV_MAP_COUNT] =" in texto


def test_nomes_por_andar(g):
    nomes = {m["id"]: m["nome"] for m in g.mapas()}
    assert len(set(nomes.values())) == 124, "nomes repetidos"
    lua = [nomes[f"MAP_MT_MOON_{a}"] for a in ("1F", "B1F", "B2F")]
    assert len(set(lua)) == 3
    for nome, andar in zip(lua, ("1F", "B1F", "B2F")):
        assert nome.startswith("Monte Lua") and nome.endswith(" " + andar), nome
    assert nomes["MAP_SEAFOAM_ISLANDS_B3F"] == "Ilhas Seafoam B3F"
    assert nomes["MAP_ROUTE21_NORTH"] != nomes["MAP_ROUTE21_SOUTH"]
    assert nomes["MAP_ROUTE1"] == "Rota 1"  # um mapa só na seção: sem andar
    assert nomes["MAP_SIX_ISLAND_ALTERING_CAVE"] == "Caverna Mutante"
    # largura na coluna da lista (DEXNAV_NAME_WIDTH, FONT_NORMAL), medida pela esteira, e só caracteres do charmap
    largura = _define(_ler(DEXNAV_H), "DEXNAV_NAME_WIDTH")
    env = ct._load_env(REPO_ROOT)
    for mapa, nome in nomes.items():
        medida = ct.measure(nome, env, "normal")
        assert medida.widest <= largura, (mapa, nome, medida.widest)
        assert not medida.bad, (mapa, nome, medida.bad)
    # a checagem de texto do build mede os mesmos nomes com a mesma largura
    regra = ct.rule_for("src/data/dexnav_mapas.h", "sDexNavNome_0")
    assert regra is not None and regra.px == largura


def test_header_em_dia():
    r = subprocess.run([sys.executable, "-I", str(GERAR), "--conferir"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# --- chances -------------------------------------------------------------------------------------------------------

def _todas_as_enumeracoes(g):
    for mapa in g.mapas():
        conjuntos = range(9) if mapa["id"] == "MAP_SIX_ISLAND_ALTERING_CAVE" else (0,)
        for conjunto in conjuntos:
            yield mapa, conjunto, g.enumerar(mapa["id"], conjunto_mutante=conjunto)


def test_chances_somam(g):
    total_metodos = 0
    for mapa, conjunto, entradas in _todas_as_enumeracoes(g):
        assert entradas, mapa  # todo mapa da lista tem encontro (Tanoby liberada é o padrão do espelho)
        for metodo in range(g.METODOS):
            do_metodo = [e for e in entradas if e["metodo"] == metodo]
            if do_metodo:
                total_metodos += 1
            for p in range(3):
                soma = sum(e["chances"][p] for e in do_metodo)
                assert soma in (0, 1000), (mapa["id"], conjunto, metodo, p, soma)
            for e in do_metodo:
                assert e["periodos"] == sum(1 << p for p in range(3) if e["chances"][p]), e
                assert 1 <= e["min"] <= e["max"] <= 100, e
        chaves = [(e["especie"], e["metodo"]) for e in entradas]
        assert len(chaves) == len(set(chaves)), "uma entrada por (espécie, método)"
    assert total_metodos > 124


def test_cabe_no_buffer(g):
    maior = max(len(entradas) for _, _, entradas in _todas_as_enumeracoes(g))
    assert maior <= _define(_ler(DEXNAV_H), "DEXNAV_MAX_ENTRIES")


def test_regras_do_jogo(g):
    def por_especie(mapa, metodo, **kw):
        return {e["especie"]: e for e in g.enumerar(mapa, **kw) if e["metodo"] == metodo}

    # Hack 7: a Rota 1 muda de manhã/dia para a noite (Hoothoot só à noite)
    rota1 = por_especie("MAP_ROUTE1", g.LAND)
    assert rota1["SPECIES_HOOTHOOT"]["chances"][0] == 0 and rota1["SPECIES_HOOTHOOT"]["chances"][2] > 0
    # Hack 8: metade LeafGreen nos slots 4, 8 e 10 (10% + 4% + 1%) da Mansão 1F, sem tabela por horário
    mansao = por_especie("MAP_POKEMON_MANSION_1F", g.LAND)
    assert mansao["SPECIES_VULPIX"]["chances"] == mansao["SPECIES_GROWLITHE"]["chances"] == [75, 75, 75]
    assert (mansao["SPECIES_VULPIX"]["min"], mansao["SPECIES_VULPIX"]["max"]) == (30, 32)
    # ... e só quando a espécie do horário é a do FireRed: na Estrada da Vitória 1F a tabela por horário troca o
    # Arbok do slot 6 em todo período, então a metade Sandslash nunca aparece (TimeTableKeepsLandSlot)
    vr = por_especie("MAP_VICTORY_ROAD_1F", g.LAND)
    assert "SPECIES_SANDSLASH" not in vr and "SPECIES_ARBOK" not in vr
    # Safari Centro na água: Psyduck e Slowpoke dividem todos os slots
    agua = por_especie("MAP_SAFARI_ZONE_CENTER", g.WATER)
    assert agua["SPECIES_SLOWPOKE"]["chances"] == [500, 500, 500]
    # Caverna Mutante: cada conjunto é uma tabela só de uma espécie
    assert [e["especie"] for e in g.enumerar("MAP_SIX_ISLAND_ALTERING_CAVE")] == ["SPECIES_ZUBAT"]
    assert len({g.enumerar("MAP_SIX_ISLAND_ALTERING_CAVE", conjunto_mutante=c)[0]["especie"] for c in range(9)}) == 9
    # conjunto fora da faixa vale 0, como em GetCurrentMapWildMonHeaderId
    assert g.enumerar("MAP_SIX_ISLAND_ALTERING_CAVE", conjunto_mutante=9) == g.enumerar("MAP_SIX_ISLAND_ALTERING_CAVE")
    # Tanoby: Unown numa entrada só, e nenhuma antes de FLAG_SYS_UNLOCKED_TANOBY_RUINS
    camara = "MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER"
    assert [(e["especie"], e["chances"]) for e in g.enumerar(camara)] == [("SPECIES_UNOWN", [1000, 1000, 1000])]
    assert g.enumerar(camara, tanoby_liberado=False) == []
    # as varas ficam separadas, pela ordem do método
    pallet = g.enumerar("MAP_PALLET_TOWN")
    assert sorted({e["metodo"] for e in pallet}) == [g.WATER, g.OLD_ROD, g.GOOD_ROD, g.SUPER_ROD]


# --- C -------------------------------------------------------------------------------------------------------------

def test_interface_do_header():
    h = _ler(DEXNAV_H)
    for nome, valor in (("DEXNAV_METHOD_LAND", 0), ("DEXNAV_METHOD_WATER", 1), ("DEXNAV_METHOD_OLD_ROD", 2),
                        ("DEXNAV_METHOD_GOOD_ROD", 3), ("DEXNAV_METHOD_SUPER_ROD", 4), ("DEXNAV_METHOD_ROCK", 5),
                        ("DEXNAV_METHOD_COUNT", 6), ("DEXNAV_PERIOD_MORNING", 1), ("DEXNAV_PERIOD_DAY", 2),
                        ("DEXNAV_PERIOD_NIGHT", 4), ("DEXNAV_MAGIC", 0x31564E44)):
        assert _define(h, nome) == valor, nome
    assert 0x31564E44 == int.from_bytes(b"DNV1", "little")
    for decl in ("u8 DexNav_GetMapEntries(u8 mapIndex, struct DexNavEntry *out, u8 max);",
                 "u8 DexNav_CurrentPeriodBit(void);", "s16 DexNav_MapIndexOf(u8 mapGroup, u8 mapNum);",
                 "void DexNav_MarkVisited(u8 mapGroup, u8 mapNum);", "bool8 DexNav_IsVisited(u8 mapIndex);",
                 "void DexNav_InitSave(void);", "void DexNav_UpgradeOldSave(void);",
                 "extern const struct DexNavMap gDexNavMaps[DEXNAV_MAP_COUNT];"):
        assert decl in h, decl
    corpo = re.sub(r"//[^\n]*|/\*.*?\*/", "", re.search(r"struct DexNavEntry\n\{(.*?)\n\};", h, re.S).group(1))
    assert re.findall(r"(\w+)\s*(?:\[\w+\])?;", corpo) == ["species", "method", "minLevel", "maxLevel", "periods",
                                                         "rateX10"]


def test_save_dexnav():
    texto = _ler(GLOBAL_H)
    assert "u8 unused_3A94[" not in texto
    assert re.search(r"/\*0x3A94\*/ struct DexNavSave dexNav; // POK-47, era unused_3A94\[64\]", texto)
    corpo = re.search(r"struct DexNavSave\n\{(.*?)\n\};", texto, re.S).group(1)
    corpo = re.sub(r"//[^\n]*", "", corpo)
    assert re.findall(r"/\*(0x[0-9A-F]+)\*/\s*u(\d+) (\w+)(?:\[(\d+)\])?", corpo) == [
        ("0x00", "32", "magic", ""), ("0x04", "8", "visitedMaps", "16"), ("0x14", "8", "unused", "44")]
    fonte = _ler(DEXNAV_C)
    for esperado in ("sizeof(struct DexNavSave) == 64", "offsetof(struct SaveBlock1, dexNav) == 0x3A94",
                     "offsetof(struct SaveBlock1, registeredTexts) == 0x3AD4", "sizeof(struct SaveBlock1) == 0x3D68",
                     "DEXNAV_MAP_COUNT <= sizeof(((struct DexNavSave *)0)->visitedMaps) * 8",
                     "DEXNAV_MAPAS_GERADOS == DEXNAV_MAP_COUNT"):
        assert re.search(rf"STATIC_ASSERT\({re.escape(esperado)},", fonte), esperado


def test_save_antigo():
    fonte = _ler(DEXNAV_C)
    corpo = _corpo(fonte, "DexNav_UpgradeOldSave")
    assert "DEXNAV_MAGIC" in corpo and "FlagGet(FLAG_SYS_GAME_CLEAR)" in corpo
    # sem marcador: zera a área antes (lixo de um save antigo não vira mapa visitado)
    assert corpo.index("DEXNAV_MAGIC") < corpo.index("FLAG_SYS_GAME_CLEAR")
    assert "CpuFill" in corpo or "memset" in corpo
    init = _corpo(fonte, "DexNav_InitSave")
    assert "DEXNAV_MAGIC" in init and "FLAG_SYS_GAME_CLEAR" not in init
    # CONTINUAR (com e sem cenas do Quest Log) e jogo novo, junto do PC Portátil
    ow = _ler(OVERWORLD_C)
    for funcao in ("CB2_ContinueSavedGame", "CB2_EnterFieldFromQuestLog"):
        c = _corpo(ow, funcao)
        assert "DexNav_UpgradeOldSave();" in c, funcao
        assert c.index("DexNav_UpgradeOldSave();") < c.index("InitMapFromSavedGame();"), funcao
    novo = _corpo(_ler(NEW_GAME_C), "NewGameInitData")
    assert novo.index("ClearSav1();") < novo.index("DexNav_InitSave();") < novo.index("WarpToPlayersRoom();")


def test_marca_visitado_ao_carregar_mapa():
    # InitMapLayoutData roda em todo carregamento de mapa: warp, voo, borda de mapa, CONTINUAR e Quest Log
    corpo = _corpo(_ler(FIELDMAP_C), "InitMapLayoutData")
    assert "DexNav_MarkVisited(gSaveBlock1Ptr->location.mapGroup, gSaveBlock1Ptr->location.mapNum);" in corpo
    fm = _ler(FIELDMAP_C)
    for chamador in ("InitMap", "InitMapFromSavedGame"):
        assert "InitMapLayoutData(&gMapHeader);" in _corpo(fm, chamador)


def _base(rel: str) -> str:
    return subprocess.run(["git", "show", f"{BASE_SHA}:{rel}"], cwd=REPO_ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def test_caminho_real_intocado():
    """A enumeração é código novo: o sorteio real e a ordem do RNG ficam iguais à base."""
    atual, base = _ler(WILD_C), _base("src/wild_encounter.c")
    for funcao in ("GetLeafGreenSlotMon", "TimeTableKeepsLandSlot", "GetTimeOfDayLandSpecies",
                   "ChooseWildMonIndex_Land", "ChooseWildMonIndex_WaterRock", "ChooseWildMonIndex_Fishing",
                   "ChooseWildMonLevel", "GetCurrentMapWildMonHeaderId", "UnlockedTanobyOrAreNotInTanoby",
                   "TryGenerateWildMon", "GenerateFishingEncounter", "StandardWildEncounter", "TestRollWild"):
        assert _corpo(atual, funcao) == _corpo(base, funcao), funcao
    # a função nova e os auxiliares dela não sorteiam; o horário da tarde-noite (TIME_EVENING) nunca é pedido
    inicio = atual.index("// POK-47 DexNav")
    fim = atual.index("// POK-47 DexNav: fim")
    novo = atual[inicio:fim]
    codigo = re.sub(r"//[^\n]*|/\*.*?\*/", "", novo, flags=re.S)
    assert "Random(" not in codigo and "TIME_EVENING" not in codigo
    assert "GetTimeOfDayLandSpecies(" in codigo  # a mesma tabela por horário, só com manhã/tarde/noite
    # Caverna Mutante: dentro dela, a var do encontro; de fora, o conjunto do dia que o script de entrada grava
    mutante = _corpo(atual, "DexNav_GetWildHeader")
    assert "VarGet(VAR_ALTERING_CAVE_WILD_SET)" in mutante and "GetAlteringCaveSetForScript()" in mutante
    assert "SixIsland_AlteringCave_OnTransition" in _ler(REPO_ROOT / "data" / "maps" / "SixIsland_AlteringCave" /
                                                         "scripts.inc")
    assert "specialvar VAR_ALTERING_CAVE_WILD_SET, GetAlteringCaveSetForScript" in _ler(
        REPO_ROOT / "data" / "maps" / "SixIsland_AlteringCave" / "scripts.inc")
    assert "u8 DexNav_GetMapEntries(u8 mapIndex, struct DexNavEntry *out, u8 max)" in novo


def test_atalhos():
    assert (hooks.CMD_DEXNAV_ENTRY, hooks.CMD_DEXNAV_RATE, hooks.CMD_DEXNAV_ROLL) == (0xE0, 0xE1, 0xE2)
    fonte = _ler(REPO_ROOT / "src" / "test_hooks.c")
    for cmd in ("TEST_CMD_DEXNAV_ENTRY", "TEST_CMD_DEXNAV_RATE", "TEST_CMD_DEXNAV_ROLL"):
        assert f"case {cmd}:" in fonte, cmd
