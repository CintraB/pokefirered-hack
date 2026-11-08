"""POK-54, Task 6: Pokédex dos 4 extras (Gible, Gabite, Garchomp e Darkrai) e a regra dos 386.

Os 4 entram na Pokédex como os números internos 387-390, logo depois do Deoxys, mas as telas imprimem os números reais
da Gen 4 (443, 444, 445 e 491). Aparecem na lista e nas contagens de vistos/capturados da tela da Pokédex, e nunca
são exigidos por nada que completa, premia ou avalia a Dex: o diploma, `HasAllMons`, o Amuleto, a conquista de Dex, os
100% do DexNav, o cabeçalho da ROM e qualquer "X/386" continuam nos 386. Estes testes leem o C como texto.
"""

import re

from esteira import hooks
from esteira.scenarios import REPO_ROOT
from test_ids_do_save import _constantes_de_hoje

EXTRAS = ("GIBLE", "GABITE", "GARCHOMP", "DARKRAI")
EXIBIDOS = {387: 443, 388: 444, 389: 445, 390: 491}


def _ler(rel: str) -> str:
    return (REPO_ROOT / rel).read_text("utf-8")


def _corpo(texto: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", texto, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _sem_comentarios(texto: str) -> str:
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.S)
    return re.sub(r"//[^\n]*", "", texto)


def _dex() -> dict[str, int]:
    """Os NATIONAL_DEX_* de include/constants/pokedex.h (enum e #define), já avaliados."""
    return _constantes_de_hoje()["NATIONAL_DEX_"]


def _tabela_exibida() -> dict[int, int]:
    """Lê `sExtraDexDisplayedNumbers` de pokemon.c: {número interno: número impresso}."""
    texto = _ler("src/pokemon.c")
    m = re.search(r"sExtraDexDisplayedNumbers\[NATIONAL_DEX_EXTRAS_COUNT\]\s*=\s*\{(.*?)\};", texto, re.S)
    assert m, "tabela sExtraDexDisplayedNumbers não encontrada"
    dex = _dex()
    achado = {}
    for nome, num in re.findall(r"\[(NATIONAL_DEX_\w+) - NATIONAL_DEX_COUNT - 1\]\s*=\s*(\d+)", m.group(1)):
        achado[dex[nome]] = int(num)
    return achado


def test_numeros_exibidos():
    """Mapeamento exato: 387→443, 388→444, 389→445, 390→491; o resto devolve o próprio número."""
    dex = _dex()
    assert [dex[f"NATIONAL_DEX_{n}"] for n in EXTRAS] == [387, 388, 389, 390]
    assert _tabela_exibida() == EXIBIDOS
    corpo = _corpo(_ler("src/pokemon.c"), "NationalDexNumToDisplayed")
    # só os 4 extras são trocados; o resto (inclusive o 0 e as letras velhas do Unown) volta como entrou
    assert "nationalNum > NATIONAL_DEX_COUNT && nationalNum <= NATIONAL_DEX_TOTAL" in corpo
    assert re.search(r"return sExtraDexDisplayedNumbers\[nationalNum - NATIONAL_DEX_COUNT - 1\];", corpo)
    assert re.search(r"return nationalNum;\s*$", corpo.strip())
    assert "u16 NationalDexNumToDisplayed(u16 nationalNum);" in _ler("include/pokemon.h")
    # a tabela cobre exatamente os 4 extras
    assert re.search(r"#define NATIONAL_DEX_EXTRAS_COUNT 4$", _ler("include/constants/pokedex.h"), re.M)


def test_todo_numero_impresso_passa_pela_funcao():
    """As 3 telas que imprimem o número da Dex (Pokédex, resumo e Hall da Fama) chamam NationalDexNumToDisplayed."""
    tela = _ler("src/pokedex_screen.c")
    corpo = _corpo(tela, "DexScreen_PrintMonDexNo")
    assert "NationalDexNumToDisplayed(SpeciesToNationalPokedexNum(species))" in corpo
    # os 4 lugares que imprimem o número da lista, da categoria, da página e da área passam por ela
    assert len(re.findall(r"\bDexScreen_PrintMonDexNo\(", tela)) == 6   # protótipo, definição e 4 chamadas (lista, categoria, página, área)
    # nenhuma outra impressão de número da Dex fora dela
    assert tela.count("DexScreen_PrintNum3LeadingZeroes(") == 2   # definição e a chamada dentro de PrintMonDexNo

    resumo = _corpo(_ler("src/pokemon_summary_screen.c"), "BufferMonInfo")
    assert re.search(r"dexNumStrBuf, NationalDexNumToDisplayed\(dexNum\), STR_CONV_MODE_LEADING_ZEROS, 3\)", resumo)

    hall = _ler("src/hall_of_fame.c")
    m = re.search(r"dexNumber = SpeciesToPokedexNum\(currMon->species\);(.*?)StringAppend\(text2, text\);", hall, re.S)
    assert m, "o número do Hall da Fama mudou de lugar"
    assert "if (dexNumber != 0xFFFF)" in m.group(1)
    assert "dexNumber = NationalDexNumToDisplayed(dexNumber);" in m.group(1)
    # o 0xFFFF ("???") é decidido antes de converter: o número escondido continua escondido
    assert m.group(1).index("0xFFFF") < m.group(1).index("NationalDexNumToDisplayed")


def test_a_lista_e_as_contagens_da_tela_incluem_os_extras():
    tela = _ler("src/pokedex_screen.c")
    assert "Alloc(NATIONAL_DEX_TOTAL * sizeof(struct ListMenuItem))" in tela
    assert "IsNationalPokedexUiEnabled() ? NATIONAL_DEX_TOTAL : KANTO_DEX_COUNT" in tela
    nacional = re.search(r"case DEX_ORDER_NUMERICAL_NATIONAL:\n\s+for \(i = 0; (i < \w+); i\+\+\)", tela)
    assert nacional and nacional.group(1) == "i < NATIONAL_DEX_TOTAL"
    contagem = _corpo(tela, "DexScreen_GetDexCount")
    assert "GetNationalPokedexCountWithExtras(caseId)" in contagem
    assert "NATIONAL_DEX_COUNT" not in _sem_comentarios(contagem)
    # nenhum laço ou filtro da tela ficou preso nos 386
    assert "NATIONAL_DEX_COUNT" not in _sem_comentarios(tela)
    # as 4 listas por ordem filtram pelo mesmo teto (max_n) e andam pela tabela inteira
    assert tela.count("if (ndex_num <= max_n)") == 4


def test_contagem_com_extras_so_na_tela_e_nos_atalhos():
    """GetNationalPokedexCount não muda (386); a versão com extras só existe na Pokédex e no atalho de teste."""
    dex = _ler("src/pokedex.c")
    corpo = _corpo(dex, "GetNationalPokedexCount")
    assert "i < NATIONAL_DEX_COUNT" in corpo and "NATIONAL_DEX_TOTAL" not in corpo
    extras = _corpo(dex, "GetNationalPokedexCountWithExtras")
    assert "i < NATIONAL_DEX_TOTAL" in extras
    assert "u16 GetNationalPokedexCountWithExtras(u8);" in _ler("include/pokedex.h")
    usos = {p.relative_to(REPO_ROOT).as_posix()
            for raiz in ("src", "include", "data") for p in (REPO_ROOT / raiz).rglob("*")
            if p.suffix in (".c", ".h", ".inc", ".s") and "GetNationalPokedexCountWithExtras" in p.read_text("utf-8", "replace")}
    assert usos == {"src/pokedex.c", "include/pokedex.h", "src/pokedex_screen.c", "src/test_hooks.c",
                    "include/test_hooks.h"}, usos


def test_386_intocado():
    """Nada que completa, premia ou avalia a Dex cita os extras: continua tudo nos 386."""
    nums = _dex()
    assert re.search(r"^#define NATIONAL_DEX_COUNT\s+NATIONAL_DEX_DEOXYS$", _ler("include/constants/pokedex.h"), re.M)
    assert nums["NATIONAL_DEX_COUNT"] == 386 and nums["NATIONAL_DEX_TOTAL"] == 390

    dex = _ler("src/pokedex.c")
    for nome in ("GetNationalPokedexCount", "HasAllMons", "HasAllKantoMons", "HasAllKantoMonsWithMew", "HasAllHoennMons"):
        corpo = _sem_comentarios(_corpo(dex, nome))
        assert "NATIONAL_DEX_TOTAL" not in corpo and "EXTRAS" not in corpo, nome
    assert "NATIONAL_DEX_COUNT - 2" in _corpo(dex, "HasAllMons")   # Jirachi e Deoxys fora, Mew fora: os 386 de sempre

    conquistas = _sem_comentarios(_ler("src/conquistas.c"))
    for nome in ("CumpreDexNacional", "DexTodosCapturados"):
        assert "NATIONAL_DEX_TOTAL" not in _corpo(conquistas, nome) and "EXTRAS" not in _corpo(conquistas, nome)
    assert "GetNationalPokedexCount(FLAG_GET_CAUGHT)" in _corpo(conquistas, "CumpreDexNacional")
    for arq in ("src/conquistas.c", "src/dexnav.c", "src/rom_header_gf.c", "src/main_menu.c", "src/save_menu_util.c",
                "src/trainer_card.c", "src/prof_pc.c", "src/easy_chat.c", "src/start_menu.c"):
        texto = _sem_comentarios(_ler(arq))
        assert "NATIONAL_DEX_TOTAL" not in texto and "NATIONAL_DEX_EXTRAS" not in texto, arq
        assert "WithExtras" not in texto, arq
    assert ".pokedexCount = NATIONAL_DEX_COUNT," in _ler("src/rom_header_gf.c")

    dexnav = _ler("src/dexnav.c")
    assert re.search(r"#define LINHAS_MAX\s+NATIONAL_DEX_COUNT\b", dexnav)
    assert "for (dex = 1; dex <= NATIONAL_DEX_COUNT; dex++)" in dexnav

    hooks_c = _ler("src/test_hooks.c")
    completo = _sem_comentarios(_corpo(hooks_c, "SetDexComplete"))
    assert "NATIONAL_DEX_TOTAL" not in completo and "EXTRAS" not in completo
    assert "NATIONAL_DEX_COUNT - 2" in completo

    # o roteiro da Dex dos scripts (diploma, Amuleto, Dex Nacional) lê HasAllMons / GetNationalPokedexCount
    for p in (REPO_ROOT / "data").rglob("*.inc"):
        texto = p.read_text("utf-8", "replace")
        assert "NATIONAL_DEX_TOTAL" not in texto and "NATIONAL_DEX_EXTRAS" not in texto, p.name


def test_dexnav_sem_extras():
    """Nenhuma das 4 aparece na natureza nem nos dados do DexNav (o Gible só nasce de ovo)."""
    arquivos = ["src/dexnav.c", "src/dexnav_data.c", "src/data/dexnav_mapas.h", "src/data/wild_encounters.json"]
    for arq in arquivos:
        texto = _ler(arq)
        for nome in EXTRAS:
            assert f"SPECIES_{nome}" not in texto, f"{arq} cita SPECIES_{nome}"
    # o DexNav só olha os números até o Deoxys: um extra que aparecesse seria descartado
    assert "dex <= NATIONAL_DEX_COUNT" in _ler("src/dexnav.c")


def test_atalhos_do_bloco_0x140():
    """DEX_INFO, DEX_MARCAR e DEX_COMPLETA: o enum do C e o do Python estão no bloco 0x140 e o `case` existe."""
    header = _ler("include/test_hooks.h")
    assert "TEST_CMD_DEX_INFO = 0x140," in header
    assert re.search(r"TEST_CMD_DEX_MARCAR,\s*// arg0 = internal national Dex number", header)
    assert re.search(r"TEST_CMD_DEX_COMPLETA,\s*// arg0 = internal national Dex number \(0 = none\); read-only", header)
    assert (hooks.CMD_DEX_INFO, hooks.CMD_DEX_MARCAR, hooks.CMD_DEX_COMPLETA) == (0x140, 0x141, 0x142)
    codigo = _ler("src/test_hooks.c")
    assert "case TEST_CMD_DEX_INFO:         result = DexInfo(gTestMailbox.arg0); break;" in codigo
    assert "case TEST_CMD_DEX_MARCAR:       result = DexMarcar(gTestMailbox.arg0, gTestMailbox.arg1); break;" in codigo
    marcar = _corpo(codigo, "DexMarcar")
    assert "dex > DEX_FLAGS_NO * 8" in marcar     # o bit tem de caber no save: 416
    for campo in ("pokedex.seen", "pokedex.owned", "seen1", "seen2"):   # limpar apaga as 4 cópias
        assert f"{campo}[index] &= ~mask" in marcar, campo
    assert "GetNationalPokedexCount(FLAG_GET_CAUGHT) | (u32)GetNationalPokedexCountWithExtras(FLAG_GET_CAUGHT) << 16" in marcar
    assert "case TEST_CMD_DEX_COMPLETA:     result = DexCompleta(gTestMailbox.arg0); break;" in codigo
    completa = _corpo(codigo, "DexCompleta")      # só leitura: nada de FLAG_SET_*
    assert "FLAG_SET_" not in completa and "HasAllMons()" in completa
    info = _corpo(codigo, "DexInfo")
    assert "NationalDexNumToDisplayed(dex) << 16" in info


def test_cenario_especies_tem_os_casos_da_dex():
    from esteira import refs
    from esteira.scenarios import full_especies as cen
    texto = _ler("test/esteira/scenarios/full_especies.py")
    for caso in ("numeros", "lista_nacional", "pagina_garchomp", "resumo_numero", "386_sem_extras", "extras_nao_contam",
                 "extra_antes_da_nacional"):
        assert f'"dex/{caso}:' in texto, caso
    assert cen.SCREEN_POINTS[-3:] == ("dex_lista_extras", "dex_garchomp", "dex_garchomp_area")
    assert refs.SHARED_POINTS[-3 - len(refs.JOHTO_POINTS):-len(refs.JOHTO_POINTS)] == cen.SCREEN_POINTS[-3:]   # e os do POK-28
    # os deslocamentos da struct da tela que o cenário lê (conferidos contra os contadores no próprio cenário)
    assert (cen.PDS_STATE, cen.PDS_ORDER_ID, cen.PDS_LIST_ITEMS, cen.PDS_ORDERED_COUNT, cen.PDS_DEX_SPECIES,
            cen.PDS_SEEN_NAT, cen.PDS_OWNED_NAT) == (0x01, 0x42, 0x44, 0x48, 0x5A, 0x6A, 0x6C)
    assert cen.DEX_ROWS[2:] == (("SPECIES_GIBLE", 387, 443), ("SPECIES_GABITE", 388, 444),
                                ("SPECIES_GARCHOMP", 389, 445), ("SPECIES_DARKRAI", 390, 491))
