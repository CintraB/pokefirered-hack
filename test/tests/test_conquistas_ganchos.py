"""Conquistas e diário de batalhas (POK-44), Task 4: os gatilhos de evento (batalha, captura, ovo e shiny).

Os arquivos do motor ganham ganchos de uma linha; a regra fica toda em `src/conquistas.c`. Este arquivo confere,
lendo o C como texto, que cada gancho aparece uma vez e na função certa, e as regras que não dá para ver bem no
emulador (o shiny recebido não conta duas vezes). O comportamento fica no cenário `conquistas` (grupo `evento/*`).
"""

import re

from esteira import hooks
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
CONQ_C = SRC / "conquistas.c"
CONQ_H = REPO_ROOT / "include" / "conquistas.h"
BATTLE_H = REPO_ROOT / "include" / "battle.h"
CENARIO = REPO_ROOT / "test" / "esteira" / "scenarios" / "full_conquistas.py"

# gancho -> (arquivo do motor, função onde ele mora)
GANCHOS = {
    "Conquistas_OnFimDeBatalha": ("battle_main.c", "HandleEndTurn_FinishBattle"),
    "Conquistas_OnNocaute": ("battle_script_commands.c", "Cmd_tryfaintmon"),
    "Conquistas_OnEficacia": ("battle_script_commands.c", "Cmd_typecalc"),
    "Conquistas_OnCaptura": ("battle_script_commands.c", "Cmd_givecaughtmon"),
    "Conquistas_OnPokemonRecebido": ("pokemon.c", "GiveMonToPlayer"),
    "Conquistas_OnOvoChocado": ("daycare.c", "AddHatchedMonToParty"),
}


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def test_interface():
    h = _ler(CONQ_H)
    for proto in ("void Conquistas_OnNocaute(u8 battlerAtacante);",
                  "void Conquistas_OnEficacia(u8 battlerAtacante, u16 multX10);",
                  "void Conquistas_OnFimDeBatalha(void);",
                  "void Conquistas_OnCaptura(struct Pokemon *mon, u16 bola);",
                  "void Conquistas_OnPokemonRecebido(struct Pokemon *mon);",
                  "void Conquistas_OnOvoChocado(struct Pokemon *mon);",
                  "void Conquistas_Evento(u8 evento);",
                  "void Conquistas_PerderEvento(u8 evento);",
                  "void Diario_OnFimDeBatalha(void);"):
        assert proto in h, proto


def test_cada_gancho_uma_vez_na_funcao_certa():
    """Fora de conquistas.c e de test_hooks.c, cada gancho é chamado uma vez só, dentro da função certa."""
    fontes = {p.name: _ler(p) for p in SRC.glob("*.c") if p.name not in ("conquistas.c", "test_hooks.c")}
    for gancho, (arquivo, funcao) in GANCHOS.items():
        usos = {nome: len(re.findall(rf"\b{gancho}\(", texto)) for nome, texto in fontes.items()}
        usos = {nome: n for nome, n in usos.items() if n}
        assert usos == {arquivo: 1}, (gancho, usos)
        assert re.search(rf"\b{gancho}\(", _corpo(fontes[arquivo], funcao)), (gancho, funcao)


def test_fim_de_batalha_antes_do_quest_log():
    corpo = _corpo(_ler(SRC / "battle_main.c"), "HandleEndTurn_FinishBattle")
    linhas = [l.strip() for l in corpo.splitlines()]
    i = linhas.index("Conquistas_OnFimDeBatalha();")
    assert linhas[i + 1] == "TrySetQuestLogBattleEvent();", linhas[i:i + 2]


def test_nocaute_no_ramo_do_oponente():
    corpo = _corpo(_ler(SRC / "battle_script_commands.c"), "Cmd_tryfaintmon")
    i = corpo.index("Conquistas_OnNocaute(gBattlerAttacker);")
    assert corpo.index("gBattleResults.opponentFaintCounter++") < i, "fora do ramo do oponente"
    assert i < corpo.index("HITMARKER_DESTINYBOND"), "fora do ramo do oponente"
    assert corpo.index("gBattleResults.playerFaintCounter++") < corpo.index("gBattleResults.opponentFaintCounter++")


def test_eficacia_acumula_o_multiplicador():
    """multX10 começa em 10 e é multiplicado (/ 10) a cada ModulateDmgByType; a chamada fica no fim, só com o
    atacante do lado do jogador."""
    corpo = _corpo(_ler(SRC / "battle_script_commands.c"), "Cmd_typecalc")
    assert re.search(r"\bmultX10 = 10;", corpo)
    modula = re.findall(r"ModulateDmgByType\(TYPE_EFFECT_MULTIPLIER\(i\)\);", corpo)
    acumula = re.findall(r"multX10 = multX10 \* TYPE_EFFECT_MULTIPLIER\(i\) / 10;", corpo)
    assert len(modula) == len(acumula) == 2, (modula, acumula)
    chamada = re.search(r"if \(GetBattlerSide\(gBattlerAttacker\) == B_SIDE_PLAYER\)\s*\n\s*"
                        r"Conquistas_OnEficacia\(gBattlerAttacker, multX10\);", corpo)
    assert chamada, "chamada guardada pelo lado do jogador"
    assert chamada.start() > corpo.rindex("ModulateDmgByType")
    assert chamada.start() > corpo.index("ABILITY_WONDER_GUARD"), "antes da Wonder Guard"


def test_captura_antes_de_dar_o_pokemon():
    corpo = _corpo(_ler(SRC / "battle_script_commands.c"), "Cmd_givecaughtmon")
    assert corpo.index("Conquistas_OnCaptura(") < corpo.index("GiveMonToPlayer(")
    assert "gLastUsedItem" in corpo[corpo.index("Conquistas_OnCaptura("):corpo.index("GiveMonToPlayer(")]


def test_recebido_depois_do_ot():
    """IsMonShiny precisa do OT do jogador: o gancho vem depois do SetMonData(MON_DATA_OT_ID)."""
    corpo = _corpo(_ler(SRC / "pokemon.c"), "GiveMonToPlayer")
    assert corpo.index("MON_DATA_OT_ID") < corpo.index("Conquistas_OnPokemonRecebido(mon);")


def test_ovo_chocado_no_fim():
    corpo = _corpo(_ler(SRC / "daycare.c"), "AddHatchedMonToParty")
    linhas = [l.strip() for l in corpo.splitlines() if l.strip()]
    assert linhas[-1] == "Conquistas_OnOvoChocado(mon);", linhas[-3:]


def test_campos_novos_no_fim_de_battle_struct():
    h = _ler(BATTLE_H)
    m = re.search(r"^struct BattleStruct\n\{\n(.*?)^\};", h, re.S | re.M)
    assert m
    membros = [l.strip() for l in m.group(1).splitlines() if l.strip() and not l.strip().startswith("//")]
    assert membros[-2:] == ["u32 conqPersonalidade[PARTY_SIZE];", "u8 conqNocautes[PARTY_SIZE];"], membros[-3:]
    # BattleStruct mora no heap (AllocZeroed): sem STATIC_ASSERT de tamanho que o fim novo quebre
    for arq in list(SRC.glob("*.c")) + list((REPO_ROOT / "include").glob("*.h")):
        assert not re.search(r"STATIC_ASSERT\(sizeof\((struct BattleStruct|\*gBattleStruct)\)", _ler(arq)), arq


def test_shiny_recebido():
    """`evento/shiny_recebido`: OnPokemonRecebido pula ovo e só soma com IsMonShiny (teto 0xFFFF); OnCaptura não
    soma shiny (a soma da captura vem do GiveMonToPlayer, sem contar duas vezes)."""
    fonte = _ler(CONQ_C)
    recebido = _corpo(fonte, "Conquistas_OnPokemonRecebido")
    assert "MON_DATA_IS_EGG" in recebido and "IsMonShiny(mon)" in recebido
    assert recebido.index("MON_DATA_IS_EGG") < recebido.index("shiniesObtidos++")
    assert "0xFFFF" in recebido
    captura = _corpo(fonte, "Conquistas_OnCaptura")
    assert "shiniesObtidos" not in captura and "IsMonShiny" not in captura
    assert "ITEM_POKE_BALL" in captura and "CONQ_TAXA_DIFICIL" in captura and "catchRate" in captura
    ovo = _corpo(fonte, "Conquistas_OnOvoChocado")
    assert "shiniesObtidos++" in ovo and "CONQ_EVT_OVO_SHINY" in ovo and "CONQ_EVT_OVO_6IVS" in ovo


def test_fim_de_batalha_regras():
    fonte = _ler(CONQ_C)
    ignorados = _corpo(fonte, "BatalhaIgnorada")
    # BATTLE_TYPE_RECORDED não existe no FRLG (é do Emerald)
    for flag in ("LINK", "POKEDUDE", "OLD_MAN_TUTORIAL", "TRAINER_TOWER", "EREADER_TRAINER", "BATTLE_TOWER"):
        assert f"BATTLE_TYPE_{flag}" in ignorados, flag
    fim = _corpo(fonte, "Conquistas_OnFimDeBatalha")
    for token in ("BatalhaIgnorada()", "B_OUTCOME_WON", "vitoriasTreinador++", "playerFaintCounter == 0",
                  "CONQ_EVT_SEM_DESMAIO", "CONQ_EVT_LIDER_UM_POKEMON", "CONQ_EVT_ELITE4", "CONQ_EVT_RIVAL_TODAS",
                  "Conquistas_PerderEvento(CONQ_EVT_RIVAL_TODAS)", "Diario_OnFimDeBatalha();"):
        assert token in fim, token
    assert "BatalhaIgnorada()" in _corpo(fonte, "Conquistas_OnEficacia")


def test_x4_ignora_dano_sem_tipo():
    """Dano fixo, metade do HP e OHKO passam pelo typecalc (o OHKO antes de acertar) mas não causam dano de tipo:
    ficam fora pelo efeito do golpe. `power > 1` não serve: Low Kick, Return, Flail e Hidden Power têm poder 1 e dano
    de tipo de verdade."""
    fonte = _ler(CONQ_C)
    lista = _corpo(fonte, "DanoSemTipo")
    efeitos = set(re.findall(r"case (EFFECT_\w+):", lista))
    assert efeitos == {"EFFECT_LEVEL_DAMAGE", "EFFECT_DRAGON_RAGE", "EFFECT_SONICBOOM", "EFFECT_SUPER_FANG",
                       "EFFECT_PSYWAVE", "EFFECT_OHKO", "EFFECT_ENDEAVOR"}, efeitos
    assert "gBattleMoves[move].effect" in lista
    eficacia = _corpo(fonte, "Conquistas_OnEficacia")
    assert "DanoSemTipo(gCurrentMove)" in eficacia
    assert "power > 1" not in eficacia


def test_nocaute_ignora_golpe_tardio():
    """Future Sight/Doom Desire acertam turnos depois: o Pokémon na posição do atacante pode ser outro."""
    corpo = _corpo(_ler(CONQ_C), "Conquistas_OnNocaute")
    for golpe in ("MOVE_FUTURE_SIGHT", "MOVE_DOOM_DESIRE"):
        assert f"gCurrentMove == {golpe}" in corpo, golpe
    assert corpo.index("MOVE_DOOM_DESIRE") < corpo.index("conqNocautes")


def test_atalhos_novos():
    assert (hooks.CMD_START_TRAINER_BATTLE, hooks.CMD_SET_PARTY_MOVE, hooks.CMD_PARTY_SIZE,
            hooks.CMD_CONQ_CAPTURA, hooks.CMD_CONQ_CHOCAR) == (0xB6, 0xB7, 0xB8, 0xB9, 0xBA)
    for metodo in ("start_trainer_battle", "set_party_move", "party_size", "conq_captura", "conq_chocar"):
        assert callable(getattr(hooks.Mailbox, metodo, None)), metodo


def test_cenario_tem_os_grupos_de_evento():
    texto = _ler(CENARIO)
    for grupo in ("evento/lider_e_sem_desmaio", "evento/golpe_x4", "evento/derrota_nao_conta",
                  "evento/captura_poke_ball", "evento/ovo_chocado", "evento/lider_antes_da_insignia"):
        assert f'"{grupo}"' in texto, grupo
