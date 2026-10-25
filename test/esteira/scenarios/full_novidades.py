"""Modo completo: tela de novidades do Prof. Carvalho (src/novidades.c).

Dois cenários:

`novidades` (ROM de teste, sessão própria a partir do .sav do `captura`):
1. CONTINUAR, warp para o laboratório diante do Carvalho e foto do campo (mapa, posição, música,
   objetos do mapa);
2. fala de verdade com o Carvalho (a avaliação da Pokédex roda inteira) e SIM na oferta: a tela abre
   na grade, com os 11 ícones vivos (atalho 0x91); tela `novidades_grade`;
3. grade: ◀ e ▲ no tópico 0 não mexem; ▶ e ▼ no último também não; o caminho de um tópico ao
   próximo segue a regra do cursor (sem dar a volta; ▼ do 7 vai ao 10), conferida a cada tecla;
4. em cada um dos 11 tópicos (o espelho do plano vem do JSON dos cartões): A abre no 1º cartão;
   ◀ no 1º não muda o cartão; ▶ vai até o último conferindo, em cada cartão, tópico, cartão, tipo de
   imagem e sprites vivos (atalho 0x92); ▶ no último não muda (o Pós-Liga fica em 1/1); B volta à
   grade com o mesmo tópico e os 11 ícones; telas de um cartão de cada tipo de imagem, da revelação
   dos míticos e de um cartão com ícone novo (CARD_SHOTS);
5. sprites, tiles e paletas de OBJ e matrizes afins iguais na grade antes e depois do percurso;
6. B sai: volta ao campo no mesmo mapa, posição e música, com os mesmos objetos; falar de novo com
   o Carvalho funciona (a oferta volta e NÃO solta o jogador).

`novidades_inicial` (ROM jogável, a partir do checkpoint `abertura` do modo rápido): repete a escolta
e o inicial respondendo SIM à pergunta logo depois do inicial; a tela abre, B volta ao campo com a
var de cena em 3, e a batalha do rival na saída roda normal (var 4 no fim).

Toques de >= 4 quadros e espera do estado mudar antes da próxima tecla: a volta à grade passa de um
quadro e um toque de 2 quadros logo depois do B pode se perder (review-t3, Minor 6).

Uso, a partir de test/ (a pasta OUT precisa do captura.sav e dos estados de um `rapido`):
    python3 -m esteira completo --rom R --elf E --out OUT --only novidades
    python3 -m esteira completo --rom R --elf E --out OUT --only novidades_inicial
"""

import json
import struct
from dataclasses import dataclass

from ..breeding import header_defines
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP
from ..hooks import CMD_NOVIDADES_CARD, CMD_NOVIDADES_STATE, CMD_WARP, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import SCENE_TIMEOUT, TEXT_PERIOD, YESNO_TASK, Abort
from .quick_catch_save import CatchSaveScenario
from .quick_opening import BALL_ROW, STARTER_BALL_X, OpeningScenario
from .quick_route1 import OAK_FRONT

CARTOES = REPO_ROOT / "src" / "data" / "novidades" / "cartoes.json"
LAB = "MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB"
LAB_SCENE_VAR = "VAR_MAP_SCENE_PALLET_TOWN_PROFESSOR_OAKS_LAB"

# Espelho de src/novidades.c (test_novidades_esteira.py confere com o C)
GRID_COLUMNS = 4
TOPIC_COUNT = 11
GRID_ROWS = (TOPIC_COUNT + GRID_COLUMNS - 1) // GRID_COLUMNS
IMAGE_TOPIC_ICON, IMAGE_ITEM, IMAGE_ONE_MON, IMAGE_TWO_MONS = range(4)   # CARD_IMAGE_*
LIVE_SPRITES = {IMAGE_TOPIC_ICON: 1, IMAGE_ITEM: 1, IMAGE_ONE_MON: 1, IMAGE_TWO_MONS: 2}
CLOSED = 0xFFFFFFFF
KEYS = {"left": KEY_LEFT, "right": KEY_RIGHT, "up": KEY_UP, "down": KEY_DOWN}

# Telas comparadas com a referência (test/referencias/COMUM/, não dependem do inicial)
GRID_SHOT = "novidades_grade"
CARD_SHOTS = {                                   # tela -> (tópico, cartão)
    "novidades_cartao_icone": ("ritmo", 0),          # sem imagem: ícone de item do tópico
    "novidades_cartao_icone_novo": ("resumo", 0),    # sem imagem: ícone novo (ficha)
    "novidades_cartao_item": ("shiny", 1),           # ícone de item, com ANTES/AGORA
    "novidades_cartao_especie": ("dia_noite", 2),    # uma espécie
    "novidades_cartao_evolucao": ("evolucoes", 0),   # antes -> depois (duas espécies)
    "novidades_miticos_revelacao": ("lendarios", 4),
}
SCREEN_POINTS = (GRID_SHOT,) + tuple(CARD_SHOTS)

HOLD, RELEASE = 4, 6           # toque de 4 quadros
LIMIT_WAIT = 20                # quadros esperando um ◀/▶/▲/▼ que não deve mudar nada
STEP_TIMEOUT = 120
OPEN_TIMEOUT = 20000           # avaliação da Pokédex inteira + oferta + escurecer
SHOT_SETTLE = 10
SPRITE_SIZE, SPRITE_FLAGS, MAX_SPRITES = 0x44, 0x3E, 64      # struct Sprite (include/sprite.h)
OBJECT_EVENT_SIZE, OBJECT_EVENT_COUNT = 0x24, 16             # gObjectEvents
SB1_VARS, VAR_BASE = 0x1000, 0x4000


@dataclass
class TopicPlan:
    id: str
    titles: list[str]
    kinds: list[int]
    custom_icon: bool


def _card_kind(card: dict) -> int:
    """Mesma escolha de Novidades_ShowCard: duas espécies, uma espécie, item ou o ícone do tópico."""
    if card.get("speciesBefore") and card.get("speciesAfter"):
        return IMAGE_TWO_MONS
    if card.get("speciesBefore"):
        return IMAGE_ONE_MON
    if card.get("itemId"):
        return IMAGE_ITEM
    return IMAGE_TOPIC_ICON


def card_plan() -> list[TopicPlan]:
    topics = json.loads(CARTOES.read_text(encoding="utf-8"))["topics"]
    return [TopicPlan(t["id"], [c["title"] for c in t["cards"]], [_card_kind(c) for c in t["cards"]],
                      bool(t.get("iconCustom"))) for t in topics]


def move_cursor(cursor: int, key: str) -> int:
    """Espelho de Novidades_MoveCursor: sem dar a volta; ▼ para um quadro vazio vai ao último."""
    column, row = cursor % GRID_COLUMNS, cursor // GRID_COLUMNS
    if key == "left" and column > 0:
        return cursor - 1
    if key == "right" and column < GRID_COLUMNS - 1 and cursor + 1 < TOPIC_COUNT:
        return cursor + 1
    if key == "up" and row > 0:
        return cursor - GRID_COLUMNS
    if key == "down":
        if cursor + GRID_COLUMNS < TOPIC_COUNT:
            return cursor + GRID_COLUMNS
        if row < GRID_ROWS - 1:
            return TOPIC_COUNT - 1
    return cursor


def grid_walk(topic: int) -> list[tuple[str, int]]:
    """Teclas do tópico `topic - 1` até `topic` (mesma linha: ▶; linha seguinte: ▼ e ◀ até a
    coluna 0), cada uma com o cursor esperado depois dela."""
    cursor, steps = topic - 1, []
    while cursor != topic:
        key = "right" if cursor // GRID_COLUMNS == topic // GRID_COLUMNS and cursor < topic else (
            "down" if cursor // GRID_COLUMNS < topic // GRID_COLUMNS else "left")
        cursor = move_cursor(cursor, key)
        steps.append((key, cursor))
        if len(steps) > 2 * GRID_COLUMNS:
            raise AssertionError(f"caminho da grade até {topic} não termina: {steps}")
    return steps


def _state_fields(raw: int) -> dict[str, int]:
    return {"cursor": raw & 0xFF, "ready": raw >> 8 & 0xFF, "icons": raw >> 16 & 0xFF,
            "card": (raw >> 24) - 1}   # card -1 = grade


def _card_fields(raw: int) -> dict[str, int]:
    return {"topic": raw & 0xFF, "card": raw >> 8 & 0xFF, "kind": raw >> 16 & 0xFF, "live": raw >> 24}


class NovidadesScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.plan = card_plan()
        self.vars = header_defines(REPO_ROOT, "vars.h")
        self.cursor = 0

    # --- leitura -------------------------------------------------------------------
    def _state(self) -> dict[str, int] | None:
        raw = self.box.call(CMD_NOVIDADES_STATE)
        return None if raw == CLOSED else _state_fields(raw)

    def _card(self) -> dict[str, int] | None:
        raw = self.box.call(CMD_NOVIDADES_CARD)
        return None if raw == CLOSED else _card_fields(raw)

    def _resources(self) -> dict[str, object]:
        """Recursos de OBJ que a tela aloca: sprites em uso, tiles, tags de paleta e matrizes."""
        emu, syms = self.emu, self.game.syms
        raw = emu.read(syms.addr("gSprites"), SPRITE_SIZE * MAX_SPRITES)
        in_use = sum(struct.unpack_from("<H", raw, i * SPRITE_SIZE + SPRITE_FLAGS)[0] & 1
                     for i in range(MAX_SPRITES))
        (pal_addr,) = syms.addrs("sSpritePaletteTags")
        return {"sprites": in_use,
                "tiles": sum(bin(b).count("1") for b in emu.read(syms.addr("gSpriteTileAllocBitmap"), 128)),
                "paletas": sorted(t for t in struct.unpack("<16H", emu.read(pal_addr, 32)) if t != 0xFFFF),
                "matrizes": emu.read_u32(syms.addr("gOamMatrixAllocBitmap"))}

    def _field(self) -> dict[str, object]:
        """Mapa, posição, música e objetos ativos (localId) do campo."""
        raw = self.emu.read(self.game.syms.addr("gObjectEvents"), OBJECT_EVENT_SIZE * OBJECT_EVENT_COUNT)
        objects = sorted(raw[i * OBJECT_EVENT_SIZE + 8] for i in range(OBJECT_EVENT_COUNT)
                         if raw[i * OBJECT_EVENT_SIZE] & 1)
        (music_addr,) = self.game.syms.addrs("sCurrentMapMusic")
        return {"mapa": self.game.location(), "posição": self.game.player_xy(),
                "música": self.emu.read_u16(music_addr), "objetos": objects}

    def _var(self, name: str) -> int:
        return self.emu.read_u16(self.game._sb1() + SB1_VARS + (self.vars[name] - VAR_BASE) * 2)

    # --- botões --------------------------------------------------------------------
    def _tap(self, key: int) -> None:
        self.emu.press(key, hold=HOLD, release=RELEASE)

    def _wait_state(self, pred, what: str) -> dict[str, int]:
        found: dict[str, dict[str, int] | None] = {"s": None}

        def check() -> bool:
            found["s"] = self._state()
            return found["s"] is not None and pred(found["s"])
        self.ctl.wait_until(check, STEP_TIMEOUT, what)
        return found["s"]

    def _wait_card(self, topic: int, card: int) -> dict[str, int]:
        found: dict[str, dict[str, int] | None] = {"c": None}

        def check() -> bool:
            found["c"] = self._card()
            return found["c"] is not None and (found["c"]["topic"], found["c"]["card"]) == (topic, card)
        self.ctl.wait_until(check, STEP_TIMEOUT, f"cartão {card + 1} do tópico {self.plan[topic].id}")
        return found["c"]

    def _shot_settled(self, name: str) -> str:
        self.emu.frames(SHOT_SETTLE)
        path = self._shot(name)
        self.measures.setdefault("shots", {})[name] = path
        return path

    # --- passos --------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="novidades_continue")
        group, num = self.consts.map(LAB)
        self.box.call(CMD_WARP, group | num << 8, OAK_FRONT[0] | OAK_FRONT[1] << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, "warp para o laboratório")
        self.ctl.wait_overworld_idle(600)
        self.emu.frames(30)
        self.measures["field_before"] = self._field()
        assert self._state() is None, "a tela de novidades já estava aberta"
        return f"laboratório diante do Carvalho: {self.measures['field_before']}"

    def _open_by_oak(self) -> str:
        """Fala com o Carvalho, avança a avaliação e responde SIM à oferta das novidades."""
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Carvalho")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da fala do Carvalho")
        offers, spent, in_menu = 0, 0, False
        while "Novidades" not in self.game.callback2():
            if spent >= OPEN_TIMEOUT:
                raise self.ctl.timeout_error("tela de novidades aberta pela fala do Carvalho")
            menu = YESNO_TASK in self._tasks()
            if menu and not in_menu:                     # menu novo (o A pode levar uns toques)
                assert self._novidades_offer(), f"pergunta inesperada: {self._field_message()!r}"
                offers += 1
            in_menu = menu
            self._press(KEY_A)                           # falas e SIM
            spent += TEXT_PERIOD
        assert offers == 1, f"{offers} perguntas das novidades"
        state = self._wait_state(lambda s: s["ready"] and s["card"] < 0, "grade pronta para input")
        assert state["cursor"] == 0, state
        assert state["icons"] == TOPIC_COUNT, f"{state['icons']} ícones vivos na grade"
        self.measures["resources_before"] = self._resources()
        self._shot_settled(GRID_SHOT)
        return f"SIM na oferta: grade com {state['icons']} ícones; recursos {self.measures['resources_before']}"

    def _grid_key(self, key: str, expected: int) -> None:
        self._tap(KEYS[key])
        if expected == self.cursor:
            self.emu.frames(LIMIT_WAIT)
            state = self._state()
            assert state["cursor"] == expected, f"{key} no tópico {self.cursor} levou a {state['cursor']}"
        else:
            self._wait_state(lambda s: s["cursor"] == expected, f"cursor {self.cursor} {key} -> {expected}")
        self.cursor = expected

    def _grid_limits_start(self) -> str:
        for key in ("left", "up"):
            self._grid_key(key, 0)
        return "◀ e ▲ no tópico 0 não mexem o cursor"

    def _topic(self, topic: int) -> str:
        plan = self.plan[topic]
        if topic:
            for key, expected in grid_walk(topic):
                self._grid_key(key, expected)
        assert self.cursor == topic
        last = len(plan.kinds) - 1
        self._tap(KEY_A)
        seen = []
        card = self._wait_card(topic, 0)
        self._tap(KEY_LEFT)                               # limite: ◀ no 1º
        self.emu.frames(LIMIT_WAIT)
        card = self._card()
        assert card["card"] == 0, f"◀ no 1º cartão de {plan.id} foi para o {card['card'] + 1}"
        for index in range(last + 1):
            if index:
                self._tap(KEY_RIGHT)
                card = self._wait_card(topic, index)
            want = plan.kinds[index]
            assert card["kind"] == want, f"{plan.id} {index + 1}/{last + 1}: imagem {card['kind']}, esperava {want}"
            assert card["live"] == LIVE_SPRITES[want], (
                f"{plan.id} {index + 1}/{last + 1}: {card['live']} sprites vivos, esperava {LIVE_SPRITES[want]}")
            state = self._state()
            assert state["card"] == index and state["cursor"] == topic, state
            for name, (shot_topic, shot_card) in CARD_SHOTS.items():
                if (shot_topic, shot_card) == (plan.id, index):
                    self._shot_settled(name)
            seen.append(f"{card['kind']}/{card['live']}")
        self._tap(KEY_RIGHT)                              # limite: ▶ no último
        self.emu.frames(LIMIT_WAIT)
        card = self._card()
        assert card["card"] == last, f"▶ no último cartão de {plan.id} foi para o {card['card'] + 1}"
        self._tap(KEY_B)
        state = self._wait_state(lambda s: s["card"] < 0, f"volta à grade de {plan.id}")
        assert state["cursor"] == topic, f"B voltou à grade no tópico {state['cursor']}, esperava {topic}"
        assert state["ready"] and state["icons"] == TOPIC_COUNT, state
        return f"{last + 1} cartão(ões), tipo/sprites {seen}; limites parados; B volta ao tópico {topic}"

    def _grid_limits_end(self) -> str:
        for key in ("right", "down"):
            self._grid_key(key, TOPIC_COUNT - 1)
        return "▶ e ▼ no último tópico não mexem o cursor"

    def _resources_same(self) -> str:
        after = self._resources()
        assert after == self.measures["resources_before"], (
            f"antes {self.measures['resources_before']}, depois {after}")
        return f"grade antes e depois do percurso: {after}"

    def _leave(self) -> str:
        self._tap(KEY_B)
        self.ctl.wait_until(lambda: self.game.callback2() == "CB2_Overworld", 600, "volta ao campo")
        spent = 0
        while not self._settled_idle():
            if spent >= 600:
                raise self.ctl.timeout_error("campo livre depois da tela")
            self.emu.frames(10)
            spent += 10
        assert self._state() is None, "a tela continua aberta (sNovidades não foi liberado)"
        before, after = self.measures["field_before"], self._field()
        assert after == before, f"antes {before}, depois {after}"
        return f"campo igual: {after}"

    def _talk_again(self) -> str:
        offers = int(self.measures.get("novidades_offers", 0))
        self._talk(KEY_UP, "falar de novo com o Carvalho", OPEN_TIMEOUT)
        assert int(self.measures.get("novidades_offers", 0)) == offers + 1, (
            f"a oferta não veio de novo (última fala: {self._field_message()!r}, campo {self._field()})")
        self._assert_location(LAB)
        return "o Carvalho oferece de novo; NÃO solta o jogador no laboratório"

    def run(self) -> None:
        try:
            self._flow("novidades: CONTINUAR e warp para o laboratório", self._start)
            res = self.suite.run("novidades/abre: fala do Carvalho e SIM abrem a grade", self._open_by_oak)
            if res.status == "falha":
                raise Abort("novidades/abre")
            self._flow("novidades/grade: ◀ e ▲ no 1º tópico", self._grid_limits_start)
            for topic, plan in enumerate(self.plan):
                res = self.suite.run(f"novidades/topico {topic:02d} {plan.id}", lambda t=topic: self._topic(t))
                for name, (shot_topic, _) in CARD_SHOTS.items():
                    if shot_topic == plan.id and name in self.measures.get("shots", {}):
                        res.images.append(self.measures["shots"][name])
                if res.status == "falha":
                    raise Abort(plan.id)
            self.suite.run("novidades/grade: ▶ e ▼ no último tópico", self._grid_limits_end)
            self.suite.run("novidades/recursos: iguais antes e depois do percurso", self._resources_same)
            self._flow("novidades/campo: B volta ao mesmo mapa, posição e música", self._leave)
            self.suite.run("novidades/campo: falar de novo com o Carvalho", self._talk_again)
        except Abort:
            pass


class FirstOfferScenario(OpeningScenario):
    """SIM à pergunta logo depois do inicial (ROM jogável, do checkpoint `abertura`)."""

    PREFIX = "novidades_inicial_"

    def _shot(self, name: str) -> str:
        # não sobrescreve as telas do roteiro rápido (inicial, batalha_rival)
        return super()._shot(self.PREFIX + name)

    def _to_lab(self) -> str:
        self._walk_to_oak_trigger()
        self._escort_to_lab()
        self._intro_lab_scene()
        return "escolta e cena de chegada"

    def _starter_and_yes(self) -> str:
        x = STARTER_BALL_X[self.ctx.starter]
        if not self.nav.walk_to(x, BALL_ROW + 1):
            raise self.ctl.timeout_error(f"caminho até a bola de {self.ctx.starter}")
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante da bola")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "script da bola")
        offer: dict[str, object] = {}
        spent = 0
        while "Novidades" not in self.game.callback2():
            if spent >= SCENE_TIMEOUT:
                raise self.ctl.timeout_error("tela de novidades depois do inicial")
            if YESNO_TASK in self._tasks():
                if not self.game.party():
                    self._press(KEY_A)                   # "Quer o <inicial>?" -> SIM
                elif self._novidades_offer():
                    if not offer:
                        offer = {"var": self._lab_scene_var(), "party": len(self.game.party()),
                                 "shot": self._shot_next_frame("oferta")}
                    self._press(KEY_A)                   # "Quer ver as novidades agora?" -> SIM
                else:
                    self._press(KEY_B)                   # "Dar apelido?" -> NÃO
            else:
                self._press(KEY_A)
            spent += TEXT_PERIOD
        assert offer, "a tela abriu sem a pergunta das novidades"
        assert (offer["var"], offer["party"]) == (3, 1), (
            f"pergunta com var de cena {offer['var']} e {offer['party']} Pokémon (esperava 3 e 1)")
        self.measures["offer_shot"] = offer["shot"]
        self.ctl.wait_until(lambda: "Task_Novidades_HandleInput" in self._tasks(), 600, "grade pronta")
        self.emu.frames(SHOT_SETTLE)
        self.measures["grid_shot"] = self._shot("grade")
        self.emu.press(KEY_B, hold=HOLD, release=RELEASE)
        self.ctl.wait_until(lambda: self.game.callback2() == "CB2_Overworld", 600, "volta ao campo")
        self.ctl.wait_until(self._settled_idle, 600, "campo livre depois da tela")
        self._assert_location(LAB)
        var = self._lab_scene_var()
        assert var == 3, f"var de cena {var} depois da tela, esperava 3"
        assert len(self.game.party()) == 1
        return f"pergunta com var 3 e o {self.ctx.starter} no time; SIM abre a grade; B volta ao laboratório (var 3)"

    def _rival_after(self) -> str:
        outcome = self._rival_battle()
        assert outcome in ("win", "lose"), f"batalha do rival terminou em {outcome!r}"
        assert not self.game.in_battle()
        self._assert_location(LAB)
        var = self._lab_scene_var()
        assert var == 4, f"var de cena {var} depois do rival, esperava 4"
        return f"rival: {outcome}; var de cena 4; overworld livre em {self.game.player_xy()}"

    def run(self) -> None:
        try:
            # no grupo jogável o cenário anterior termina em outro lugar: volta ao quarto
            self.ctl.restore("abertura")
            self._flow("novidades_inicial: escolta até o laboratório", self._to_lab)
            res = self.suite.run("novidades_inicial: SIM logo depois do inicial abre e fecha a tela",
                                 self._starter_and_yes)
            for key in ("offer_shot", "grid_shot"):
                if key in self.measures:
                    res.images.append(self.measures[key])
            if res.status == "falha":
                raise Abort("novidades_inicial")
            res = self.suite.run("novidades_inicial: a cena do rival continua normal", self._rival_after)
            if "battle_shot" in self.measures:
                res.images.append(self.measures["battle_shot"])
        except Abort:
            pass


def run_full_novidades(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    NovidadesScenario(ctx_test).run()


def run_full_novidades_first_offer(ctx: ScenarioContext) -> None:
    """Roda o SIM depois do inicial na ROM jogável, do checkpoint `abertura` (ver módulo)."""
    FirstOfferScenario(ctx).run()
