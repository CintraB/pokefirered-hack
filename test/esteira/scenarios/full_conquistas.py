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
- `tela/*` (Task 7): a tela de conquistas aberta pelo special (`open_conquistas`) com 3 insígnias e `rival_todas`
  perdida: aba 0, R → 1, L L → 4 (dá a volta); a ajuda (`gHelpSystemEnabled`) desligada com a tela aberta e ligada
  de novo na saída; o rodapé "História: 3 de 12"; e o cartão de treinador pelo menu Start: SELECT abre a tela, B
  volta ao cartão, B volta ao campo. Fotos conquistas_historia, conquistas_batalha e cartao_dica (SHARED_POINTS:
  sem referência até o OK do Cintra) e cartao_conquistas/cartao_volta. `cartao_dica` é só o recorte da faixa da dica
  (o relógio do cartão e os dois-pontos piscando mudam a imagem a cada execução; o cartão inteiro, para os olhos, sai
  em cartao_com_dica); `tela/ajuda_anterior`: a ajuda desligada antes de abrir continua desligada na saída.
- `diario_tela/*` (Task 8): o modo diário da mesma tela. `lista_em_ordem`: Brock (VENCEU) e Articuno (DERROTOU) de
  verdade (roteiro da Task 5), a tela abre com o cursor 0 = Brock e ▼ = Articuno; `vazio`: "Nenhuma batalha marcante
  ainda."; `select_alterna`: SELECT troca conquistas <-> diário (cada modo guarda a sua posição) e B volta ao campo;
  `varias_entradas`: 10 entradas escritas na RAM com a ordem diferente da dos eventos (VENCEU, CAPTURADO, DERROTOU; com
  e sem MVP; times de 6), andadas uma a uma pela ordem. Fotos diario_* (SHARED_POINTS: sem referência até o OK do
  Cintra) e conquistas_depois_do_diario.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only conquistas
Numa janela, em tempo real: `make test-watch CENARIO=conquistas`.
"""

import re
import struct
import sys

from PIL import Image

from .. import conquistas as cq
from ..battle import (ACTION_FIGHT, B_OUTCOME_CAUGHT, MOVE_FUNC_SUFFIX, NICKNAME_COMMAND, PARTY_CHOOSE_TASK,
                      PARTY_MENU_SLOT_ID, PARTY_SELECTION_TASK)
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_L, KEY_R, KEY_RIGHT, KEY_SELECT, KEY_START, KEY_UP
from ..field_menu import MENU_TIMEOUT, STARTMENU_BAG, STARTMENU_PLAYER, FieldMenu
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
TELA_TIMEOUT = 300       # a tela de conquistas monta e clareia (fade) em menos que isso
TELA_ASSENTA = 8         # quadros depois da entrada pronta, antes da foto
TELA_CB2 = "CB2_ConquistasTela"
CARTAO_CB2 = "CB2_TrainerCard"
CARTAO_DICA_RECORTE = (140, 118, 228, 130)   # (esquerda, topo, direita, base) da faixa "SELECT Conquistas" do cartão
CARTAO_ASSENTA = 90      # o cartão clareia e toca o som de abrir antes de ler os botões (STATE_HANDLE_INPUT_FRONT)
# Task 6: o aviso
AVISO_ATIVO = "gConquistasAvisoAtivo"   # u8: 1 enquanto o aviso está na tela (src/conquistas_aviso.c)
AVISO_TIMEOUT = 300      # a checagem de estado roda a cada 32 quadros; o aviso aparece logo depois
AVISO_ENTRADA = 24       # quadros da entrada animada (a foto sai com a janela parada)
BGM_PLAYER = "gMPlayInfo_BGM"   # struct MusicPlayerInfo: status (u32) em +4 (include/gba/m4a_internal.h)
MPLAY_TRACK, MPLAY_PAUSE = 0x0000FFFF, 0x80000000   # MUSICPLAYER_STATUS_TRACK / _PAUSE
CONQ_VITORIAS = 0x08     # u16 vitoriasTreinador em struct ConquistasSave
SB1_PC_ITEMS, PC_ITEMS_COUNT = 0x298, 30          # struct ItemSlot pcItems[30] (quantidade sem chave)
SB1_BALLS, BALLS_COUNT = 0x430, 13                # bagPocket_PokeBalls (quantidade XOR chave)
PALLET_LIVRE = (15, 9)   # Pallet: linha 9 livre de x=2 a x=21 (quick_route1.PACE_START)
VIRIDIAN_LIVRE = (26, 27)  # Viridian, diante do Centro


TAG_AVISO_ICONE = 0x5C41   # tag dos tiles e da paleta do ícone do prêmio (src/conquistas_aviso.c)
SB1_GAME_STATS = 0x1200    # u32 gameStats[] (XOR encryptionKey)
T_TILE_TRANSITION = 1      # PlayerAvatar.tileTransitionState (include/global.fieldmap.h)


def paleta_do_item(item_const: str) -> list[int]:
    """As 16 cores (RGB5) do ícone do item, do .pal que o sItemIconTable usa (src/data/item_icon_table.h →
    src/data/graphics/items.h)."""
    tabela = (REPO_ROOT / "src/data/item_icon_table.h").read_text(encoding="utf-8")
    simbolo = re.search(rf"\[{item_const}\]\s*=\s*\{{\w+,\s*(\w+)\}}", tabela).group(1)
    itens = (REPO_ROOT / "src/data/graphics/items.h").read_text(encoding="utf-8")
    caminho = re.search(rf"{simbolo}\[\]\s*=\s*INCBIN_U32\(\"([^\"]+)\.gbapal\.lz\"\)", itens).group(1)
    rgb = [int(v) for v in (REPO_ROOT / f"{caminho}.pal").read_text(encoding="utf-8").split()[3:]]
    return [(rgb[i] >> 3) | (rgb[i + 1] >> 3) << 5 | (rgb[i + 2] >> 3) << 10 for i in range(0, 48, 3)]


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

    def _paleta_do_icone(self) -> list[int] | None:
        """As 16 cores da paleta de sprite com a tag do ícone do aviso (gPlttBufferUnfaded); None sem o ícone."""
        tags = struct.unpack("<16H", self.emu.read(self.game.syms.addr("sSpritePaletteTags"), 32))
        if TAG_AVISO_ICONE not in tags:
            return None
        base = self.game.syms.addr("gPlttBufferUnfaded") + 0x200 + tags.index(TAG_AVISO_ICONE) * 32
        return list(struct.unpack("<16H", self.emu.read(base, 32)))

    def _icone_e(self, item_const: str) -> None:
        """O ícone do aviso na tela é o do item (a paleta dele: um ícone velho preso na tag apareceria aqui)."""
        self.emu.frames(AVISO_ENTRADA)
        lida, esperada = self._paleta_do_icone(), paleta_do_item(item_const)
        assert lida is not None, "aviso sem o ícone do prêmio"
        assert lida[1:] == esperada[1:], f"ícone não é o de {item_const}: {lida} ≠ {esperada}"

    def _passos(self) -> int:
        raw = self.emu.read_u32(self._sb(1) + SB1_GAME_STATS + 4 * 5)   # GAME_STAT_STEPS
        return raw ^ self.emu.read_u32(self._sb(2) + 0xF20)              # encryptionKey

    def _fechar_aviso(self, what: str, assentar: bool = True) -> None:
        """Fecha com A e espera o campo livre (o script segura o campo até a fanfarra acabar: waitfanfare).
        `assentar=False` com outro aviso na fila: o próximo abre no quadro seguinte ao release, e o campo livre ficaria
        visível ou não pela paridade do quadro; espera o campo livre ou o próximo aviso, o que vier antes."""
        self.ctl.press_until(KEY_A, lambda: not self._aviso_ativo(), what, tries=15, wait=20)
        if assentar:
            self.ctl.wait_overworld_idle(300)
        else:
            self.ctl.wait_until(lambda: self.ctl.overworld_idle() or self._aviso_ativo(), 300,
                                f"{what}: campo livre ou o próximo aviso")

    def _ir(self, mapa: str, xy: tuple[int, int], assentar: bool = True) -> None:
        """Warp pelo atalho. `assentar=False` volta assim que o mapa muda: com um aviso pendente, esperar o campo livre
        deixaria o aviso aparecer e fechar sozinho (180 quadros) antes de `_esperar_aviso` olhar."""
        group, num = self.consts.map(mapa)
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {mapa}")
        if assentar:
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

    def _bgm_status(self) -> int:
        return self.emu.read_u32(self.game.syms.addr(BGM_PLAYER) + 4)

    def _bgm_tocando(self) -> bool:
        status = self._bgm_status()
        return bool(status & MPLAY_TRACK) and not status & MPLAY_PAUSE

    def _fanfarra_devolve_bgm(self) -> str:
        """O aviso fecha com a fanfarra ainda tocando. O script segura o campo (waitfanfare) até a música do mapa
        voltar: o jogador que abre a bolsa logo depois (o ResetTasks mataria o Task_Fanfare) não deixa o mapa mudo."""
        self._flag("FLAG_BADGE01_GET", False)
        self._sem_pendentes()
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        assert self._bgm_tocando(), f"música do mapa antes do aviso: status {self._bgm_status():#x}"
        self._flag("FLAG_BADGE01_GET")
        texto = self._esperar_aviso("aviso antes da bolsa")
        assert not self._bgm_tocando(), "a fanfarra pausa a música do mapa"
        self.ctl.press_until(KEY_A, lambda: not self._aviso_ativo(), "fecha o aviso logo", tries=15, wait=20)
        fechou = self.emu.frames(0)
        menu = FieldMenu(self.ctl)
        # START a cada 10 quadros desde o fechamento: o menu só abre quando o script solta o campo
        self.ctl.press_until(KEY_START, menu.start_menu_open, "menu START logo depois do aviso", tries=60, wait=10)
        espera, no_menu = self.emu.frames(0) - fechou, self._bgm_status()
        self.ctl.wait_until(menu.accepting_input, MENU_TIMEOUT, "menu START pronto")
        menu.choose(STARTMENU_BAG)
        menu.bag.wait_ready()
        na_bolsa = self._bgm_status()
        self.ctl.press_until(KEY_B, lambda: not menu.bag.ready(), "bolsa fechada")
        self.ctl.wait_until(menu.start_menu_open, MENU_TIMEOUT, "menu START depois da bolsa")
        menu.close_start_menu()
        self.emu.frames(30)
        status = self._bgm_status()
        detalhe = (f"START aceito {espera} quadros depois de fechar o aviso; BGM status no menu {no_menu:#x}, "
                   f"na bolsa {na_bolsa:#x}, no campo {status:#x}")
        # as asserções só no fim, de volta ao campo: um grupo que falha não deixa menu nem bolsa abertos
        assert self._bgm_tocando(), f"música do mapa muda depois da bolsa: {detalhe}"
        assert not no_menu & MPLAY_PAUSE, f"o menu abriu com a fanfarra tocando: {detalhe}"
        self.nav.step("left", 1)
        return f"{texto!r}; {detalhe} (tocando)"

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
        for i, item in enumerate(("ITEM_POKE_BALL", "ITEM_SUPER_POTION")):
            textos.append(self._esperar_aviso(f"aviso {i + 1} da fila", foto="conquista_aviso_plural" if i else None))
            self._icone_e(item)    # dois avisos seguidos no mesmo mapa: cada um com o seu ícone
            entregues = [self._estado(c)[1] for c in ("insignia_rocha", "insignia_cascata")]
            assert sum(entregues) == i + 1, f"aviso {i + 1}: entregues {entregues} (um por vez)"
            self._fechar_aviso(f"fecha o aviso {i + 1}", assentar=i == 1)   # o 2º abre logo depois do 1º
        assert "Rocha" in textos[0] and "Cascata" in textos[1], textos
        assert "5 Poké Bolas na bolsa" in textos[0] and "3 Superpoções na bolsa" in textos[1], textos   # plural
        return f"dois avisos seguidos: {textos}"

    def _degrau(self) -> str:
        self._sem_pendentes()
        self.emu.write(self._sb(1) + SB1_CONQUISTAS + CONQ_VITORIAS, (10).to_bytes(2, "little"))
        great = self.consts.item("ITEM_GREAT_BALL")
        antes = self.game.bag_quantity(great)
        texto = self._esperar_aviso("aviso do degrau de treinadores", foto="conquista_aviso_degrau")
        assert "Vencer 10 treinadores" in texto and "3 Grandes Bolas" in texto, texto
        self._icone_e("ITEM_GREAT_BALL")
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
        assert "5 Poké Bolas no PC" in texto, texto
        self._icone_e("ITEM_POKE_BALL")
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
        self._ir("MAP_VIRIDIAN_CITY", VIRIDIAN_LIVRE, assentar=False)   # o aviso sai logo ao chegar
        texto2 = self._esperar_aviso("aviso com entrega depois de trocar de mapa")
        assert "na bolsa" in texto2, texto2
        assert self._estado("insignia_rocha")[:2] == (FEITA, 1), self._estado("insignia_rocha")
        self._fechar_aviso("fecha o aviso entregue")
        return (f"{ocupados} espaços cheios: {texto!r}; 20 passos em Pallet sem aviso; espaço liberado e Viridian: "
                f"{texto2!r}")

    def _fila_nao_trava(self) -> str:
        """Bolso de bolas e PC cheios: a Insígnia Rocha (Poké Bolas) não cabe, a Cascata (Superpoções) cabe. A Cascata
        sai antes, com entrega; depois, uma vez, o "fica para depois" da Rocha (e nada mais neste mapa)."""
        poke = self.consts.item("ITEM_POKE_BALL")
        for flag in ("FLAG_BADGE01_GET", "FLAG_BADGE02_GET"):
            self._flag(flag, False)
        self._sem_pendentes()
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self.box.encher_bolso(poke, pc=True)
        for flag in ("FLAG_BADGE01_GET", "FLAG_BADGE02_GET"):
            self._flag(flag)
        primeiro = self._esperar_aviso("1º aviso: o que cabe")
        assert "Cascata" in primeiro and "na bolsa" in primeiro, primeiro
        self._fechar_aviso("fecha a Cascata", assentar=False)   # o "fica para depois" abre logo em seguida
        segundo = self._esperar_aviso("2º aviso: o que não cabe")
        assert "Rocha" in segundo and "fica para depois" in segundo, segundo
        self._fechar_aviso("fecha o fica para depois")
        self.emu.frames(AVISO_TIMEOUT)
        assert not self._aviso_ativo(), "o fica para depois voltou no mesmo mapa"
        assert self._estado("insignia_cascata")[1] == 1 and self._estado("insignia_rocha")[1] == 0
        return f"{primeiro!r} → {segundo!r}"

    def _passo_antes(self) -> str:
        """O aviso fica pendente no meio de um passo: no quadro em que o passo termina (tookStep) o passo é processado
        (GAME_STAT_STEPS +1, gatilho de chão, encontro...) e o aviso sai no quadro seguinte."""
        self._flag("FLAG_BADGE03_GET", False)
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self._sem_pendentes()
        self.box.conq_silencio(True)
        self._flag("FLAG_BADGE03_GET")
        assert self.box.conq_checar() >= 1, "Trovão não ficou pendente"
        antes, xy = self._passos(), self.game.player_xy()
        avatar = self.game.syms.addr("gPlayerAvatar")
        self.emu.keys(KEY_RIGHT)
        self.ctl.wait_until(lambda: self.emu.read_u8(avatar + 3) == T_TILE_TRANSITION, 30, "começo do passo")
        self.box.conq_silencio(False)   # no meio do passo: o aviso só pode sair quando o passo terminar
        self.ctl.wait_until(lambda: self.game.player_xy() != xy, 30, "fim do passo")
        self.emu.keys(0)
        texto = self._esperar_aviso("aviso depois do passo")
        assert "Trovão" in texto, texto
        depois = self._passos()
        assert depois == antes + 1, f"GAME_STAT_STEPS {antes} → {depois}: o passo não foi processado"
        self._fechar_aviso("fecha a Trovão")
        return f"passo de {xy} a {self.game.player_xy()}: GAME_STAT_STEPS {antes} → {depois}; depois {texto!r}"

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

    # --- Task 7: a tela de conquistas e o cartão ----------------------------------------------
    def _tela(self) -> tuple[int, int, int, bool] | None:
        return self.box.conq_tela()

    def _tela_pronta(self, what: str) -> tuple[int, int, int, bool]:
        self.ctl.wait_until(lambda: (s := self._tela()) is not None and s[3], TELA_TIMEOUT, what)
        self.emu.frames(TELA_ASSENTA)
        return self._tela()

    def _foto_tela(self, nome: str) -> str:
        self.emu.frames(TELA_ASSENTA)   # as cópias das janelas para a VRAM saem em alguns VBlanks
        foto = self._shot(nome)
        self.measures.setdefault("fotos_tela", []).append(foto)
        return foto

    def _foto_recorte(self, nome: str, recorte: tuple[int, int, int, int]) -> str:
        """Foto só de um recorte da tela (a imagem de referência sai do mesmo recorte)."""
        foto = self._shot(nome)
        with Image.open(foto) as img:
            img.crop(recorte).save(foto)
        self.measures.setdefault("fotos_tela", []).append(foto)
        return foto

    def _trocar_aba(self, key: int, aba: int, what: str) -> None:
        self.ctl.press_until(key, lambda: self._tela()[1] == aba, what, tries=3, wait=10)
        assert self.game.callback2() == TELA_CB2, self.game.callback2()

    def _ajuda(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("gHelpSystemEnabled"))

    def _estado_da_tela(self) -> None:
        """O estado do estado/conta_aba: 3 insígnias (História 3 de 12) e `rival_todas` perdida (Batalha riscada)."""
        self.box.conq_silencio(True)
        self.box.conq_reset(True)
        for i, flag in enumerate(BADGES):
            self._flag(flag, i < 3)
        for flag in ("FLAG_SYS_GAME_CLEAR", "FLAG_HIDE_SAFFRON_ROCKETS", "FLAG_SYS_CAN_LINK_WITH_RS"):
            self._flag(flag, False)
        self.box.conq_checar()
        self.box.conq_aplicar(cq.num("rival_todas"), APLICAR_PERDER)

    def _abrir_tela(self) -> tuple[int, int, int, bool]:
        self.box.open_conquistas()
        return self._tela_pronta("tela de conquistas aberta pelo special")

    def _fechar_tela(self) -> None:
        self.ctl.press_until(KEY_B, lambda: self._tela() is None, "B fecha a tela de conquistas", tries=3, wait=60)
        self.ctl.wait_overworld_idle(600)

    def _abre_e_abas(self) -> str:
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self._estado_da_tela()
        estado = self._abrir_tela()
        assert estado == (0, 0, 0, True), estado
        assert self.game.callback2() == TELA_CB2, self.game.callback2()
        self._foto_tela("conquistas_historia")
        self._trocar_aba(KEY_R, 1, "R: aba Batalha")
        self._foto_tela("conquistas_batalha")
        self._trocar_aba(KEY_L, 0, "L: aba História")
        self._trocar_aba(KEY_L, 4, "L de novo: dá a volta para Exploração")
        self._fechar_tela()
        return "aba 0; R → 1; L L → 4 (dá a volta); fotos conquistas_historia e conquistas_batalha"

    def _checa_ao_abrir(self) -> str:
        """A checagem do campo é cadenciada (a cada 32 quadros): a tela roda a sua ao abrir, e uma conquista ganha há
        poucos quadros já aparece feita. Em silêncio a checagem do campo nem roda; a 4ª insígnia só vira feita na tela."""
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self._estado_da_tela()
        self._flag("FLAG_BADGE04_GET")
        self.emu.frames(64)
        antes = self._estado("insignia_arcoiris")
        assert antes[0] == PENDENTE, f"em silêncio a checagem do campo não roda: {antes}"
        self._abrir_tela()
        depois = self._estado("insignia_arcoiris")
        historia = self.box.conq_contador(4 + ABA_HISTORIA)
        self._fechar_tela()
        self._estado_da_tela()     # volta às 3 insígnias dos grupos seguintes (o rodapé conta 3 de 12)
        assert depois[0] == FEITA, f"a tela abriu sem checar: {depois}"
        assert historia == 4 | 12 << 8, f"história = {historia & 0xFF} de {historia >> 8}"
        return f"Insígnia Arco-íris: {antes[0]} (pendente) no campo → {depois[0]} (feita) com a tela aberta; História 4 de 12"

    def _lr_sem_ajuda(self) -> str:
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        assert self._ajuda() == 1, "a ajuda já estava desligada no campo"
        self._abrir_tela()
        assert self._ajuda() == 0, "ajuda ligada com a tela aberta"
        self._trocar_aba(KEY_R, 1, "R")
        self._trocar_aba(KEY_R, 2, "R")
        self._trocar_aba(KEY_L, 1, "L")
        assert self._ajuda() == 0
        self._fechar_tela()
        assert self._ajuda() == 1, "a ajuda não voltou na saída"
        return "gHelpSystemEnabled 1 → 0 com a tela aberta (L/R trocam a aba, o CB2 é o da tela) → 1 na saída"

    def _rodape(self) -> str:
        historia = self.box.conq_contador(4 + ABA_HISTORIA)
        assert historia == 3 | 12 << 8, f"história = {historia & 0xFF} de {historia >> 8}"
        foto = self.shots / "conquistas_historia.png"
        assert foto.is_file(), "sem a foto da aba História (tela/abre_e_abas)"
        return "Conquistas_ContarAba(História) = 3 de 12; o rodapé \"História: 3 de 12\" está na foto conquistas_historia"

    def _cartao(self) -> str:
        menu = FieldMenu(self.ctl)
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        menu.open_start_menu()
        menu.choose(STARTMENU_PLAYER)
        self.ctl.wait_until(lambda: self.game.callback2() == CARTAO_CB2, TELA_TIMEOUT, "cartão de treinador")
        self.emu.frames(CARTAO_ASSENTA)
        self._foto_tela("cartao_com_dica")
        self._foto_recorte("cartao_dica", CARTAO_DICA_RECORTE)
        self.ctl.press_until(KEY_SELECT, lambda: self._tela() is not None, "SELECT abre as conquistas", tries=3,
                             wait=60)
        estado = self._tela_pronta("tela de conquistas pelo cartão")
        assert estado == (0, 0, 0, True), estado
        assert self._ajuda() == 0
        self._foto_tela("cartao_conquistas")
        self.ctl.press_until(KEY_B, lambda: self._tela() is None, "B fecha a tela", tries=3, wait=60)
        self.ctl.wait_until(lambda: self.game.callback2() == CARTAO_CB2, TELA_TIMEOUT, "de volta ao cartão")
        self.emu.frames(CARTAO_ASSENTA)
        self._foto_tela("cartao_volta")
        self.ctl.press_until(KEY_B, menu.start_menu_open, "B no cartão volta ao menu Start", tries=3, wait=90)
        menu.close_start_menu()
        assert self._ajuda() == 1, "a ajuda não voltou"
        return "menu Start → cartão (fotos cartao_com_dica e o recorte cartao_dica) → SELECT → conquistas → B → cartão (cartao_volta) → B → campo"

    def _ajuda_anterior(self) -> str:
        """A ajuda desligada antes de abrir a tela continua desligada na saída (a saída restaura o valor de antes)."""
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        ajuda = self.game.syms.addr("gHelpSystemEnabled")
        self.emu.write(ajuda, b"\x00")
        try:
            self._abrir_tela()
            assert self._ajuda() == 0
            self._fechar_tela()
            assert self._ajuda() == 0, "a saída religou a ajuda que já estava desligada"
        finally:
            self.emu.write(ajuda, b"\x01")
        return "gHelpSystemEnabled 0 antes → 0 com a tela aberta → 0 na saída (e 1 → 0 → 1 em tela/lr_sem_ajuda)"

    # --- Task 8: o diário --------------------------------------------------------------------
    def _diario_escrever(self, entradas: list[tuple[str, dict]]) -> None:
        """Escreve entradas do diário direto na RAM (só na ROM de teste): [(id do evento, entrada)], sobre o diário
        zerado; proximaOrdem = maior ordem + 1."""
        base = self._sb(2) + SB2_DIARIO
        raw = bytearray(self._diario_raw())
        raw[4:4 + 20 * 48] = bytes(20 * 48)
        for eid, e in entradas:
            pos = 4 + cq.evento(eid) * cq.DIARIO_ENTRADA_SIZE
            raw[pos:pos + cq.DIARIO_ENTRADA_SIZE] = cq.pack_entrada(e)
        raw[0] = max(e["ordem"] for _, e in entradas) + 1
        self.emu.write(base, bytes(raw))

    def _abrir_diario(self) -> tuple[int, int, int, bool]:
        self.box.open_conquistas(True)
        return self._tela_pronta("tela do diário aberta pelo special")

    def _mover(self, key: int, cursor: int, what: str) -> None:
        self.ctl.press_until(key, lambda: self._tela()[2] == cursor, what, tries=3, wait=10)
        assert self.game.callback2() == TELA_CB2, self.game.callback2()

    def _diario_selecao(self) -> tuple[int, int, int]:
        """(entradas, DIARIO_EVT_* da linha selecionada, primeira linha visível)."""
        estado = self.box.conq_tela_diario()
        assert estado is not None, "a tela não está no modo diário"
        return estado

    def _diario_lista_em_ordem(self) -> str:
        """Brock vencido e Articuno derrotado de verdade (o roteiro da Task 5): a lista tem o Brock primeiro (cursor
        0), o Articuno depois (▼); Diario_ListarEmOrdem e Diario_GetEntrada rodam aqui, em execução."""
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self.box.conq_silencio(True)
        self.box.conq_reset(True)
        self._flag("FLAG_SYS_GAME_CLEAR", False)
        self._time_de_um("MEWTWO", 100, "MOVE_PSYCHIC")
        self.box.start_trainer_battle(self._trainer_const("TRAINER_LEADER_BROCK"))
        self._lutar("Brock", "win")
        assert self.box.call(CMD_START_WILD_BATTLE, self.consts.species("ARTICUNO"), 50) == 1, "START_WILD_BATTLE"
        self._lutar("Articuno (derrotado)", "win")
        brock, articuno = self._entrada("brock"), self._entrada("articuno")
        assert brock is not None and articuno is not None and brock["ordem"] < articuno["ordem"], (brock, articuno)
        estado = self._abrir_diario()
        assert estado[0] == 1 and estado[2] == 0 and estado[3], estado
        assert self.game.callback2() == TELA_CB2
        assert self._diario_selecao() == (2, cq.evento("brock"), 0), self._diario_selecao()
        self._foto_tela("diario_lista")
        self._mover(KEY_DOWN, 1, "▼: o Articuno")
        assert self._diario_selecao() == (2, cq.evento("articuno"), 0), self._diario_selecao()
        self._foto_tela("diario_detalhe")
        self.emu.press(KEY_DOWN, hold=2, release=2)    # na última linha o cursor não anda
        self.emu.frames(10)
        assert self._tela()[2] == 1, self._tela()
        self._mover(KEY_UP, 0, "▲: o Brock")
        self.emu.press(KEY_UP, hold=2, release=2)      # na primeira linha também não
        self.emu.frames(10)
        assert self._tela()[2] == 0, self._tela()
        self._fechar_tela()
        self.box.party_size(1)
        return (f"Brock (ordem {brock['ordem']}, VENCEU) e Articuno (ordem {articuno['ordem']}, DERROTOU): cursor 0 = "
                "Brock, ▼ = Articuno; as pontas não dão a volta; fotos diario_lista e diario_detalhe")

    def _diario_vazio(self) -> str:
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self.box.conq_silencio(True)
        self.box.conq_reset(True)
        estado = self._abrir_diario()
        assert estado[0] == 1 and estado[2] == 0 and estado[3], estado
        assert self._diario_selecao() == (0, 0xFF, 0), self._diario_selecao()
        self._foto_tela("diario_vazio")
        self.emu.press(KEY_DOWN, hold=2, release=2)
        self.emu.frames(10)
        assert self._tela()[2] == 0 and self._diario_selecao() == (0, 0xFF, 0), self._tela()
        self._fechar_tela()
        return "diário vazio: 0 entradas, cursor 0 parado, mensagem 'Nenhuma batalha marcante ainda.' (diario_vazio)"

    def _diario_select_alterna(self) -> str:
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self.box.conq_silencio(True)
        squirtle = self.consts.species("SQUIRTLE")
        base = {"minutos": 90, "turnos": 7, "mvp": 0, "mvpNocautes": 2, "tamanhoTime": 1, "time": [(squirtle, 12)]}
        self.box.conq_reset(True)
        self._diario_escrever([
            ("brock", {**base, "resultado": cq.DIARIO_VENCEU, "ordem": 1}),
            ("misty", {**base, "resultado": cq.DIARIO_VENCEU, "ordem": 2, "minutos": 150}),
            ("surge", {**base, "resultado": cq.DIARIO_VENCEU, "ordem": 3, "minutos": 210})])
        self.box.open_conquistas(False)
        assert self._tela_pronta("conquistas pelo special") == (0, 0, 0, True)
        self._trocar_aba(KEY_R, 1, "R: aba Batalha")
        ajuda = self._ajuda()
        self.ctl.press_until(KEY_SELECT, lambda: self._tela()[0] == 1, "SELECT: conquistas -> diário", tries=3, wait=10)
        self.emu.frames(TELA_ASSENTA)
        assert self._tela() == (1, 1, 0, True), self._tela()      # a aba fica guardada no modo diário
        assert self._diario_selecao() == (3, cq.evento("brock"), 0)
        self._mover(KEY_DOWN, 1, "▼")
        self._mover(KEY_DOWN, 2, "▼")
        assert self._diario_selecao() == (3, cq.evento("surge"), 0)
        self.ctl.press_until(KEY_SELECT, lambda: self._tela()[0] == 0, "SELECT: diário -> conquistas", tries=3, wait=10)
        self.emu.frames(TELA_ASSENTA)
        assert self._tela() == (0, 1, 0, True), self._tela()      # a aba voltou, o topo também
        assert self.box.conq_tela_diario() is None, "no modo conquistas não há estado do diário"
        self._foto_tela("conquistas_depois_do_diario")
        self.ctl.press_until(KEY_SELECT, lambda: self._tela()[0] == 1, "SELECT: conquistas -> diário", tries=3, wait=10)
        self.emu.frames(TELA_ASSENTA)
        assert self._tela() == (1, 1, 2, True), self._tela()      # o cursor também voltou
        assert self._diario_selecao() == (3, cq.evento("surge"), 0)
        assert self._ajuda() == ajuda == 0, "a ajuda continua desligada com a tela aberta"
        self._fechar_tela()
        assert self._ajuda() == 1, "a ajuda não voltou na saída"
        return "SELECT alterna conquistas <-> diário e guarda a aba (1) e o cursor (2); B no diário volta ao campo"

    def _diario_varias_entradas(self) -> str:
        """10 entradas com a ordem de registro diferente da ordem dos eventos: a lista sai pela `ordem`."""
        self._ir("MAP_PALLET_TOWN", PALLET_LIVRE)
        self.box.conq_silencio(True)
        sp = self.consts.species
        V, C, D = cq.DIARIO_VENCEU, cq.DIARIO_CAPTURADO, cq.DIARIO_DERROTOU

        def entrada(ordem, resultado, minutos, turnos, time, mvp=None):
            time = [(sp(nome), nivel) for nome, nivel in time]
            return {"minutos": minutos, "turnos": turnos, "resultado": resultado, "ordem": ordem,
                    "mvp": 0xFF if mvp is None else mvp[0], "mvpNocautes": 0 if mvp is None else mvp[1],
                    "tamanhoTime": len(time), "time": time}
        entradas = [
            ("rival_lab", entrada(1, V, 23, 5, [("SQUIRTLE", 5)], (0, 2))),
            ("brock", entrada(2, V, 71, 9, [("SQUIRTLE", 12), ("PIDGEY", 10)], (0, 2))),
            ("misty", entrada(3, V, 138, 14, [("WARTORTLE", 21), ("PIDGEOTTO", 19), ("RATTATA", 18)], (0, 2))),
            ("surge", entrada(4, V, 215, 11, [("WARTORTLE", 25), ("PIDGEOTTO", 23), ("RATTATA", 20),
                                              ("PIKACHU", 21)], (1, 1))),
            ("rival_ss_anne", entrada(5, V, 301, 16, [("BLASTOISE", 36), ("PIDGEOT", 31), ("RATICATE", 24),
                                                      ("PIKACHU", 28), ("ABRA", 25)], (2, 3))),
            ("articuno", entrada(6, D, 1844, 21, [("BLASTOISE", 50), ("PIDGEOT", 46), ("ALAKAZAM", 48),
                                                  ("PIKACHU", 40), ("SNORLAX", 52), ("LAPRAS", 50)], (4, 5))),
            ("zapdos", entrada(7, C, 7425, 4, [("BLASTOISE", 58), ("PIDGEOT", 55), ("ALAKAZAM", 57), ("PIKACHU", 51),
                                               ("SNORLAX", 60), ("LAPRAS", 54)])),
            ("campeao", entrada(8, V, 8999, 38, [("KANGASKHAN", 100), ("CHARMELEON", 100), ("CHARMANDER", 100),
                                                 ("WEEPINBELL", 100), ("VICTREEBEL", 100), ("MISDREAVUS", 100)],
                                (3, 12))),
            ("mewtwo", entrada(9, C, 9940, 3, [("MEWTWO", 100)])),
            ("lugia", entrada(10, C, 10200, 255, [("MEWTWO", 100), ("ARTICUNO", 99)])),
        ]
        # a ordem de registro não é a ordem dos eventos: embaralha a escrita e confere a lista pela `ordem`
        self.box.conq_reset(True)
        self._diario_escrever(list(reversed(entradas)))
        esperado = [eid for eid, e in sorted(entradas, key=lambda x: x[1]["ordem"])]
        assert [cq.evento(eid) for eid in esperado] != sorted(cq.evento(eid) for eid in esperado), "ordem trivial"
        estado = self._abrir_diario()
        assert estado[0] == 1 and estado[2] == 0 and estado[3], estado
        assert self._diario_selecao() == (len(entradas), cq.evento(esperado[0]), 0), self._diario_selecao()
        self._foto_tela("diario_varias")
        fotos = {2: "diario_detalhe_mvp", 7: "diario_time6", 6: "diario_detalhe_sem_mvp", 5: "diario_rolado"}
        visto = [self._diario_selecao()[1]]
        for i in range(1, len(entradas)):
            self._mover(KEY_DOWN, i, f"▼ até a linha {i}")
            n, evt, topo = self._diario_selecao()
            assert evt == cq.evento(esperado[i]), (i, evt, esperado[i])
            assert topo == max(0, i - 3), (i, topo)        # a janela rola quando o cursor passa da 4ª linha
            visto.append(evt)
            if i in fotos:
                self._foto_tela(fotos[i])
        assert visto == [cq.evento(eid) for eid in esperado]
        # de volta pelo ▲: o topo só desce quando o cursor sai pelo alto
        topo_esperado = len(entradas) - 4
        for i in range(len(entradas) - 2, -1, -1):
            self._mover(KEY_UP, i, f"▲ até a linha {i}")
            topo_esperado = min(topo_esperado, i)
            n, evt, topo = self._diario_selecao()
            assert evt == cq.evento(esperado[i]) and topo == topo_esperado, (i, evt, topo, topo_esperado)
        self._fechar_tela()
        assert [self._entrada(eid)["ordem"] for eid, _ in entradas] == [e["ordem"] for _, e in entradas]
        return (f"{len(entradas)} entradas pela ordem de registro {esperado}; rola de 4 em 4 linhas; fotos diario_varias, "
                "diario_rolado, diario_detalhe_mvp, diario_detalhe_sem_mvp e diario_time6")

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
                             ("aviso/fanfarra_devolve_bgm", self._fanfarra_devolve_bgm),
                             ("aviso/espera_fim_da_batalha", self._espera_fim_da_batalha),
                             ("aviso/fila", self._fila),
                             ("aviso/degrau", self._degrau),
                             ("premio/bolsa_cheia_vai_ao_pc", self._bolsa_cheia),
                             ("premio/tudo_cheio_fica_pendente", self._tudo_cheio),
                             ("premio/fila_nao_trava", self._fila_nao_trava),
                             ("aviso/passo_antes", self._passo_antes),
                             ("aviso/resumo_retro", self._resumo_retro)):
                res = self.suite.run(nome, fn)
                res.images += self.measures.pop("fotos_aviso", [])
                if self._aviso_ativo():      # um grupo que falhou no meio não deixa o aviso para o próximo
                    self._fechar_aviso(f"fecha o aviso que {nome} deixou")
            for nome, fn in (("tela/abre_e_abas", self._abre_e_abas),
                             ("tela/lr_sem_ajuda", self._lr_sem_ajuda),
                             ("tela/rodape", self._rodape),
                             ("tela/cartao", self._cartao),
                             ("tela/ajuda_anterior", self._ajuda_anterior),
                             ("tela/checa_ao_abrir", self._checa_ao_abrir),
                             ("diario_tela/lista_em_ordem", self._diario_lista_em_ordem),
                             ("diario_tela/vazio", self._diario_vazio),
                             ("diario_tela/select_alterna", self._diario_select_alterna),
                             ("diario_tela/varias_entradas", self._diario_varias_entradas)):
                res = self.suite.run(nome, fn)
                res.images += self.measures.pop("fotos_tela", [])
                if self._tela() is not None:   # um grupo que falhou no meio não deixa a tela aberta para o próximo
                    self._fechar_tela()
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
