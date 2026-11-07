"""Modo completo: a Família Sombra (POK-51), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`). O aviso das conquistas fica em
silêncio (ele pausa o campo). A ocupação vem do atalho FAMILIA_SET; as lutas começam pelos atalhos
START_TRAINER_BATTLE (capanga, sem fala de abertura) e FAMILIA_GEMEOS (o trainerbattle_double de verdade).

Task 3 (capangas como treinadores):

- `familia/capanga_apresentacao`: ocupação 1 ATIVA, batalha contra TRAINER_FAMILIA_CAPANGA_1: o texto de abertura é
  gText_FamiliaCapangaQuerLutar e o sprite do oponente é o Pokémon (callbacks do selvagem), não um humano; nenhum
  sprite está no SpriteCB_TrainerSlideIn. Tela `familia_capanga_batalha` (só gravada; a comparação entra com o
  registro dos pontos de tela, Ruling R6);
- `familia/bola_capanga`: 5 Poké Bolas a mais na bolsa; uma jogada: o texto do desvio, a bolsa com as mesmas Poké
  Bolas e a batalha segue (de volta ao menu de ação, o capanga em campo);
- `familia/vitoria_sem_premio`: vencendo o capanga 1 (Shadow Ball): "Você derrotou Capanga da Família!", sem o
  prêmio em dinheiro (o dinheiro não muda) e com a flag do treinador ligada;
- `familia/thief`: Mewtwo com Ladrão (sem item) e com Truque (segurando Restos) contra o capanga 1: depois do turno o
  Mewtwo continua sem item / com os Restos (na batalha e no time) e o capanga com o Talismã Fantasma;
- `familia/time_por_ocupacao`: BUILD_TRAINER_PARTY na ocupação 1 e na 2: espécie, nível, item e golpes do capanga 1
  batem com src/data/familia_sombra_times.h; gêmeos (2, dupla) e as 2 lutas do pedágio (plantel, níveis 56/58 + 6);
- `familia/gemeos_dupla`: 2 Pokémon no time, FAMILIA_GEMEOS: 2 Machamp nv 60 em campo (batalhadores 1 e 3), a fala
  gText_FamiliaGemeosQueremLutar, sem sprite de treinador e a música MUS_VS_GYM_LEADER. Tela `familia_gemeos_batalha`.

Task 4 (andares 4-5, efeito de filme e o chefe). Os andares 4-5 só existem na Task 5 (Ruling R4): o encontro começa pelo
atalho FAMILIA_WILD, que monta o mesmo Pokémon do encontro do andar e liga BATTLE_TYPE_FAMILIA.

- `familia/encontro_wild`: espécie do plantel da ocupação 1, nível 54-58, item e golpes do plantel, o texto do
  capanga, sprite do selvagem, a música de treinador e a paleta do oponente = noir() da prévia aplicado à paleta
  normal da espécie (gPlttBufferUnfaded, índice 0 intocado). Tela `familia_filme_batalha`;
- `familia/passos_andar_escuro`: o atalho FAMILIA_PASSOS roda o TryStandardWildEncounter de verdade com o andar escuro
  forçado (o mapa sem tabela própria): com chefe ativo sai um capanga do plantel; sem chefe, 400 passos sem encontro;
- `familia/bola_selvagem`: a bola desviada e não gasta, como no capanga;
- `familia/thief_selvagem`: Ladrão e Truque não tiram o item do encontro;
- `familia/chefe`: o special FamiliaSombra_IniciarChefe: abertura "GENGAR, O DOM, quer acertar as contas!", Gengar
  shiny nv 62 com os golpes e o item da tabela,
  batalha lendária com BATTLE_TYPE_FAMILIA_CHEFE (sem BATTLE_TYPE_FAMILIA), gTrainerBattleOpponent_A = 0,
  MUS_VS_LEGEND e as cores shiny sem filme. Tela `familia_chefe_batalha`;
- `familia/bola_chefe`: a Master Ball é gasta e captura o chefe;
- `familia/chefe_ia`: Golem nv 100 (imune a Raio) só com Endurecer contra o chefe por 3 turnos: a IA usa as 5 flags
  de chefe (aiLogicId 9) e nunca escolhe Raio, nem Comedor de Sonhos com o Golem acordado, nem Hipnose com ele
  dormindo (ao acaso, passar nos 3 turnos tem 1/8 de chance).

Task 5 (o prédio da Rota 23: 6 andares e a sala do Dom). As insígnias vêm do atalho SET_FLAG (Ruling R7); o atalho
WARP só chega a y < 128, então a frente da porta (4, 150) se alcança saindo pelo tapete do 1º andar.

- `familia/porta_trancada`: sem a 8ª insígnia a porta não abre e a placa fala do charuto (tela
  `familia_porta_trancada`); com ela, entrar na Rota 23 liga a ocupação 1 e a porta leva ao 1º andar (tela
  `familia_rota23_predio`);
- `familia/ciclo`: save antigo com a insígnia = ocupação 1; queda + 6 meios-dias = sem chefe; +7 = ocupação 2 com
  itens e treinadores de volta, uma vez só; a 2ª queda + 7 = continua sem chefe e o andar fica vazio;
- `familia/capanga_ve`: o capanga 2 do 1º andar vê o jogador, vem até ele, luta e some depois da derrota;
- `familia/subida`: da porta ao 6º andar pelas escadas (música, escuro e névoa por andar; o Gengar shiny e os 2
  Machamp na sala); telas `familia_andar_1`, `familia_andar_4` e `familia_sala_do_dom`;
- `familia/encontro_andar4` e `familia/sem_encontro_sem_chefe` (Ruling R4): passos de verdade no 4º andar;
- `familia/gemeos_um_pokemon`: com 1 Pokémon a dupla é recusada e nada começa;
- `familia/chefe_fuga`: gêmeos já vencidos, a cena vai direto ao chefe; fugindo, ele fica e não há rosa;
- `familia/rosa`: a cena inteira (gêmeos, Dom) e a Rosa Vermelha na bolsa (tela `familia_rosa`).

Task 6 (o pedágio da Rota 23, nos dois sentidos). O cobrador é um Persian de chapéu no corredor (x 13-15, y 145-148); o
jogador chega do sul pela porta do prédio e do norte por um WARP a (10, 126) mais uma caminhada; o dinheiro vem da
escrita direta no save (como full_egg) e a Rota 23 sem guardas (VAR_MAP_SCENE_ROUTE23 = 0).

- `familia/pedagio_paga`: o Persian está lá; pagando ¥1.000 o dinheiro cai 1000, a flag liga e o jogador passa; entrar
  no prédio e sair não cobra de novo (tela `familia_pedagio`, a pergunta de pagar);
- `familia/pedagio_sem_dinheiro`: com ¥999 vai direto ao menu "Voltar depois / Passar à força" (sem a pergunta de
  pagar) e voltar empurra um passo para o sul; recusando com dinheiro, a pergunta vem antes do mesmo menu;
- `familia/pedagio_forca`: passar à força = TRAINER_FAMILIA_PEDAGIO_1 e depois _2 (2 espécies diferentes do plantel),
  sem prêmio, e a passagem fica paga;
- `familia/pedagio_volta`: pago, sair pela Victory Road 1F limpa a flag; descendo, cobra no lado norte (voltar
  depois empurra um passo para o norte; pagando, passa);
- `familia/pedagio_sem_chefe`: sem chefe não há cobrador e o corredor fica livre.

Task 7 (conquistas e diário). O estado das conquistas vem de conq_reset(True) (jogo novo) e o aviso fica em silêncio:

- `familia/conquista_dom`: com o jogo já zerado (FLAG_SYS_GAME_CLEAR), a cena do 6º andar até vencer o Dom (gêmeos já
  vencidos): "Vencer o Dom" passa de pendente a feita e as outras 4 seguem pendentes; o diário ganha a entrada
  "O Dom" (Gengar, derrotado, o time e os turnos); telas `familia_conquistas_batalha` (aba Batalha rolada até o fim)
  e `familia_diario_dom` (o diário com a entrada);
- `familia/gengar_fora_nao_conta`: um Gengar selvagem comum (nv 62) vencido não grava a entrada do Dom nem a conquista;
- `familia/pedagio_forca` também confere "Pagar ou lutar": pendente antes das 2 lutas, feita depois.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only familia
"""

import importlib.util
import re

from ..battle import ACTION_FIGHT, MENU_TIMEOUT, MOVE_FUNC_SUFFIX, BattleDriver
from ..breeding import header_defines
from ..game import POKEMON_SIZE, SB1_MONEY, mon_checksum_ok
from .. import conquistas as cq
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_R, KEY_UP
from ..hooks import CMD_GIVE_ITEM, CMD_SET_VAR, CMD_START_WILD_BATTLE, CMD_WARP, Mailbox
from ..nav import Navigator
from . import REPO_ROOT, ScenarioContext
from .base import YESNO_TASK, Abort
from .quick_catch_save import CatchSaveScenario

ESTADO_FECHADO = 0                   # FAMILIA_ESTADO_FECHADO (include/constants/familia_sombra.h)
ESTADO_ATIVA = 1                     # FAMILIA_ESTADO_ATIVA
ESTADO_SEM_CHEFE = 2                 # FAMILIA_ESTADO_SEM_CHEFE
PASSOS = 400                         # passos do caso familia/passos_andar_escuro
SPRITE_SIZE, SPRITE_CALLBACK, SPRITE_DATA, SPRITE_IN_USE = 0x44, 0x1C, 0x2E, 0x3E   # struct Sprite
MAX_SPRITES = 64
# o Pokémon do oponente que aparece direto (OpponentHandleLoadMonSprite → SpriteCB_EnemyMon e seguintes)
WILD_MON_CALLBACKS = {"SpriteCB_EnemyMon", "SpriteCB_MoveWildMonToRight", "SpriteCB_WildMonShowHealthbox",
                      "SpriteCallbackDummy_2"}
TRAINER_SLIDE = "SpriteCB_TrainerSlideIn"
STRING_BYTES = 300                   # gDisplayedStringBattle[300]
# Telas que o cenário grava em OUT/telas/ e que entram na comparação com as referências (esteira/refs.py)
SCREEN_POINTS = ("familia_capanga_batalha", "familia_filme_batalha", "familia_chefe_batalha", "familia_gemeos_batalha",
                 "familia_rosa", "familia_porta_trancada", "familia_rota23_predio", "familia_pedagio",
                 "familia_andar_1", "familia_andar_4", "familia_sala_do_dom",
                 "familia_conquistas_batalha")   # `familia_diario_dom` é gravada mas fica fora: traz o TEMPO de jogo (00:08 x 00:09)
SONG_SIZE = 8                        # struct Song (header, ms, me)
BATTLE_MON_SIZE, BATTLE_MON_ITEM = 0x58, 0x2E   # struct BattlePokemon (include/pokemon.h)
PLAYER_LEVEL = 60
INTRO_TIMEOUT = 3000
EXTRA_BALLS = 5
DODGE_TEXT = "desvia a Poké Bola"
TEAM = (("SPECIES_MEWTWO", PLAYER_LEVEL), ("SPECIES_SNORLAX", PLAYER_LEVEL))
TIMES_H = REPO_ROOT / "src" / "data" / "familia_sombra_times.h"
BATTLE_TYPE_TRAINER, BATTLE_TYPE_LEGENDARY = 1 << 3, 1 << 13
BATTLE_TYPE_FAMILIA, BATTLE_TYPE_FAMILIA_CHEFE = 1 << 20, 1 << 21   # include/constants/battle.h
OBJ_PLTT = 256                       # gPlttBufferUnfaded: as paletas de sprite começam na 256; batalhador n = 256 + 16n
PALETTE_ENTRY = 8                    # struct CompressedSpritePalette (data, tag)
BATTLE_MON_STATUS1 = 0x4C            # struct BattlePokemon
STATUS1_SLEEP = 0x7
AI_RESOURCES, AI_LOGIC_ID = 0x14, 0x11   # gBattleResources->ai, AI_ThinkingStruct.aiLogicId
CHEFE_AI_BITS = 9                    # FAMILIA_AI_CHEFE vai até AI_SCRIPT_HP_AWARE (bit 8)
AI_TURNS = 3
# Task 5: o prédio (posições de tools/familia_sombra/predio.json e dos map.json)
PORTA_FRENTE = (4, 150)              # Rota 23: o tile na frente da porta do prédio (porta em (4, 149))
PORTA = (4, 149)
ROTA23_SUL = (10, 126)               # Rota 23: um tile livre ao sul (o atalho WARP só aceita y < 128)
SAIDA_1F = (7, 11)                   # 1º andar: o tapete da saída
ANTES_DA_ESCADA = (10, 3)            # andares 1-5: o tile à esquerda do warp da escada para cima (11, 3)
SAIDA_ESCADA_6F = (4, 3)             # 6º andar: onde a escada deixa o jogador; um passo para baixo é o gatilho (4, 4)
VAI_E_VEM_4F = ((4, 6), ("down", "up"))   # 4º andar: corredor da esquerda, (4, 6) a (4, 10) e de volta
PASSOS_ANDAR = 400
# 1º andar: do tapete (7, 11) até (10, 6), na linha do capanga 2 (12, 6), que vem até (11, 6)
VISTA_CAPANGA_2 = ((("right", 2), ("up", 2), ("right", 1), ("up", 3)), (11, 6))
OBJECT_EVENT_XY, MAP_OFFSET = 0x10, 7  # ObjectEvent.currentCoords (coordenadas do mapa + 7)
QUEDA_ROSA = 30                      # meio-dia do relógio na vitória do caso familia/rosa
TRAINER_FLAGS_START = 0x500
REPEL_VAR = 0x4020                   # VAR_REPEL_STEP_COUNT
SB1_FLASH_LEVEL = 0x30               # SaveBlock1.flashLevel
SB2_GAME_CLOCK = 0x90                # SaveBlock2.gameClockFrames (src/day_night.c)
GAME_CLOCK_FRAMES_PER_MINUTE, GAME_CLOCK_START_MINUTE, HALF_DAY_MINUTES = 150, 480, 720   # constants/day_night.h
BUTTON_WAIT_STATES = {1, 2, 3}       # RENDER_STATE_WAIT/CLEAR/SCROLL_START: o texto espera um botão
PALETTE_FADE_ACTIVE = 7              # byte de gPaletteFade com o bit `active` (0x80)
OBJECT_EVENTS_COUNT, OBJECT_EVENT_SIZE, OBJECT_EVENT_LOCAL_ID, OBJECT_EVENT_GFX = 16, 0x24, 8, 5
FOG_CALLBACK = "FogHorizontalSpriteCallback"
LOCALID_PLAYER, LOCALID_FOLLOWER = 0xFF, 0xFE
# Task 7: estados das conquistas (include/constants/conquistas.h), o resultado do diário e a tela de conquistas
CONQ_PENDENTE, CONQ_FEITA = 0, 1
DIARIO_DERROTOU = 3
CONQ_BATALHA_ABA = 1
TELA_PRONTA_TIMEOUT = 300
TELA_ASSENTA = 20
DESCE_ATE_O_FIM = 12                 # apertos de Baixo: a aba Batalha tem 10 linhas ativas
# Task 6: o pedágio
LOCALID_COBRADOR = 8                 # 8º objeto de Route23 (os 7 guardas vêm antes; o teste estático confere)
VAR_MAP_SCENE_ROUTE23 = 0x405F
MULTICHOICE_TASK = "Task_MultichoiceMenu_HandleInput"
PEDAGIO_SUL = (14, 148)              # um passo antes do gatilho do lado sul (14, 147)
PEDAGIO_NORTE = (14, 144)            # um passo antes do gatilho do lado norte (14, 145)
PEDAGIO = 1000
VR_1F_LIVRE = (11, 19)               # Victory Road 1F: tile livre ao lado do warp de volta à Rota 23


def _noir_tool():
    spec = importlib.util.spec_from_file_location("familia_noir", REPO_ROOT / "tools" / "familia_sombra" / "noir.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def lz77(data: bytes) -> bytes:
    """Descompacta o LZ77 do BIOS do GBA (cabeçalho 0x10 + tamanho de 24 bits)."""
    assert data[0] == 0x10, data[0]
    size = int.from_bytes(data[1:4], "little")
    out, i = bytearray(), 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                length = (data[i] >> 4) + 3
                disp = ((data[i] & 0xF) << 8 | data[i + 1]) + 1
                i += 2
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size])


def chefe_da_tabela(ocupacao: int) -> tuple[str, int, str, list[str]]:
    """(espécie, nível, item, golpes) do chefe da ocupação em sFamiliaChefes."""
    text = TIMES_H.read_text(encoding="utf-8")
    text = text[text.index("sFamiliaChefes["):]
    sp, lv, item, moves = re.findall(r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", text)[ocupacao - 1]
    return sp, int(lv), item, [m.strip() for m in moves.split(",")]


def times_table(name: str) -> list[list[tuple[str, int, str, list[str]]]]:
    """[ocupação][membro] = (espécie, nível, item, golpes) da tabela `name` de familia_sombra_times.h."""
    text = TIMES_H.read_text(encoding="utf-8")
    body = text[text.index(f"{name}["):]
    body = body[body.index("{") + 1:]
    out, depth, start = [], 0, 0
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
            if depth == 1:
                start = i
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append([(sp, int(lv), item, [m.strip() for m in moves.split(",")]) for sp, lv, item, moves in
                            re.findall(r"MEMBRO\((\w+),\s*(\d+),\s*(\w+),\s*([\w ,]+)\)", body[start:i])])
            elif depth < 0:
                return out
    raise AssertionError(name)


class FamiliaScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.driver: BattleDriver | None = None
        self.moves = header_defines(REPO_ROOT, "moves.h")
        self.moves_names = {v: k for k, v in self.moves.items() if k.startswith("MOVE_")}
        self.songs = header_defines(REPO_ROOT, "songs.h")
        self.nav = Navigator(self.ctl)
        self.gfx = header_defines(REPO_ROOT, "event_objects.h")

    # --- leitura --------------------------------------------------------------------
    def _sym(self, name: str) -> int:
        return self.game.syms.addr(name)

    def _rom_text(self, symbol: str) -> str:
        return self.game.charmap.decode(self.emu.read(self._sym(symbol), STRING_BYTES).split(b"\xff")[0])

    def _battle_text(self) -> str:
        return self._rom_text("gDisplayedStringBattle")

    def _sprite_callback(self, sprite_id: int) -> str:
        ptr = self.emu.read_u32(self._sym("gSprites") + sprite_id * SPRITE_SIZE + SPRITE_CALLBACK)
        return self.game.syms.name_at(ptr & ~1) or hex(ptr)

    def _battler_sprite(self, battler: int) -> tuple[str, int]:
        """(callback, data[2]) do sprite do batalhador: no Pokémon, data[2] = espécie."""
        sprite_id = self.emu.read_u8(self._sym("gBattlerSpriteIds") + battler)
        data2 = self.emu.read_u16(self._sym("gSprites") + sprite_id * SPRITE_SIZE + SPRITE_DATA + 4)
        return self._sprite_callback(sprite_id), data2

    def _sliding_trainers(self) -> int:
        base = self._sym("gSprites")
        return sum(1 for i in range(MAX_SPRITES)
                   if self.emu.read_u16(base + i * SPRITE_SIZE + SPRITE_IN_USE) & 1
                   and self._sprite_callback(i) == TRAINER_SLIDE)

    def _bgm_is(self, song: str) -> bool:
        header = self.emu.read_u32(self._sym("gMPlayInfo_BGM"))
        number = self.songs[song]
        return header == self.emu.read_u32(self._sym("gSongTable") + number * SONG_SIZE)

    def _sp(self, name: str) -> int:
        return self.consts.species(f"SPECIES_{name}")

    def _trainer(self, name: str) -> int:
        return self.consts._eval(name)

    # --- preparo --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self.driver = BattleDriver(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="familia_continue")
        self.box.conq_silencio(True)
        for slot, (species, level) in enumerate(TEAM):
            self.box.set_party_mon(slot, self.consts.species(species), level)
        self.box.party_size(len(TEAM))
        self.box.familia_set(1, ESTADO_ATIVA)
        self.ctl.checkpoint("familia_base")
        return f"CONTINUAR; time {TEAM}; ocupação 1 ATIVA; savestate familia_base"

    def _restore(self, name: str) -> None:
        self.ctl.restore(name)
        self.emu.frames(12)

    def _wait_intro(self, symbol: str, battlers: tuple[int, ...]) -> list[str]:
        """Espera a fala de abertura `symbol` na caixa e confere, nesse instante, o sprite de cada batalhador."""
        want = self._rom_text(symbol)
        self.driver.wait_battle_start()
        self.ctl.wait_until(lambda: self._battle_text() == want, INTRO_TIMEOUT, f"abertura {symbol}")
        seen = []
        for battler in battlers:
            callback, data2 = self._battler_sprite(battler)
            species = self.driver.battler_species_level(battler)[0]
            assert callback in WILD_MON_CALLBACKS and data2 == species, \
                f"batalhador {battler}: sprite com callback {callback}, data[2] {data2} (espécie {species})"
            seen.append(f"{battler}: {self.consts.species_name(species)} ({callback})")
        assert self._sliding_trainers() == 0, "sprite de treinador entrando na tela"
        return seen

    # --- casos ----------------------------------------------------------------------
    def _capanga(self) -> str:
        self._restore("familia_base")
        self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        seen = self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        self.emu.frames(30)
        shot = self._shot("familia_capanga_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        self.ctl.checkpoint("familia_capanga")
        return f"abertura = gText_FamiliaCapangaQuerLutar; oponente {seen}; sem treinador; tela {shot}"

    def _ball(self, checkpoint: str = "familia_capanga") -> str:
        self._restore(checkpoint)
        ball = self.consts.item("ITEM_POKE_BALL")
        assert self.box.call(CMD_GIVE_ITEM, ball, EXTRA_BALLS) == 1
        before = self.game.bag_quantity(ball)
        d = self.driver
        d._open_bag_on_item(ball)
        d.bag.use_selected()
        texts = set()
        result = d._advance_until_menu_or_end("bola no capanga", INTRO_TIMEOUT,
                                              on_step=lambda: texts.add(self._battle_text()))
        after = self.game.bag_quantity(ball)
        dodge = [t for t in texts if DODGE_TEXT in t]
        assert dodge, f"sem o texto do desvio; vi {sorted(texts)}"
        assert dodge[0] == self._rom_text("gText_FamiliaDesviaBola"), dodge[0]
        assert result == "menu" and self.game.in_battle(), f"a batalha não seguiu: {result}"
        assert after == before >= EXTRA_BALLS, f"Poké Bolas: {before} antes, {after} depois"
        species = self.consts.species_name(self.driver.battler_species_level(1)[0])
        return f"desvio: {dodge[0]!r}; Poké Bolas {before} → {after}; batalha segue contra {species}"

    def _win(self) -> str:
        """A vitória sem humano: 'Você derrotou Capanga da Família!', a fala de derrota, nenhum prêmio em dinheiro
        e a flag do treinador ligada (o capanga some do mapa até a próxima ocupação)."""
        self._restore("familia_base")
        self.box.set_party_move(0, 0, self.moves["MOVE_SHADOW_BALL"])   # Fantasma 2x no Misdreavus
        money = self.game.money()
        self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        texts = set()
        result = self.driver.fight_to_end(on_step=lambda: texts.add(self._battle_text()))
        assert result == "win", f"resultado {result}; textos {sorted(texts)}"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        won = [t for t in texts if t.startswith("Você derrotou")]
        assert won and "Capanga da Família!" in won[0], f"sem a frase da vitória: {sorted(texts)}"
        prize = [t for t in texts if "pela vitória" in t]
        assert not prize and self.game.money() == money, f"prêmio: {prize}, dinheiro {money} → {self.game.money()}"
        flag = 0x500 + self._trainer("TRAINER_FAMILIA_CAPANGA_1")       # TRAINER_FLAGS_START + id
        assert self.game.flag(flag), "flag do capanga 1 desligada depois da vitória"
        return f"{won[0]!r}; dinheiro {money} → {self.game.money()}; flag do treinador {flag:#x} ligada"

    def _item_move(self, move: str, held: str | None, start=None) -> str:
        """Um turno de `move` (no golpe 0) do Mewtwo segurando `held` contra o capanga 1 (Misdreavus com Talismã
        Fantasma) ou contra a batalha que `start` começa: o item não muda de dono, nem na batalha nem no time."""
        self._restore("familia_base")
        held_id = self.consts.item(f"ITEM_{held}") if held else 0
        self.box.set_party_mon(0, self._sp("MEWTWO"), PLAYER_LEVEL, held_id)
        self.box.set_party_move(0, 0, self.moves[f"MOVE_{move}"])
        if start is None:
            self.box.start_trainer_battle(self._trainer("TRAINER_FAMILIA_CAPANGA_1"))
        else:
            start()
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        foe_item = self.game.enemy_party()[0].held_item
        assert start is not None or foe_item == self.consts.item("ITEM_SPELL_TAG"), foe_item
        assert foe_item and self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_SIZE + BATTLE_MON_ITEM) == foe_item
        result = self.driver.fight_turn(INTRO_TIMEOUT)
        mine = self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_ITEM)
        # o time lido com o checksum certo (a leitura pode pegar o Pokémon no meio de um GetMonData/SetMonData)
        raw = lambda: self.emu.read(self._sym("gPlayerParty"), POKEMON_SIZE)
        self.ctl.wait_until(lambda: mon_checksum_ok(raw()), 10, "time com checksum certo")
        party_item = self.game.party()[0].held_item
        assert (mine, party_item) == (held_id, held_id), \
            f"{move}: item do Mewtwo {mine} (batalha) / {party_item} (time), esperava {held_id}"
        detail = f"{move}: Mewtwo continua com {held or 'nada'}"
        if result == "menu":
            foe = self.emu.read_u16(self._sym("gBattleMons") + BATTLE_MON_SIZE + BATTLE_MON_ITEM)
            assert foe == foe_item, f"{move}: o capanga ficou com {foe}, esperava o item dele ({foe_item})"
            detail += f"; o capanga continua com o item {foe_item}"
        return detail

    def _thief(self) -> str:
        return self._item_move("THIEF", None) + " | " + self._item_move("TRICK", "LEFTOVERS")

    def _party_matches(self, mon, expected: tuple[str, int, str, list[str]], level: int | None = None) -> str:
        sp, lv, item, moves = expected
        got = (mon.species, mon.level, mon.held_item, mon.moves)
        want = (self._sp(sp), lv if level is None else level, self.consts.item(f"ITEM_{item}"),
                [self.moves[f"MOVE_{m}"] for m in moves])
        assert got == want, f"{sp}: {got}, esperava {want}"
        assert not mon.is_shiny, f"{sp} shiny"
        return f"{sp} nv {want[1]}"

    def _teams(self) -> str:
        self._restore("familia_base")
        capangas, gemeos, plantel = (times_table(t) for t in ("sFamiliaCapangas", "sFamiliaGemeos",
                                                               "sFamiliaPlantel"))
        seen = []
        for ocupacao in (1, 2):
            self.box.familia_set(ocupacao, ESTADO_ATIVA)
            extra = (ocupacao - 1) * 6
            size, _tier, double = self.box.build_trainer_party(self._trainer("TRAINER_FAMILIA_CAPANGA_1"), False)
            assert (size, double) == (1, False), (ocupacao, size, double)
            capanga = self._party_matches(self.game.enemy_party()[0], capangas[ocupacao - 1][0])
            size, _tier, double = self.box.build_trainer_party(self._trainer("TRAINER_FAMILIA_GEMEOS"), False)
            mons = self.game.enemy_party()
            assert (size, double, len(mons)) == (2, True, 2), (ocupacao, size, double, len(mons))
            twins = [self._party_matches(m, e) for m, e in zip(mons, gemeos[ocupacao - 1])]
            pedagio = []
            for n, level in (("1", 56 + extra), ("2", 58 + extra)):
                size, _tier, _double = self.box.build_trainer_party(self._trainer(f"TRAINER_FAMILIA_PEDAGIO_{n}"), False)
                mon = self.game.enemy_party()[0]
                match = [e for e in plantel[ocupacao - 1] if self._sp(e[0]) == mon.species]
                assert size == 1 and match, f"pedágio {n}: espécie {mon.species} fora do plantel da ocupação {ocupacao}"
                pedagio.append(self._party_matches(mon, match[0], level))
            assert pedagio[0].split()[0] != pedagio[1].split()[0], f"pedágio com a mesma espécie: {pedagio}"
            seen.append(f"ocupação {ocupacao}: capanga 1 {capanga}; gêmeos {twins}; pedágio {pedagio}")
        self.box.familia_set(1, ESTADO_ATIVA)
        return "; ".join(seen)

    # --- Task 4: andares 4-5 e o chefe ----------------------------------------------------------
    def _species_palette(self, species: int, shiny: bool) -> list[int]:
        """As 16 cores (GBA) da paleta da espécie, descompactadas da ROM (gMonPaletteTable / gMonShinyPaletteTable)."""
        table = self._sym("gMonShinyPaletteTable" if shiny else "gMonPaletteTable")
        ptr = self.emu.read_u32(table + species * PALETTE_ENTRY)
        raw = lz77(self.emu.read(ptr, 64))
        return [int.from_bytes(raw[i:i + 2], "little") for i in range(0, 32, 2)]

    def _battler_palette(self, battler: int) -> list[int]:
        base = self._sym("gPlttBufferUnfaded") + (OBJ_PLTT + 16 * battler) * 2
        return [self.emu.read_u16(base + 2 * i) for i in range(16)]

    def _encontro(self) -> str:
        self._restore("familia_base")
        plantel = times_table("sFamiliaPlantel")[0]
        species, level = self.box.familia_wild()
        member = [m for m in plantel if self._sp(m[0]) == species]
        assert member, f"espécie {species} fora do plantel da ocupação 1"
        assert 54 <= level <= 58, f"nível {level} fora de 54-58"
        seen = self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & (BATTLE_TYPE_TRAINER | BATTLE_TYPE_FAMILIA_CHEFE), \
            f"gBattleTypeFlags {flags:#x}"
        detail = self._party_matches(self.game.enemy_party()[0], member[0], level)
        assert self._bgm_is("MUS_VS_TRAINER"), "a música não é a de treinador"
        normal = self._species_palette(species, False)
        want = [normal[0]] + [_noir_tool().noir_gba(c) for c in normal[1:]]
        got = self._battler_palette(1)
        assert got == want, f"paleta do oponente {[hex(c) for c in got]}, esperava o filme {[hex(c) for c in want]}"
        self.emu.frames(30)
        shot = self._shot("familia_filme_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        self.ctl.checkpoint("familia_selvagem")
        return f"{detail} com item e golpes do plantel; {seen}; MUS_VS_TRAINER; paleta = noir(normal); tela {shot}"

    def _wild_ball(self) -> str:
        return self._ball("familia_selvagem")

    def _wild_thief(self) -> str:
        start = self.box.familia_wild
        return self._item_move("THIEF", None, start) + " | " + self._item_move("TRICK", "LEFTOVERS", start)

    def _chefe(self) -> str:
        self._restore("familia_base")
        expected = chefe_da_tabela(1)
        gengar = self._sp(expected[0])
        self.box.familia_chefe()
        seen = self._wait_intro("gText_FamiliaChefeDom", (1,))     # "GENGAR, O DOM, quer acertar as contas!"
        assert self.driver.battler_species_level(1)[0] == gengar, seen
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE and flags & BATTLE_TYPE_LEGENDARY, f"gBattleTypeFlags {flags:#x}"
        assert not flags & (BATTLE_TYPE_FAMILIA | BATTLE_TYPE_TRAINER), f"gBattleTypeFlags {flags:#x}"
        assert self.emu.read_u16(self._sym("gTrainerBattleOpponent_A")) == 0, "gTrainerBattleOpponent_A não zerado"
        mon = self.game.enemy_party()[0]
        assert mon.is_shiny, f"chefe não shiny: pid {mon.personality:#x}, OT {mon.ot_id:#x}"
        assert mon.ot_id == self.game.party()[0].ot_id, "o OT do chefe não é o jogador"
        sp, lv, item, moves = expected
        got = (mon.species, mon.level, mon.held_item, mon.moves)
        want = (gengar, lv, self.consts.item(f"ITEM_{item}"), [self.moves[f"MOVE_{m}"] for m in moves])
        assert got == want, f"{sp}: {got}, esperava {want}"
        assert self._bgm_is("MUS_VS_LEGEND"), "a música não é a de lendário"
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        self.emu.frames(10)
        shiny = self._species_palette(gengar, True)
        got = self._battler_palette(1)
        assert got == shiny, f"paleta do chefe {[hex(c) for c in got]}, esperava a shiny {[hex(c) for c in shiny]}"
        shot = self._shot("familia_chefe_batalha")
        self.ctl.checkpoint("familia_chefe")
        return (f"{sp} nv {lv} shiny, {item}, {moves}; abertura {self._rom_text('gText_FamiliaChefeDom')!r}; "
                f"lendária + FAMILIA_CHEFE; MUS_VS_LEGEND; paleta shiny sem filme; tela {shot}")

    def _passos(self) -> str:
        """O caminho de cada passo (TryStandardWildEncounter) com o mapa valendo como andar escuro e SEM entrada em
        wild_encounters.json para ele: com chefe ativo sai um capanga do plantel; sem chefe, nada em 400 passos."""
        self._restore("familia_base")
        plantel = times_table("sFamiliaPlantel")[0]
        steps, started = self.box.familia_passos(PASSOS)
        assert started, f"nenhum encontro em {PASSOS} passos com chefe ativo"
        self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & BATTLE_TYPE_TRAINER, f"gBattleTypeFlags {flags:#x}"
        species, level = self.driver.battler_species_level(1)
        assert any(self._sp(m[0]) == species for m in plantel) and 54 <= level <= 58, (species, level)
        ativo = f"chefe ativo: encontro no passo {steps} ({self.consts.species_name(species)} nv {level})"
        self._restore("familia_base")
        self.box.familia_set(1, ESTADO_SEM_CHEFE)
        steps, started = self.box.familia_passos(PASSOS)
        self.emu.frames(30)
        assert not started and steps == PASSOS and not self.game.in_battle(), (steps, started)
        self.box.familia_set(1, ESTADO_ATIVA)
        return f"{ativo}; sem chefe: {PASSOS} passos sem encontro"

    def _chefe_ball(self) -> str:
        self._restore("familia_chefe")
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1
        before = self.game.bag_quantity(master)
        caught = self.driver.throw_ball(master)
        after = self.game.bag_quantity(master)
        assert caught, "a Master Ball não capturou o chefe"
        assert after == before - 1, f"Master Ball: {before} antes, {after} depois (não foi gasta)"
        return f"capturado; Master Ball {before} -> {after}"

    def _chefe_ia(self) -> str:
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("GOLEM"), 100)
        self.box.set_party_move(0, 0, self.moves["MOVE_HARDEN"])
        self.box.familia_chefe()
        thunderbolt = self.moves["MOVE_THUNDERBOLT"]
        dream, hypnosis = self.moves["MOVE_DREAM_EATER"], self.moves["MOVE_HYPNOSIS"]
        chosen = []
        for turn in range(1, AI_TURNS + 1):
            self.driver.wait_action_menu(INTRO_TIMEOUT)
            asleep = bool(self.emu.read_u32(self._sym("gBattleMons") + BATTLE_MON_STATUS1) & STATUS1_SLEEP)
            self.emu.frames(10)
            move, result = self._turn_reading_foe_move()
            name = self.moves_names.get(move, str(move))
            chosen.append(name + (" (Golem dormindo)" if asleep else ""))
            assert move != thunderbolt, f"turno {turn}: Raio contra o Golem (imune)"
            bad = hypnosis if asleep else dream
            assert move != bad, f"turno {turn}: {name} com o Golem {'dormindo' if asleep else 'acordado'}"
            if turn == 1:
                ai = self.emu.read_u32(self.emu.read_u32(self._sym("gBattleResources")) + AI_RESOURCES)
                bits = self.emu.read_u8(ai + AI_LOGIC_ID)
                assert bits == CHEFE_AI_BITS, f"IA do chefe com {bits} bits de flags, esperava {CHEFE_AI_BITS}"
            assert result == "menu", f"turno {turn}: a batalha acabou ({result})"
        return f"IA de chefe (aiLogicId {CHEFE_AI_BITS}); golpes {chosen}"

    def _turn_reading_foe_move(self) -> tuple[int, str]:
        """Um turno de LUTAR (1º golpe com PP), como BattleDriver.fight_turn, lendo gChosenMoveByBattler[1] logo que o
        jogador escolhe (o motor zera a escolha no fim do turno): (golpe do oponente, 'menu' ou 'end')."""
        d = self.driver
        d._choose_action(ACTION_FIGHT)
        in_moves = lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX)
        self.ctl.wait_until(in_moves, MENU_TIMEOUT, "menu de golpes")
        d._choose_first_move_with_pp()
        self.ctl.wait_until(lambda: not in_moves(), 60, "saída do menu de golpes")
        chosen = self._sym("gChosenMoveByBattler") + 2
        self.ctl.wait_until(lambda: self.emu.read_u16(chosen) != 0, MENU_TIMEOUT, "escolha do chefe")
        move = self.emu.read_u16(chosen)
        return move, d._advance_until_menu_or_end("fim do turno", INTRO_TIMEOUT)

    def _twins(self) -> str:
        self._restore("familia_base")
        self.box.familia_gemeos()
        seen = self._wait_intro("gText_FamiliaGemeosQueremLutar", (1, 3))
        flags = self.driver.battle_type_flags()
        assert flags & 1, f"não é dupla: gBattleTypeFlags {flags:#x}"
        for battler in (1, 3):
            species, level = self.driver.battler_species_level(battler)
            assert (species, level) == (self._sp("MACHAMP"), 60), f"batalhador {battler}: {(species, level)}"
        assert self._bgm_is("MUS_VS_GYM_LEADER"), "a música não é a de líder de ginásio"
        self.emu.frames(30)
        shot = self._shot("familia_gemeos_batalha")
        self.driver.wait_action_menu(INTRO_TIMEOUT)
        return f"dupla: {seen}, 2 Machamp nv 60; MUS_VS_GYM_LEADER; tela {shot}"

    # --- Task 5: o prédio ------------------------------------------------------------------------
    def _flag(self, name: str) -> int:
        return self.consts.flag(name)

    def _trainer_flag(self, name: str) -> int:
        return TRAINER_FLAGS_START + self._trainer(name)

    def _message(self) -> str:
        """A última caixa de mensagem do campo (gStringVar4)."""
        return self.game.charmap.decode(self.emu.read(self._sym("gStringVar4"), STRING_BYTES).split(b"\xff")[0])

    def _fade_active(self) -> bool:
        return bool(self.emu.read_u8(self._sym("gPaletteFade") + PALETTE_FADE_ACTIVE) & 0x80)

    def _settle(self, what: str) -> None:
        self.ctl.wait_overworld_idle(900)
        self.ctl.wait_until(lambda: not self._fade_active(), 300, f"fim do fade: {what}")
        self.emu.frames(4)

    def _warp(self, map_name: str, xy: tuple[int, int]) -> None:
        """Atalho WARP (fade e carga do mapa como numa porta: o on_transition do destino roda)."""
        group, num = self.consts.map(map_name)
        self._settle(f"antes do warp para {map_name}")
        self.box.call(CMD_WARP, group | num << 8, xy[0] | xy[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_name}")
        self._settle(f"warp para {map_name}")

    def _at(self, map_name: str) -> bool:
        return self.game.location() == self.consts.map(map_name)

    def _half_day(self) -> int:
        """Meio-dia do relógio da hack (FamiliaSombra_MeiosDiasAgora)."""
        frames = self.emu.read_u32(self.emu.read_u32(self._sym("gSaveBlock2Ptr")) + SB2_GAME_CLOCK)
        return (frames // GAME_CLOCK_FRAMES_PER_MINUTE + GAME_CLOCK_START_MINUTE) // HALF_DAY_MINUTES

    def _set_half_day(self, half: int) -> None:
        self.box.set_clock(half // 2, (half % 2) * HALF_DAY_MINUTES)
        assert self._half_day() == half, (self._half_day(), half)

    def _repovoaveis(self) -> dict[str, bool]:
        """O que FamiliaSombra_Repovoar desmarca: 1 item, 1 capanga e os gêmeos (amostra) e a flag dos gêmeos."""
        return {
            "item 1_1": self.game.flag(self._flag("FLAG_FAMILIA_ITEM_1_1")),
            "capanga 1": self.game.flag(self._trainer_flag("TRAINER_FAMILIA_CAPANGA_1")),
            "treinador gêmeos": self.game.flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS")),
            "gêmeos vencidos": self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")),
        }

    def _mark_repovoaveis(self) -> None:
        for flag in (self._flag("FLAG_FAMILIA_ITEM_1_1"), self._trainer_flag("TRAINER_FAMILIA_CAPANGA_1"),
                     self._trainer_flag("TRAINER_FAMILIA_GEMEOS"), self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")):
            assert self.box.set_flag(flag, True)

    def _active_objects(self) -> list[int]:
        """localId dos objetos ativos do mapa (sem o jogador e o seguidor), em ordem."""
        base = self._sym("gObjectEvents")
        ids = []
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            local = self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID)
            if self.emu.read_u8(addr) & 1 and local not in (LOCALID_PLAYER, LOCALID_FOLLOWER):
                ids.append(local)
        return sorted(ids)

    def _waiting(self) -> bool:
        """Página inteira na tela, esperando botão (ou impressão acabada)."""
        return not self.game.text_printer_active() or self.game.text_printer_state(0) in BUTTON_WAIT_STATES

    def _sprites_with(self, callback: str) -> int:
        base = self._sym("gSprites")
        return sum(1 for i in range(MAX_SPRITES)
                   if self.emu.read_u16(base + i * SPRITE_SIZE + SPRITE_IN_USE) & 1 and self._sprite_callback(i) == callback)

    def _object_gfx(self, local: int) -> int:
        base = self._sym("gObjectEvents")
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID) == local:
                return self.emu.read_u8(addr + OBJECT_EVENT_GFX)
        raise AssertionError(f"objeto {local} não está no mapa")

    def _scene(self, until, what: str, timeout: int = 4000, shot: tuple[str, str] | None = None) -> list[str]:
        """Aperta A até `until()`; devolve as mensagens do campo vistas (gStringVar4). `shot` = (trecho, tela):
        foto quando o trecho está na caixa, já impresso e esperando o botão."""
        seen, spent, taken = [], 0, False
        while not until():
            if spent > timeout:
                raise self.ctl.timeout_error(f"{what}; mensagens {seen}")
            msg = self._message()
            if self.ctl.script_active() and msg and (not seen or seen[-1] != msg):
                seen.append(msg)
            if shot and not taken and shot[0] in msg and self.ctl.script_active():
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, f"texto {shot[0]!r}")
                self._shot(shot[1])
                taken = True
            if self.ctl.script_active() and not self.game.in_battle():
                self.emu.press(KEY_A, hold=2, release=8)
                spent += 10
            else:
                self.emu.frames(4)
                spent += 4
        return seen

    def _sair_do_predio(self) -> None:
        """Pelo tapete do 1º andar até a frente da porta na Rota 23 (o atalho WARP não chega a y >= 128)."""
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        if self.game.player_xy() == PORTA:      # porta trancada: sai sem a animação e fica no tile da porta
            self.nav.step("down")
        assert self._at("MAP_ROUTE23") and self.game.player_xy() == PORTA_FRENTE, \
            (self.game.location(), self.game.player_xy())

    def _porta(self) -> str:
        """Sem a 8ª insígnia a porta do prédio está trancada (o metatile vira o da porta sem comportamento e a placa
        fala do charuto); com ela, a 1ª entrada liga a ocupação 1 e a porta leva ao 1º andar."""
        self._restore("familia_base")
        badge = self._flag("FLAG_BADGE08_GET")
        self.box.set_flag(badge, False)
        self.box.familia_set(0, ESTADO_FECHADO)
        self._sair_do_predio()
        self.emu.keys(KEY_UP)
        self.emu.frames(60)
        self.emu.keys(0)
        self.emu.frames(10)
        assert self._at("MAP_ROUTE23") and self.game.player_xy() == PORTA_FRENTE, \
            f"a porta trancada deixou passar: {self.game.location()} {self.game.player_xy()}"
        self.ctl.press_until(KEY_A, self.ctl.script_active, "placa da porta", tries=5)
        self.ctl.wait_until(self._waiting, 600, "texto da porta")
        msg = self._message()
        assert msg == self._rom_text("Route23_Text_PortaFamiliaTrancada"), msg
        self._shot("familia_porta_trancada")
        self._scene(self.ctl.overworld_idle, "fim da placa")
        assert self.box.familia_estado()[:2] == (0, ESTADO_FECHADO)
        self.box.set_flag(badge, True)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA), self.box.familia_estado()
        self._sair_do_predio()
        self._shot("familia_rota23_predio")
        self.nav.go_through_warp("up")
        assert self._at("MAP_ROUTE23_UNUSED_HOUSE"), self.game.location()
        return f"trancada: {msg!r}; com a 8ª insígnia: ocupação 1 ATIVA e a porta leva ao 1º andar"

    def _ciclo(self) -> str:
        """O ciclo pelo relógio: save antigo com a 8ª insígnia entra = ocupação 1; queda + 6 meios-dias = ainda sem
        chefe; +7 = ocupação 2 com itens e treinadores de volta (uma vez só); a 2ª queda + 7 = continua sem chefe."""
        self._restore("familia_base")
        log = []
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), True)
        self.box.familia_set(0, ESTADO_FECHADO)
        self._mark_repovoaveis()
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA), self.box.familia_estado()
        assert not any(self._repovoaveis().values()), self._repovoaveis()
        log.append("save antigo com a insígnia: ocupação 1 ATIVA, tudo no lugar")
        queda = 20
        self._set_half_day(queda)
        self.box.familia_set(1, ESTADO_SEM_CHEFE, queda)
        self._mark_repovoaveis()
        self._set_half_day(queda + 6)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, queda), self.box.familia_estado()
        log.append("queda + 6 meios-dias: sem chefe")
        self._set_half_day(queda + 7)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (2, ESTADO_ATIVA), self.box.familia_estado()
        assert not any(self._repovoaveis().values()), f"não repovoou: {self._repovoaveis()}"
        log.append("+7: ocupação 2 ATIVA, itens e treinadores de volta")
        self._mark_repovoaveis()           # o jogador vence o capanga e pega o item da ocupação 2
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.box.familia_estado()[:2] == (2, ESTADO_ATIVA)
        assert all(self._repovoaveis().values()), f"repovoou de novo: {self._repovoaveis()}"
        log.append("entrar de novo não repovoa outra vez")
        queda2 = queda + 9
        self._set_half_day(queda2)
        self.box.familia_set(2, ESTADO_SEM_CHEFE, queda2)
        self._set_half_day(queda2 + 7)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        assert self.box.familia_estado() == (2, ESTADO_SEM_CHEFE, queda2), self.box.familia_estado()
        assert self._active_objects() == [], f"objetos no 1º andar sem chefe: {self._active_objects()}"
        log.append("2ª queda + 7: continua sem chefe (FAMILIA_OCUPACOES_ATIVAS 2), andar vazio")
        return "; ".join(log)

    # --- o pedágio (Task 6) -----------------------------------------------------------
    def _set_money(self, amount: int) -> None:
        """Dinheiro do jogador (u32 XOR encryptionKey): escrita na RAM, só na ROM de teste."""
        self.emu.write(self.game._sb1() + SB1_MONEY, (amount ^ self.game._key()).to_bytes(4, "little"))

    def _pedagio_prep(self) -> None:
        """Uma vez só: monta os dois pontos de partida (norte e sul do corredor) como savestates."""
        if getattr(self, "_pedagio_pronto", False):
            return
        self._restore("familia_base")
        self.box.set_flag(self._flag("FLAG_BADGE08_GET"), True)
        self.box.set_flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"), False)
        self.box.call(CMD_SET_VAR, VAR_MAP_SCENE_ROUTE23, 0)      # sem a cena dos guardas das insígnias
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.set_party_move(0, 0, self.moves["MOVE_SHADOW_BALL"])
        self.box.familia_set(1, ESTADO_ATIVA)
        self._set_money(5000)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert self.nav.walk_to(*PEDAGIO_NORTE), f"não chegou ao lado norte: {self.game.player_xy()}"
        self.ctl.checkpoint("pedagio_norte")
        self._sair_do_predio()
        assert self.nav.walk_to(*PEDAGIO_SUL), f"não chegou ao lado sul: {self.game.player_xy()}"
        self.ctl.checkpoint("pedagio_sul")
        self._pedagio_pronto = True

    def _pedagio_cena(self, pagar: bool = False, forca: bool = False, shot: str | None = None) -> dict:
        """Roda a cena do pedágio até o campo ficar livre: A avança as falas; a pergunta sim/não recebe A (pagar) ou B;
        o menu recebe A em "Voltar depois" ou BAIXO + A em "Passar à força"; cada batalha é lutada até o fim."""
        info = {"msgs": [], "yesno": False, "menu": False, "lutas": [], "especies": []}
        spent, handled = 0, False
        while not (self.ctl.overworld_idle() and info["msgs"]):
            if spent > 30000:
                raise self.ctl.timeout_error(f"cena do pedágio; mensagens {info['msgs']}, lutas {info['lutas']}")
            if self.game.in_battle():
                self.driver.wait_battle_start()
                info["lutas"].append(self.emu.read_u16(self._sym("gTrainerBattleOpponent_A")))
                info["especies"].append(self.driver.battler_species_level(1)[0])
                result = self.driver.fight_to_end()
                assert result == "win", f"perdeu para o pedágio: {result}"
                self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
                spent += 100
                continue
            tasks = self._tasks()
            msg = self._message()
            if self.ctl.script_active() and msg and (not info["msgs"] or info["msgs"][-1] != msg):
                info["msgs"].append(msg)
            if YESNO_TASK in tasks:
                info["yesno"] = True
                self.ctl.wait_until(lambda: self._waiting() and not self._fade_active(), 300, "pergunta de pagar")
                if shot and not handled:
                    info["shot"] = self._shot(shot)
                handled = True
                self.emu.press(KEY_A if pagar else KEY_B, hold=2, release=8)
                spent += 10
            elif MULTICHOICE_TASK in tasks:
                info["menu"] = True
                self.emu.frames(10)
                if forca:
                    self.emu.press(KEY_DOWN, hold=2, release=8)
                self.emu.press(KEY_A, hold=2, release=20)
                spent += 40
            elif self.ctl.script_active():
                self.emu.press(KEY_A, hold=2, release=8)
                spent += 10
            else:
                self.emu.frames(4)
                spent += 4
        self.emu.frames(10)
        return info

    def _pedagio_passo(self, direction: str) -> None:
        """Um passo para o gatilho: o script começa um quadro depois do passo (o jogador já pode estar parado)."""
        assert self.nav.step(direction) == 1
        self.ctl.wait_until(self.ctl.script_active, 60, f"o gatilho do pedágio ({direction})")

    def _pedagio_gatilho(self, checkpoint: str = "pedagio_sul") -> None:
        """Do checkpoint, um passo para o gatilho (sul: y 147; norte: y 145); o script do pedágio toma os controles."""
        self._pedagio_prep()
        self._restore(checkpoint)
        self._pedagio_passo("down" if checkpoint == "pedagio_norte" else "up")

    def _pedagio_paga(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        assert self.game.money() == 5000 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert LOCALID_COBRADOR in self._active_objects(), f"sem o cobrador: {self._active_objects()}"
        assert self._object_gfx(LOCALID_COBRADOR) == self.gfx["OBJ_EVENT_GFX_FAMILIA_PERSIAN"]
        assert self._object_xy(LOCALID_COBRADOR) == (14, 146), self._object_xy(LOCALID_COBRADOR)
        self._pedagio_gatilho()
        info = self._pedagio_cena(pagar=True, shot="familia_pedagio")
        assert info["yesno"] and not info["menu"] and not info["lutas"], info
        assert self._rom_text("Route23_Text_PedagioPago") in info["msgs"], info["msgs"]
        assert self.game.money() == 5000 - PEDAGIO, f"dinheiro {self.game.money()}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        # passa pela esquerda do Persian e anda sem ser cobrado
        assert self.game.player_xy() == (14, 147), self.game.player_xy()
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        assert self.game.player_xy() == (13, 144), self.game.player_xy()
        # entra no prédio e sai: continua pago, e não cobra na volta
        assert self.nav.walk_to(*PORTA_FRENTE), f"não voltou à porta: {self.game.player_xy()}"
        self.nav.go_through_warp("up")
        assert self._at("MAP_ROUTE23_UNUSED_HOUSE") and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        assert self._at("MAP_ROUTE23") and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO")), \
            "o prédio zerou o pago"
        assert self.nav.walk_to(14, 148)
        self.nav.step("up")                     # o gatilho arma de novo a cada carga do mapa: o pago o deixa passar
        self.ctl.wait_overworld_idle()
        assert self.game.player_xy() == (14, 147) and self.game.money() == 5000 - PEDAGIO
        assert YESNO_TASK not in self._tasks() and self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        return (f"cobrador no (14, 146); pagou: ¥5.000 → ¥{self.game.money()}, flag ligada; passou, entrou no "
                f"prédio, saiu e subiu sem ser cobrado; tela {info['shot']}")

    def _pedagio_sem_dinheiro(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        self._set_money(PEDAGIO - 1)
        self.ctl.checkpoint("pedagio_pobre")
        self._pedagio_gatilho("pedagio_pobre")
        info = self._pedagio_cena()
        assert not info["yesno"] and info["menu"] and not info["lutas"], info
        assert self._rom_text("Route23_Text_PedagioSemDinheiro") in info["msgs"], info["msgs"]
        assert self._rom_text("Route23_Text_PedagioVoltar") in info["msgs"], info["msgs"]
        assert self.game.money() == PEDAGIO - 1 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.game.player_xy() == PEDAGIO_SUL, f"não voltou um passo: {self.game.player_xy()}"
        # com dinheiro, recusando: a pergunta vem antes do mesmo menu e nada é cobrado
        self._pedagio_gatilho("pedagio_sul")
        info2 = self._pedagio_cena(pagar=False)
        assert info2["yesno"] and info2["menu"] and not info2["lutas"], info2
        assert self._rom_text("Route23_Text_PedagioRecusou") in info2["msgs"], info2["msgs"]
        assert self.game.money() == 5000 and not self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self.game.player_xy() == PEDAGIO_SUL
        return (f"sem dinheiro (¥{PEDAGIO - 1}): só o menu, voltou um passo, nada cobrado; "
                f"recusando com ¥5.000: pergunta + menu, voltou, ¥5.000 intactos")

    def _pedagio_forca(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        self._set_money(500)
        self.box.conq_reset(True)
        assert self._conq("familia_pedagio") == CONQ_PENDENTE
        self.ctl.checkpoint("pedagio_pobre")
        self._pedagio_gatilho("pedagio_pobre")
        info = self._pedagio_cena(forca=True)
        assert info["menu"] and not info["yesno"], info
        want = [self._trainer("TRAINER_FAMILIA_PEDAGIO_1"), self._trainer("TRAINER_FAMILIA_PEDAGIO_2")]
        assert info["lutas"] == want, f"lutas {info['lutas']}, esperava {want}"
        assert len(set(info["especies"])) == 2, f"as 2 lutas com a mesma espécie: {info['especies']}"
        assert self.game.money() == 500, f"prêmio ou cobrança: ¥{self.game.money()}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_PEDAGIO_PAGO"))
        assert self._rom_text("Route23_Text_PedagioLivre") in info["msgs"], info["msgs"]
        assert self.nav.step("left") == 1 and self.nav.step("up", 3) == 3 and self.nav.interrupted is None
        nomes = [self.consts.species_name(sp) for sp in info["especies"]]
        assert self._conq("familia_pedagio") == CONQ_FEITA, "Pagar ou lutar não ficou feita"
        assert self._conq("familia_dom") == CONQ_PENDENTE
        return f"2 lutas seguidas ({nomes}), dinheiro intacto, passagem paga e livre; Pagar ou lutar feita"

    def _pedagio_volta(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_norte")
        pago = self._flag("FLAG_FAMILIA_PEDAGIO_PAGO")
        self.box.set_flag(pago, True)           # pagou na ida
        self._warp("MAP_VICTORY_ROAD_1F", VR_1F_LIVRE)
        assert not self.game.flag(pago), "a Victory Road 1F não zerou o pago"
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        assert not self.game.flag(pago)
        assert self.nav.walk_to(*PEDAGIO_NORTE), f"descida interrompida em {self.game.player_xy()}"
        # descendo: cobra no lado norte; recusar + voltar depois empurra um passo para o norte
        self._pedagio_passo("down")
        info = self._pedagio_cena(pagar=False)
        assert info["yesno"] and info["menu"], info
        assert self._rom_text("Route23_Text_PedagioCobra") in info["msgs"], info["msgs"]
        assert self.game.player_xy() == PEDAGIO_NORTE and self.game.money() == 5000 \
            and not self.game.flag(pago), (self.game.player_xy(), self.game.money())
        # de novo e pagando: passa pela direita e desce até o sul sem ser cobrado
        self._pedagio_passo("down")
        info = self._pedagio_cena(pagar=True)
        assert info["yesno"] and not info["menu"], info
        assert self.game.money() == 5000 - PEDAGIO and self.game.flag(pago)
        assert self.nav.step("right") == 1 and self.nav.step("down", 3) == 3 and self.nav.interrupted is None
        assert self.game.player_xy() == (15, 148), self.game.player_xy()
        return "pago na ida, a Victory Road 1F zera; descendo cobra no norte: voltar empurra ao norte, pagar libera"

    def _pedagio_sem_chefe(self) -> str:
        self._pedagio_prep()
        self._restore("pedagio_sul")
        queda = 20
        self._set_half_day(queda)
        self.box.familia_set(1, ESTADO_SEM_CHEFE, queda)
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        self.nav.go_through_warp("down")
        self._settle("saída do prédio")
        assert self._at("MAP_ROUTE23") and self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, queda)
        assert LOCALID_COBRADOR not in self._active_objects(), f"cobrador sem chefe: {self._active_objects()}"
        assert self.nav.walk_to(*PEDAGIO_SUL)
        assert self.nav.step("up", 5) == 5 and self.nav.interrupted is None, "o pedágio disparou sem chefe"
        assert self.game.player_xy() == (14, 143) and not self.ctl.script_active()
        return "sem chefe: sem Persian, sem gatilho, o corredor livre (inclusive o tile do cobrador)"

    def _subida(self) -> str:
        """Da porta ao 6º andar pelas escadas de verdade (capangas já vencidos, Repelente com o Mewtwo nv 100 na
        frente): música, clima e escuro de cada andar; telas do 1º, do 4º (escuro e névoa) e da sala do Dom."""
        self._restore("familia_base")
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        self.box.call(CMD_SET_VAR, REPEL_VAR, 999)
        self._warp("MAP_ROUTE23", ROTA23_SUL)
        self._sair_do_predio()
        self.nav.go_through_warp("up")
        self._settle("1º andar")
        shots = [self._shot("familia_andar_1")]
        for slot in range(1, 10):
            self.box.set_flag(self._trainer_flag(f"TRAINER_FAMILIA_CAPANGA_{slot}"), True)
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        seen = []
        for andar in range(1, 6):
            name = "MAP_ROUTE23_UNUSED_HOUSE" if andar == 1 else f"MAP_ROUTE23_FAMILIA_SOMBRA_{andar}F"
            assert self._at(name), (andar, self.game.location())
            song = "MUS_ROCKET_HIDEOUT" if andar <= 3 else "MUS_POKE_TOWER"
            assert self._bgm_is(song), f"{andar}º andar sem {song}"
            flash = self.emu.read_u8(self.emu.read_u32(self._sym("gSaveBlock1Ptr")) + SB1_FLASH_LEVEL)
            assert (flash > 0) == (andar in (4, 5)), f"{andar}º andar: flashLevel {flash}"
            fog = self._sprites_with(FOG_CALLBACK)
            assert (fog > 0) == (andar in (4, 5)), f"{andar}º andar: {fog} sprites de névoa"
            if andar == 4:
                shots.append(self._shot("familia_andar_4"))
            seen.append(f"{andar}º ({song}, escuro {flash}, névoa {fog})")
            assert self.nav.walk_to(*ANTES_DA_ESCADA), f"{andar}º andar: não chegou à escada"
            self.nav.go_through_warp("right")
            self._settle(f"{andar + 1}º andar")
        assert self._at("MAP_ROUTE23_FAMILIA_SOMBRA_6F"), self.game.location()
        self.emu.frames(30)
        shots.append(self._shot("familia_sala_do_dom"))
        objs = sorted(self._active_objects())
        assert objs == [1, 2, 3], f"sala do Dom: objetos {objs} (chefe e os 2 gêmeos)"
        gfx = [self._object_gfx(local) for local in objs]
        want = [self.gfx[f"OBJ_EVENT_GFX_FAMILIA_{n}"] for n in ("GENGAR_SHINY", "MACHAMP", "MACHAMP")]
        assert gfx == want, f"gráficos da sala {gfx}, esperava {want}"
        return f"andares {seen}; 6º com o Gengar shiny e os 2 Machamp; telas {shots}"

    def _capanga_ve(self) -> str:
        """O capanga 2 do 1º andar (visão 4, olhando para a esquerda) vê o jogador a 2 tiles, vem até ele e luta;
        vencido, some do mapa na hora (a flag do treinador é a flag do objeto)."""
        self._restore("familia_base")
        self.box.set_party_move(0, 0, self.moves["MOVE_THUNDERBOLT"])
        self._warp("MAP_ROUTE23_UNUSED_HOUSE", SAIDA_1F)
        assert 2 in self._active_objects(), self._active_objects()
        start = self._object_xy(2)
        for direction, n in VISTA_CAPANGA_2[0]:     # pela direita, longe da vista do capanga 1
            assert self.nav.step(direction, n) == n, (direction, n, self.game.player_xy())
        self.ctl.wait_until(self.ctl.script_active, 60, "o capanga vê o jogador")
        self._scene(self.game.in_battle, "o capanga vem lutar")
        moved = self._object_xy(2)
        trainer = self.emu.read_u16(self._sym("gTrainerBattleOpponent_A"))
        assert trainer == self._trainer("TRAINER_FAMILIA_CAPANGA_2"), trainer
        assert moved == VISTA_CAPANGA_2[1], f"o capanga não veio até o jogador: {start} -> {moved}"
        assert self.driver.fight_to_end() == "win", "perdeu para o capanga 2"
        self._scene(self.ctl.overworld_idle, "volta da batalha")
        assert 2 not in self._active_objects(), f"o capanga vencido continua no mapa: {self._active_objects()}"
        assert self.game.flag(self._trainer_flag("TRAINER_FAMILIA_CAPANGA_2"))
        return f"o capanga 2 andou de {start} para {moved}, lutou e sumiu depois da derrota"

    def _object_xy(self, local: int) -> tuple[int, int]:
        base = self._sym("gObjectEvents")
        for i in range(OBJECT_EVENTS_COUNT):
            addr = base + i * OBJECT_EVENT_SIZE
            if self.emu.read_u8(addr) & 1 and self.emu.read_u8(addr + OBJECT_EVENT_LOCAL_ID) == local:
                return (self.emu.read_u16(addr + OBJECT_EVENT_XY) - MAP_OFFSET,
                        self.emu.read_u16(addr + OBJECT_EVENT_XY + 2) - MAP_OFFSET)
        raise AssertionError(f"objeto {local} não está no mapa")

    def _to_scene(self, party: tuple[tuple[str, int], ...], gemeos_vencidos: bool) -> None:
        """Na sala do Dom, um passo antes do gatilho (o tile da saída da escada), com o time `party`."""
        self._restore("familia_base")
        for slot, (species, level) in enumerate(party):
            self.box.set_party_mon(slot, self._sp(species), level)
        self.box.party_size(len(party))
        self.box.set_flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS"), gemeos_vencidos)
        self.box.set_flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS"), gemeos_vencidos)
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_6F", SAIDA_ESCADA_6F)

    def _gatilho(self) -> None:
        """Um passo para baixo, da saída da escada para o gatilho da cena (4, 4), e a cena começa."""
        self.nav.step("down")
        self.ctl.wait_until(self.ctl.script_active, 60, "cena do 6º andar")

    def _gemeos_um(self) -> str:
        """Com 1 Pokémon só: o chefe fala, os gêmeos recusam a dupla ("Os gêmeos só lutam em dupla.") e nada começa;
        o jogador anda de novo e tudo fica como estava."""
        self._to_scene((("MEWTWO", 100),), False)
        self._gatilho()
        msgs = self._scene(self.ctl.overworld_idle, "recusa dos gêmeos")
        assert not self.game.in_battle(), "começou uma batalha com 1 Pokémon"
        want = self._rom_text("Route23_FamiliaSombra_6F_Text_SoEmDupla")
        assert want in msgs, f"sem a recusa; mensagens {msgs}"
        dom = self._rom_text("Route23_FamiliaSombra_6F_Text_Dom").split("\n")[0]
        assert any(m.startswith(dom) for m in msgs), f"sem a fala do Dom: {msgs}"
        assert not self.game.flag(self._trainer_flag("TRAINER_FAMILIA_GEMEOS"))
        assert not self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS"))
        assert self.box.familia_estado()[:2] == (1, ESTADO_ATIVA)
        assert self.nav.step("up") == 1, "o jogador ficou preso depois da recusa"
        return f"recusa {want!r}; sem batalha; gêmeos e chefe no lugar; o jogador anda"

    def _chefe_fuga(self) -> str:
        """Gêmeos já vencidos: a cena vai direto ao chefe. Fugindo, o chefe fica (objeto, estado ATIVA, sem queda nem
        rosa) e os gêmeos não voltam."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        objs = sorted(self._active_objects())
        assert objs == [1], f"gêmeos vencidos voltaram: {objs}"
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA_CHEFE and not flags & 1, f"gBattleTypeFlags {flags:#x}"
        assert self.driver.run_away(), "não fugiu do chefe"
        msgs = self._scene(self.ctl.overworld_idle, "volta da fuga")
        assert any(self._rom_text("Route23_FamiliaSombra_6F_Text_FugaDom") in m for m in msgs), msgs
        assert self.box.familia_estado() == (1, ESTADO_ATIVA, 0), self.box.familia_estado()
        assert sorted(self._active_objects()) == [1], self._active_objects()
        assert not self.game.flag(self._flag("FLAG_FAMILIA_ROSA_1"))
        assert self.game.bag_quantity(self.consts.item("ITEM_ROSA_VERMELHA")) == 0
        return "direto ao chefe (gêmeos vencidos); fugiu: chefe no lugar, ATIVA, sem rosa"

    def _rosa(self) -> str:
        """A cena inteira: o Dom fala, a dupla dos gêmeos (vencida), o Dom fala de novo, a luta (vencida): a queda
        conta, a Rosa Vermelha vai para a bolsa com FLAG_FAMILIA_ROSA_1 e a sala esvazia."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), False)
        self._set_half_day(QUEDA_ROSA)
        for slot in (0, 1):
            for i in range(4):
                self.box.set_party_move(slot, i, self.moves["MOVE_PSYCHIC"])
        self._gatilho()
        self._scene(self.game.in_battle, "começo da dupla")
        assert self.driver.battle_type_flags() & 1, "os gêmeos não lutaram em dupla"
        assert self.driver.fight_to_end() == "win", "perdeu para os gêmeos"
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.game.flag(self._flag("FLAG_FAMILIA_GEMEOS_VENCIDOS")), "gêmeos vencidos sem a flag"
        assert self.driver.fight_to_end() == "win", "perdeu para o Dom"
        half = self._half_day()
        assert half == QUEDA_ROSA, half
        msgs = self._scene(self.ctl.overworld_idle, "a rosa", shot=("Rosa Vermelha", "familia_rosa"))
        rosa = self.consts.item("ITEM_ROSA_VERMELHA")
        assert self.game.bag_quantity(rosa) == 1, f"Rosa Vermelha na bolsa: {self.game.bag_quantity(rosa)}"
        assert self.game.flag(self._flag("FLAG_FAMILIA_ROSA_1"))
        assert self.box.familia_estado() == (1, ESTADO_SEM_CHEFE, half), self.box.familia_estado()
        assert self._active_objects() == [], self._active_objects()
        drop = self._rom_text("Route23_FamiliaSombra_6F_Text_RosaDom")
        assert drop in msgs, msgs
        return f"gêmeos e Dom vencidos; {drop!r}; Rosa Vermelha na bolsa; SEM_CHEFE na queda {half}"

    # --- Task 7: conquistas e diário -------------------------------------------------------------------
    def _conq(self, cid: str) -> int:
        return self.box.conq_estado(cq.num(cid))[0]

    def _tela_pronta(self, what: str) -> tuple[int, int, int, bool]:
        self.ctl.wait_until(lambda: (s := self.box.conq_tela()) is not None and s[3], TELA_PRONTA_TIMEOUT, what)
        self.emu.frames(TELA_ASSENTA)
        return self.box.conq_tela()

    def _fechar_tela(self) -> None:
        self.ctl.press_until(KEY_B, lambda: self.box.conq_tela() is None, "B fecha a tela de conquistas",
                             tries=3, wait=60)
        self.ctl.wait_overworld_idle(600)

    def _conquista_dom(self) -> str:
        """O jogo já zerado e o Dom vencido pela cena de verdade: a conquista e a entrada do diário (com o título)."""
        self._to_scene((("MEWTWO", 100), ("SNORLAX", 100)), True)
        self.box.conq_reset(True)
        self.box.set_flag(self._flag("FLAG_SYS_GAME_CLEAR"), True)   # a sala é do pós-jogo: o diário não depende do Hall
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        assert [self._conq(c) for c in ("familia_dom", "familia_cobrador", "familia_pedagio")] == [CONQ_PENDENTE] * 3
        assert self.box.diario_entrada(cq.evento("familia_dom")) is None
        self._gatilho()
        self._scene(self.game.in_battle, "começo da batalha do chefe")
        assert self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self._conq("familia_dom") == CONQ_PENDENTE, "feita antes de vencer"
        assert self.driver.fight_to_end() == "win", "perdeu para o Dom"
        self._scene(self.ctl.overworld_idle, "a rosa")
        assert self._conq("familia_dom") == CONQ_FEITA, "Vencer o Dom não ficou feita"
        outras = [self._conq(c) for c in ("familia_cobrador", "familia_pedagio", "familia_mercenario", "familia_toda")]
        assert outras == [CONQ_PENDENTE] * 4, outras
        e = self.box.diario_entrada(cq.evento("familia_dom"))
        assert e is not None, "o Dom vencido e o diário vazio"
        assert e["resultado"] == DIARIO_DERROTOU and e["turnos"] >= 1, e
        assert e["time"] == [(self._sp("MEWTWO"), 100), (self._sp("SNORLAX"), 100)], e
        assert self.box.diario_entrada(cq.evento("familia_cobrador")) is None
        titulo = cq.dados()["diario"][cq.evento("familia_dom")]
        assert titulo["nome"] == "O Dom" and titulo["especie"] == "SPECIES_GENGAR", titulo
        # a tela de conquistas, na aba Batalha rolada até o fim, e o diário com a entrada
        self.box.open_conquistas()
        self._tela_pronta("tela de conquistas")
        self.ctl.press_until(KEY_R, lambda: self.box.conq_tela()[1] == CONQ_BATALHA_ABA, "R: aba Batalha",
                             tries=3, wait=10)
        for _ in range(DESCE_ATE_O_FIM):
            self.emu.press(KEY_DOWN, hold=2, release=6)
        self.emu.frames(TELA_ASSENTA)
        shot_conq = self._shot("familia_conquistas_batalha")
        self._fechar_tela()
        self.box.open_conquistas(True)
        self._tela_pronta("tela do diário")
        shot_diario = self._shot("familia_diario_dom")
        self._fechar_tela()
        return (f"Dom vencido com o jogo zerado: Vencer o Dom feita, as outras 4 pendentes; diário: {titulo['nome']!r} "
                f"derrotado em {e['turnos']} turnos, time {len(e['time'])}; telas {shot_conq} e {shot_diario}")

    def _gengar_fora(self) -> str:
        """Um Gengar selvagem comum (fora da sala do Dom, sem BATTLE_TYPE_FAMILIA_CHEFE) não grava nada."""
        self._restore("familia_base")
        self.box.conq_reset(True)
        self.box.set_flag(self._flag("FLAG_SYS_GAME_CLEAR"), True)
        self.box.set_party_mon(0, self._sp("MEWTWO"), 100)
        for i in range(4):
            self.box.set_party_move(0, i, self.moves["MOVE_PSYCHIC"])
        assert self.box.call(CMD_START_WILD_BATTLE, self._sp("GENGAR"), 62) == 1, "START_WILD_BATTLE"
        self.driver.wait_battle_start()
        assert not self.driver.battle_type_flags() & BATTLE_TYPE_FAMILIA_CHEFE
        assert self.driver.fight_to_end() == "win", "perdeu para o Gengar selvagem"
        self.ctl.wait_until(lambda: not self.game.in_battle(), 900, "volta ao campo")
        self.ctl.wait_overworld_idle(900)
        assert self.box.diario_entrada(cq.evento("familia_dom")) is None, "o Gengar selvagem entrou como o Dom"
        assert self._conq("familia_dom") == CONQ_PENDENTE
        return "Gengar selvagem nv 62 vencido: sem entrada do Dom no diário e a conquista pendente"

    def _encontro_andar4(self) -> str:
        """Passos de verdade no 4º andar com chefe ativo: sai um capanga do plantel (BATTLE_TYPE_FAMILIA)."""
        self._restore("familia_base")
        group, num = self.consts.map("MAP_ROUTE23_FAMILIA_SOMBRA_4F")
        self.box.call(CMD_WARP, group | num << 8, VAI_E_VEM_4F[0][0] | VAI_E_VEM_4F[0][1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para o 4º andar")
        self.ctl.wait_until(lambda: self.ctl.overworld_idle() or self.game.in_battle(), 900, "4º andar")
        steps = self._walk_until_battle(PASSOS_ANDAR)
        assert self.game.in_battle(), f"nenhum encontro em {PASSOS_ANDAR} passos no 4º andar"
        self._wait_intro("gText_FamiliaCapangaQuerLutar", (1,))
        flags = self.driver.battle_type_flags()
        assert flags & BATTLE_TYPE_FAMILIA and not flags & BATTLE_TYPE_TRAINER, f"gBattleTypeFlags {flags:#x}"
        plantel = times_table("sFamiliaPlantel")[0]
        species, level = self.driver.battler_species_level(1)
        assert any(self._sp(m[0]) == species for m in plantel) and 54 <= level <= 58, (species, level)
        return f"encontro no passo {steps}: {self.consts.species_name(species)} nv {level}"

    def _sem_encontro(self) -> str:
        """Sem chefe, o 4º andar fica vazio: nenhum item e nenhum encontro em PASSOS_ANDAR passos."""
        self._restore("familia_base")
        self.box.familia_set(1, ESTADO_SEM_CHEFE, self._half_day())
        self._warp("MAP_ROUTE23_FAMILIA_SOMBRA_4F", VAI_E_VEM_4F[0])
        assert self._active_objects() == [], f"objetos no 4º andar sem chefe: {self._active_objects()}"
        steps = self._walk_until_battle(PASSOS_ANDAR)
        assert not self.game.in_battle() and steps == PASSOS_ANDAR, steps
        return f"{steps} passos sem encontro e sem itens"

    def _walk_until_battle(self, limit: int) -> int:
        steps, k = 0, 0
        while steps < limit and not self.game.in_battle():
            # o encontro começa no fim de um passo e a batalha demora uns quadros para aparecer
            self.ctl.wait_until(lambda: self.ctl.overworld_idle() or self.game.in_battle(), 600, "4º andar livre")
            if self.game.in_battle():
                break
            direction = VAI_E_VEM_4F[1][k % 2]
            moved = self.nav.step(direction, 4)
            steps += moved
            k += 1
            if self.nav.interrupted == "battle" or self.game.in_battle():
                break
        return steps

    def run(self) -> None:
        try:
            self._flow("familia: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("familia/capanga_apresentacao", self._capanga)
            self.suite.run("familia/bola_capanga", self._ball)
            self.suite.run("familia/vitoria_sem_premio", self._win)
            self.suite.run("familia/thief", self._thief)
            self.suite.run("familia/time_por_ocupacao", self._teams)
            self.suite.run("familia/gemeos_dupla", self._twins)
            self.suite.run("familia/encontro_wild", self._encontro)
            self.suite.run("familia/passos_andar_escuro", self._passos)
            self.suite.run("familia/bola_selvagem", self._wild_ball)
            self.suite.run("familia/thief_selvagem", self._wild_thief)
            self.suite.run("familia/chefe", self._chefe)
            self.suite.run("familia/bola_chefe", self._chefe_ball)
            self.suite.run("familia/chefe_ia", self._chefe_ia)
            self.suite.run("familia/porta_trancada", self._porta)
            self.suite.run("familia/ciclo", self._ciclo)
            self.suite.run("familia/capanga_ve", self._capanga_ve)
            self.suite.run("familia/subida", self._subida)
            self.suite.run("familia/encontro_andar4", self._encontro_andar4)
            self.suite.run("familia/sem_encontro_sem_chefe", self._sem_encontro)
            self.suite.run("familia/gemeos_um_pokemon", self._gemeos_um)
            self.suite.run("familia/chefe_fuga", self._chefe_fuga)
            self.suite.run("familia/rosa", self._rosa)
            self.suite.run("familia/conquista_dom", self._conquista_dom)
            self.suite.run("familia/gengar_fora_nao_conta", self._gengar_fora)
            self.suite.run("familia/pedagio_paga", self._pedagio_paga)
            self.suite.run("familia/pedagio_sem_dinheiro", self._pedagio_sem_dinheiro)
            self.suite.run("familia/pedagio_forca", self._pedagio_forca)
            self.suite.run("familia/pedagio_volta", self._pedagio_volta)
            self.suite.run("familia/pedagio_sem_chefe", self._pedagio_sem_chefe)
        except Abort:
            pass


def run_full_familia(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FamiliaScenario(ctx_test).run()
