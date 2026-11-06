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

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only familia
"""

import importlib.util
import re

from ..battle import ACTION_FIGHT, MENU_TIMEOUT, MOVE_FUNC_SUFFIX, BattleDriver
from ..breeding import header_defines
from ..game import POKEMON_SIZE, mon_checksum_ok
from ..hooks import CMD_GIVE_ITEM, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

ESTADO_ATIVA = 1                     # FAMILIA_ESTADO_ATIVA (include/constants/familia_sombra.h)
ESTADO_SEM_CHEFE = 2                 # FAMILIA_ESTADO_SEM_CHEFE
PASSOS = 400                         # passos do caso familia/passos_andar_escuro
SPRITE_SIZE, SPRITE_CALLBACK, SPRITE_DATA, SPRITE_IN_USE = 0x44, 0x1C, 0x2E, 0x3E   # struct Sprite
MAX_SPRITES = 64
# o Pokémon do oponente que aparece direto (OpponentHandleLoadMonSprite → SpriteCB_EnemyMon e seguintes)
WILD_MON_CALLBACKS = {"SpriteCB_EnemyMon", "SpriteCB_MoveWildMonToRight", "SpriteCB_WildMonShowHealthbox",
                      "SpriteCallbackDummy_2"}
TRAINER_SLIDE = "SpriteCB_TrainerSlideIn"
STRING_BYTES = 300                   # gDisplayedStringBattle[300]
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
        except Abort:
            pass


def run_full_familia(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    FamiliaScenario(ctx_test).run()
