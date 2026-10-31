"""Modo completo: conquistas e diário de batalhas (POK-44), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). Os atalhos do bloco
0xB0 (include/test_hooks.h) leem e montam o estado no save; as áreas são lidas também direto da RAM
(`gSaveBlock1Ptr->conquistas` em +0x348C, `gSaveBlock2Ptr->diario` em +0xB20):

- `save/jogo_novo`: o diário com lixo e `conq_reset(True)` (Conquistas_IniciarJogoNovo, o que o
  NewGameInitData chama logo depois do ClearSav1) → marcador "CQD1", versão 1, origem jogo novo,
  `adiadoNoMapa` 0xFFFF, todos os estados pendentes, nada entregue, contadores e diário zerados;
- `save/antigo_sem_marcador`: `conq_reset(False)` (as duas áreas zeradas, como em todo save de antes
  das conquistas) → magic 0 (a checagem desse save entra na varredura: `retro/*`);
- `save/num_invalido`: um `num` fora da tabela devolve 0xFFFFFFFF;
- `estado/*` (Task 3): as regras de `Conquistas_ChecarEstado` num save com marcador (insígnia, dinheiro,
  nível no time, degraus de horas, contagem por aba) e os acessores Marcar/Perder/SetEntregue/
  SetDegrauEntregue em tempo de execução (`conq_aplicar`): feita fica feita, perdida nunca vira feita;
- `retro/*` (Task 3): um save sem marcador passa pela varredura uma vez (origem save antigo, resumo
  pendente; insígnias, Campeão, Elite 4 e nível feitos, vitórias = flags de treinador ligadas,
  `lider_um_pokemon` e `rival_todas` perdidas), e a varredura não roda de novo.
- `evento/*` (Task 4): os gatilhos em batalhas de verdade (`start_trainer_battle`, `CMD_START_WILD_BATTLE`, lutando
  com o 1º golpe): líder vencido com um Pokémon só e sem desmaio, golpe x4, derrota para o rival (perde
  `rival_todas`, não conta vitória), Poké Ball numa espécie difícil (`conq_captura`) e o caso real do 8º líder no
  Ginásio de Viridian (a marca vem antes do `setflag FLAG_BADGE08_GET` do script).
- `diario/*` (Task 5): a entrada do Brock (VENCEU, turnos, time, MVP, minutos; ordem 1 com proximaOrdem 0), só a
  1ª vitória entra, o Articuno derrotado (DERROTOU) e depois capturado com Master Ball (CAPTURADO, ordem nova), o
  MVP pela personalidade depois de uma troca, a 1ª Liga registrada e a revanche (FLAG_SYS_GAME_CLEAR) não, e o
  jogo novo zerando o diário (`diario_entrada`, CMD_DIARIO_ENTRADA).
- `aviso/*` e `premio/*` (Task 6): a sessão da ROM de teste começa em silêncio (`conq_silencio(True)`, para os grupos
  acima, que montam o estado sem o aviso entregar nada no meio); estes grupos desligam o silêncio. O aviso aparece no
  campo e pausa o jogo (`gConquistasAvisoAtivo`), entrega o prêmio na bolsa, senão no PC de itens, e com a bolsa e o
  PC cheios deixa o prêmio para depois (não volta no mesmo mapa); nunca em batalha; vários de uma vez saem um por
  vez; num save antigo, um aviso-resumo só entrega tudo. Fotos em telas/conquista_*.png (sem referência: quem
  aprova o visual é o Cintra).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only conquistas
Numa janela, em tempo real: `make test-watch CENARIO=conquistas`.
"""

import re
import struct
import sys

from .. import conquistas as cq
from ..battle import (ACTION_FIGHT, B_OUTCOME_CAUGHT, MOVE_FUNC_SUFFIX, NICKNAME_COMMAND, PARTY_CHOOSE_TASK,
                      PARTY_MENU_SLOT_ID, PARTY_SELECTION_TASK)
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_UP
from ..game import SB1_MONEY
from ..hooks import CMD_CONQ_ESTADO, CMD_GIVE_ITEM, CMD_START_WILD_BATTLE, CMD_WARP, NO_RESULT, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import WHITEOUT_TIMEOUT, CatchSaveScenario
from .quick_route1 import POST_BATTLE_TIMEOUT

MOVES = {m.group(1): int(m.group(2)) for m in re.finditer(
    r"^#define (MOVE_\w+)\s+(\d+)\b", (REPO_ROOT / "include/constants/moves.h").read_text(encoding="utf-8"), re.M)}
GIOVANNI_FRENTE = (2, 3)   # o Giovanni fica em (2, 2), virado para baixo (data/maps/ViridianCity_Gym/map.json)
ACTION_POKEMON = 2       # menu de ação: LUTAR, BOLSA, POKéMON, FUGIR (cursor 2x2)
PARTY_SIZE = 6
# struct BattleStruct (include/battle.h): os 0x200 do jogo, conqPersonalidade[6] (u32), conqNocautes[6], conqGolpeTardio
BS_CONQ_NOCAUTES, BS_CONQ_GOLPE_TARDIO = 0x218, 0x21E
TENTATIVAS_TARDIO = 4    # Future Sight tem precisão 90: a chance de errar 4 vezes seguidas é 1 em 10.000

SB1_CONQUISTAS, SB2_DIARIO = 0x348C, 0xB20
CONQ_SAVE_SIZE, DIARIO_SAVE_SIZE = 400, 0x400
ADIADO_NO_MAPA = 0x2C   # offset de adiadoNoMapa em struct ConquistasSave
SB2_PLAY_TIME_HOURS = 0x0E   # u16 playTimeHours, seguido de u8 playTimeMinutes
PENDENTE, FEITA, PERDIDA = cq.CONQ_PENDENTE, cq.CONQ_FEITA, cq.CONQ_PERDIDA
ABA_HISTORIA, ABA_BATALHA = 0, 1
APLICAR_MARCAR, APLICAR_PERDER, APLICAR_ENTREGUE, APLICAR_DEGRAU = 0, 1, 2, 3
BADGES = [f"FLAG_BADGE0{i}_GET" for i in range(1, 9)]
# Task 6: o aviso
AVISO_ATIVO = "gConquistasAvisoAtivo"   # u8: 1 enquanto o aviso está na tela (src/conquistas_aviso.c)
AVISO_TIMEOUT = 300      # a checagem de estado roda a cada 32 quadros; o aviso aparece logo depois
AVISO_ENTRADA = 24       # quadros da entrada animada (a foto sai com a janela parada)
CONQ_VITORIAS = 0x08     # u16 vitoriasTreinador em struct ConquistasSave
SB1_PC_ITEMS, PC_ITEMS_COUNT = 0x298, 30          # struct ItemSlot pcItems[30] (quantidade sem chave)
SB1_BALLS, BALLS_COUNT = 0x430, 13                # bagPocket_PokeBalls (quantidade XOR chave)
PALLET_LIVRE = (15, 9)   # Pallet: linha 9 livre de x=2 a x=21 (quick_route1.PACE_START)
VIRIDIAN_LIVRE = (26, 27)  # Viridian, diante do Centro


def struct_unpack(raw: bytes, i: int) -> tuple[int, int]:
    """(item, quantidade) do ItemSlot `i` de um bolso/PC lido cru."""
    return struct.unpack_from("<HH", raw, i * 4)


class ConquistasScenario(CatchSaveScenario):
    def _sb(self, n: int) -> int:
        return self.emu.read_u32(self.game.syms.addr(f"gSaveBlock{n}Ptr"))

    def _conq_raw(self) -> bytes:
        return self.emu.read(self._sb(1) + SB1_CONQUISTAS, CONQ_SAVE_SIZE)

    def _diario_raw(self) -> bytes:
        return self.emu.read(self._sb(2) + SB2_DIARIO, DIARIO_SAVE_SIZE)

    # --- passos ------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="conquistas_continue")
        magic = self.box.conq_contador(3)
        # O captura.sav de uma ROM de antes das conquistas não tem marcador e tem as duas áreas zeradas.
        # Quando a ROM jogável já trouxer as conquistas (Task 9), o modo rápido começa um jogo novo e o
        # save sai com o marcador de jogo novo; qualquer outra coisa é lixo.
        if magic == 0:
            assert not any(self._conq_raw()), "save sem marcador com a área das conquistas suja"
            assert not any(self._diario_raw()), "save sem marcador com a área do diário suja"
        else:
            assert magic == cq.CONQ_MAGIC, f"magic = {magic:#x}"
            assert self.box.conq_contador(2) & 0xFF == cq.CONQ_ORIGEM_JOGO_NOVO, "origem"
        return f"CONTINUAR com o save do modo rápido; magic do save = {magic:#010x}"

    def _jogo_novo(self) -> str:
        # lixo nas duas áreas: o jogo novo zera tudo (o de um jogo anterior não sobrevive)
        self.emu.write(self._sb(2) + SB2_DIARIO, bytes([0x5A]) * DIARIO_SAVE_SIZE)
        self.emu.write(self._sb(1) + SB1_CONQUISTAS, bytes([0xA5]) * CONQ_SAVE_SIZE)
        magic = self.box.conq_reset(True)
        assert magic == cq.CONQ_MAGIC == self.box.conq_contador(3), f"magic = {magic:#x}"
        assert self.box.conq_contador(2) == cq.CONQ_ORIGEM_JOGO_NOVO, "origem | resumoPendente"
        assert self.box.conq_contador(0) == 0 and self.box.conq_contador(1) == 0, "contadores"
        raw = self._conq_raw()
        assert raw[4] == 1 and not any(raw[5:8]), f"versão/origem/resumo/livre0 = {raw[4:8].hex()}"
        assert int.from_bytes(raw[ADIADO_NO_MAPA:ADIADO_NO_MAPA + 2], "little") == 0xFFFF, "adiadoNoMapa"
        assert not any(raw[8:ADIADO_NO_MAPA]) and not any(raw[ADIADO_NO_MAPA + 2:]), "área com lixo"
        estados = {n: self.box.conq_estado(n) for n in range(len(cq.dados()["conquistas"]))}
        assert all(e == (0, 0, 0, 0) for e in estados.values()), {n: e for n, e in estados.items() if any(e)}
        diario = self._diario_raw()
        assert diario[1] == 1 and not any(diario[:1]) and not any(diario[2:]), "diário não zerado"
        return f"magic CQD1, {len(estados)} conquistas pendentes, diário zerado"

    def _antigo(self) -> str:
        magic = self.box.conq_reset(False)
        assert magic == 0 == self.box.conq_contador(3), f"magic = {magic:#x}"
        assert not any(self._conq_raw()) and not any(self._diario_raw()), "áreas não zeradas"
        # a checagem num save assim entra na varredura: grupo retro/*
        return "save sem marcador: magic 0"

    def _invalido(self) -> str:
        assert self.box.call(CMD_CONQ_ESTADO, 63) == NO_RESULT
        assert self.box.call(CMD_CONQ_ESTADO, 0x100) == NO_RESULT
        return "num 63 e 0x100 → 0xFFFFFFFF"

    # --- Task 3: regras de estado -------------------------------------------------------
    def _flag(self, name: str, on: bool = True) -> None:
        assert self.box.set_flag(self.consts.flag(name), on) == on, name

    def _estado(self, cid: str) -> tuple[int, int, int, int]:
        return self.box.conq_estado(cq.num(cid))

    def _set_money(self, amount: int) -> None:
        """Dinheiro do jogador (u32 XOR encryptionKey), escrito na RAM (molde de full_egg.py)."""
        self.emu.write(self._sb(1) + SB1_MONEY, (amount ^ self.game._key()).to_bytes(4, "little"))

    def _set_horas(self, horas: int) -> None:
        self.emu.write(self._sb(2) + SB2_PLAY_TIME_HOURS, horas.to_bytes(2, "little") + bytes([0]))

    def _insignia(self) -> str:
        self.box.conq_reset(True)
        self._flag("FLAG_BADGE01_GET", False)
        self.box.conq_checar()
        assert self._estado("insignia_rocha")[0] == PENDENTE, "sem a insígnia"
        self._flag("FLAG_BADGE01_GET")
        avisos = self.box.conq_checar()
        assert self._estado("insignia_rocha") == (FEITA, 0, 0, 0), self._estado("insignia_rocha")
        assert avisos >= 1, f"avisos = {avisos}"
        return f"FLAG_BADGE01_GET → insignia_rocha feita, não entregue; {avisos} aviso(s) pendente(s)"

    def _dinheiro(self) -> str:
        self.box.conq_reset(True)
        self._set_money(999998)
        self.box.conq_checar()
        assert self._estado("dinheiro")[0] == PENDENTE, "₽999.998 não basta"
        self._set_money(999999)
        self.box.conq_checar()
        assert self._estado("dinheiro")[0] == FEITA, self._estado("dinheiro")
        return "₽999.998 pendente, ₽999.999 feita"

    def _nivel(self) -> str:
        self.box.conq_reset(True)
        mewtwo = self.consts.species("MEWTWO")
        for slot, mon in enumerate(self.game.party()):
            if mon.level >= 50:   # o time do save não pode ter nível 50 antes do teste
                self.box.set_party_mon(slot, mewtwo, 5)
        self.box.set_party_mon(0, mewtwo, 49)
        self.box.conq_checar()
        assert self._estado("nivel_50")[0] == PENDENTE == self._estado("nivel_100")[0], "nível 49"
        self.box.set_party_mon(0, mewtwo, 100)
        self.box.conq_checar()
        assert self._estado("nivel_50")[0] == FEITA == self._estado("nivel_100")[0], (
            self._estado("nivel_50"), self._estado("nivel_100"))
        return "Mewtwo nv 49: pendentes; nv 100: nivel_50 e nivel_100 feitas"

    def _degraus_horas(self) -> str:
        self.box.conq_reset(True)
        self._set_horas(9)
        self.box.conq_checar()
        assert self._estado("horas") == (PENDENTE, 0, 0, 0), self._estado("horas")
        self._set_horas(37)
        antes = self.box.conq_checar()
        assert self._estado("horas") == (PENDENTE, 0, 0, 1), self._estado("horas")
        self._set_horas(100)
        depois = self.box.conq_checar()
        assert self._estado("horas") == (FEITA, 0, 0, 3), self._estado("horas")
        assert depois == antes + 2, f"avisos {antes} → {depois} (2 degraus a mais)"
        return f"9 h: degrau 0; 37 h: degrau 1, pendente; 100 h: degrau 3, feita; avisos {antes} → {depois}"

    def _conta_aba(self) -> str:
        self.box.conq_reset(True)
        for i, flag in enumerate(BADGES):
            self._flag(flag, i < 3)
        for flag in ("FLAG_SYS_GAME_CLEAR", "FLAG_HIDE_SAFFRON_ROCKETS", "FLAG_SYS_CAN_LINK_WITH_RS"):
            self._flag(flag, False)
        self.box.conq_checar()
        historia = self.box.conq_contador(4 + ABA_HISTORIA)
        assert historia == 3 | 12 << 8, f"história = {historia & 0xFF} de {historia >> 8}"
        ativas = [c for c in cq.dados()["conquistas"] if c.get("ativa", True) and c["aba"] == "batalha"]
        batalha = self.box.conq_contador(4 + ABA_BATALHA)
        assert batalha >> 8 == len(ativas) == 5, f"batalha: {batalha >> 8} válidas"
        self.box.conq_aplicar(cq.num("rival_todas"), APLICAR_PERDER)
        perdeu = self.box.conq_contador(4 + ABA_BATALHA)
        assert perdeu >> 8 == 4 and perdeu & 0xFF == batalha & 0xFF, f"batalha depois = {perdeu:#x}"
        return f"3 insígnias: história 3 de 12; rival_todas perdida: batalha {batalha >> 8} → {perdeu >> 8} válidas"

    def _marcar_perder(self) -> str:
        self.box.conq_reset(True)
        sem, x4, trein = cq.num("sem_desmaio"), cq.num("golpe_x4"), cq.num("treinadores")
        base = self.box.conq_checar()
        assert self.box.conq_aplicar(sem, APLICAR_MARCAR) == (FEITA, 0, 0, 0)
        assert self.box.conq_aplicar(sem, APLICAR_PERDER) == (FEITA, 0, 0, 0), "feita virou perdida"
        assert self.box.conq_checar() == base + 1, "a feita não entregue é um aviso"
        assert self.box.conq_aplicar(sem, APLICAR_ENTREGUE) == (FEITA, 1, 0, 0)
        assert self.box.conq_checar() == base, "a entregue deixa de ser aviso"
        assert self.box.conq_aplicar(x4, APLICAR_PERDER) == (PERDIDA, 0, 0, 0)
        assert self.box.conq_aplicar(x4, APLICAR_MARCAR) == (PERDIDA, 0, 0, 0), "perdida virou feita"
        assert self.box.conq_aplicar(trein, APLICAR_DEGRAU, 2) == (PENDENTE, 0, 2, 0)
        assert self.box.conq_aplicar(sem, APLICAR_DEGRAU, 2) == (FEITA, 1, 0, 0), "degrau sem degraus"
        # os vizinhos de bit não mudaram
        for cid in ("golpe_x4", "rival_todas", "lider_um_pokemon"):
            assert self._estado(cid)[1] == 0, cid
        assert self._estado("rival_todas")[0] == PENDENTE == self._estado("lider_um_pokemon")[0]
        return "Marcar/Perder/SetEntregue/SetDegrauEntregue: feita fica feita, perdida nunca vira feita"

    # --- Task 3: varredura do save antigo -------------------------------------------------
    def _trainer_const(self, name: str) -> int:
        return self.consts._eval(name)   # TRAINER_* e NUM_TRAINERS (opponents.h), TRAINER_FLAGS_START (flags.h)

    def _do_ginasio(self) -> set[int]:
        """Treinadores que o set_gym_trainers dos Ginásios com a insígnia ligou (não provam vitória)."""
        return {self._trainer_const(t) for i, ginasio in enumerate(cq.treinadores_do_ginasio())
                if self.game.flag(self.consts.flag(BADGES[i])) for t in ginasio}

    def _flags_brutas(self) -> int:
        inicio = self._trainer_const("TRAINER_FLAGS_START")
        return sum(self.game.flag(inicio + t) for t in range(1, self._trainer_const("NUM_TRAINERS")))

    def _flags_de_treinador(self) -> int:
        """O espelho da varredura: flags de treinador ligadas, menos as dos Ginásios já vencidos."""
        inicio, fora = self._trainer_const("TRAINER_FLAGS_START"), self._do_ginasio()
        return sum(self.game.flag(inicio + t) for t in range(1, self._trainer_const("NUM_TRAINERS"))
                   if t not in fora)

    def _save_antigo(self) -> str:
        assert self.box.conq_reset(False) == 0
        for flag in BADGES + ["FLAG_SYS_GAME_CLEAR"]:
            self._flag(flag)
        inicio = self._trainer_const("TRAINER_FLAGS_START")
        assert self.box.set_flag(inicio + self._trainer_const("TRAINER_RIVAL_OAKS_LAB_SQUIRTLE"))
        self.box.set_party_mon(0, self.consts.species("MEWTWO"), 100)
        vitorias = self._flags_de_treinador()
        avisos = self.box.conq_checar()
        assert self.box.conq_contador(3) == cq.CONQ_MAGIC, "marcador"
        assert self.box.conq_contador(2) == cq.CONQ_ORIGEM_SAVE_ANTIGO | 1 << 8, "origem | resumoPendente"
        assert avisos == 1, f"com o resumo pendente o aviso é um só: {avisos}"
        feitas = [f"insignia_{n}" for n in ("rocha", "cascata", "trovao", "arcoiris", "alma", "pantano",
                                              "vulcao", "terra")] + ["campeao", "vencer_elite4", "nivel_100"]
        for cid in feitas:
            assert self._estado(cid)[0] == FEITA, (cid, self._estado(cid))
        for cid in ("lider_um_pokemon", "rival_todas"):
            assert self._estado(cid)[0] == PERDIDA, (cid, self._estado(cid))
        assert self._estado("sem_desmaio")[0] == PENDENTE, self._estado("sem_desmaio")
        assert self.box.conq_contador(0) == vitorias, f"vitórias {self.box.conq_contador(0)} ≠ flags {vitorias}"
        diario = self._diario_raw()
        assert diario[1] == 1 and not any(diario[:1]) and not any(diario[2:]), "diário de save antigo"
        self._vitorias_retro = vitorias
        return f"varredura: {len(feitas)} feitas conferidas, 2 perdidas, {vitorias} vitórias pelas flags"

    def _roda_uma_vez(self) -> str:
        assert getattr(self, "_vitorias_retro", None) is not None, "depende de retro/save_antigo"
        inicio = self._trainer_const("TRAINER_FLAGS_START")
        fora = {self._trainer_const(t) for ginasio in cq.treinadores_do_ginasio() for t in ginasio}
        livre = next(t for t in range(1, self._trainer_const("NUM_TRAINERS"))
                     if not self.game.flag(inicio + t) and t not in fora)
        assert self.box.set_flag(inicio + livre)
        self.box.conq_checar()
        assert self.box.conq_contador(0) == self._vitorias_retro, "a varredura rodou de novo"
        assert self.box.conq_contador(2) & 0xFF == cq.CONQ_ORIGEM_SAVE_ANTIGO, "origem"
        return f"flag do treinador {livre} ligada depois: vitórias continuam {self._vitorias_retro}"

    def _ginasio_desconta(self) -> str:
        """O set_gym_trainers liga todos os treinadores do Ginásio ao vencer o líder: com a insígnia, as
        flags deles não provam vitória e saem da conta (sem a insígnia, contam)."""
        inicio = self._trainer_const("TRAINER_FLAGS_START")
        cerulean = cq.treinadores_do_ginasio()[1]   # FLAG_BADGE02_GET
        for flag in BADGES:
            self._flag(flag, False)
        for t in cerulean + ["TRAINER_LEADER_MISTY"]:
            assert self.box.set_flag(inicio + self._trainer_const(t))
        # sem a insígnia: as flags do Ginásio vieram de batalha e contam
        assert self.box.conq_reset(False) == 0
        self.box.conq_checar()
        sem = self.box.conq_contador(0)
        assert sem == self._flags_brutas() == self._flags_de_treinador(), (sem, self._flags_brutas())
        # com a insígnia: o set_gym_trainers pode ter ligado as dos treinadores do Ginásio
        self._flag("FLAG_BADGE02_GET")
        assert self.box.conq_reset(False) == 0
        self.box.conq_checar()
        com, brutas = self.box.conq_contador(0), self._flags_brutas()
        assert com == self._flags_de_treinador() == brutas - len(cerulean), (com, brutas, len(cerulean))
        assert com != brutas, "a regra antiga (todas as flags) contaria os do Ginásio"
        return (f"Ginásio de Cerulean com a insígnia: {com} vitórias (não {brutas}); "
                f"sem a insígnia: {sem}; a Misty conta")

    def _pc(self) -> str:
        """Shiny chocado pelo jogador e um nível 100 só no PC (o time fica sem nível 100 nem shiny)."""
        mewtwo, pidgey = self.consts.species("MEWTWO"), self.consts.species("PIDGEY")
        for slot, _ in enumerate(self.game.party()):
            self.box.set_party_mon(slot, pidgey, 5)   # personalidade fixa nunca shiny
        caixa = 13                                    # a última caixa: o save do modo rápido não chega lá
        for pos in (28, 29):
            self.box.conq_pc_mon(caixa, pos, 0)
        assert self.box.conq_reset(False) == 0
        self.box.conq_checar()
        antes = self.box.conq_contador(1)
        for cid in ("nivel_100", "ovo_shiny", "ovo_6ivs"):
            assert self._estado(cid)[0] == PENDENTE, (cid, self._estado(cid))
        self.box.conq_pc_mon(caixa, 28, pidgey, 5, shiny=True, chocado=True)
        self.box.conq_pc_mon(caixa, 29, mewtwo, 100)
        assert self.box.conq_reset(False) == 0
        self.box.conq_checar()
        depois = self.box.conq_contador(1)
        assert depois == antes + 1, f"shinies {antes} → {depois}"
        for cid in ("nivel_100", "ovo_shiny", "ovo_6ivs"):
            assert self._estado(cid)[0] == FEITA, (cid, self._estado(cid))
        for pos in (28, 29):
            self.box.conq_pc_mon(caixa, pos, 0)
        return f"PC: shinies {antes} → {depois}; nivel_100, ovo_shiny e ovo_6ivs feitas só pelo PC"

    # --- Task 4: gatilhos de evento ------------------------------------------------------
    def _time_de_um(self, species: str, level: int, move: str) -> None:
        """Time = só `species` nv `level`, com `move` no 1º golpe (o que o BattleDriver usa)."""
        self.box.set_party_mon(0, self.consts.species(species), level)
        assert self.box.party_size(1) == 1, "time de um só"
        self.box.set_party_move(0, 0, MOVES[move])

    def _lutar(self, what: str, esperado: str) -> None:
        resultado = self.driver.fight_to_end()
        assert resultado == esperado, f"{what}: batalha terminou em {resultado}, esperava {esperado}"
        if resultado == "lose":
            self._finish_script(f"{what}: desmaio, volta ao Centro", WHITEOUT_TIMEOUT)
        else:
            self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)

    def _lider_e_sem_desmaio(self) -> str:
        self.box.conq_reset(True)
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        self.box.start_trainer_battle(self._trainer_const("TRAINER_LEADER_BROCK"))
        self._lutar("Brock", "win")
        for cid in ("lider_um_pokemon", "sem_desmaio"):
            assert self._estado(cid)[0] == FEITA, (cid, self._estado(cid))
        assert self._estado("rival_todas")[0] == PENDENTE, self._estado("rival_todas")
        assert self.box.conq_contador(0) == 1, f"vitórias = {self.box.conq_contador(0)}"
        return "Mewtwo sozinho vence o Brock: lider_um_pokemon e sem_desmaio feitas, vitórias 0 → 1"

    def _golpe_x4(self) -> str:
        self.box.conq_reset(True)
        geodude = self.consts.species("GEODUDE")
        self._time_de_um("BLASTOISE", 100, "MOVE_PSYCHIC")
        assert self.box.call(CMD_START_WILD_BATTLE, geodude, 5) == 1, "START_WILD_BATTLE"
        self._lutar("Psychic no Geodude", "win")
        assert self._estado("golpe_x4")[0] == PENDENTE, ("Psychic (x1)", self._estado("golpe_x4"))
        # dano fixo: o typecalc vê x4 (Lutador contra Pedra/Noturno), mas o dano não depende do tipo
        self.box.set_party_move(0, 0, MOVES["MOVE_SEISMIC_TOSS"])
        assert self.box.call(CMD_START_WILD_BATTLE, self.consts.species("TYRANITAR"), 5) == 1, "START_WILD_BATTLE"
        self._lutar("Seismic Toss no Tyranitar", "win")
        assert self._estado("golpe_x4")[0] == PENDENTE, ("Seismic Toss (dano fixo)", self._estado("golpe_x4"))
        self.box.set_party_move(0, 0, MOVES["MOVE_SURF"])
        assert self.box.call(CMD_START_WILD_BATTLE, geodude, 5) == 1, "START_WILD_BATTLE"
        self._lutar("Surf no Geodude", "win")
        assert self._estado("golpe_x4")[0] == FEITA, ("Surf (x4)", self._estado("golpe_x4"))
        assert self.box.conq_contador(0) == 0, "batalha selvagem não é vitória de treinador"
        return ("Blastoise: Psychic (x1) no Geodude e Seismic Toss (dano fixo, x4 de tipo) no Tyranitar pendentes; "
                "Surf (x4) no Geodude feita")

    def _derrota_nao_conta(self) -> str:
        self.box.conq_reset(True)
        # o retro/* deixa o Hall ligado: com ele o slot do rival ficaria vazio também por ser "revanche"
        self._flag("FLAG_SYS_GAME_CLEAR", False)
        self._time_de_um("MAGIKARP", 2, "MOVE_SPLASH")
        self.box.start_trainer_battle(self._trainer_const("TRAINER_RIVAL_OAKS_LAB_SQUIRTLE"))
        self._lutar("rival do laboratório", "lose")
        assert self._estado("rival_todas")[0] == PERDIDA, self._estado("rival_todas")
        for cid in ("sem_desmaio", "lider_um_pokemon", "golpe_x4"):
            assert self._estado(cid)[0] == PENDENTE, (cid, self._estado(cid))
        assert self.box.conq_contador(0) == 0, f"vitórias = {self.box.conq_contador(0)}"
        assert self.box.diario_entrada(cq.evento("rival_lab")) is None, "derrota entrou no diário"
        return "Magikarp perde para o rival: rival_todas perdida, vitórias 0, nada de batalha feito, diário vazio"

    def _captura_poke_ball(self) -> str:
        self.box.conq_reset(True)
        pidgey, snorlax = self.consts.species("PIDGEY"), self.consts.species("SNORLAX")
        poke, ultra = self.consts.item("ITEM_POKE_BALL"), self.consts.item("ITEM_ULTRA_BALL")
        self.box.conq_captura(pidgey, poke)
        assert self._estado("poke_ball_dificil")[0] == PENDENTE, "Pidgey (taxa 255)"
        self.box.conq_captura(snorlax, ultra)
        assert self._estado("poke_ball_dificil")[0] == PENDENTE, "Snorlax com Ultra Ball"
        self.box.conq_captura(snorlax, poke)
        assert self._estado("poke_ball_dificil")[0] == FEITA, ("Snorlax com Poké Ball", self._estado("poke_ball_dificil"))
        assert self.box.conq_contador(1) == 0, "a captura não soma shiny (é o GiveMonToPlayer que soma)"
        return "Pidgey/Poké Ball e Snorlax/Ultra Ball pendentes; Snorlax (taxa 25)/Poké Ball feita"

    def _trocar_para(self, slot: int) -> None:
        """No menu de ação: POKéMON → slot → TROCAR (a 1ª opção do submenu)."""
        d = self.driver
        d.wait_action_menu()
        d._choose_action(ACTION_POKEMON)
        self.ctl.wait_until(lambda: PARTY_CHOOSE_TASK in self._tasks(), 300, "tela de Pokémon da batalha")
        cursor = self.game.syms.addr("gPartyMenu") + PARTY_MENU_SLOT_ID
        for _ in range(PARTY_SIZE):
            if self.emu.read_u8(cursor) == slot:
                break
            antes = self.emu.read_u8(cursor)
            self.ctl.press_until(KEY_DOWN, lambda: self.emu.read_u8(cursor) != antes, f"cursor no slot {slot}")
        assert self.emu.read_u8(cursor) == slot, f"cursor em {self.emu.read_u8(cursor)}"
        self.ctl.press_until(KEY_A, lambda: PARTY_SELECTION_TASK in self._tasks(), "submenu TROCAR")
        self.ctl.press_until(KEY_A, lambda: PARTY_SELECTION_TASK not in self._tasks(), "TROCAR")
        d.wait_action_menu()
        assert d.active_slot() == slot, f"em campo o slot {d.active_slot()}"

    def _turno_golpe_1(self, on_step) -> str:
        """Um turno de LUTAR com o 1º golpe, olhando a batalha a cada passo: 'menu' ou 'end'."""
        d = self.driver
        d.wait_action_menu()
        d._choose_action(ACTION_FIGHT)
        em_golpes = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(em_golpes, 300, "menu de golpes")
        d._choose_first_move_with_pp()
        self.ctl.wait_until(lambda: not em_golpes(), 60, "saída do menu de golpes")
        return d._advance_until_menu_or_end("fim do turno", 3000, on_step=on_step)

    def _tardio_info(self) -> tuple[int, int, int]:
        """(PS do oponente, contador e dano guardado do golpe tardio contra ele: gWishFutureKnock, battler 1)."""
        base = self.game.syms.addr("gWishFutureKnock")
        return (self.driver.battler_hp(1), self.emu.read_u8(base + 1),
                int.from_bytes(self.emu.read(base + 8 + 4, 4), "little", signed=True))

    def _nocaute_tardio(self) -> str:
        """Mewtwo usa Future Sight e sai; o Magikarp que entrou só usa Splash, e a batida tardia derruba o Pidgey.
        O nocaute não vai para o Magikarp (gBattlerAttacker é a posição, não quem usou o golpe). A batida tardia
        tem precisão 90: se errar, foge e tenta de novo (até TENTATIVAS_TARDIO vezes)."""
        self.box.conq_reset(True)
        visto = {"tardio": 0, "nocautes": bytes(PARTY_SIZE)}

        def olhar() -> None:
            if not self.game.in_battle():
                return
            base = self.emu.read_u32(self.game.syms.addr("gBattleStruct"))
            if not 0x02000000 <= base < 0x02040000:
                return
            visto["tardio"] = max(visto["tardio"], self.emu.read_u8(base + BS_CONQ_GOLPE_TARDIO))
            nocautes = self.emu.read(base + BS_CONQ_NOCAUTES, PARTY_SIZE)
            if any(nocautes):
                visto["nocautes"] = nocautes
        tentativas = []
        for _ in range(TENTATIVAS_TARDIO):
            self.box.set_party_mon(0, self.consts.species("MEWTWO"), 100)
            self.box.set_party_mon(1, self.consts.species("MAGIKARP"), 50)
            assert self.box.party_size(2) == 2
            self.box.set_party_move(0, 0, MOVES["MOVE_FUTURE_SIGHT"])
            self.box.set_party_move(1, 0, MOVES["MOVE_SPLASH"])
            assert self.box.call(CMD_START_WILD_BATTLE, self.consts.species("PIDGEY"), 2) == 1, "START_WILD_BATTLE"
            historia = []
            assert self._turno_golpe_1(olhar) == "menu", "turno 1 (Future Sight)"
            historia.append(("Future Sight", *self._tardio_info()))
            self._trocar_para(1)
            historia.append(("troca", *self._tardio_info()))
            fim = "menu"
            for _ in range(3):
                fim = self._turno_golpe_1(olhar)
                if fim == "end":
                    break
                historia.append(("Splash", *self._tardio_info()))
            tentativas.append(historia)
            if fim == "end":
                break
            # a batida errou (o contador já chegou a 0): foge e recomeça
            while self.game.in_battle() and not self.driver.run_away():
                pass
            self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)
        assert fim == "end" and self.driver.outcome() == 1, f"o Pidgey não caiu em {len(tentativas)}: {tentativas}"
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)
        assert self.game.party()[1].hp > 0 and self.game.party()[0].hp > 0, "alguém do time desmaiou"
        assert not any(visto["nocautes"]), f"nocaute creditado: conqNocautes = {visto['nocautes'].hex()}"
        assert visto["tardio"] == 1, "conqGolpeTardio nunca foi ligado"
        self.box.party_size(1)
        return (f"Future Sight do Mewtwo derruba o Pidgey com o Magikarp em campo, na tentativa {len(tentativas)} "
                f"(PS, contador e dano por turno: {tentativas[-1]}): conqNocautes todo 0, conqGolpeTardio ligado")

    def _ovo_chocado(self) -> str:
        """Ovos do jogador chocados pelo special de verdade (AddHatchedMonToParty → Conquistas_OnOvoChocado)."""
        self.box.conq_reset(True)
        pidgey = self.consts.species("PIDGEY")
        self.box.set_party_mon(0, pidgey, 5)
        assert self.box.party_size(1) == 1
        self.box.conq_chocar(1, pidgey)
        assert self.box.conq_contador(1) == 0, "ovo comum não é shiny"
        for cid in ("ovo_shiny", "ovo_6ivs"):
            assert self._estado(cid)[0] == PENDENTE, (cid, self._estado(cid))
        self.box.conq_chocar(2, pidgey, shiny=True)
        assert self.box.conq_contador(1) == 1, f"shinies = {self.box.conq_contador(1)}"
        assert self._estado("ovo_shiny")[0] == FEITA, self._estado("ovo_shiny")
        assert self._estado("ovo_6ivs")[0] == PENDENTE, self._estado("ovo_6ivs")
        self.box.conq_chocar(3, pidgey, ivs31=True)
        assert self._estado("ovo_6ivs")[0] == FEITA, self._estado("ovo_6ivs")
        assert self.box.conq_contador(1) == 1, "o ovo de 6 IVs não é shiny"
        self.box.party_size(1)
        return "ovo comum: nada; ovo shiny: shinies 0 → 1 e ovo_shiny feita; ovo com 6 IVs 31: ovo_6ivs feita"

    def _lider_antes_da_insignia(self) -> str:
        """Caso real, o 8º líder: com 7 insígnias, vencer o Giovanni com um Pokémon só no Ginásio de verdade. A marca
        vem no fim da batalha, antes do `setflag FLAG_BADGE08_GET` do script; a checagem seguinte, já com as 8
        insígnias (que perderia a pendente), encontra a conquista feita."""
        self.box.conq_reset(True)
        for i, flag in enumerate(BADGES):
            self._flag(flag, i < 7)
        inicio = self._trainer_const("TRAINER_FLAGS_START")
        assert not self.box.set_flag(inicio + self._trainer_const("TRAINER_LEADER_GIOVANNI"), False)
        for t in cq.treinadores_do_ginasio()[7]:     # ninguém no caminho do olhar
            assert self.box.set_flag(inicio + self._trainer_const(t))
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        group, num = self.consts.map("MAP_VIRIDIAN_CITY_GYM")
        self.box.call(CMD_WARP, group | num << 8, GIOVANNI_FRENTE[0] | GIOVANNI_FRENTE[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para o Ginásio de Viridian")
        self.ctl.wait_overworld_idle(600)
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Giovanni")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "fala do Giovanni")
        resultado = self.driver.fight_to_end()
        assert resultado == "win", f"Giovanni: batalha terminou em {resultado}"
        assert self._estado("lider_um_pokemon")[0] == FEITA, ("fim da batalha", self._estado("lider_um_pokemon"))
        self._finish_script("Giovanni entrega a Insígnia Terra e a MT26")
        assert self.game.flag(self.consts.flag("FLAG_BADGE08_GET")), "o script não ligou a 8ª insígnia"
        self.box.conq_checar()
        assert self._estado("lider_um_pokemon")[0] == FEITA, ("depois da checagem", self._estado("lider_um_pokemon"))
        assert self._estado("insignia_terra")[0] == FEITA, self._estado("insignia_terra")
        return ("Giovanni vencido com o Mewtwo sozinho: feita no fim da batalha; o script liga FLAG_BADGE08_GET "
                "depois e a checagem com 8 insígnias mantém lider_um_pokemon feita")

    # --- Task 5: diário das batalhas marcantes ---------------------------------------------
    def _entrada(self, eid: str) -> dict | None:
        return self.box.diario_entrada(cq.evento(eid))

    def _minutos_de_jogo(self) -> int:
        raw = self.emu.read(self._sb(2) + SB2_PLAY_TIME_HOURS, 3)
        return int.from_bytes(raw[:2], "little") * 60 + raw[2]

    def _diario_brock(self) -> str:
        """Mewtwo nv 100 com Psychic vence o Brock (2 Pokémon, um golpe cada): a 1ª entrada do diário, com a ordem 1
        num diário recém-zerado (proximaOrdem 0 conta como 1)."""
        self.box.conq_reset(True)
        assert self._diario_raw()[0] == 0, "proximaOrdem do jogo novo"
        self._flag("FLAG_SYS_GAME_CLEAR", False)    # o retro/* deixa ligada; com ela, treinador não entra (revanche)
        assert self._entrada("brock") is None, "diário de jogo novo com o Brock"
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        self.box.start_trainer_battle(self._trainer_const("TRAINER_LEADER_BROCK"))
        self._lutar("Brock", "win")
        minutos = self._minutos_de_jogo()
        e = self._entrada("brock")
        assert e is not None, "Brock vencido e o diário vazio"
        assert (e["resultado"], e["ordem"], e["turnos"]) == (cq.DIARIO_VENCEU, 1, 2), e
        assert e["time"] == [(self.consts.species("MEWTWO"), 100)] and e["tamanhoTime"] == 1, e
        assert (e["mvp"], e["mvpNocautes"]) == (0, 2), e
        assert abs(e["minutos"] - minutos) <= 1, (e["minutos"], minutos)
        assert self._diario_raw()[0] == 2, f"proximaOrdem = {self._diario_raw()[0]}"
        self._brock = e
        return f"entrada do Brock: {e}"

    def _diario_so_a_primeira(self) -> str:
        """Vencer o Brock de novo (com outro time) não mexe na entrada: só a 1ª vitória entra."""
        antes = getattr(self, "_brock", None)
        assert antes is not None, "sem a entrada do diario/brock"
        self.box.set_party_mon(0, self.consts.species("MEWTWO"), 99)
        self.box.party_size(1)
        self.box.set_party_move(0, 0, MOVES["MOVE_PSYCHIC"])
        self.box.start_trainer_battle(self._trainer_const("TRAINER_LEADER_BROCK"))
        self._lutar("Brock de novo", "win")
        depois = self._entrada("brock")
        assert depois == antes, (antes, depois)
        assert self._diario_raw()[0] == 2, f"proximaOrdem = {self._diario_raw()[0]}"
        return f"2ª vitória (Mewtwo nv 99): entrada igual, ordem {depois['ordem']}, turnos {depois['turnos']}"

    def _diario_lendario(self) -> str:
        """Articuno nv 50: derrotado entra como DERROTOU; capturado depois (Master Ball) troca a entrada, com ordem
        nova, maior que a do Brock."""
        articuno = self.consts.species("ARTICUNO")
        brock = self._entrada("brock")
        assert brock is not None, "o diário perdeu o Brock"
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        assert self.box.call(CMD_START_WILD_BATTLE, articuno, 50) == 1, "START_WILD_BATTLE"
        self._lutar("Articuno (derrotado)", "win")
        derrotado = self._entrada("articuno")
        assert derrotado is not None and derrotado["resultado"] == cq.DIARIO_DERROTOU, derrotado
        assert derrotado["ordem"] > brock["ordem"], (derrotado, brock)
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1, "GIVE_ITEM Master Ball"
        assert self.box.call(CMD_START_WILD_BATTLE, articuno, 50) == 1, "START_WILD_BATTLE"
        assert self.driver.throw_ball(master), "Master Ball não capturou"
        d = self.driver
        while not d._battle_over():          # sem apelido (B) e o resto das mensagens
            d._press(KEY_B if d._script_command() == NICKNAME_COMMAND else KEY_A)
        assert d.outcome() == B_OUTCOME_CAUGHT, f"gBattleOutcome = {d.outcome()}"
        self.ctl.wait_overworld_idle(POST_BATTLE_TIMEOUT)
        e = self._entrada("articuno")
        assert e is not None and e["resultado"] == cq.DIARIO_CAPTURADO, e
        assert e["ordem"] > derrotado["ordem"] > brock["ordem"], (e, derrotado, brock)
        assert e["time"] == [(self.consts.species("MEWTWO"), 100)], e
        assert (e["mvp"], e["mvpNocautes"]) == (0xFF, 0), e
        assert self._entrada("brock") == brock, "o Brock mudou"
        self.box.party_size(1)
        return f"Articuno DERROTOU (ordem {derrotado['ordem']}) → CAPTURADO (ordem {e['ordem']}); Brock {brock['ordem']}"

    def _diario_mvp_depois_da_troca(self) -> str:
        """Magikarp nv 5 na frente e Mewtwo nv 100 atrás: troca para o Mewtwo no 1º turno e ele vence o Brock.
        O MVP é o Mewtwo (índice 1 do time, pela personalidade) e o time sai na ordem do time. O set_party_mon dá a
        todos a mesma personalidade fixa: o Magikarp sai de um ovo shiny chocado (conq_chocar), com outra."""
        magikarp = self.consts.species("MAGIKARP")
        self.box.set_party_mon(0, magikarp, 5)
        self.box.set_party_mon(1, self.consts.species("MEWTWO"), 100)
        assert self.box.party_size(2) == 2
        self.box.conq_chocar(0, magikarp, shiny=True)
        pids = [m.personality for m in self.game.party()[:2]]
        assert pids[0] != pids[1], f"personalidades iguais: {pids}"
        self.box.conq_reset(True)
        self.box.set_party_move(0, 0, MOVES["MOVE_SPLASH"])
        self.box.set_party_move(1, 0, MOVES["MOVE_PSYCHIC"])
        self.box.start_trainer_battle(self._trainer_const("TRAINER_LEADER_BROCK"))
        self._trocar_para(1)
        self._lutar("Brock depois da troca", "win")
        e = self._entrada("brock")
        assert e is not None and e["resultado"] == cq.DIARIO_VENCEU and e["ordem"] == 1, e
        # o Magikarp ganha EXP pelo Geodude (estava em campo no 1º turno): o nível é o do fim da batalha
        nivel_magikarp = self.game.party()[0].level
        assert e["time"] == [(magikarp, nivel_magikarp), (self.consts.species("MEWTWO"), 100)], e
        assert (e["mvp"], e["mvpNocautes"]) == (1, 2), e
        self.box.party_size(1)
        return f"troca no 1º turno: {e}"

    def _diario_liga_e_revanche(self) -> str:
        """Sem FLAG_SYS_GAME_CLEAR (a 1ª Liga, antes do Hall da Fama), o Campeão entra no diário; com ela ligada (o
        save já passou pelo Hall), a vitória sobre a Lorelei com o slot vazio é revanche e não entra."""
        self.box.conq_reset(True)
        self._flag("FLAG_SYS_GAME_CLEAR", False)
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        self.box.start_trainer_battle(self._trainer_const("TRAINER_CHAMPION_FIRST_SQUIRTLE"))
        self._lutar("Campeão (1ª Liga)", "win")
        campeao = self._entrada("campeao")
        assert campeao is not None and campeao["resultado"] == cq.DIARIO_VENCEU and campeao["ordem"] == 1, campeao
        self._flag("FLAG_SYS_GAME_CLEAR")
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        assert self._entrada("lorelei") is None
        self.box.start_trainer_battle(self._trainer_const("TRAINER_ELITE_FOUR_LORELEI"))
        self._lutar("Lorelei (revanche)", "win")
        assert self._entrada("lorelei") is None, self._entrada("lorelei")
        assert self._diario_raw()[0] == 2, f"proximaOrdem = {self._diario_raw()[0]}"
        self._flag("FLAG_SYS_GAME_CLEAR", False)
        return f"Campeão sem a flag: entrada {campeao}; Lorelei com FLAG_SYS_GAME_CLEAR: slot vazio"

    def _diario_jogo_novo_zera(self) -> str:
        assert self._entrada("campeao") is not None, "nada para zerar"
        self.box.conq_reset(True)
        assert self._entrada("campeao") is None and self._entrada("brock") is None
        assert self._diario_raw()[0] == 0, "proximaOrdem"
        return "jogo novo: entrada do Campeão vazia"

    # --- Task 6: o aviso e o prêmio ------------------------------------------------------------
    def _aviso_ativo(self) -> bool:
        return self.emu.read_u8(self.game.syms.addr(AVISO_ATIVO)) == 1

    def _esperar_aviso(self, what: str, foto: str | None = None) -> str:
        """Espera o aviso aparecer; devolve o texto montado (gStringVar4) e grava a foto com a janela parada."""
        self.ctl.wait_until(self._aviso_ativo, AVISO_TIMEOUT, what)
        texto = self._field_message()
        if foto:
            self.emu.frames(AVISO_ENTRADA)
            self.measures.setdefault("fotos_aviso", []).append(self._shot(foto))
        return texto

    def _fechar_aviso(self, what: str) -> None:
        self.ctl.press_until(KEY_A, lambda: not self._aviso_ativo(), what, tries=15, wait=20)
        self.ctl.wait_overworld_idle(300)

    def _ir(self, mapa: str, xy: tuple[int, int]) -> None:
        group, num = self.consts.map(mapa)
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {mapa}")
        self.ctl.wait_overworld_idle(600)

    def _sem_pendentes(self) -> None:
        """Jogo novo nas conquistas, com tudo o que o save já prova marcado como entregue: nenhum aviso pendente.
        Monta em silêncio (senão o aviso entregaria no meio) e religa os avisos no fim."""
        self.box.conq_silencio(True)
        self.box.conq_reset(True)
        self.box.conq_checar()
        for c in cq.dados()["conquistas"]:
            if not c.get("ativa", True):
                continue
            estado, entregue, deg_entregue, deg_atual = self.box.conq_estado(c["num"])
            if c.get("degraus"):
                if deg_atual > deg_entregue:
                    self.box.conq_aplicar(c["num"], APLICAR_DEGRAU, deg_atual)
            elif estado == FEITA and not entregue:
                self.box.conq_aplicar(c["num"], APLICAR_ENTREGUE)
        assert self.box.conq_checar() == 0, "sobrou aviso pendente"
        self.box.conq_silencio(False)

    def _pc_qtd(self, item: int) -> int:
        raw = self.emu.read(self._sb(1) + SB1_PC_ITEMS, PC_ITEMS_COUNT * 4)
        return sum(q for i in range(PC_ITEMS_COUNT) for it, q in [struct_unpack(raw, i)] if it == item)

    def _poke_ball_na_bolsa(self, qtd: int) -> None:
        """Muda a quantidade da Poké Ball no bolso de bolas (escrita na RAM, quantidade XOR chave)."""
        poke = self.consts.item("ITEM_POKE_BALL")
        base = self._sb(1) + SB1_BALLS
        raw = self.emu.read(base, BALLS_COUNT * 4)
        slot = next(i for i in range(BALLS_COUNT) if struct_unpack(raw, i)[0] == poke)
        self.emu.write(base + slot * 4 + 2, (qtd ^ (self.game._key() & 0xFFFF)).to_bytes(2, "little"))

    def _preparar_avisos(self) -> str:
        """Ponto de volta dos grupos de aviso, ainda em silêncio (o `_sem_pendentes` de cada grupo desliga o silêncio
        com nada pendente: os grupos anteriores deixam conquistas feitas e não entregues)."""
        self.ctl.checkpoint("conquistas_avisos")
        return "checkpoint conquistas_avisos (em silêncio)"

    def _aparece_e_entrega(self) -> str:
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self._set_money(0)              # o estado/dinheiro deixou ₽999.999: sem isto o Milionário já viria entregue
        self._sem_pendentes()
        self._set_money(999999)
        moeda = self.consts.item("ITEM_AMULET_COIN")
        antes = self.game.bag_quantity(moeda)
        self.nav.step("left", 1)
        texto = self._esperar_aviso("aviso do Milionário", foto="conquista_aviso")
        assert "Milionário" in texto and "na bolsa" in texto, texto
        assert self._estado("dinheiro")[:2] == (FEITA, 1), self._estado("dinheiro")
        assert self.game.bag_quantity(moeda) == antes + 1, "Moeda Amuleto não foi para a bolsa"
        self._fechar_aviso("A fecha o aviso")
        assert not self._aviso_ativo()
        self.nav.step("right", 1)       # o jogo voltou: anda de novo
        return f"aviso: {texto!r}; Moeda Amuleto {antes} → {antes + 1}; dinheiro entregue"

    def _espera_fim_da_batalha(self) -> str:
        self.box.conq_silencio(True)
        self._time_de_um("BLASTOISE", 100, "MOVE_SURF")   # nível 100 já entregue pelo _sem_pendentes
        self._sem_pendentes()
        visto = []
        assert self.box.call(CMD_START_WILD_BATTLE, self.consts.species("GEODUDE"), 5) == 1, "START_WILD_BATTLE"
        resultado = self.driver.fight_to_end(on_step=lambda: visto.append(self._aviso_ativo()))
        assert resultado == "win", resultado
        assert visto and not any(visto), "aviso durante a batalha"
        assert self._estado("golpe_x4")[:2] == (FEITA, 0), ("feita na batalha, entregue depois", self._estado("golpe_x4"))
        texto = self._esperar_aviso("aviso do golpe x4 de volta ao campo")
        assert "Golpe 4" in texto, texto
        self._fechar_aviso("fecha o aviso do x4")
        assert self._estado("golpe_x4")[:2] == (FEITA, 1), self._estado("golpe_x4")
        return f"{len(visto)} leituras na batalha com o aviso fechado; no campo: {texto!r}"

    def _fila(self) -> str:
        for flag in ("FLAG_BADGE01_GET", "FLAG_BADGE02_GET"):
            self._flag(flag, False)
        self._sem_pendentes()
        for flag in ("FLAG_BADGE01_GET", "FLAG_BADGE02_GET"):
            self._flag(flag)
        textos = []
        for i in range(2):
            textos.append(self._esperar_aviso(f"aviso {i + 1} da fila"))
            entregues = [self._estado(c)[1] for c in ("insignia_rocha", "insignia_cascata")]
            assert sum(entregues) == i + 1, f"aviso {i + 1}: entregues {entregues} (um por vez)"
            self._fechar_aviso(f"fecha o aviso {i + 1}")
        assert "Rocha" in textos[0] and "Cascata" in textos[1], textos
        return f"dois avisos seguidos: {textos}"

    def _degrau(self) -> str:
        self._sem_pendentes()
        self.emu.write(self._sb(1) + SB1_CONQUISTAS + CONQ_VITORIAS, (10).to_bytes(2, "little"))
        great = self.consts.item("ITEM_GREAT_BALL")
        antes = self.game.bag_quantity(great)
        texto = self._esperar_aviso("aviso do degrau de treinadores", foto="conquista_aviso_degrau")
        assert "Vencer 10 treinadores" in texto, texto
        self._fechar_aviso("fecha o aviso do degrau")
        assert self._estado("treinadores")[2] == 1, self._estado("treinadores")
        assert self.game.bag_quantity(great) == antes + 3
        return f"10 vitórias: {texto!r}, degrau entregue 1"

    def _bolsa_cheia(self) -> str:
        poke = self.consts.item("ITEM_POKE_BALL")
        self._flag("FLAG_BADGE01_GET", False)
        self._sem_pendentes()
        ocupados = self.box.encher_bolso(poke)
        assert ocupados >= 12, ocupados
        pc = self._pc_qtd(poke)
        self._flag("FLAG_BADGE01_GET")
        texto = self._esperar_aviso("aviso da Insígnia Rocha com a bolsa cheia", foto="conquista_aviso_pc")
        assert "no PC" in texto, texto
        assert self._pc_qtd(poke) == pc + 5, f"PC: {pc} → {self._pc_qtd(poke)}"
        assert self._estado("insignia_rocha")[1] == 1
        self._fechar_aviso("fecha o aviso no PC")
        return f"bolso de bolas com {ocupados} espaços cheios: {texto!r}; PC +5 Poké Ball"

    def _tudo_cheio(self) -> str:
        poke = self.consts.item("ITEM_POKE_BALL")
        self._flag("FLAG_BADGE01_GET", False)
        self._sem_pendentes()
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        ocupados = self.box.encher_bolso(poke, pc=True)
        self._flag("FLAG_BADGE01_GET")
        texto = self._esperar_aviso("aviso com bolsa e PC cheios", foto="conquista_aviso_pendente")
        assert "fica para depois" in texto, texto
        assert self._estado("insignia_rocha")[:2] == (FEITA, 0), self._estado("insignia_rocha")
        self._fechar_aviso("fecha o aviso pendente")
        mapa = self.consts.map("MAP_PALLET_TOWN")
        adiado = int.from_bytes(self._conq_raw()[ADIADO_NO_MAPA:ADIADO_NO_MAPA + 2], "little")
        assert adiado == mapa[0] << 8 | mapa[1], f"adiadoNoMapa = {adiado:#x}"
        for i in range(20):
            self.nav.step("left" if i % 2 == 0 else "right", 1)
            assert not self._aviso_ativo(), f"aviso de novo no mesmo mapa (passo {i + 1})"
        self.emu.frames(64)
        assert not self._aviso_ativo() and self._estado("insignia_rocha")[1] == 0
        self._poke_ball_na_bolsa(1)
        self._ir("MAP_VIRIDIAN_CITY", VIRIDIAN_LIVRE)
        texto2 = self._esperar_aviso("aviso com entrega depois de trocar de mapa")
        assert "na bolsa" in texto2, texto2
        assert self._estado("insignia_rocha")[:2] == (FEITA, 1), self._estado("insignia_rocha")
        self._fechar_aviso("fecha o aviso entregue")
        return (f"{ocupados} espaços cheios: {texto!r}; 20 passos em Pallet sem aviso; espaço liberado e Viridian: "
                f"{texto2!r}")

    def _resumo_retro(self) -> str:
        self.ctl.restore("conquistas_avisos")       # sem a bolsa e o PC cheios dos grupos premio/*
        self.box.conq_silencio(True)
        for i, flag in enumerate(BADGES):
            self._flag(flag, i < 3)
        self._flag("FLAG_SYS_GAME_CLEAR", False)
        itens = {c["id"]: self.consts.item(c["premios"][0]["item"]) for c in cq.dados()["conquistas"][:3]}
        antes = {k: self.game.bag_quantity(v) for k, v in itens.items()}
        assert self.box.conq_reset(False) == 0
        self.box.conq_silencio(False)
        texto = self._esperar_aviso("aviso-resumo do save antigo", foto="conquista_resumo")
        assert "Você já tinha" in texto and "conquista" in texto, texto
        assert self.box.conq_contador(2) == cq.CONQ_ORIGEM_SAVE_ANTIGO, "resumoPendente desligado"
        for cid, v in itens.items():
            qtd = cq.dados()["conquistas"][cq.num(cid)]["premios"][0]["qtd"]
            # outros prêmios do save (a 1ª captura também dá Poké Bolas) podem somar no mesmo item
            assert self.game.bag_quantity(v) >= antes[cid] + qtd, (cid, antes[cid], self.game.bag_quantity(v))
            assert self._estado(cid)[:2] == (FEITA, 1), (cid, self._estado(cid))
        self._fechar_aviso("fecha o resumo")
        self.emu.frames(AVISO_TIMEOUT)
        assert not self._aviso_ativo(), "um segundo aviso depois do resumo"
        assert self.box.conq_checar() == 0
        return f"um aviso só: {texto!r}; os 3 prêmios das insígnias na bolsa"

    def run(self) -> None:
        try:
            self._flow("conquistas: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("save/jogo_novo", self._jogo_novo)
            self.suite.run("save/antigo_sem_marcador", self._antigo)
            self.suite.run("save/num_invalido", self._invalido)
            self.suite.run("estado/insignia", self._insignia)
            self.suite.run("estado/dinheiro", self._dinheiro)
            self.suite.run("estado/nivel", self._nivel)
            self.suite.run("estado/degraus_horas", self._degraus_horas)
            self.suite.run("estado/conta_aba", self._conta_aba)
            self.suite.run("estado/marcar_perder", self._marcar_perder)
            self.suite.run("retro/save_antigo", self._save_antigo)
            self.suite.run("retro/roda_uma_vez", self._roda_uma_vez)
            self.suite.run("retro/ginasio_desconta", self._ginasio_desconta)
            self.suite.run("retro/pc", self._pc)
            self.suite.run("evento/lider_e_sem_desmaio", self._lider_e_sem_desmaio)
            self.suite.run("evento/golpe_x4", self._golpe_x4)
            self.suite.run("evento/derrota_nao_conta", self._derrota_nao_conta)
            self.suite.run("evento/captura_poke_ball", self._captura_poke_ball)
            self.suite.run("evento/ovo_chocado", self._ovo_chocado)
            self.suite.run("evento/nocaute_tardio", self._nocaute_tardio)
            self.suite.run("evento/lider_antes_da_insignia", self._lider_antes_da_insignia)
            self.suite.run("diario/brock", self._diario_brock)
            self.suite.run("diario/so_a_primeira", self._diario_so_a_primeira)
            self.suite.run("diario/lendario", self._diario_lendario)
            self.suite.run("diario/mvp_depois_da_troca", self._diario_mvp_depois_da_troca)
            self.suite.run("diario/liga_e_revanche", self._diario_liga_e_revanche)
            self.suite.run("diario/jogo_novo_zera", self._diario_jogo_novo_zera)
            self._flow("aviso: ponto de partida dos grupos de aviso", self._preparar_avisos)
            for nome, fn in (("aviso/aparece_e_entrega", self._aparece_e_entrega),
                             ("aviso/espera_fim_da_batalha", self._espera_fim_da_batalha),
                             ("aviso/fila", self._fila),
                             ("aviso/degrau", self._degrau),
                             ("premio/bolsa_cheia_vai_ao_pc", self._bolsa_cheia),
                             ("premio/tudo_cheio_fica_pendente", self._tudo_cheio),
                             ("aviso/resumo_retro", self._resumo_retro)):
                res = self.suite.run(nome, fn)
                res.images += self.measures.pop("fotos_aviso", [])
                if self._aviso_ativo():      # um grupo que falhou no meio não deixa o aviso para o próximo
                    self._fechar_aviso(f"fecha o aviso que {nome} deixou")
        except Abort:
            pass


def run_full_conquistas(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    ConquistasScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only conquistas ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "conquistas", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
