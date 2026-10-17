"""Escolha do golpe pelo dano esperado (sem emulador): tabela de tipos e pontuação."""

from pathlib import Path

from esteira.battle import TYPE_ENDTABLE, TYPE_FORESIGHT, move_score, parse_type_table

NORMAL, GROUND, ROCK, GHOST, STEEL, FIRE, WATER, GRASS = 0, 4, 5, 7, 8, 10, 11, 12
TABLE = bytes([
    FIRE, GRASS, 20, FIRE, ROCK, 5, WATER, GROUND, 20, WATER, ROCK, 20,
    GRASS, GROUND, 20, GRASS, ROCK, 20, NORMAL, ROCK, 5, STEEL, ROCK, 20,
    TYPE_FORESIGHT, TYPE_FORESIGHT, 0,
    NORMAL, GHOST, 0,
    TYPE_ENDTABLE, TYPE_ENDTABLE, 0,
    WATER, FIRE, 20,                     # depois do fim: ignorado
])


def test_parse_type_table_para_no_fim_e_pula_o_marcador_da_foresight():
    table = parse_type_table(TABLE)
    assert table[(FIRE, ROCK)] == 0.5 and table[(GRASS, GROUND)] == 2.0
    assert table[(NORMAL, GHOST)] == 0.0
    assert (WATER, FIRE) not in table and (TYPE_FORESIGHT, TYPE_FORESIGHT) not in table


def test_move_score_multiplica_poder_stab_efetividade_e_precisao():
    table = parse_type_table(TABLE)
    geodude = (ROCK, GROUND)
    # Vine Whip (35, grama, 100%) de um Bulbasaur (grama/veneno): 35 * 1,5 * 4
    assert move_score(35, GRASS, 100, (GRASS, 3), geodude, table) == 35 * 1.5 * 4
    # Ember (40, fogo) de Charmander contra pedra/terra: 40 * 1,5 * 0,5
    assert move_score(40, FIRE, 100, (FIRE, FIRE), geodude, table) == 30
    # Metal Claw (50, aço, 95%) sem STAB: 50 * 2 * 0,95
    assert move_score(50, STEEL, 95, (FIRE, FIRE), geodude, table) == 95
    # tipo repetido (monotipo) conta uma vez só; precisão 0 = nunca erra
    assert move_score(40, WATER, 0, (WATER, WATER), (ROCK, ROCK), table) == 40 * 1.5 * 2
    # golpe de status não pontua
    assert move_score(0, GRASS, 90, (GRASS, 3), geodude, table) == 0
