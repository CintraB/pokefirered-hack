"""POK-54 (Task 3): Gible, Gabite, Garchomp e Darkrai em todas as tabelas do jogo.

As 4 espécies (ids 440-443, Dex interna 387-390) entram em cada tabela indexada por espécie ou por número da Dex:
dados, golpes, evolução, gráficos, ícone, pegada, posição na tela, Pokédex (entrada, texto, ordens e habitat) e
grito. Os dados vêm de `tools/gen4/gen4.json` e as coordenadas de `tools/gen4/coordenadas.json` (Task 1). Estes
testes leem o C como texto.

Fora da lista de tabelas, de propósito:
- easy chat: nenhuma palavra nova (o grupo POKéMON do easy chat é fixo);
- `src/dexnav_data.c` e `tools/dexnav/`: nenhuma das 4 aparece na natureza;
- `src/data/rematch_tiers.h` e `tools/revanches/temas.json`: não entram em times de treinador;
- `tools/hgss_encounters/`: não são selvagens;
- `tools/gen6/`: nenhuma é do tipo Fada;
- seguidor (`follower_species.h`): entra na Task 4.
"""

import json
import re

import pytest

from esteira.scenarios import REPO_ROOT

GEN4 = json.loads((REPO_ROOT / "tools" / "gen4" / "gen4.json").read_text("utf-8"))["especies"]
COORDS = json.loads((REPO_ROOT / "tools" / "gen4" / "coordenadas.json").read_text("utf-8"))

# (constante, nome dos símbolos, pasta/arquivo)
ESPECIES = [("GIBLE", "Gible", "gible"), ("GABITE", "Gabite", "gabite"),
            ("GARCHOMP", "Garchomp", "garchomp"), ("DARKRAI", "Darkrai", "darkrai")]
TODAS = tuple(c for c, _, _ in ESPECIES)


def _ler(rel: str) -> str:
    return (REPO_ROOT / rel).read_text("utf-8")


def _bloco(texto: str, inicio: str) -> str:
    """O corpo `{ ... };` do primeiro array cuja declaração contém `inicio`."""
    i = texto.index(inicio)
    abre = texto.index("{", i)
    fim = re.search(r"^\};", texto[abre:], re.M)
    return texto[abre:abre + fim.start()]


def _secao_asm(texto: str, rotulo: str) -> str:
    """As linhas depois de `rotulo::` até a próxima linha em branco seguida de `.align` ou o fim."""
    i = texto.index(f"{rotulo}::")
    resto = texto[i + len(rotulo) + 2:]
    fim = resto.find("\n\n")
    return resto if fim < 0 else resto[:fim]


# Cada linha: (rótulo, arquivo, onde procurar dentro do arquivo, padrões por espécie, espécies)
# Um padrão é uma regex com {C} (constante), {N} (nome dos símbolos) e {P} (pasta); (regex, n) exige n ocorrências.
LINHAS = [
    ("species_info", "src/data/pokemon/species_info.h", None, [r"\[SPECIES_{C}\] =\s*\{{"], TODAS),
    ("level_up_learnsets", "src/data/pokemon/level_up_learnsets.h", None,
     [r"static const u16 s{N}LevelUpLearnset\[\] = \{{"], TODAS),
    ("level_up_learnset_pointers", "src/data/pokemon/level_up_learnset_pointers.h", None,
     [r"\[SPECIES_{C}\] = s{N}LevelUpLearnset,"], TODAS),
    # Garchomp é só alvo; Darkrai não evolui (test_evolucoes confere que não tem entrada)
    ("evolution", "src/data/pokemon/evolution.h", None, [r"\bSPECIES_{C}\b"], ("GIBLE", "GABITE", "GARCHOMP")),
    ("tmhm_learnsets", "src/data/pokemon/tmhm_learnsets.h", None, [r"\[SPECIES_{C}\]\s*= TMHM_LEARNSET\("], TODAS),
    ("tutor_learnsets", "src/data/pokemon/tutor_learnsets.h", None, [r"\[SPECIES_{C}\] = (TUTOR\(|0,)"], TODAS),
    ("egg_moves", "src/data/pokemon/egg_moves.h", None, [r"egg_moves\({C},"], ("GIBLE",)),   # só a forma base
    ("cry_ids", "src/data/pokemon/cry_ids.h", None,
     [r"\[SPECIES_{C} - HOENN_MON_SPECIES_START\] = CRY_{C},"], TODAS),
    ("pokedex_entries", "src/data/pokemon/pokedex_entries.h", None,
     [r"\[NATIONAL_DEX_{C}\] =\s*\{{\s*\.categoryName = _\(\"[^\"]+\"\),", r"\.description = g{N}PokedexText,"],
     TODAS),
    ("pokedex_text_fr", "src/data/pokemon/pokedex_text_fr.h", None, [r"const u8 g{N}PokedexText\[\] = _\("], TODAS),
    ("pokedex_text_lg", "src/data/pokemon/pokedex_text_lg.h", None, [r"const u8 g{N}PokedexText\[\] = _\("], TODAS),
    ("ordem_alfabetica", "src/data/pokemon/pokedex_orders.h", "gPokedexOrder_Alphabetical",
     [r"\bNATIONAL_DEX_{C},"], TODAS),
    ("ordem_peso", "src/data/pokemon/pokedex_orders.h", "gPokedexOrder_Weight", [r"\bNATIONAL_DEX_{C}\b"], TODAS),
    ("ordem_altura", "src/data/pokemon/pokedex_orders.h", "gPokedexOrder_Height", [r"\bNATIONAL_DEX_{C}\b"], TODAS),
    ("ordem_tipo", "src/data/pokemon/pokedex_orders.h", "gPokedexOrder_Type", [r"\bSPECIES_{C}\b"], TODAS),
    ("pokedex_categories", "src/data/pokemon/pokedex_categories.h", None, [r"^\s+SPECIES_{C},$"], TODAS),
    ("species_names", "src/data/text/species_names.h", None, [r"\[SPECIES_{C}\] = _\(\"{C}\"\),"], TODAS),
    ("graphics_pokemon", "src/data/graphics/pokemon.h", None,
     [r'const u32 gMonFrontPic_{N}\[\] = INCBIN_U32\("graphics/pokemon/{P}/front\.4bpp\.lz"\);',
      r'const u32 gMonPalette_{N}\[\] = INCBIN_U32\("graphics/pokemon/{P}/normal\.gbapal\.lz"\);',
      r'const u32 gMonBackPic_{N}\[\] = INCBIN_U32\("graphics/pokemon/{P}/back\.4bpp\.lz"\);',
      r'const u32 gMonShinyPalette_{N}\[\] = INCBIN_U32\("graphics/pokemon/{P}/shiny\.gbapal\.lz"\);',
      r'const u8 gMonIcon_{N}\[\] = INCBIN_U8\("graphics/pokemon/{P}/icon\.4bpp"\);',
      r'const u8 gMonFootprint_{N}\[\] = INCBIN_U8\("graphics/pokemon/{P}/footprint\.1bpp"\);'], TODAS),
    # dois blocos: pics (6 extern) e ícones (o extern do ícone de novo)
    ("graphics_h", "include/graphics.h", None,
     [r"extern const u32 gMonFrontPic_{N}\[\];", r"extern const u32 gMonPalette_{N}\[\];",
      r"extern const u32 gMonBackPic_{N}\[\];", r"extern const u32 gMonShinyPalette_{N}\[\];",
      (r"extern const u8 gMonIcon_{N}\[\];", 2), r"extern const u8 gMonFootprint_{N}\[\];"], TODAS),
    ("front_pic_table", "src/data/pokemon_graphics/front_pic_table.h", None,
     [r"SPECIES_SPRITE\({C}, gMonFrontPic_{N}\),"], TODAS),
    ("back_pic_table", "src/data/pokemon_graphics/back_pic_table.h", None,
     [r"SPECIES_SPRITE\({C}, gMonBackPic_{N}\),"], TODAS),
    ("palette_table", "src/data/pokemon_graphics/palette_table.h", None,
     [r"SPECIES_PAL\({C}, gMonPalette_{N}\),"], TODAS),
    ("shiny_palette_table", "src/data/pokemon_graphics/shiny_palette_table.h", None,
     [r"SPECIES_SHINY_PAL\({C}, gMonShinyPalette_{N}\),"], TODAS),
    ("front_pic_coordinates", "src/data/pokemon_graphics/front_pic_coordinates.h", None,
     [r"\[SPECIES_{C}\] =\s*\{{\s*\.size = MON_COORDS_SIZE\("], TODAS),
    ("back_pic_coordinates", "src/data/pokemon_graphics/back_pic_coordinates.h", None,
     [r"\[SPECIES_{C}\] =\s*\{{\s*\.size = MON_COORDS_SIZE\("], TODAS),
    ("enemy_mon_elevation", "src/data/pokemon_graphics/enemy_mon_elevation.h", None,
     [r"\[SPECIES_{C}\] = \d+,"], TODAS),
    ("footprint_table", "src/data/pokemon_graphics/footprint_table.h", None,
     [r"\[SPECIES_{C}\] = gMonFootprint_{N},"], TODAS),
    ("gMonIconTable", "src/pokemon_icon.c", "gMonIconTable[]", [r"\[SPECIES_{C}\]\s*= gMonIcon_{N},"], TODAS),
    ("gMonIconPaletteIndices", "src/pokemon_icon.c", "gMonIconPaletteIndices[]",
     [r"\[SPECIES_{C}\]\s*= [0-2],"], TODAS),
    ("sMonPosAttributes", "src/menu2.c", "sMonPosAttributes[]", [r"\[SPECIES_{C}\s*- 1\] = \{{"], TODAS),
    ("sSpeciesToNationalPokedexNum", "src/pokemon.c", "sSpeciesToNationalPokedexNum[",
     [r"SPECIES_TO_NATIONAL\({C}\),"], TODAS),
    ("gCryTable", "sound/cry_tables.inc", "gCryTable", [r"\tcry Cry_{N}$"], TODAS),
    ("gCryTable_Reverse", "sound/cry_tables.inc", "gCryTable_Reverse", [r"\tcry_reverse Cry_{N}$"], TODAS),
    ("direct_sound_data", "sound/direct_sound_data.inc", None,
     [r'\.align 2\nCry_{N}::\n\t\.incbin "sound/direct_sound_samples/cries/{P}\.bin"'], TODAS),
]


def _trecho(arquivo: str, onde: str | None) -> str:
    texto = _ler(arquivo)
    if onde is None:
        return texto
    if arquivo.endswith(".inc"):
        return _secao_asm(texto, onde)
    return _bloco(texto, onde)


def test_lista_tem_as_34_linhas_do_plano():
    assert len(LINHAS) == 34
    assert len({rotulo for rotulo, *_ in LINHAS}) == 34


@pytest.mark.parametrize("rotulo,arquivo,onde,padroes,especies", LINHAS, ids=[linha[0] for linha in LINHAS])
def test_cada_tabela_tem_as_4(rotulo, arquivo, onde, padroes, especies):
    texto = _trecho(arquivo, onde)
    faltam = []
    for c, n, p in ESPECIES:
        if c not in especies:
            continue
        for padrao in padroes:
            regex, minimo = padrao if isinstance(padrao, tuple) else (padrao, 1)
            achados = re.findall(regex.format(C=c, N=n, P=p), texto, re.M)
            if len(achados) < minimo:
                faltam.append(f"{c}: {regex.format(C=c, N=n, P=p)} ({len(achados)}/{minimo})")
    assert not faltam, f"{rotulo} ({arquivo}): " + "; ".join(faltam)


# --- dados contra o gen4.json ------------------------------------------------------------------

def _species_info(c: str) -> dict[str, str]:
    m = re.search(rf"\[SPECIES_{c}\] =\s*\{{(.*?)\n    \}},", _ler("src/data/pokemon/species_info.h"), re.S)
    assert m, c
    return dict(re.findall(r"\.(\w+) = (.+?),\n", m.group(1) + "\n"))


def _learnset(n: str) -> list[list]:
    m = re.search(rf"s{n}LevelUpLearnset\[\] = \{{(.*?)LEVEL_UP_END", _ler("src/data/pokemon/level_up_learnsets.h"), re.S)
    return [[int(lv), mv] for lv, mv in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+), (MOVE_\w+)\)", m.group(1))]


def _entrada_tabela(arquivo: str, c: str) -> str:
    m = re.search(rf"\[SPECIES_{c}\]\s*= (.*?)(?=\n\n|\n\s*\[SPECIES_|\n\}};)", _ler(arquivo), re.S)
    assert m, (arquivo, c)
    return m.group(1)


def _dex(c: str) -> dict:
    m = re.search(rf"\[NATIONAL_DEX_{c}\] =\s*\{{(.*?)\n    \}},", _ler("src/data/pokemon/pokedex_entries.h"), re.S)
    assert m, c
    return dict(re.findall(r"\.(\w+) = (.+?),\n", m.group(1) + "\n"))


@pytest.mark.parametrize("c,n,p", ESPECIES)
def test_dados_batem_com_gen4_json(c, n, p):
    g = GEN4[p]
    info = _species_info(c)
    stats = [int(info[k]) for k in ("baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
                                    "baseSpDefense")]
    evs = [int(info[k]) for k in ("evYield_HP", "evYield_Attack", "evYield_Defense", "evYield_Speed",
                                  "evYield_SpAttack", "evYield_SpDefense")]
    assert stats == g["stats"] and evs == g["evs"]
    assert info["types"] == "{" + ", ".join(g["tipos"]) + "}"
    assert int(info["catchRate"]) == g["captura"] and int(info["expYield"]) == g["exp"]
    assert info["genderRatio"] == g["sexo"] and int(info["eggCycles"]) == g["ciclos"]
    assert int(info["friendship"]) == g["amizade"] and info["growthRate"] == g["crescimento"]
    assert info["eggGroups"] == "{" + ", ".join(g["ovos"]) + "}"
    assert info["abilities"] == "{" + ", ".join(g["habilidades"]) + "}"
    assert info["bodyColor"] == g["cor"]
    # golpes por nível: a lista crua da Gen 4 (com as trocas), duplicatas inclusive, como no Salamence
    assert _learnset(n) == g["nivel"]
    tmhm = re.findall(r"TMHM\((\w+)\)", _entrada_tabela("src/data/pokemon/tmhm_learnsets.h", c))
    assert sorted(tmhm) == sorted(g["mt"])
    tutor = re.findall(r"TUTOR\((MOVE_\w+)\)", _entrada_tabela("src/data/pokemon/tutor_learnsets.h", c))
    assert sorted(tutor) == sorted(g["tutor"])
    ovo = re.search(rf"egg_moves\({c},(.*?)\)", _ler("src/data/pokemon/egg_moves.h"), re.S)
    assert (re.findall(r"MOVE_\w+", ovo.group(1)) if ovo else []) == g["ovo"]
    dex = _dex(c)
    assert int(dex["height"]) == g["altura"] and int(dex["weight"]) == g["peso"]


@pytest.mark.parametrize("c,n,p", ESPECIES)
def test_coordenadas_e_icone_de_coordenadas_json(c, n, p):
    for arquivo, lado in (("front_pic_coordinates.h", "front"), ("back_pic_coordinates.h", "back")):
        m = re.search(rf"\[SPECIES_{c}\] =\s*\{{\s*\.size = MON_COORDS_SIZE\((\d+), (\d+)\),\s*\.y_offset = (\d+),",
                      _ler(f"src/data/pokemon_graphics/{arquivo}"))
        assert [int(x) for x in m.groups()] == COORDS[p][lado], (c, lado)
    icones = _bloco(_ler("src/pokemon_icon.c"), "gMonIconPaletteIndices[]")
    assert re.search(rf"\[SPECIES_{c}\]\s*= (\d),", icones).group(1) == str(COORDS[p]["icone_paleta"])


# Pokédex e posição na tela copiadas de uma espécie de silhueta parecida
MOLDES = {"GIBLE": "BAGON", "GABITE": "SHELGON", "GARCHOMP": "SALAMENCE", "DARKRAI": "DUSCLOPS"}


@pytest.mark.parametrize("c", TODAS)
def test_escalas_e_posicao_copiadas_do_molde(c):
    molde = MOLDES[c]
    campos = ("pokemonScale", "pokemonOffset", "trainerScale", "trainerOffset")
    assert [_dex(c)[k] for k in campos] == [_dex(molde)[k] for k in campos]
    pos = _bloco(_ler("src/menu2.c"), "sMonPosAttributes[]")
    linha = lambda e: re.search(rf"\[SPECIES_{e}\s*- 1\] = (\{{[^}}]*\}})", pos).group(1)
    assert linha(c) == linha(molde)


def test_categorias_e_texto_da_dex():
    assert {c: _dex(c)["categoryName"] for c in TODAS} == {
        "GIBLE": '_("Tubarão")', "GABITE": '_("Caverna")', "GARCHOMP": '_("Mach")', "DARKRAI": '_("Breu")'}
    fr, lg = _ler("src/data/pokemon/pokedex_text_fr.h"), _ler("src/data/pokemon/pokedex_text_lg.h")
    for _c, n, _p in ESPECIES:
        textos = [re.search(rf"const u8 g{n}PokedexText\[\] = _\((.*?)\);", t, re.S).group(1) for t in (fr, lg)]
        assert textos[0] == textos[1], n                      # o mesmo texto PT-BR nos dois
        assert textos[0].count("\\n") == 2, n                 # 3 linhas
        assert re.search(rf"const u8 g{n}PokedexTextUnused\[\] = _\(\"\"\);", fr), n


def test_evolucoes():
    texto = _ler("src/data/pokemon/evolution.h")
    entradas = dict(re.findall(r"\[(SPECIES_\w+)\]\s*= (\{.*\}),", texto))
    assert entradas["SPECIES_GIBLE"] == "{{EVO_LEVEL, 24, SPECIES_GABITE}}"
    assert entradas["SPECIES_GABITE"] == "{{EVO_LEVEL, 48, SPECIES_GARCHOMP}}"
    assert "SPECIES_GARCHOMP" not in entradas and "SPECIES_DARKRAI" not in entradas


def test_darkrai_nao_cruza():
    info = _species_info("DARKRAI")
    assert info["eggGroups"] == "{EGG_GROUP_UNDISCOVERED, EGG_GROUP_UNDISCOVERED}"
    assert info["genderRatio"] == "MON_GENDERLESS"
    assert not re.search(r"egg_moves\((GABITE|GARCHOMP|DARKRAI),", _ler("src/data/pokemon/egg_moves.h"))


# --- ordens da Pokédex ---------------------------------------------------------------------------

def _dex_nums() -> dict[str, int]:
    corpo = re.search(r"enum\s*\{(.*?)\};", _ler("include/constants/pokedex.h"), re.S).group(1)
    corpo = re.sub(r"//[^\n]*", "", corpo)
    nomes = [n.strip() for n in corpo.split(",") if n.strip()]
    return {n: i for i, n in enumerate(nomes)}


def _nomes() -> dict[str, str]:
    return dict(re.findall(r"\[SPECIES_(\w+)\] = _\(\"([^\"]*)\"\)", _ler("src/data/text/species_names.h")))


def _tipos() -> dict[str, int]:
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"#define (TYPE_\w+)\s+(\d+)", _ler("include/constants/pokemon.h"))}


def _lista(nome: str) -> list[str]:
    return re.findall(r"(?:NATIONAL_DEX|SPECIES)_(\w+)", _bloco(_ler("src/data/pokemon/pokedex_orders.h"), nome))


def _vizinhos(lista: list[str], c: str) -> tuple[str, str]:
    i = lista.index(c)
    assert lista.count(c) == 1, c
    return lista[i - 1], lista[i + 1]


@pytest.mark.parametrize("c", TODAS)
def test_ordens_da_dex(c):
    nomes = _nomes()
    alfa = _lista("gPokedexOrder_Alphabetical")
    antes, depois = _vizinhos(alfa, c)
    assert nomes[antes] < nomes[c] < nomes[depois], (antes, c, depois)
    for lista, campo in (("gPokedexOrder_Weight", "weight"), ("gPokedexOrder_Height", "height")):
        antes, depois = _vizinhos(_lista(lista), c)
        valor = lambda e: int(_dex(e)[campo])
        assert valor(antes) <= valor(c) <= valor(depois), (lista, antes, c, depois)
    # tipo: grupo do 1º tipo; dentro dele os de tipo único primeiro, depois pelo 2º tipo e pelo número da Dex
    tipos, dex = _tipos(), _dex_nums()

    def chave(e: str) -> tuple:
        t1, t2 = (tipos[t] for t in re.findall(r"TYPE_\w+", _species_info(e)["types"]))
        return t1, t1 != t2, t2, dex[f"NATIONAL_DEX_{e}"]

    antes, depois = _vizinhos(_lista("gPokedexOrder_Type"), c)
    assert chave(antes)[0] == chave(c)[0] or chave(depois)[0] == chave(c)[0], (antes, c, depois)
    if chave(antes)[0] == chave(c)[0]:
        assert chave(antes) < chave(c), (antes, c)
    if chave(depois)[0] == chave(c)[0]:
        assert chave(c) < chave(depois), (c, depois)


def test_listas_por_ordem_percorrem_a_tabela_inteira():
    """Peso e altura cresceram de 386 para 390 entradas: o laço vai até o fim de cada lista (o filtro `<= max_n`
    continua escondendo os extras até a Task 6), senão os 4 mais pesados/altos sumiriam da Pokédex."""
    tela = _ler("src/pokedex_screen.c")
    for lista in ("gPokedexOrder_Weight", "gPokedexOrder_Height"):
        assert re.search(rf"for \(i = 0; i < NELEMS\({lista}\); i\+\+\)", tela), lista
    for lista in ("gPokedexOrder_Weight", "gPokedexOrder_Height"):
        assert len(_lista(lista)) == 390
    assert len(_lista("gPokedexOrder_Alphabetical")) == 415 and len(_lista("gPokedexOrder_Type")) == 415


def _paginas() -> dict[str, list[str]]:
    texto = _ler("src/data/pokemon/pokedex_categories.h")
    return {m.group(1): re.findall(r"SPECIES_(\w+)", m.group(2))
            for m in re.finditer(r"static const u16 sDexCategory_(\w+)\[\] = \{(.*?)\};", texto, re.S)}


def _categorias() -> dict[str, list[str]]:
    texto = _ler("src/data/pokemon/pokedex_categories.h")
    return {m.group(1): re.findall(r"DEX_CATEGORY\((\w+)\)", m.group(2))
            for m in re.finditer(r"PokedexCategoryPage sDexCategory_(\w+)\[\] = \{(.*?)\};", texto, re.S)}


def test_categorias():
    paginas, categorias = _paginas(), _categorias()
    usadas = [p for ps in categorias.values() for p in ps]
    for c in TODAS:
        onde = [p for p in usadas if c in paginas[p]]
        assert len(onde) == 1, (c, onde)
    assert all(len(paginas[p]) <= 4 for p in usadas)
    pagina = lambda c: next(p for p in usadas if c in paginas[p])
    assert pagina("GIBLE") == pagina("GABITE") == pagina("GARCHOMP")
    assert paginas[pagina("GIBLE")] == ["GIBLE", "GABITE", "GARCHOMP"]
    assert pagina("GIBLE") in categorias["CavePkmn"] and categorias["CavePkmn"][-1] == pagina("GIBLE")
    assert paginas[pagina("DARKRAI")] == ["DARKRAI"]
    assert pagina("DARKRAI") in categorias["RarePkmn"] and categorias["RarePkmn"][-1] == pagina("DARKRAI")


# --- grito ---------------------------------------------------------------------------------------

def test_gritos_no_fim():
    cries = _ler("sound/cry_tables.inc")
    ids = {m.group(1): int(m.group(2))
           for m in re.finditer(r"(CRY_\w+) = (\d+),", _ler("include/constants/hoenn_cries.h"))}
    for rotulo, macro in (("gCryTable", "cry"), ("gCryTable_Reverse", "cry_reverse")):
        linhas = re.findall(rf"^\t{macro} (Cry_\w+)$", _secao_asm(cries, rotulo), re.M)
        assert linhas[-4:] == [f"Cry_{n}" for _, n, _ in ESPECIES], rotulo
        for c, n, _ in ESPECIES:                  # o id do grito é a posição na tabela
            assert linhas.index(f"Cry_{n}") == ids[f"CRY_{c}"], (rotulo, c)
    assert [ids[f"CRY_{c}"] for c in TODAS] == [388, 389, 390, 391]


# --- o que fica entre o Ovo e as novas -----------------------------------------------------------

def test_nomes_do_ovo_e_das_letras_sao_seguros():
    """Com as 4 em 440-443, `gSpeciesNames` passa por 412-439. Sem nome escrito, essas posições ficariam com zeros
    (espaços, sem EOS). O Ovo e as letras do Unown ganham o que `GetSpeciesName` já mostrava antes do POK-54:
    o Ovo lia o nome logo depois da tabela (gMoveNames[0], "-" seguido de EOS) e as letras caíam no SPECIES_NONE."""
    texto = _ler("src/data/text/species_names.h")
    assert re.search(r'\[SPECIES_EGG\] = _\("-"\),', texto)
    letras = [f"UNOWN_{x}" for x in "BCDEFGHIJKLMNOPQRSTUVWXYZ"] + ["UNOWN_EMARK", "UNOWN_QMARK"]
    for letra in letras:
        assert re.search(rf'\[SPECIES_{letra}\] = _\("\?\?\?\?\?\?\?\?\?\?"\),', texto), letra


def test_cenario_especies_registrado_e_telas_no_fim():
    from esteira import refs
    from esteira.__main__ import FULL_SCENARIOS, TEST, WATCH_FULL_SCENARIOS
    from esteira.scenarios import full_especies as cen
    spec = next(s for s in FULL_SCENARIOS if s.name == "especies")
    assert (spec.rom, spec.save_from, spec.needs) == (TEST, "captura", None)
    assert "especies" in WATCH_FULL_SCENARIOS
    assert refs.ESPECIES_POINTS == cen.SCREEN_POINTS
    assert refs.SHARED_POINTS[-len(cen.SCREEN_POINTS):] == cen.SCREEN_POINTS
    texto = (REPO_ROOT / "test" / "esteira" / "scenarios" / "full_especies.py").read_text("utf-8")
    for caso in ("especies/resumo", "especies/icones", "especies/evolucao", "especies/creche", "especies/batalha"):
        assert f'"{caso}:' in texto, caso
    # o time do resumo fica abaixo dos golpes novos (Task 5): Dragon Rush no 37/49/55 e Dark Void no 66
    primeiro = {c: min(lv for lv, mv in GEN4[p]["nivel"] if mv in ("MOVE_DRAGON_RUSH", "MOVE_DARK_VOID"))
                for c, _, p in ESPECIES}
    assert all(lv < primeiro[s.removeprefix("SPECIES_")] for s, lv in cen.TEAM), cen.TEAM


def test_habilidade_do_darkrai_tem_nome_e_descricao():
    """O resumo imprime nome e descrição da habilidade: sem eles (zeros e ponteiro nulo) a tela do Darkrai trava.
    O efeito do Bad Dreams é da Task 5; o texto é o do plano."""
    texto = _ler("src/data/text/abilities.h")
    assert re.search(r'\[ABILITY_BAD_DREAMS\] = _\("Sonhos Ruins"\),', texto)
    assert re.search(r"\[ABILITY_BAD_DREAMS\] = sBadDreamsDescription,", texto)
    assert re.search(r'static const u8 sBadDreamsDescription\[\] = _\("Fere quem dorme a cada turno\."\);', texto)


def test_hoenn_continua_sem_as_novas():
    assert not re.search(r"SPECIES_TO_HOENN\((GIBLE|GABITE|GARCHOMP|DARKRAI)\)", _ler("src/pokemon.c"))
