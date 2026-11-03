"""Seguidores (POK-48), Task 3: o seguidor anda junto e não colide (sem emulador: lê o C como texto; o comportamento
no jogo é o cenário `seguidor`, test/esteira/scenarios/full_seguidor.py).

- `test_gancho_so_no_held_movement`: `Follower_OnPlayerMovement` é chamado só de `ObjectEventSetHeldMovement`, só para o
  jogador e só depois de a ação ter sido aceita (o `return TRUE` de movimento sobreposto vem antes);
- `test_ritmo_do_seguidor`: `IsPlayerMovingByInput` vale também para o seguidor (o ritmo do Hack 2 sai igual) e a
  corrida dele usa os quadros de andar (`GetRunAnimNum`) nas duas ações de correr;
- `test_sem_colisao`: `DoesObjectCollideWithObjectAt` ignora o seguidor dos dois lados e `GetObjectEventIdByPosition`
  o pula;
- `test_a_no_seguidor`: `GetInteractedObjectEventScript` devolve NULL para o seguidor antes de ler o script do template.
- `test_mapa_de_acoes`: toda ação de `sFollowerMoves` é a 1ª de um bloco de 4 (sul, norte, oeste, leste) existente.
"""

import re

from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
INCLUDE = REPO_ROOT / "include"


def _ler(caminho):
    return caminho.read_text(encoding="utf-8")


def _sem_comentarios(texto: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", texto, flags=re.S)


def _funcao(texto: str, nome: str) -> str:
    """Corpo de `nome(...)` { ... } (chaves balanceadas)."""
    m = re.search(rf"^\w[\w\s\*]*\b{nome}\s*\([^;{{]*\)\s*\{{", texto, re.M)
    assert m, f"função {nome} não encontrada"
    i, prof = m.end(), 1
    while prof:
        prof += {"{": 1, "}": -1}.get(texto[i], 0)
        i += 1
    return texto[m.end():i - 1]


def _eom() -> str:
    return _sem_comentarios(_ler(SRC / "event_object_movement.c"))


def test_gancho_so_no_held_movement():
    chamadas = []
    for arquivo in SRC.rglob("*.c"):
        texto = _sem_comentarios(_ler(arquivo))
        for m in re.finditer(r"\bFollower_OnPlayerMovement\s*\(", texto):
            chamadas.append(arquivo.name)
    # a definição (follower.c) e a única chamada (event_object_movement.c)
    assert sorted(chamadas) == ["event_object_movement.c", "follower.c"], chamadas
    corpo = _funcao(_eom(), "ObjectEventSetHeldMovement")
    gancho = corpo.index("Follower_OnPlayerMovement(objectEvent, movementActionId)")
    assert re.search(r"if \(objectEvent->isPlayer\)\s*Follower_OnPlayerMovement", corpo), corpo
    assert corpo.index("return TRUE;") < gancho < corpo.rindex("return FALSE;"), corpo


def test_ritmo_do_seguidor():
    eom = _eom()
    corpo = _funcao(eom, "IsPlayerMovingByInput")
    assert "objectEvent->isPlayer || Follower_IsFollowerObject(objectEvent)" in corpo, corpo
    assert "!ScriptContext_IsEnabled()" in corpo, corpo
    for nome in ("StartRunningAnim", "InitRunSlow"):
        assert "GetRunAnimNum(objectEvent)" in _funcao(eom, nome), nome
    assert "FOLLOWER_ANIM_RUN_SOUTH" in _funcao(eom, "GetRunAnimNum")
    # o último quadro do passo não anima: na corrida por input (5 quadros/tile) cada quadro dura no máximo 3
    header = _ler(INCLUDE / "follower.h")
    ticks = int(re.search(r"#define FOLLOWER_RUN_TICKS (\d+)", header).group(1))
    assert ticks <= 3, ticks
    run = {d: int(re.search(rf"#define FOLLOWER_ANIM_RUN_{d}\s+\(ANIM_STD_COUNT \+ (\d+)\)", header).group(1))
           for d in ("SOUTH", "NORTH", "WEST", "EAST")}
    assert list(run.values()) == [4, 5, 6, 7], run   # logo depois das 4 paradas
    anims = _ler(SRC / "data" / "object_events" / "object_event_anims.h")
    for d in ("South", "North", "West", "East"):
        assert re.search(rf"FOLLOWER_WALK_ANIM\(sAnim_FollowerRun{d}, \d, FOLLOWER_RUN_TICKS\);", anims), d
        assert f"[FOLLOWER_ANIM_RUN_{d.upper()}] = sAnim_FollowerRun{d}," in anims, d


def test_perna_continua_entre_passos():
    """A animação parada só entra depois de FOLLOWER_IDLE_DELAY quadros sem ação: no quadro em que um passo termina,
    StartSpriteAnim zeraria o animCmdIndex que o passo seguinte retoma."""
    corpo = _funcao(_sem_comentarios(_ler(SRC / "follower.c")), "UpdateIdleAnim")
    espera = corpo.index("sFollowerState.stillFrames < FOLLOWER_IDLE_DELAY")
    assert espera < corpo.index("StartSpriteAnim"), corpo
    assert "sFollowerState.stillFrames = 0;" in corpo, corpo


def test_sem_colisao():
    eom = _eom()
    corpo = _funcao(eom, "DoesObjectCollideWithObjectAt")
    assert re.search(r"if \(Follower_IsFollowerObject\(objectEvent\)\)\s*return FALSE;", corpo), corpo
    assert "!Follower_IsFollowerObject(curObject)" in corpo, corpo
    assert "!Follower_IsFollowerObject(&gObjectEvents[i])" in _funcao(eom, "GetObjectEventIdByPosition")


def test_a_no_seguidor():
    corpo = _funcao(_sem_comentarios(_ler(SRC / "field_control_avatar.c")), "GetInteractedObjectEventScript")
    guarda = re.search(r"if \(Follower_IsFollowerObject\(&gObjectEvents\[objectEventId\]\)\)\s*return NULL;", corpo)
    assert guarda, corpo
    assert guarda.start() < corpo.index("GetObjectEventScriptPointerByObjectEventId"), corpo


def test_mapa_de_acoes():
    constantes = dict(re.findall(r"#define (MOVEMENT_ACTION_\w+)\s+(0x[0-9A-Fa-f]+)",
                                 _ler(INCLUDE / "constants" / "event_object_movement.h")))
    valor = {k: int(v, 16) for k, v in constantes.items()}
    nomes = {v: k for k, v in valor.items()}
    tabela = re.search(r"sFollowerMoves\[\] = \{(.*?)\n\};", _ler(SRC / "follower.c"), re.S).group(1)
    linhas = re.findall(r"\{ (MOVEMENT_ACTION_\w+),\s*FOLLOW_\w+,\s*(MOVEMENT_ACTION_\w+) \}", tabela)
    assert len(linhas) >= 10, tabela
    for jogador, seguidor in linhas:
        for acao in (jogador, seguidor):
            assert acao.endswith("_DOWN") or acao.endswith("_DOWN_SLOW"), acao
            base = valor[acao]
            sufixos = [nomes.get(base + i, "") for i in range(4)]
            esperado = [acao.replace("DOWN", d) for d in ("DOWN", "UP", "LEFT", "RIGHT")]
            assert sufixos == esperado, (acao, sufixos)
