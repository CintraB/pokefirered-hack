"""Modo completo: Pokémon seguidor (POK-48), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`), com o aviso das conquistas em
silêncio. A preparação (`_start`, savestate `seguidor_base`) põe um CHARMANDER nv 50 (nunca shiny) no 1º lugar da
equipe, o relógio no dia 0 ao meio-dia (tarde: tom neutro, clima limpo), Repel ligado (nenhum selvagem atrapalha os
passos) e o jogador em Pallet Town (12, 9), virado para o sul.

- `seguidor/aparece`: depois do warp, existe, espécie CHARMANDER, sem shiny, visível, no tile atrás do jogador (12, 8),
  virado para o sul, 1 objeto com o localId do seguidor (foto `seguidor_parado`);
- `seguidor/parado_anima`: lido a cada quadro, o quadro da animação parada alterna 0/1 em trechos de exatamente
  FOLLOWER_IDLE_FRAMES quadros (include/follower.h);
- `seguidor/warp`: Cidade de Viridian, entrar no Centro Pokémon pela porta e sair: 1 objeto do seguidor em cada mapa;
- `seguidor/borda_mapa`: Rota 1 → Pallet Town pela conexão (sem warp), 11 tiles para o sul, e de volta: o seguidor
  atravessa junto, 1 objeto dos dois lados, sempre no tile anterior do jogador;
- `seguidor/save_continuar`: salvar, ver que o save não tem o seguidor, resetar e CONTINUAR: o seguidor é recriado
  da equipe, atrás do jogador, 1 objeto;
- `seguidor/noite`: às 22:00 a paleta do seguidor (slot PALSLOT_FOLLOWER) recebe o tom, como a do jogador (foto
  `seguidor_noite`);
- `seguidor/paleta_especial`: no cais do S.S. Anne, a paleta do navio (slot 10) e a do seguidor (slot 11) são as do
  ROM, ao mesmo tempo (foto `seguidor_paleta_especial`); no porto da Ilha Um (o Seagallop usa o slot 11 para o
  reflexo) o seguidor não aparece;
- `seguidor/cinnabar`: em Cinnabar o Seagallop do mapa só aparece na cena do Bill (FLAG_HIDE_CINNABAR_SEAGALLOP): com
  ele escondido, o seguidor existe atrás do jogador, com a paleta do ROM, 1 objeto (foto `seguidor_cinnabar`);

Andar junto (Task 3; o seguidor e o jogador lidos em gObjectEvents a cada quadro):
- `seguidor/anda`: 10 passos em L na Rota 1 (6 para a esquerda, 4 para baixo): no quadro em que o jogador começa cada
  passo, o seguidor começa o dele para o tile de onde o jogador saiu; nunca a mais de 1 tile; os dois no ritmo do
  andar por input (WALK_FRAMES_PER_TILE de pace.py); a perna alterna: em cada 2 tiles seguidos o sprite do seguidor
  mostra os 2 quadros da animação de andar;
- `seguidor/corre`: o mesmo com B segurado (FLAG_SYS_B_DASH ligada), 6 tiles, no ritmo da corrida (RUN_FRAMES_PER_TILE),
  também com os 2 quadros em cada 2 tiles;
- `seguidor/ledge`: pular a ledge da Rota 22 alinhado: o seguidor pula junto (2 tiles) e cai do outro lado, no tile
  da ledge, logo atrás do jogador; pular vindo de lado (seguidor ao lado): ele pula a ledge da coluna dele e cai ao
  lado do jogador; nos dois casos, depois de mais um passo, está no tile anterior do jogador;
- `seguidor/troca`: virar e andar para o tile do seguidor: o jogador não é bloqueado e os dois trocam de lugar;
- `seguidor/a_no_seguidor`: virado para o seguidor, A não começa script nenhum;
- `seguidor/cena_pewter`: a cena do menino que leva o jogador ao Ginásio de Pewter (gatilho em (42, 22), applymovement
  no jogador e no NPC) termina, o jogador fica onde a cena o deixa e o seguidor continua junto, 1 objeto;
- `seguidor/npc_atravessa`: a menina de Celadon (rota fixa em quadrado) passa pelo tile do seguidor sem parar;
- `seguidor/grama`: o seguidor entra na grama alta da Rota 1 e ganha as folhinhas (sprite do efeito de grama com o
  localId dele, no tile dele) (foto `seguidor_grama`).

Estados (Task 4):
- `seguidor/bicicleta`: com a BICICLETA registrada no SELECT, montar apaga o seguidor (e ele não volta pedalando);
  descer o recria atrás do jogador, 1 objeto, e ele segue o passo seguinte;
- `seguidor/surf`: em Pallet, A diante da água (SURF com a 5ª insígnia): na água não existe, nem depois de um passo;
  ao sair, existe (no tile do jogador, escondido: atrás é água) e o 1º passo em terra o põe atrás, visível;
- `seguidor/voar`: o voo de verdade (TEST_CMD_START_FLY = o A da tela de voo) até Pewter: na chegada existe, atrás do
  jogador, 1 objeto, e não existia durante a chegada do pássaro;
- `seguidor/corda_fuga`: entrar no Mt. Moon pela Rota 4 (o ponto de fuga) e usar a CORDA DE FUGA pela bolsa: na saída
  existe, atrás do jogador, 1 objeto;
- `seguidor/troca_equipe`: pelo menu da equipe (TROCAR), PIDGEY no 1º lugar: o seguidor vira PIDGEY (POK-53: os 386
  seguem); de volta CHARMANDER: existe, atrás;
- `seguidor/desmaiado_centro`: 1º com PS 0: não existe no Centro de Viridian; a enfermeira cura: no fim da cena
  existe, atrás do jogador, sem abrir menu;
- `seguidor/shiny`: o 1º shiny (TEST_CMD_SET_LEAD_SHINY) e um warp: estado com shiny e a paleta shiny do ROM (foto
  `seguidor_shiny`);
- `seguidor/evolucao`: CHARMANDER nv 15 vence um CHANSEY com 1% de PS, sobe de nível e evolui depois da batalha: na
  volta ao campo o seguidor é CHARMELEON;
- `seguidor/opcao`: no menu de Opções a linha SEGUIDOR (8 linhas, foto `seguidor_opcoes`); Não: ao fechar, o seguidor
  some e o bit do save liga; Sim: volta;
- `seguidor/mapa_cheio`: com todos os objetos ocupados (TEST_CMD_FILL_OBJECT_EVENTS), o refresh não cria o seguidor,
  o jogador anda e nada trava; liberados, ele volta;
- `seguidor/pc_guardar`: no PC do Centro de Viridian, DEPOSITAR o CHARMANDER (1º) deixa o PIDGEY no 1º: ao desligar o
  PC o seguidor é o PIDGEY; RETIRAR o CHARMANDER (vai para o 2º): continua PIDGEY; TROCAR para o 1º: CHARMANDER, atrás,
  1 objeto;
- `seguidor/veneno`: o 1º com 1 PS e envenenado (PIDGEY no 2º) anda na Rota 1 até desmaiar pelo veneno do campo: no
  fim da mensagem não existe seguidor, o campo fica livre e o jogador anda.

As telas `seguidor_*` são novas: ficam para a aprovação do Cintra (Task 5).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only seguidor
"""

import re
import struct
import sys

from ..breeding import header_defines
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_SELECT, KEY_UP
from ..field_menu import STARTMENU_BAG, STARTMENU_OPTION, STARTMENU_POKEMON
from ..game import MON_HP
from ..hooks import CMD_GIVE_ITEM, CMD_SET_VAR, CMD_START_FLY, CMD_START_WILD_BATTLE, CMD_WARP, Mailbox
from ..nav import DIRECTIONS
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .full_pc import (CURSOR_AREA_IN_BOX, CURSOR_AREA_IN_PARTY, DEPOSIT_CHOOSE_BOX, OPTION_DEPOSIT, OPTION_WITHDRAW,
                      STORAGE_DEPOSIT, STORAGE_MAIN, STORAGE_TIMEOUT, PcScenario)
from .pace import RUN_FRAMES_PER_TILE, WALK_FRAMES_PER_TILE

CLOCK = (0, 12 * 60)          # dia 0, 12:00: tarde, tom neutro (sTints[TIME_AFTERNOON] = 256, 256, 256)
NIGHT = 22 * 60
LEAD = ("CHARMANDER", 50)
PALLET = ("MAP_PALLET_TOWN", (12, 9))       # linha 8 livre: o seguidor nasce em (12, 8)
VIRIDIAN_DOOR = ("MAP_VIRIDIAN_CITY", (26, 27))   # logo abaixo da porta do Centro Pokémon (26, 26)
CENTER = "MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F"
ROUTE1_SOUTH = ("MAP_ROUTE1", (12, 35))     # x 12 livre até o fim da Rota 1 e até a linha 7 de Pallet
BORDER_STEPS = 11                           # 4 na Rota 1 + 7 em Pallet (até y 6): seguidor a 12 tiles
SS_ANNE_DOCK = ("MAP_SSANNE_EXTERIOR", (32, 12))   # o navio (30, 16) na tela
SEAGALLOP_HARBOR = ("MAP_ONE_ISLAND_HARBOR", (8, 3))
CINNABAR = ("MAP_CINNABAR_ISLAND", (10, 14))   # o Seagallop do mapa fica escondido (FLAG_HIDE_CINNABAR_SEAGALLOP)
ROUTE1_WALK = ("MAP_ROUTE1", (21, 22))      # linha 22 livre de x 2 a 21; x 15 livre (grama) até y 28
WALK_LEGS = (("left", 6), ("down", 4))      # 10 passos em L
RUN_LEGS = (("left", 6),)
ROUTE22_LEDGE = ("MAP_ROUTE22", (10, 14))   # ledge (MB_JUMP_SOUTH) em toda a linha 15, x 4..38; linhas 13, 14 e 16 livres
ROUTE22_SIDE = ("MAP_ROUTE22", (12, 13))    # para o pulo vindo de lado: andar até (14, 14) e pular em x 14
PEWTER_GUIDE = ("MAP_PEWTER_CITY", (41, 22))   # um passo para a direita = gatilho do meio (42, 22)
PEWTER_GUIDE_END = (15, 18)   # (42, 22) + walk_up, walk_left e walk_to_gym (26 esquerda, 3 para cima)
SCRIPT_FRAMES_PER_TILE = 16   # walk_* por applymovement: MOVE_SPEED_NORMAL, sem o ritmo do Hack 2
CELADON_GIRL = ("MAP_CELADON_CITY", (16, 21))  # a menina sai de (11, 18) e anda o quadrado x 11..15, y 18..22
CELADON_GIRL_LOCAL = 4        # LITTLE_GIRL: object_event 4 em data/maps/CeladonCity/events.inc
CELADON_FOLLOWER = (15, 21)   # 2 passos para a esquerda: jogador em (14, 21), dentro do quadrado
ROUTE1_GRASS = ("MAP_ROUTE1", (12, 33))     # 3 para a esquerda: jogador em (9, 33), seguidor na grama (10, 33)
DIR_SOUTH, DIR_NORTH = 1, 2
MAP_OFFSET = 7
OBJ_FLAGS2, OBJ_COORDS, OBJ_FACING = 2, 0x10, 0x18
SPRITE_SIZE, SPRITE_CALLBACK, SPRITE_DATA, MAX_SPRITES = 0x44, 0x1C, 0x2E, 64   # struct Sprite (include/sprite.h)
SPRITE_ANIM_NUM, OBJ_SPRITE_ID = 0x2A, 4          # Sprite.animNum (+ animCmdIndex em 0x2B); ObjectEvent.spriteId
ANIM_GO_FIRST, ANIM_GO_LAST = 4, 19               # ANIM_STD_GO_SOUTH .. ANIM_STD_GO_FASTEST_EAST (2 quadros: índice 0/1)
ANIM_RUN_FIRST = 20 + 4                           # FOLLOWER_ANIM_RUN_SOUTH = ANIM_STD_COUNT + 4 (include/follower.h)
PALSLOT_FOLLOWER, PALSLOT_NPC_SPECIAL = 11, 10
PLTT_SIZE_4BPP = 32
OBJ_EVENT_SIZE, SB1_OBJECT_EVENTS, OBJECT_EVENTS_COUNT = 0x24, 0x6A0, 16
OBJ_GRAPHICS_ID, OBJ_LOCAL_ID = 5, 8
FOLLOWER_H = REPO_ROOT / "include" / "follower.h"
MOVES = {m.group(1): int(m.group(2)) for m in re.finditer(
    r"^#define (MOVE_\w+)\s+(\d+)\b", (REPO_ROOT / "include/constants/moves.h").read_text(encoding="utf-8"), re.M)}
SCREEN_POINTS = ("seguidor_parado", "seguidor_noite", "seguidor_paleta_especial", "seguidor_cinnabar", "seguidor_grama",
                 "seguidor_shiny", "seguidor_opcoes")
# Task 4
PALLET_WATER = ("MAP_PALLET_TOWN", (8, 16))   # água (MB_POND_WATER) em x 7..10, y 17..19, logo abaixo
SURF_MON = ("LAPRAS", 50)
PLAYER_AVATAR_FLAG_SURFING, PLAYER_AVATAR_FLAG_MACH_BIKE = 1 << 3, 1 << 1   # include/global.fieldmap.h
SB1_REGISTERED_ITEM = 0x296
ROUTE4_CAVE = ("MAP_ROUTE4", (19, 6))          # logo abaixo da entrada do Mt. Moon (warp em (19, 5))
MT_MOON = "MAP_MT_MOON_1F"
VIRIDIAN_NURSE = ("MAP_VIRIDIAN_CITY_POKEMON_CENTER_1F", (7, 4))   # enfermeira em (7, 2), balcão em (7, 3)
PEWTER = "MAP_PEWTER_CITY"
SWAP_MON = ("PIDGEY", 10)
EVO_LEAD = ("CHARMANDER", 15)                  # evolui no 16
EVO_FOE = ("CHANSEY", 20)                      # 255 de EXP base: 255 * 20 / 7 = 728 > 500 que faltam do 15 ao 16
EVOLVED = "CHARMELEON"
MENUITEM_FOLLOWER = 6                          # src/option_menu.c (antes de MENUITEM_CANCEL)
OPTION_CURSOR, OPTION_LOAD_STATE = 0x10, 0x12   # struct OptionMenu: option[8] (u16), cursorPos, loadState
SB2_OPTIONS = 0x14
MON_STATUS, STATUS1_POISON = 0x50, 1 << 3        # Pokemon.status (u32); STATUS1_POISON (include/constants/battle.h)
POISON_MAX_STEPS = 12                          # o veneno do campo tira 1 PS a cada 4 passos (DoPoisonFieldEffect)
OPTIONS_FOLLOWER_OFF_BIT = 12                 # u16 em 0x14: textSpeed:3 frame:5 sound:1 style:1 scene:1 zoom:1 seguidor:1


def _follower_define(name: str) -> int:
    m = re.search(rf"#define {name}\s+(0x[0-9A-Fa-f]+|\d+)", FOLLOWER_H.read_text(encoding="utf-8"))
    assert m, f"{name} não está em include/follower.h"
    return int(m.group(1), 0)


class FollowerScenario(PcScenario):   # PcScenario (CatchSaveScenario + PC): depositar/retirar pela tela das caixas
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.anims: list[tuple[int, int, int]] = []   # (quadro, animNum, animCmdIndex) do seguidor no último _track
        self.vars = header_defines(REPO_ROOT, "vars.h")

    # --- utilidades -------------------------------------------------------------------------------------------------
    def _sb(self, n: int) -> int:
        return self.emu.read_u32(self.game.syms.addr(f"gSaveBlock{n}Ptr"))

    def _teleport(self, where: tuple[str, tuple[int, int]]) -> None:
        map_id, (x, y) = where
        group, num = self.consts.map(map_id)
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_id}")
        self.ctl.wait_overworld_idle(900)
        self.emu.frames(30)

    def _state(self) -> dict:
        state = self.box.follower_state()
        assert state is not None, f"estado do seguidor fora do campo ({self.game.callback2()})"
        return state

    def _expect_one(self, where: str, species: str = LEAD[0]) -> dict:
        state = self._state()
        assert state["existe"] and state["objetos"] == 1, f"{where}: {state}"
        assert state["especie"] == self.consts.species(species), f"{where}: espécie {state['especie']}"
        return state

    def _palette(self, slot: int) -> bytes:
        """Paleta de sprite `slot` em gPlttBufferUnfaded (antes do gamma do clima)."""
        base = self.game.syms.addr("gPlttBufferUnfaded")
        return self.emu.read(base + (16 + slot) * PLTT_SIZE_4BPP, PLTT_SIZE_4BPP)

    def _rom(self, symbol: str) -> bytes:
        return self.emu.read(self.game.syms.addr(symbol), PLTT_SIZE_4BPP)

    def _restore(self) -> None:
        self.ctl.restore("seguidor_base")
        self.emu.frames(12)

    # --- passos -----------------------------------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="seguidor_continue")
        self.box.conq_silencio(True)
        self.box.set_clock(*CLOCK)
        self.box.set_party_mon(0, self.consts.species(LEAD[0]), LEAD[1])
        self.box.call(CMD_SET_VAR, self.vars["VAR_REPEL_STEP_COUNT"], 250)
        self._teleport(PALLET)
        assert self.game.player_xy() == PALLET[1], self.game.player_xy()
        self.ctl.checkpoint("seguidor_base")
        return f"CONTINUAR; {LEAD[0]} nv {LEAD[1]} no 1º lugar, 12:00, Repel; Pallet Town {PALLET[1]}"

    def _aparece(self) -> str:
        self._restore()
        state = self._expect_one("Pallet")
        px, py = self.game.player_xy()
        assert state["xy"] == (px, py - 1), f"seguidor em {state['xy']}, jogador em {(px, py)} virado para o sul"
        assert not state["shiny"] and not state["escondido"], state
        assert state["direcao"] == DIR_SOUTH, state
        self.emu.frames(10)
        self._shot("seguidor_parado")
        return f"seguidor {state} atrás do jogador {(px, py)} (foto seguidor_parado)"

    def _parado_anima(self) -> str:
        self._restore()
        period = _follower_define("FOLLOWER_IDLE_FRAMES")
        frames = [self.box.follower_idle_frame() for _ in range(4 * period + 2)]
        assert set(frames) == {0, 1}, f"quadro parado não alterna: {frames}"
        runs, last, size = [], frames[0], 0
        for f in frames:
            if f == last:
                size += 1
            else:
                runs.append(size)
                last, size = f, 1
        inner = runs[1:]      # o 1º trecho começou antes da leitura
        assert len(inner) >= 2 and all(r == period for r in inner), (
            f"trechos {runs} (cada troca a {period} quadros esperada): {frames}")
        return f"{len(frames)} quadros lidos: troca a cada {period} ({runs})"

    def _warp(self) -> str:
        self._restore()
        self._teleport(VIRIDIAN_DOOR)
        out = self._expect_one("Viridian")
        loc = self.nav.go_through_warp("up")
        assert loc == self.consts.map(CENTER), loc
        self.emu.frames(30)
        inside = self._expect_one("Centro Pokémon")
        loc = self.nav.go_through_warp("down")
        assert loc == self.consts.map(VIRIDIAN_DOOR[0]), loc
        self.emu.frames(30)
        back = self._expect_one("Viridian de volta")
        return f"fora {out['xy']}, dentro {inside['xy']} (escondido {inside['escondido']}), fora de novo {back['xy']}"

    def _borda_mapa(self) -> str:
        self._restore()
        self._teleport(ROUTE1_SOUTH)
        route1, pallet = self.consts.map(ROUTE1_SOUTH[0]), self.consts.map(PALLET[0])
        start = self._expect_one("Rota 1")
        x, y = ROUTE1_SOUTH[1]
        assert start["xy"] == (x, y - 1), start
        moved = self.nav.step("down", BORDER_STEPS)
        assert moved == BORDER_STEPS and self.game.location() == pallet, (moved, self.game.location())
        far = self._expect_one("Pallet")
        px, py = self.game.player_xy()
        assert far["xy"] == (px, py - 1) and not far["escondido"], (far, (px, py))
        moved = self.nav.step("up", BORDER_STEPS)
        assert moved == BORDER_STEPS and self.game.location() == route1, (moved, self.game.location())
        back = self._expect_one("Rota 1 de volta")
        assert back["xy"] == (x, y + 1), back   # o 1º passo para cima trocou de lugar com o seguidor
        return f"Rota 1 {start['xy']} → Pallet {far['xy']} → Rota 1 {back['xy']}: atrás do jogador, 1 objeto sempre"

    def _saved_followers(self) -> list[int]:
        base = self._sb(1) + SB1_OBJECT_EVENTS
        raw = self.emu.read(base, OBJ_EVENT_SIZE * OBJECT_EVENTS_COUNT)
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        return [i for i in range(OBJECT_EVENTS_COUNT)
                if raw[i * OBJ_EVENT_SIZE] & 1 and raw[i * OBJ_EVENT_SIZE + OBJ_LOCAL_ID] == local]

    def _save_continuar(self) -> str:
        self._restore()
        before = self._expect_one("antes de salvar")
        status = self.menu.save_game()
        assert status == 1, f"gSaveAttemptStatus = {status}"
        saved = self._saved_followers()
        assert not saved, f"o seguidor foi para o save (slots {saved})"
        self.emu.flush_save()
        self.emu.reset()
        self._title_to_continue("tela de título depois do reset", shot="seguidor_save_continue")
        self.box.conq_silencio(True)
        self.emu.frames(30)
        after = self._expect_one("depois de CONTINUAR")
        px, py = self.game.player_xy()
        assert after["xy"] == (px, py - 1) and after["xy"] == before["xy"], (before, after, (px, py))
        return f"save sem o seguidor; CONTINUAR: {after}"

    def _noite(self) -> str:
        self._restore()
        rom = self._rom("sFollowerPal_Charmander")
        day, player_day = self._palette(PALSLOT_FOLLOWER), self._palette(0)
        assert day == rom, "ao meio-dia (tom neutro) a paleta do seguidor não é a do ROM"
        self.box.set_clock(0, NIGHT)
        self.ctl.wait_until(lambda: self._palette(PALSLOT_FOLLOWER) != day, 600, "tom da noite no seguidor")
        self.emu.frames(30)
        night = self._palette(PALSLOT_FOLLOWER)
        assert night != rom and self._palette(0) != player_day, "à noite o seguidor ou o jogador ficaram sem tom"
        self._expect_one("à noite")
        self._shot("seguidor_noite")
        return f"22:00: paleta do seguidor com tom ({rom[:4].hex()} → {night[:4].hex()}); foto seguidor_noite"

    def _paleta_especial(self) -> str:
        self._restore()
        self.box.set_flag(self.consts.flag("FLAG_HIDE_SS_ANNE"), False)
        self._teleport(SS_ANNE_DOCK)
        self._expect_one("cais do S.S. Anne")
        ship, follower = self._palette(PALSLOT_NPC_SPECIAL), self._palette(PALSLOT_FOLLOWER)
        assert ship == self._rom("gObjectEventPal_SSAnne"), "paleta do S.S. Anne (slot 10) errada"
        assert follower == self._rom("sFollowerPal_Charmander"), "paleta do seguidor (slot 11) errada no cais"
        self._shot("seguidor_paleta_especial")
        self._teleport(SEAGALLOP_HARBOR)
        state = self._state()
        assert not state["existe"] and state["objetos"] == 0, f"seguidor no porto do Seagallop: {state}"
        return "S.S. Anne no slot 10 e seguidor no 11 com as cores do ROM; no porto do Seagallop, sem seguidor"

    def _cinnabar(self) -> str:
        self._restore()
        hidden = self.consts.flag("FLAG_HIDE_CINNABAR_SEAGALLOP")
        self.box.set_flag(hidden, True)
        self._teleport(CINNABAR)
        state = self._expect_one("Cinnabar")
        px, py = self.game.player_xy()
        assert state["xy"] == (px, py - 1) and not state["escondido"], (state, (px, py))
        assert self._palette(PALSLOT_FOLLOWER) == self._rom("sFollowerPal_Charmander"), "paleta do seguidor em Cinnabar"
        self._shot("seguidor_cinnabar")
        return f"Cinnabar com o Seagallop escondido por flag: {state}"

    # --- andar junto (Task 3) ---------------------------------------------------------------------------------------
    def _objects(self) -> list[bytes]:
        raw = self.emu.read(self.game.syms.addr("gObjectEvents"), OBJ_EVENT_SIZE * OBJECT_EVENTS_COUNT)
        return [raw[i * OBJ_EVENT_SIZE:(i + 1) * OBJ_EVENT_SIZE] for i in range(OBJECT_EVENTS_COUNT)]

    @staticmethod
    def _xy(obj: bytes) -> tuple[int, int]:
        x, y = struct.unpack_from("<hh", obj, OBJ_COORDS)
        return x - MAP_OFFSET, y - MAP_OFFSET

    def _pair(self) -> tuple[tuple[int, int], tuple[int, int] | None]:
        """(tile do jogador, tile do seguidor ou None), de gObjectEvents (currentCoords muda no início do passo)."""
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        player = follower = None
        for obj in self._objects():
            if not obj[0] & 1:
                continue
            if obj[OBJ_FLAGS2] & 1:
                player = self._xy(obj)
            elif obj[OBJ_LOCAL_ID] == local:
                follower = self._xy(obj)
        assert player is not None, "jogador fora de gObjectEvents"
        return player, follower

    def _follower_anim(self) -> tuple[int, int]:
        """(animNum, animCmdIndex) do sprite do seguidor ((-1, -1) sem seguidor)."""
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        for obj in self._objects():
            if obj[0] & 1 and not obj[OBJ_FLAGS2] & 1 and obj[OBJ_LOCAL_ID] == local:
                base = self.game.syms.addr("gSprites") + obj[OBJ_SPRITE_ID] * SPRITE_SIZE
                anim = self.emu.read(base + SPRITE_ANIM_NUM, 2)
                return anim[0], anim[1]
        return -1, -1

    def _check_legs(self, samples: list[tuple]) -> list[list[int]]:
        """Em cada janela de 2 tiles seguidos (de um passo do jogador ao 2º seguinte), o sprite do seguidor mostra os 2
        quadros da animação de andar (animCmdIndex 0 e 1 de uma GO_*). Devolve a sequência de quadros por passo."""
        moves = [frame for (_, p0, _), (frame, p1, _) in zip(samples, samples[1:]) if p1 != p0]
        per_step = []
        for a, b in zip(moves, moves[1:]):
            per_step.append([idx for f, num, idx in self.anims
                             if a <= f < b and (ANIM_GO_FIRST <= num <= ANIM_GO_LAST
                                                or ANIM_RUN_FIRST <= num < ANIM_RUN_FIRST + 4)])
        for i in range(len(per_step) - 1):
            seen = set(per_step[i]) | set(per_step[i + 1])
            assert {0, 1} <= seen, (f"passos {i + 1}-{i + 2}: o seguidor mostrou só os quadros {sorted(seen)} da "
                                    f"animação de andar ({per_step})")
            # a perna continua de um passo para o outro: cada passo começa no quadro em que o anterior não começou
            assert per_step[i] and per_step[i + 1] and per_step[i][0] != per_step[i + 1][0], (
                f"passos {i + 1}-{i + 2} começam no mesmo quadro da animação de andar ({per_step})")
        return per_step

    def _moving(self) -> bool:
        """Jogador ou seguidor com ação de movimento em curso (heldMovementActive sem heldMovementFinished)."""
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        return any(obj[0] & 1 and (obj[OBJ_FLAGS2] & 1 or obj[OBJ_LOCAL_ID] == local) and obj[0] & 0xC0 == 0x40
                   for obj in self._objects())

    def _facing(self) -> int:
        for obj in self._objects():
            if obj[0] & 1 and obj[OBJ_FLAGS2] & 1:
                return obj[OBJ_FACING] & 0xF
        raise AssertionError("jogador fora de gObjectEvents")

    def _track(self, direction: str, tiles: int, run: bool = False, timeout: int = 300) -> list[tuple]:
        """Segura a direção (com B se `run`) até o jogador mudar de tile `tiles` vezes; lê os dois a cada quadro e
        devolve [(quadro, jogador, seguidor)]. Para no fim do último passo."""
        mask = DIRECTIONS[direction][2] | (KEY_B if run else 0)
        self.ctl.wait_overworld_idle()
        samples = [(0, *self._pair())]
        self.anims = []
        changes, frame = 0, 0
        self.emu.keys(mask)
        try:
            while changes < tiles:
                if frame >= timeout:
                    raise self.ctl.timeout_error(f"{tiles} passos {direction} com o seguidor")
                self.emu.frames(1)
                frame += 1
                assert not self.ctl.script_active() and not self.game.in_battle(), "script/batalha no meio dos passos"
                player, follower = self._pair()
                if player != samples[-1][1]:
                    changes += 1
                samples.append((frame, player, follower))
                self.anims.append((frame, *self._follower_anim()))
        finally:
            self.emu.keys(0)
        self.ctl.wait_until(lambda: self.nav._player_still() and not self._moving(), 90, "fim do passo com o seguidor")
        self.emu.frames(2)
        samples.append((frame + 1, *self._pair()))
        return samples

    @staticmethod
    def _check_follow(samples: list[tuple], pace: int | None) -> list[int]:
        """No quadro em que o jogador muda de tile, o seguidor muda para o tile de onde ele saiu; nunca a mais de 1
        tile; com `pace`, os passos seguidos (o 1º depois da virada não conta) levam `pace` quadros. Devolve os
        intervalos entre os passos."""
        moves: list[int] = []
        for (_, p0, f0), (frame, p1, f1) in zip(samples, samples[1:]):
            assert f1 is not None, f"quadro {frame}: sem seguidor"
            dist = abs(p1[0] - f1[0]) + abs(p1[1] - f1[1])
            assert dist <= 1, f"quadro {frame}: jogador {p1}, seguidor {f1} (distância {dist})"
            if p1 != p0:
                assert f1 == p0, f"quadro {frame}: jogador {p0} → {p1}, seguidor {f0} → {f1} (esperava {p0})"
                moves.append(frame)
            else:
                assert f1 == f0, f"quadro {frame}: seguidor {f0} → {f1} sem passo do jogador"
        gaps = [b - a for a, b in zip(moves, moves[1:])]
        if pace is not None:
            assert gaps and all(g == pace for g in gaps), f"quadros por tile {gaps}, esperava {pace}"
        return gaps

    def _anda(self) -> str:
        self._restore()
        self._teleport(ROUTE1_WALK)
        report = []
        for direction, tiles in WALK_LEGS:
            samples = self._track(direction, tiles)
            gaps = self._check_follow(samples, WALK_FRAMES_PER_TILE)
            legs = self._check_legs(samples)
            player, follower = samples[-1][1:]
            dx, dy, _ = DIRECTIONS[direction]
            assert follower == (player[0] - dx, player[1] - dy), (player, follower)
            report.append(f"{direction} {tiles}: jogador {player}, seguidor {follower}, quadros/tile {gaps}, "
                          f"perna {[''.join(map(str, step)) for step in legs]}")
        self._expect_one("Rota 1 depois do L")
        return "; ".join(report)

    def _corre(self) -> str:
        self._restore()
        self.box.set_flag(self.consts.flag("FLAG_SYS_B_DASH"), True)
        self._teleport(ROUTE1_WALK)
        report = []
        for direction, tiles in RUN_LEGS:
            samples = self._track(direction, tiles, run=True)
            gaps = self._check_follow(samples, RUN_FRAMES_PER_TILE)
            legs = self._check_legs(samples)
            report.append(f"{direction} {tiles} correndo: {samples[-1][1:]}, quadros/tile {gaps}, "
                          f"perna {[''.join(map(str, step)) for step in legs]}")
        self._expect_one("Rota 1 depois da corrida")
        return "; ".join(report)

    def _ledge(self) -> str:
        self._restore()
        self._teleport(ROUTE22_LEDGE)
        x, y = ROUTE22_LEDGE[1]
        start = self._pair()
        assert start == ((x, y), (x, y - 1)), start
        # o pulo de 2 tiles muda currentCoords 2 vezes (início e meio do pulo, UpdateJumpAnim): 2 mudanças de tile
        samples = self._track("down", 2, timeout=120)
        player, follower = samples[-1][1:]
        assert player == (x, y + 2) and follower == (x, y + 1), f"depois do pulo: jogador {player}, seguidor {follower}"
        self._check_follow(samples, None)       # o seguidor pula junto, nos mesmos quadros
        after = self._track("down", 1)
        self._check_follow(after, None)
        aligned = f"alinhado: jogador {player}, seguidor {follower}; +1 passo {after[-1][1:]}"

        # vindo de lado: andou para a direita na linha 14 (o seguidor fica à esquerda) e desce: a ledge continua na
        # coluna do seguidor, que pula a dele e cai ao lado do jogador
        self._restore()
        self._teleport(ROUTE22_SIDE)
        sx, sy = ROUTE22_SIDE[1]
        self._track("down", 1)      # atrás é parede: nasceu no tile do jogador, escondido; o 1º passo só o revela
        state = self._state()
        assert state["xy"] == (sx, sy) and not state["escondido"], state
        self._track("right", 2)
        player, follower = self._pair()
        assert player == (sx + 2, sy + 1) and follower == (sx + 1, sy + 1), (player, follower)
        samples = self._track("down", 2, timeout=120)
        player, follower = samples[-1][1:]
        assert player == (sx + 2, sy + 3), player
        assert follower == (sx + 1, sy + 3), f"de lado: o seguidor devia pular a ledge dele, está em {follower}"
        side = follower
        after = self._track("down", 1)
        player, follower = after[-1][1:]
        assert follower == (player[0], player[1] - 1), f"de lado, +1 passo: jogador {player}, seguidor {follower}"
        self._expect_one("Rota 22")
        return f"{aligned}; de lado: cai em {side}, +1 passo: jogador {player}, seguidor {follower}"

    def _troca(self) -> str:
        self._restore()
        px, py = PALLET[1]
        assert self._pair() == ((px, py), (px, py - 1)), self._pair()
        moved = self.nav.step("up", 1)       # vira e anda para o tile do seguidor
        assert moved == 1, moved
        player, follower = self._pair()
        assert player == (px, py - 1) and follower == (px, py), f"jogador {player}, seguidor {follower}"
        self._expect_one("depois da troca")
        return f"jogador {(px, py)} → {player}, seguidor {(px, py - 1)} → {follower}"

    def _a_no_seguidor(self) -> str:
        self._restore()
        px, py = PALLET[1]
        self.emu.press(KEY_UP, hold=2, release=2)     # toque curto: só vira
        self.ctl.wait_overworld_idle()
        self.emu.frames(10)
        assert self._facing() == DIR_NORTH and self._pair() == ((px, py), (px, py - 1)), (self._facing(), self._pair())
        self.emu.press(KEY_A, hold=2, release=2)
        started = False
        for _ in range(60):
            self.emu.frames(1)
            started = started or self.ctl.script_active() or self.game.text_printer_active()
        assert not started, "A no seguidor começou um script"
        assert self.ctl.overworld_idle(), self.game.callback2()
        self._expect_one("depois do A")
        return "virado para o seguidor, A: nenhum script em 60 quadros"

    def _cena_pewter(self) -> str:
        self._restore()
        self._teleport(PEWTER_GUIDE)
        x, y = PEWTER_GUIDE[1]
        self._expect_one("Pewter")
        moved = self.nav.step("right", 1)
        assert moved == 1 and self.game.player_xy() == (x + 1, y), (moved, self.game.player_xy())
        self.ctl.wait_until(self.ctl.script_active, 60, "gatilho do guia de Pewter")
        # A a cada 16 quadros até o fim do script; a cada quadro, o seguidor a no máximo 1 tile do jogador
        frame, last, moves, worst = 0, self._pair(), [], 0
        while self.ctl.script_active():
            if frame >= 3600:
                raise self.ctl.timeout_error("fim da cena do guia de Pewter")
            self.emu.keys(KEY_A if frame % 16 < 2 else 0)
            self.emu.frames(1)
            frame += 1
            pair = self._pair()
            assert pair[1] is not None, f"quadro {frame} da cena: sem seguidor"
            worst = max(worst, abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]))
            if pair[1] != last[1]:
                moves.append(frame)
            last = pair
        self.emu.keys(0)
        self.ctl.wait_overworld_idle()
        self.emu.frames(30)
        player, follower = self._pair()
        assert player == PEWTER_GUIDE_END, f"a cena deixou o jogador em {player}, esperava {PEWTER_GUIDE_END}"
        assert worst <= 1, f"o seguidor ficou a {worst} tiles do jogador durante a cena"
        gaps = [b - a for a, b in zip(moves, moves[1:])]
        assert gaps and min(gaps) == SCRIPT_FRAMES_PER_TILE, f"ritmo do seguidor na cena: {gaps}"
        state = self._expect_one("fim da cena")
        dist = abs(player[0] - follower[0]) + abs(player[1] - follower[1])
        assert dist == 1 and not state["escondido"], (player, state)
        moved = self.nav.step("down", 1)
        assert moved == 1, "o jogador não anda depois da cena"
        return (f"cena de (42, 22) até {player} em {frame} quadros, seguidor em {follower}; {len(moves)} passos do "
                f"seguidor, a no máximo {worst} tile, {min(gaps)} quadros/tile no ritmo do script")

    def _npc_atravessa(self) -> str:
        self._restore()
        self._teleport(CELADON_GIRL)
        self._track("left", 2)
        player, follower = self._pair()
        assert player == (14, 21) and follower == CELADON_FOLLOWER, (player, follower)
        group, num = self.consts.map(CELADON_GIRL[0])
        girl = None
        for i, obj in enumerate(self._objects()):
            if obj[0] & 1 and obj[OBJ_LOCAL_ID] == CELADON_GIRL_LOCAL and obj[9] == num and obj[10] == group:
                girl = i
        assert girl is not None, "a menina de Celadon não está no mapa"
        path, crossed, still, worst = [], False, 0, 0
        for _ in range(400):
            self.emu.frames(1)
            xy = self._xy(self._objects()[girl])
            crossed = crossed or xy == follower
            still = still + 1 if path and xy == path[-1] else 0
            worst = max(worst, still)
            if not path or xy != path[-1]:
                path.append(xy)
            if crossed and xy == (15, 22):
                break
        assert crossed, f"a menina não passou por {follower}: {path}"
        assert worst <= 16, f"a menina parou {worst} quadros (caminho {path})"
        assert self._pair()[1] == follower, "o seguidor saiu do lugar"
        return f"caminho da menina {path}: passou por {follower}, no máximo {worst} quadros no mesmo tile"

    def _grama(self) -> str:
        self._restore()
        self._teleport(ROUTE1_GRASS)
        self._track("left", 3)
        player, follower = self._pair()
        assert follower == (10, 33), (player, follower)
        self.emu.frames(20)
        callback = self.game.syms.addr("UpdateTallGrassFieldEffect") & ~1
        local = _follower_define("OBJ_EVENT_ID_FOLLOWER")
        base = self.game.syms.addr("gSprites")
        raw = self.emu.read(base, SPRITE_SIZE * MAX_SPRITES)
        found = []
        for i in range(MAX_SPRITES):
            spr = raw[i * SPRITE_SIZE:(i + 1) * SPRITE_SIZE]
            cb, = struct.unpack_from("<I", spr, SPRITE_CALLBACK)
            if cb & ~1 != callback:
                continue
            data = struct.unpack_from("<8h", spr, SPRITE_DATA)
            if (data[3] & 0xFFFF) >> 8 == local:
                found.append((data[1] - MAP_OFFSET, data[2] - MAP_OFFSET))
        assert follower in found, f"sem folhas de grama no seguidor {follower} (efeitos dele: {found})"
        self._shot("seguidor_grama")
        return f"seguidor na grama {follower}, efeito de grama dele em {found} (foto seguidor_grama)"

    # --- estados (Task 4) -------------------------------------------------------------------------------------------
    def _avatar_flags(self) -> int:
        return self.emu.read_u8(self.game.syms.addr("gPlayerAvatar"))

    def _gone(self, where: str) -> dict:
        state = self._state()
        assert not state["existe"] and state["objetos"] == 0, f"{where}: {state}"
        return state

    def _behind(self, where: str, species: str = LEAD[0]) -> dict:
        """1 objeto da espécie `species`, visível, no tile atrás do jogador (oposto ao facing)."""
        state = self._expect_one(where, species)
        px, py = self.game.player_xy()
        dx, dy = {1: (0, -1), 2: (0, 1), 3: (1, 0), 4: (-1, 0)}[self._facing()]
        assert state["xy"] == (px + dx, py + dy) and not state["escondido"], f"{where}: {state}, jogador {(px, py)}"
        return state

    def _idle_after(self, what: str, timeout: int = 6000) -> None:
        """A a cada 16 quadros (sem B: B cancela evolução) até o campo ficar livre."""
        spent = 0
        while not (self.game.callback2() == "CB2_Overworld" and self.ctl.overworld_idle()
                   and not self.game.in_battle()):
            if spent >= timeout:
                raise self.ctl.timeout_error(what)
            self.emu.keys(KEY_A if spent % 16 < 2 else 0)
            self.emu.frames(1)
            spent += 1
        self.emu.keys(0)
        self.emu.frames(30)

    def _bicicleta(self) -> str:
        self._restore()
        bike = self.consts.item("ITEM_BICYCLE")
        self.box.call(CMD_GIVE_ITEM, bike, 1)
        self.emu.write(self._sb(1) + SB1_REGISTERED_ITEM, struct.pack("<H", bike))
        self._behind("a pé")
        self.ctl.press_until(KEY_SELECT, lambda: self._avatar_flags() & PLAYER_AVATAR_FLAG_MACH_BIKE, "montar",
                             tries=5, wait=30)
        self.ctl.wait_overworld_idle()
        self._gone("montado")
        moved = self.nav.step("down", 2)
        assert moved == 2, moved
        self._gone("pedalando")
        self.ctl.press_until(KEY_SELECT, lambda: not self._avatar_flags() & PLAYER_AVATAR_FLAG_MACH_BIKE, "descer",
                             tries=5, wait=30)
        self.ctl.wait_overworld_idle()
        self.emu.frames(10)
        down = self._behind("depois de descer")
        samples = self._track("down", 1)
        self._check_follow(samples, None)
        return f"montado: sem seguidor (também depois de 2 passos); desceu: {down}; +1 passo {samples[-1][1:]}"

    def _surf(self) -> str:
        self._restore()
        self.box.set_flag(self.consts.flag("FLAG_BADGE05_GET"), True)
        self.box.set_party_mon(1, self.consts.species(SURF_MON[0]), SURF_MON[1])
        self.box.set_party_move(1, 0, MOVES["MOVE_SURF"])
        self._teleport(PALLET_WATER)
        x, y = PALLET_WATER[1]
        self._behind("diante da água")
        self._talk(KEY_DOWN, "SURF")
        assert self._avatar_flags() & PLAYER_AVATAR_FLAG_SURFING and self.game.player_xy() == (x, y + 1), (
            self._avatar_flags(), self.game.player_xy())
        self._gone("na água")
        for direction, what in (("down", "na água"), ("up", "na água, de volta"), ("up", "para a terra")):
            # o último desce do Pokémon: o pulo para a terra trava os controles (LockPlayerFieldControls), e o nav o
            # conta como interrupção; vale o tile de chegada
            moved = self.nav.step(direction, 1)
            assert moved == 1 or (what == "para a terra" and self.game.player_xy() == (x, y)), (
                f"{direction} {what}: andou {moved}, em {self.game.player_xy()}, flags {self._avatar_flags():#x}, "
                f"interrompido {self.nav.interrupted}")
            if what == "na água":
                self._gone("surfando")
        self.ctl.wait_until(lambda: not self._avatar_flags() & PLAYER_AVATAR_FLAG_SURFING
                            and self.ctl.overworld_idle(), 300, "sair da água")
        self.emu.frames(10)
        out = self._expect_one("fora da água")
        assert out["xy"] == (x, y) and out["escondido"], f"atrás é água: no tile do jogador, escondido ({out})"
        samples = self._track("up", 1)
        self._check_follow(samples, None)
        after = self._behind("1º passo em terra")
        return f"na água: sem seguidor; saiu em {(x, y)}: {out}; 1º passo: {after}"

    def _voar(self) -> str:
        self._restore()
        heal = {m.group(1): i for i, m in enumerate(re.finditer(r"^\s*(HEAL_LOCATION_\w+),", (
            REPO_ROOT / "include/constants/heal_locations.h").read_text(encoding="utf-8"), re.M))}
        pewter = self.consts.map(PEWTER)
        assert self.box.call(CMD_START_FLY, heal["HEAL_LOCATION_PEWTER_CITY"], 0) == 1, "START_FLY recusado"
        seen, frames = [], 0
        while not (self.game.location() == pewter and self.game.callback2() == "CB2_Overworld"
                   and self.ctl.overworld_idle()):
            if frames >= 3000:
                raise self.ctl.timeout_error("voo até Pewter")
            self.emu.frames(1)
            frames += 1
            if frames % 4 == 0 and self.game.callback2() == "CB2_Overworld":
                pair = self._pair()
                seen.append((self.game.location(), pair[1] is not None))
        arrival = [s for loc, s in seen if loc == pewter]
        departure = [s for loc, s in seen if loc != pewter]
        self.emu.frames(30)
        assert arrival and not any(arrival[:-5]), f"seguidor durante a chegada do pássaro: {arrival}"
        assert departure and not departure[-1], f"seguidor no fim da saída: {departure[-10:]}"
        # pousa virado para o sul, diante do Centro: atrás (norte) é a parede, então ele nasce no tile do jogador,
        # escondido, e o 1º passo o põe atrás (a regra do spawn)
        landed = self._expect_one("Pewter")
        assert landed["xy"] == self.game.player_xy() and landed["escondido"], (landed, self.game.player_xy())
        samples = self._track("down", 1)
        self._check_follow(samples, None)
        state = self._behind("Pewter, 1º passo")
        return (f"voo em {frames} quadros, sem seguidor na saída nem na chegada; pousou em {landed['xy']} (escondido: "
                f"atrás é o Centro); 1º passo: {state}")

    def _corda_fuga(self) -> str:
        self._restore()
        rope = self.consts.item("ITEM_ESCAPE_ROPE")
        self.box.call(CMD_GIVE_ITEM, rope, 1)
        self._teleport(ROUTE4_CAVE)
        loc = self.nav.go_through_warp("up")
        assert loc == self.consts.map(MT_MOON), loc
        self.emu.frames(30)
        inside = self._expect_one("Mt. Moon")
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_BAG)
        self.menu.bag.wait_ready()
        self.menu.bag.select(rope)
        self.menu.bag.use_selected()
        route4 = self.consts.map(ROUTE4_CAVE[0])
        spent, seen = 0, []
        while not (self.game.location() == route4 and self.game.callback2() == "CB2_Overworld"
                   and self.ctl.overworld_idle()):
            if spent >= 3000:
                raise self.ctl.timeout_error("Corda de Fuga até a Rota 4")
            self.emu.keys(KEY_A if spent % 16 < 2 else 0)
            self.emu.frames(1)
            spent += 1
            if spent % 4 == 0 and self.game.callback2() == "CB2_Overworld" and self.game.location() == route4:
                seen.append(self._pair()[1] is not None)
        self.emu.keys(0)
        self.emu.frames(30)
        out = self._behind("saída do Mt. Moon")
        assert seen and not any(seen[:-5]), f"seguidor durante a chegada girando: {seen}"
        return (f"no Mt. Moon {inside['xy']}; Corda de Fuga: Rota 4 {self.game.player_xy()}, {out}; sem seguidor em "
                f"{len(seen) - sum(seen)} leituras da chegada")

    def _party_swap_first(self) -> None:
        """START > POKéMON > 1º > TROCAR > 2º; sai do menu e fecha o START."""
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_POKEMON)
        tasks = self.game.active_tasks
        self.ctl.wait_until(lambda: "Task_HandleChooseMonInput" in tasks(), 600, "tela de Pokémon")
        before = [m.species for m in self.game.party()[:2]]
        cursor = self.game.syms.addr("gPartyMenu") + 9    # gPartyMenu.slotId (include/party_menu.h)
        assert self.emu.read_u8(cursor) == 0, self.emu.read_u8(cursor)
        self.ctl.press_until(KEY_A, lambda: "Task_HandleSelectionMenuInput" in tasks(), "ações do 1º")
        self.emu.frames(10)
        self.emu.press(KEY_DOWN, hold=2, release=8)        # RESUMO → TROCAR
        self.ctl.press_until(KEY_A, lambda: "Task_HandleSelectionMenuInput" not in tasks(), "TROCAR")
        self.ctl.wait_until(lambda: "Task_HandleChooseMonInput" in tasks(), 120, "escolher com quem trocar")
        # escolhendo com quem trocar, o cursor é gPartyMenu.slotId2 (slotId fica no 1º)
        self.ctl.press_until(KEY_DOWN, lambda: self.emu.read_u8(cursor + 1) == 1, "cursor no 2º")
        self.ctl.press_until(KEY_A, lambda: "Task_HandleChooseMonInput" not in tasks(), "trocar")
        self.ctl.wait_until(lambda: "Task_HandleChooseMonInput" in tasks(), 600, "troca feita")
        after = [m.species for m in self.game.party()[:2]]
        assert after == before[::-1], (before, after)
        self.ctl.press_until(KEY_B, self.menu.start_menu_open, "volta ao menu START", tries=5, wait=60)
        self.ctl.wait_until(self.menu.accepting_input, 600, "menu START")
        self.menu.close_start_menu()
        self.emu.frames(10)

    def _troca_equipe(self) -> str:
        self._restore()
        self.box.set_party_mon(1, self.consts.species(SWAP_MON[0]), SWAP_MON[1])
        self._behind("antes")
        self._party_swap_first()
        assert self.game.party()[0].species == self.consts.species(SWAP_MON[0]), self.game.party()[0]
        self._behind("PIDGEY no 1º lugar", SWAP_MON[0])
        self._party_swap_first()
        state = self._behind("CHARMANDER de volta")
        return f"PIDGEY no 1º: seguidor PIDGEY; CHARMANDER de volta: {state}"

    def _desmaiado_centro(self) -> str:
        self._restore()
        party = self.game.syms.addr("gPlayerParty")
        self.emu.write(party + MON_HP, b"\0\0")
        self._teleport(VIRIDIAN_NURSE)
        assert self.game.party()[0].hp == 0
        self._gone("1º desmaiado no Centro")
        self._talk(KEY_UP, "enfermeira cura o time")
        assert self.game.party()[0].hp == self.game.party()[0].max_hp, self.game.party()[0]
        assert self.game.callback2() == "CB2_Overworld" and not self.menu.start_menu_open()
        state = self._behind("fim da cura")
        return f"PS 0: sem seguidor; depois da cura: {state}"

    def _shiny(self) -> str:
        self._restore()
        species = self.box.set_lead_shiny(True)
        assert species == self.consts.species(LEAD[0]), species
        self._teleport(PALLET)
        state = self._behind("1º shiny")
        assert state["shiny"], state
        assert self._palette(PALSLOT_FOLLOWER) == self._rom("sFollowerPalShiny_Charmander"), "paleta shiny"
        self._shot("seguidor_shiny")
        return f"shiny: {state} com a paleta shiny do ROM (foto seguidor_shiny)"

    def _evolucao(self) -> str:
        self._restore()
        self.box.set_party_mon(0, self.consts.species(EVO_LEAD[0]), EVO_LEAD[1])
        self._teleport(PALLET)
        self._behind("CHARMANDER nv 15")
        assert self.box.call(CMD_START_WILD_BATTLE, self.consts.species(EVO_FOE[0]), EVO_FOE[1]) == 1
        self.driver.wait_battle_start()
        self.driver.wait_action_menu()
        self.box.set_enemy_mon(0, self.consts.species(EVO_FOE[0]), EVO_FOE[1], hp_percent=1)
        outcome = self.driver.fight_to_end()
        assert outcome == "win", outcome
        self._idle_after("subida de nível, evolução e volta ao campo")
        lead = self.game.party()[0]
        assert lead.species == self.consts.species(EVOLVED), lead
        state = self._expect_one("depois da evolução", EVOLVED)
        return f"{EVO_LEAD[0]} → {EVOLVED} nv {lead.level}: seguidor {state}"

    def _option_ptr(self) -> int:
        return self.emu.read_u32(self.game.syms.addr("sOptionMenuPtr"))

    def _options_toggle_follower(self, shot: bool) -> None:
        """START > OPÇÕES > SEGUIDOR > ← (troca Sim/Não) > B; volta ao campo com o START fechado."""
        self.menu.open_start_menu()
        self.menu.choose(STARTMENU_OPTION)
        ready = lambda: (self._option_ptr() != 0 and "Task_OptionMenu" in self.game.active_tasks()
                         and self.emu.read_u8(self._option_ptr() + OPTION_LOAD_STATE) == 2)
        self.ctl.wait_until(ready, 600, "menu de Opções")
        cursor = lambda: self.emu.read_u16(self._option_ptr() + OPTION_CURSOR)
        self.ctl.press_until(KEY_UP, lambda: cursor() == MENUITEM_FOLLOWER, "cursor no SEGUIDOR", tries=4, wait=10)
        value = lambda: self.emu.read_u16(self._option_ptr() + MENUITEM_FOLLOWER * 2)
        old = value()
        self.ctl.press_until(KEY_LEFT, lambda: value() != old, "troca Sim/Não")
        self.emu.frames(10)
        if shot:
            self._shot("seguidor_opcoes")
        self.ctl.press_until(KEY_B, lambda: self._option_ptr() == 0, "fecha as Opções", tries=3, wait=60)
        self.ctl.wait_until(self.menu.accepting_input, 600, "menu START depois das Opções")
        self.menu.close_start_menu()
        self.emu.frames(10)

    def _follower_off_bit(self) -> bool:
        return bool(self.emu.read_u16(self._sb(2) + SB2_OPTIONS) >> OPTIONS_FOLLOWER_OFF_BIT & 1)

    def _opcao(self) -> str:
        self._restore()
        self._behind("Sim")
        assert not self._follower_off_bit()
        self._options_toggle_follower(True)
        assert self._follower_off_bit(), "Não não foi para o save"
        self._gone("Não")
        assert self.nav.step("down", 1) == 1
        self._gone("Não, depois de um passo")
        self._options_toggle_follower(False)
        assert not self._follower_off_bit()
        state = self._behind("Sim de novo")
        return f"Não: some ao fechar (bit {OPTIONS_FOLLOWER_OFF_BIT} do 0x14); Sim: {state} (foto seguidor_opcoes)"

    def _mapa_cheio(self) -> str:
        self._restore()
        self._behind("antes")
        full = self.box.fill_object_events(True)
        assert full == OBJECT_EVENTS_COUNT, full
        assert self.box.set_follower_option(False)        # Não: o refresh apaga o seguidor
        assert self.box.fill_object_events(True) == OBJECT_EVENTS_COUNT   # o slot dele também
        self.box.set_follower_option(True)                # Sim: sem objeto livre, não nasce
        self._gone("mapa cheio")
        assert self.nav.step("up", 1) == 1, "o jogador não anda com o mapa cheio"
        self.emu.frames(30)
        assert self.ctl.overworld_idle(), self.game.callback2()
        self._gone("mapa cheio, depois de um passo")
        left = self.box.fill_object_events(False)
        self.box.set_follower_option(True)
        state = self._behind("objetos liberados")
        return f"{OBJECT_EVENTS_COUNT} objetos: sem seguidor, o jogador anda; liberados ({left} ativos): {state}"

    def _pc_guardar(self) -> str:
        self._restore()
        self.box.set_party_mon(1, self.consts.species(SWAP_MON[0]), SWAP_MON[1])
        self._teleport(VIRIDIAN_NURSE)
        self._expect_one("Centro de Viridian")   # diante da enfermeira: atrás é o balcão, nasce escondido
        lead = self.game.party()[0]
        self._open_storage(OPTION_DEPOSIT)
        self._move_cursor(CURSOR_AREA_IN_PARTY, 0)
        self._select_first_option()
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_DEPOSIT, DEPOSIT_CHOOSE_BOX), STORAGE_TIMEOUT,
                            "pergunta Depositar em qual caixa?")
        self._press(KEY_A)
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), STORAGE_TIMEOUT, "fim do depósito")
        self._close_storage()
        party = [m.species for m in self.game.party()]
        assert party == [self.consts.species(SWAP_MON[0])], party
        self._expect_one("CHARMANDER guardado no PC, PIDGEY no 1º", SWAP_MON[0])
        slot = next(i for i, m in enumerate(self._box()) if m is not None and self._ident(m) == self._ident(lead))
        self._open_storage(OPTION_WITHDRAW)
        self._move_cursor(CURSOR_AREA_IN_BOX, slot)
        self._select_first_option()
        self.ctl.wait_until(lambda: self._storage_at(STORAGE_MAIN, 0), STORAGE_TIMEOUT, "fim da retirada")
        self._close_storage()
        party = [m.species for m in self.game.party()]
        assert party == [self.consts.species(SWAP_MON[0]), lead.species], party
        self._expect_one("CHARMANDER retirado, no 2º lugar", SWAP_MON[0])
        self._party_swap_first()
        state = self._behind("CHARMANDER de volta ao 1º")
        return f"guardado (só PIDGEY): seguidor PIDGEY; retirado (2º): continua PIDGEY; trocado para o 1º: {state}"

    def _veneno(self) -> str:
        self._restore()
        self.box.set_party_mon(1, self.consts.species(SWAP_MON[0]), SWAP_MON[1])
        self._teleport(ROUTE1_WALK)
        self._expect_one("Rota 1")
        party = self.game.syms.addr("gPlayerParty")
        self.emu.write(party + MON_STATUS, struct.pack("<I", STATUS1_POISON))
        self.emu.write(party + MON_HP, struct.pack("<H", 1))
        steps = 0
        while self.game.party()[0].hp > 0:
            assert steps < POISON_MAX_STEPS, f"{steps} passos envenenado e o 1º não desmaiou"
            self.nav.step("left", 1)
            steps += 1
            if self.nav.interrupted:
                break
        self._finish_script("1º desmaia pelo veneno", 3000)
        assert self.game.party()[0].hp == 0, self.game.party()[0]
        assert self.ctl.overworld_idle(), self.game.callback2()
        self._gone("1º desmaiado pelo veneno")
        assert self.nav.step("left", 1) == 1, "o jogador não anda depois do desmaio"
        self._gone("depois de mais um passo")
        return f"{steps} passos envenenado: o 1º desmaiou, sem seguidor, o jogador anda"

    def run(self) -> None:
        try:
            self._flow("seguidor: CONTINUAR, CHARMANDER no 1º lugar, 12:00 e Pallet Town", self._start)
            self.suite.run("seguidor/aparece: atrás do jogador, espécie certa, 1 objeto", self._aparece)
            self.suite.run("seguidor/parado_anima: alterna os 2 quadros parado", self._parado_anima)
            self.suite.run("seguidor/warp: entra e sai do Centro Pokémon, 1 objeto", self._warp)
            self.suite.run("seguidor/borda_mapa: Rota 1 ↔ Pallet sem sumir nem duplicar", self._borda_mapa)
            self.suite.run("seguidor/save_continuar: fora do save, recriado ao CONTINUAR", self._save_continuar)
            self.suite.run("seguidor/noite: paleta do seguidor com o tom da noite", self._noite)
            self.suite.run("seguidor/paleta_especial: S.S. Anne e seguidor com as cores certas",
                           self._paleta_especial)
            self.suite.run("seguidor/cinnabar: aparece com o Seagallop do mapa escondido", self._cinnabar)
            self.suite.run("seguidor/anda: 10 passos em L, sempre no tile anterior do jogador", self._anda)
            self.suite.run("seguidor/corre: correndo, no mesmo quadro e ritmo do jogador", self._corre)
            self.suite.run("seguidor/ledge: pula a ledge da Rota 22 junto", self._ledge)
            self.suite.run("seguidor/troca: voltar para o tile do seguidor troca os dois", self._troca)
            self.suite.run("seguidor/a_no_seguidor: A no seguidor não faz nada", self._a_no_seguidor)
            self.suite.run("seguidor/cena_pewter: cena com applymovement no jogador termina", self._cena_pewter)
            self.suite.run("seguidor/npc_atravessa: NPC de rota fixa passa pelo seguidor", self._npc_atravessa)
            self.suite.run("seguidor/grama: folhas da grama alta no seguidor", self._grama)
            self.suite.run("seguidor/bicicleta: some ao montar, volta atrás ao descer", self._bicicleta)
            self.suite.run("seguidor/surf: some na água, volta ao sair", self._surf)
            self.suite.run("seguidor/voar: Voar para Pewter, 1 objeto no destino", self._voar)
            self.suite.run("seguidor/corda_fuga: Corda de Fuga no Mt. Moon, 1 objeto na saída", self._corda_fuga)
            self.suite.run("seguidor/troca_equipe: PIDGEY no 1º vira o seguidor, CHARMANDER volta", self._troca_equipe)
            self.suite.run("seguidor/desmaiado_centro: 1º desmaiado, volta ao fim da cura", self._desmaiado_centro)
            self.suite.run("seguidor/shiny: paleta shiny com o 1º shiny", self._shiny)
            self.suite.run("seguidor/evolucao: evoluiu na batalha, volta com o sprite novo", self._evolucao)
            self.suite.run("seguidor/opcao: SEGUIDOR Não some, Sim volta", self._opcao)
            self.suite.run("seguidor/mapa_cheio: sem objeto livre, não aparece e nada trava", self._mapa_cheio)
            self.suite.run("seguidor/pc_guardar: 1º guardado no PC some; retirado e de volta ao 1º, volta",
                           self._pc_guardar)
            self.suite.run("seguidor/veneno: 1º desmaiado pelo veneno no campo some, nada trava", self._veneno)
        except Abort:
            pass


def run_full_seguidor(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FollowerScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only seguidor ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "seguidor", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
