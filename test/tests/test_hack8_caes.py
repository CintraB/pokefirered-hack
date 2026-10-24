"""Hack 8: os 3 cães lendários em sequência.

O cão do inicial começa a correr depois das Ilhas Sevii (como no original). Quando o cão errante
para (capturado, derrotado ou empate), passa a correr o próximo cão não capturado na Pokédex depois
dele no ciclo fixo Entei -> Raikou -> Suicune, dando a volta e com o próprio cão por último: o
derrotado só volta quando for o único que falta. Sem campo novo no save: o "próximo" sai da Pokédex.
Save antigo (cão capturado ou derrotado, errante parado): o mesmo teste roda ao CONTINUAR o jogo.

Testes estáticos (C lido como texto) + espelho Python da regra. O comportamento é conferido no
emulador (relatório em .superpowers/sdd/hack8-caes/).
"""

import re

from esteira.scenarios import REPO_ROOT


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _func(src: str, name: str) -> str:
    """Corpo da função C `name` (da assinatura até a `}` na coluna 0)."""
    m = re.search(rf"^\w[\w\s\*]*\b{name}\([^)]*\)\n\{{\n(.*?)^\}}", src, re.M | re.S)
    assert m, f"função {name} não encontrada"
    return m.group(1)


ROAMER = "src/roamer.c"
CICLO = ["SPECIES_ENTEI", "SPECIES_RAIKOU", "SPECIES_SUICUNE"]
CAO_DO_INICIAL = {"BULBASAUR": "SPECIES_ENTEI", "CHARMANDER": "SPECIES_SUICUNE", "SQUIRTLE": "SPECIES_RAIKOU"}


# ---- espelho Python da regra -------------------------------------------------------------------

def _ciclo_do_c() -> list[str]:
    m = re.search(r"sRoamerCycle\[\]\s*=\s*\{([^}]*)\}", _read(ROAMER))
    assert m, "tabela sRoamerCycle não encontrada em src/roamer.c"
    return re.findall(r"SPECIES_\w+", m.group(1))


def _inicio_do_c() -> dict[str, str]:
    """GetStarterRoamerIndex: inicial -> cão (pelo índice em sRoamerCycle)."""
    body = _func(_read(ROAMER), "GetStarterRoamerIndex")
    ciclo = _ciclo_do_c()
    out = {}
    for starter, idx in re.findall(r"case SPECIES_(\w+):\s*return (\d+);", body):
        out[starter] = ciclo[int(idx)]
    m = re.search(r"default:\s*return (\d+);", body)
    assert m, "GetStarterRoamerIndex sem default"
    out.setdefault("SQUIRTLE", ciclo[int(m.group(1))])
    return out


def proximo_cao(atual: str, capturados: set[str]) -> str | None:
    """Próximo não capturado depois de `atual` no ciclo, com o próprio `atual` por último."""
    ciclo = _ciclo_do_c()
    start = ciclo.index(atual) + 1
    for i in range(len(ciclo)):
        s = ciclo[(start + i) % len(ciclo)]
        if s not in capturados:
            return s
    return None


def _jogar(inicial: str, eventos: list[str]) -> list[str]:
    """Simula: 'c' = captura o cão que corre, 'd' = derrota. Devolve os cães que correram."""
    atual, capturados, correram = _inicio_do_c()[inicial], set(), []
    for e in eventos:
        correram.append(atual)
        if e == "c":
            capturados.add(atual)
        atual = proximo_cao(atual, capturados)
        if atual is None:
            break
    return correram


def test_ciclo_fixo_dos_caes():
    assert _ciclo_do_c() == CICLO


def test_cao_do_inicial_como_no_original():
    assert _inicio_do_c() == CAO_DO_INICIAL


def test_sequencia_completa_por_inicial():
    esperado = {
        "BULBASAUR": ["SPECIES_ENTEI", "SPECIES_RAIKOU", "SPECIES_SUICUNE"],
        "CHARMANDER": ["SPECIES_SUICUNE", "SPECIES_ENTEI", "SPECIES_RAIKOU"],
        "SQUIRTLE": ["SPECIES_RAIKOU", "SPECIES_SUICUNE", "SPECIES_ENTEI"],
    }
    for inicial, seq in esperado.items():
        assert _jogar(inicial, ["c"] * 5) == seq, inicial


def test_pula_cao_ja_capturado_por_troca():
    # Entei capturado e Raikou já na Pokédex (troca): o próximo é o Suicune.
    assert proximo_cao("SPECIES_ENTEI", {"SPECIES_ENTEI", "SPECIES_RAIKOU"}) == "SPECIES_SUICUNE"
    assert proximo_cao("SPECIES_RAIKOU", set(CICLO)) is None


def test_derrotado_passa_a_vez_e_volta_por_ultimo():
    # Bulbasaur: Entei derrotado -> Raikou; capturar Raikou e Suicune -> Entei volta; captura.
    assert _jogar("BULBASAUR", ["d", "c", "c", "c"]) == [
        "SPECIES_ENTEI", "SPECIES_RAIKOU", "SPECIES_SUICUNE", "SPECIES_ENTEI"]
    # derrotar o último que falta: ele volta na hora
    assert proximo_cao("SPECIES_SUICUNE", {"SPECIES_ENTEI", "SPECIES_RAIKOU"}) == "SPECIES_SUICUNE"
    # Charmander: Suicune derrotado, Entei derrotado -> Raikou -> Suicune -> Entei
    assert _jogar("CHARMANDER", ["d", "d", "c", "c", "c"]) == [
        "SPECIES_SUICUNE", "SPECIES_ENTEI", "SPECIES_RAIKOU", "SPECIES_SUICUNE", "SPECIES_ENTEI"]


# ---- o C implementa a mesma regra -------------------------------------------------------------

def test_get_next_roamer_species_percorre_o_ciclo_pela_pokedex():
    body = _func(_read(ROAMER), "GetNextRoamerSpecies")
    assert "GetRoamerCycleIndex(current) + 1" in body
    assert "sRoamerCycle[" in body
    assert "IsRoamerSpeciesCaught(" in body
    assert "SPECIES_NONE" in body
    caught = _func(_read(ROAMER), "IsRoamerSpeciesCaught")
    assert "FLAG_GET_CAUGHT" in caught and "SpeciesToNationalPokedexNum(" in caught


def test_errante_inicial_continua_sendo_o_cao_do_inicial():
    src = _read(ROAMER)
    body = _func(src, "CreateInitialRoamerMon")
    assert "sRoamerCycle[GetStarterRoamerIndex()]" in body
    assert "GetNextRoamerSpecies" not in body
    # nível e criação nova como hoje: nível 50, IVs aleatórios
    create = _func(src, "CreateRoamerMonOfSpecies")
    assert re.search(r"CreateMon\(&mon, species, 50, USE_RANDOM_IVS", create)
    assert "ROAMER->level = 50;" in create
    assert "ROAMER->active = TRUE;" in create


def test_try_start_next_roamer_com_o_errante_parado():
    body = _func(_read(ROAMER), "TryStartNextRoamer")
    # só com o errante parado e se ele era um cão (capturado ou derrotado, tanto faz)
    assert "ROAMER->active" in body
    assert "IsRoamerDog(ROAMER->species)" in body
    assert "IsRoamerSpeciesCaught(ROAMER->species)" not in body
    assert "GetNextRoamerSpecies(ROAMER->species)" in body
    assert "ClearRoamerData()" in body
    assert "CreateRoamerMonOfSpecies(" in body
    assert "TryStartNextRoamer(void);" in _read("include/roamer.h")


def test_gatilho_quando_o_errante_para_na_batalha():
    src = _read("src/battle_main.c")
    body = _func(src, "ReturnFromBattleToOverworld")
    i_inativo = body.index("SetRoamerInactive();")
    i_prox = body.index("TryStartNextRoamer();")
    assert i_prox > i_inativo
    # sem condição de resultado: captura, derrota e empate (os que param o errante) passam a vez
    assert not re.search(r"if \(gBattleOutcome == B_OUTCOME_CAUGHT\)\s*TryStartNextRoamer", body)
    assert body.count("TryStartNextRoamer") == 1


def test_gatilho_de_save_antigo_ao_continuar():
    body = _func(_read("src/overworld.c"), "Overworld_ResetStateOnContinue")
    assert "TryStartNextRoamer();" in body
    assert body.index("TryStartNextRoamer();") < body.index("RoamerMoveToOtherLocationSet();")


def test_sem_campo_novo_no_save_nem_ram_nova():
    glob = _read("include/global.h")
    m = re.search(r"struct Roamer\n\{(.*?)\};", glob, re.S)
    campos = re.findall(r"\b(\w+)(?:\[\w+\])?;", m.group(1))
    assert campos == ["ivs", "personality", "species", "hp", "level", "status", "cool", "beauty",
                      "cute", "smart", "tough", "active", "filler"], campos
    assert "/*0x30D0*/ struct Roamer roamer;" in glob
    ewram = re.findall(r"^(?:static )?EWRAM_DATA .*$", _read(ROAMER), re.M)
    assert len(ewram) == 2 and all(("sLocationHistory" in l or "sRoamerLocation" in l) for l in ewram), ewram
    # nenhum `static` mutável novo no roamer.c
    assert not re.search(r"^static (?!const|void|bool|u16 |u32 |s32 )\w+ s\w+", _read(ROAMER), re.M)


def test_area_da_pokedex_segue_o_cao_que_esta_correndo():
    body = _func(_read("src/wild_pokemon_area.c"), "GetRoamerPokedexAreaMarkers")
    assert "GetStarterSpecies()" not in body
    assert "gSaveBlock1Ptr->roamer.species != species" in body
