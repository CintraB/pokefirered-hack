"""POK-54: espécies depois do Ovo.

Até o POK-54, `NUM_SPECIES` era o Ovo (412) e as letras do Unown (413-439) ficavam acima dele, então o código usava
`NUM_SPECIES` como "o Ovo" e `species > NUM_SPECIES` como "letra do Unown ou lixo". As espécies novas entram no fim,
em 440-443, e `NUM_SPECIES` passa a 444: o Ovo e as letras continuam onde estavam (o save guarda a espécie), e quem
pensava no Ovo passa a dizer `SPECIES_EGG`. Estes testes leem o C como texto.
"""

import re

from esteira.constants import Constants
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"


def _ler(rel: str) -> str:
    return (REPO_ROOT / rel).read_text("utf-8")


def _fontes_c() -> dict[str, str]:
    return {p.relative_to(REPO_ROOT).as_posix(): p.read_text("utf-8", errors="replace")
            for p in sorted(SRC.rglob("*.[ch]"))}


def _ocorrencias(padrao: str) -> list[str]:
    regex = re.compile(padrao)
    return [f"{rel}:{i}: {linha.strip()}"
            for rel, texto in _fontes_c().items()
            for i, linha in enumerate(texto.splitlines(), 1) if regex.search(linha)]


def _funcao(texto: str, assinatura: str) -> str:
    m = re.search(rf"^{re.escape(assinatura)}\n\{{(.*?)^\}}", texto, re.S | re.M)
    assert m, assinatura
    return m.group(1)


def test_ids_novos_no_fim():
    k = Constants.load(str(REPO_ROOT), ["species.h"])
    assert k.species("SPECIES_EGG") == 412
    assert [k.species(n) for n in ("GIBLE", "GABITE", "GARCHOMP", "DARKRAI")] == [440, 441, 442, 443]
    assert k._eval("NUM_SPECIES") == 444


def test_unown_e_ovo_fora_de_num_species():
    """Nada mais soma em cima de NUM_SPECIES: o Ovo e as letras ficam presos ao SPECIES_EGG."""
    assert _ocorrencias(r"\bNUM_SPECIES\s*\+") == []
    assert re.search(r"^#define NUM_SPECIES \(SPECIES_DARKRAI \+ 1\)$", _ler("include/constants/species.h"), re.M)
    assert "NUM_SPECIES +" not in _ler("include/constants/species.h")
    k = Constants.load(str(REPO_ROOT), ["species.h"])
    letras = [f"UNOWN_{c}" for c in "BCDEFGHIJKLMNOPQRSTUVWXYZ"] + ["UNOWN_EMARK", "UNOWN_QMARK"]
    assert [k.species(n) for n in letras] == list(range(413, 440))
    menu2 = _ler("src/menu2.c")
    assert re.search(r"#define SPECIES_OLD_UNOWN_EMARK \(SPECIES_EGG \+ 0\)", menu2)
    assert re.search(r"#define SPECIES_OLD_UNOWN_QMARK \(SPECIES_EGG \+ 1\)", menu2)
    assert "unownSpecies = SPECIES_EGG + unownForm;" in _ler("src/battle_main.c")


def test_sem_maior_que_num_species():
    """`> NUM_SPECIES` deixava passar o 444 (fora das tabelas); `> SPECIES_EGG` jogava fora as espécies novas."""
    assert _ocorrencias(r">\s*NUM_SPECIES\b") == []
    assert _ocorrencias(r">\s*SPECIES_EGG\b") == []
    assert _ocorrencias(r">\s*\(?\s*SPECIES_UNOWN_B\s*-\s*1\s*\)?") == []


def test_seguidor_ovo_explicito():
    corpo = _funcao(_ler("src/follower.c"), "const struct FollowerSpecies *Follower_GetSpeciesInfo(u16 species)")
    assert re.search(r"species == SPECIES_EGG", corpo)
    assert "NUM_SPECIES = SPECIES_EGG" not in corpo


def test_laco_das_ordens_da_dex():
    """As ordens alfabética e por tipo têm 411 entradas; NUM_SPECIES - 1 (443) leria além do fim."""
    texto = _ler("src/pokedex_screen.c")
    assert "NUM_SPECIES - 1" not in texto
    assert "for (i = 0; i < NELEMS(gPokedexOrder_Alphabetical); i++)" in texto
    assert "for (i = 0; i < NELEMS(gPokedexOrder_Type); i++)" in texto


def test_dex_zero_protegido():
    """Espécie sem número na Dex (o Ovo, as letras) dá 0; 0 - 1 virava o byte 255 e lia/gravava fora da Pokédex."""
    corpo = _funcao(_ler("src/pokedex_screen.c"),
                    "s8 DexScreen_GetSetPokedexFlag(u16 nationalDexNo, u8 caseId, bool8 indexIsSpecies)")
    guarda = re.search(r"if \(nationalDexNo == 0 \|\| nationalDexNo > DEX_FLAGS_NO \* 8\)\s*return FALSE;", corpo)
    assert guarda, "falta a guarda da Dex 0 / fora dos 416 bits"
    assert guarda.start() < corpo.index("nationalDexNo--")
    assert guarda.start() < corpo.index("gSaveBlock")
    assert corpo.index("SpeciesToNationalPokedexNum") < guarda.start()  # a guarda vale também para indexIsSpecies


def test_resort_gorgeous_sem_dex_zero():
    """O sorteio vai até NUM_SPECIES - 1 e passa pelo Ovo e pelas letras: só vale espécie com número na Dex."""
    texto = _ler("src/field_specials.c")
    visto = _funcao(texto, "static bool8 ResortGorgeousMonSeen(u16 species)")
    assert "dex != 0 && GetSetPokedexFlag(dex, FLAG_GET_SEEN) == TRUE" in visto
    corpo = _funcao(texto, "static u16 SampleResortGorgeousMon(void)")
    assert "GetSetPokedexFlag" not in corpo
    assert corpo.count("ResortGorgeousMonSeen(species)") == 2  # no sorteio e na busca para trás
