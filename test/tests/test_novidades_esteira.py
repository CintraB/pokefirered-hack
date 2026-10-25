"""Tela de novidades, Task 6: o cenário da esteira (sem emulador).

O cenário `novidades` (ROM de teste, a partir do .sav do `captura`) abre a tela pela fala do Carvalho no
laboratório, percorre os 11 tópicos e o primeiro e o último cartão de cada um e afirma pelos atalhos
0x91/0x92. Ele espelha em Python a regra do cursor da grade e o tipo de imagem de cada cartão, lido do
JSON único dos cartões. O `novidades_inicial` (ROM jogável, a partir do checkpoint `abertura`) responde
SIM à pergunta logo depois do inicial e confere que a cena do rival continua normal.
"""

import json
import re

import pytest

import esteira.__main__ as cli
from esteira.__main__ import TEST
from esteira.refs import KEY_POINTS, SHARED_POINTS
from esteira.scenarios import REPO_ROOT
from esteira.scenarios import full_novidades as fn

SRC = REPO_ROOT / "src" / "novidades.c"
CARTOES = REPO_ROOT / "src" / "data" / "novidades" / "cartoes.json"


def _define(path, nome: str) -> int:
    m = re.search(rf"^#define\s+{nome}\s+(\d+)", path.read_text(encoding="utf-8"), re.M)
    assert m, nome
    return int(m.group(1))


def test_espelho_usa_as_medidas_do_c():
    assert fn.GRID_COLUMNS == _define(SRC, "NOVIDADES_GRID_COLUMNS")
    assert fn.TOPIC_COUNT == _define(REPO_ROOT / "include" / "novidades.h", "NOVIDADES_TOPIC_COUNT")


@pytest.mark.parametrize("cursor,tecla,esperado", [
    (0, "left", 0), (0, "up", 0),              # canto: não dá a volta
    (3, "right", 3), (4, "left", 4),           # fim e começo de linha
    (2, "right", 3), (5, "left", 4),
    (1, "down", 5), (9, "up", 5),
    (6, "down", 10), (4, "down", 8),
    (7, "down", 10),                           # ▼ para um quadro vazio vai ao último tópico
    (10, "right", 10), (10, "down", 10), (8, "down", 8),
])
def test_espelho_do_cursor_da_grade(cursor, tecla, esperado):
    assert fn.move_cursor(cursor, tecla) == esperado


def test_caminho_da_grade_passa_pelos_11_topicos_em_ordem():
    # grid_walk(t): as teclas de t - 1 até t, cada uma com o cursor esperado depois dela
    cursor = 0
    for topic in range(1, fn.TOPIC_COUNT):
        passos = fn.grid_walk(topic)
        assert passos, topic
        for tecla, depois in passos:
            cursor = fn.move_cursor(cursor, tecla)
            assert cursor == depois, (topic, tecla)
        assert cursor == topic
    # de 7 para 8 o caminho passa pela regra do ▼ (7 -> 10) e volta com ◀
    assert fn.grid_walk(8)[0] == ("down", 10)


def test_plano_dos_cartoes_vem_do_json():
    topics = json.loads(CARTOES.read_text(encoding="utf-8"))["topics"]
    plano = fn.card_plan()
    assert [t.id for t in plano] == [t["id"] for t in topics]
    assert len(plano) == fn.TOPIC_COUNT
    by_id = {t.id: t for t in plano}
    assert by_id["evolucoes"].kinds[0] == fn.IMAGE_TWO_MONS
    assert by_id["dia_noite"].kinds[-1] == fn.IMAGE_ONE_MON
    assert by_id["shiny"].kinds == [fn.IMAGE_TOPIC_ICON, fn.IMAGE_ITEM]
    assert by_id["pos_liga"].kinds == [fn.IMAGE_ITEM]
    assert by_id["lendarios"].titles[-1] == "Míticos: revelação"
    assert by_id["resumo"].custom_icon and not by_id["ritmo"].custom_icon


@pytest.mark.parametrize("tipo,vivos", [(0, 1), (1, 1), (2, 1), (3, 2)])
def test_sprites_vivos_por_tipo_de_imagem(tipo, vivos):
    assert fn.LIVE_SPRITES[tipo] == vivos


def test_telas_novas_sao_comuns_aos_tres_iniciais():
    assert fn.SCREEN_POINTS and all(p.startswith("novidades_") for p in fn.SCREEN_POINTS)
    assert set(fn.SCREEN_POINTS) <= set(SHARED_POINTS)
    assert not set(fn.SCREEN_POINTS) & set(KEY_POINTS)
    # a grade, um cartão de cada tipo de imagem, a revelação dos míticos e um cartão com ícone novo
    plano = {t.id: t for t in fn.card_plan()}
    tipos = {plano[topic].kinds[card] for topic, card in fn.CARD_SHOTS.values()}
    assert tipos == {fn.IMAGE_TOPIC_ICON, fn.IMAGE_ITEM, fn.IMAGE_ONE_MON, fn.IMAGE_TWO_MONS}
    assert ("lendarios", len(plano["lendarios"].kinds) - 1) in fn.CARD_SHOTS.values()
    assert any(plano[topic].custom_icon and plano[topic].kinds[card] == fn.IMAGE_TOPIC_ICON
               for topic, card in fn.CARD_SHOTS.values())
    # todo cartão fotografado é o primeiro ou o último do tópico (os que o cenário visita)
    for topic, card in fn.CARD_SHOTS.values():
        assert card in (0, len(plano[topic].kinds) - 1), (topic, card)
    assert set(fn.SCREEN_POINTS) == {fn.GRID_SHOT, *fn.CARD_SHOTS}


def test_registro_dos_cenarios_da_tela():
    specs = {s.name: s for s in cli.FULL_SCENARIOS}
    spec = specs["novidades"]
    assert (spec.rom, spec.save_from, spec.needs) == (TEST, "captura", None)
    assert spec.run is fn.run_full_novidades
    inicial = specs["novidades_inicial"]
    assert (inicial.rom, inicial.save_from, inicial.needs) == (cli.PLAYABLE, None, "abertura")
    assert inicial.run is fn.run_full_novidades_first_offer
    assert "novidades" in cli.WATCH_FULL_SCENARIOS
