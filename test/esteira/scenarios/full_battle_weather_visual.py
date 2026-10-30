"""Modo completo: clima sempre visível na batalha (POK-15), na build de teste.

O módulo src/battle_weather_visual.c mostra o clima da batalha o tempo todo: gotas de chuva,
pedrinhas de granizo e grãos de areia (sprites) ou o tom quente do sol, e esconde tudo durante as
animações. O estado fica em gBattleWeatherVisual (include/battle_weather_visual.h). Sessão própria
da ROM de teste a partir do .sav do `captura` (`save_from="captura"`); a batalha é selvagem pelo
atalho START_WILD_BATTLE (Pikachu nível 5, Magikarp nível 50 na frente para o turno não derrubar
ninguém) e o clima é escrito direto em gBattleWeather:

- `clima_batalha/<clima>` (chuva, granizo, areia, sol): estado e número de partículas certos, só
  partículas do clima atual (tela `batalha_clima_<clima>`);
- `clima_batalha/golpe`: com chuva, um turno de Splash: nada do clima durante a animação, as 10
  gotas de volta depois;
- `clima_batalha/troca_no_meio`: areia → chuva sem grão de areia sobrando;
- `clima_batalha/bolsa_e_volta`: com chuva, abre a BOLSA e fecha: 10 gotas, não 20;
- `clima_batalha/cena_desligada`: "Animação de batalha" desligada → nada;
- `clima_batalha/fim_da_batalha`: foge com chuva → no campo, nenhum sprite do módulo.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only clima_batalha
"""

from ..battle import ACTION_BAG, ACTION_FIGHT, ACTION_FUNC, MOVE_FUNC_SUFFIX, NICKNAME_COMMAND
from ..emu import KEY_B, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP
from ..hooks import CMD_GIVE_ITEM
from . import ScenarioContext
from .base import Abort
from .full_weather import LEAD_LEVEL, LEAD_SPECIES, WeatherScenario

# include/battle_weather_visual.h
BWV_NONE, BWV_RAIN, BWV_HAIL, BWV_SAND, BWV_SUN = range(5)
VIS_SHOWN, VIS_COUNT, VIS_SPRITE_IDS, VIS_SUN_APPLIED = 0, 1, 2, 14
BATTLER0_PAL = 16                 # paleta de sprite do batalhador 0 (OBJ 0)
MAIN_VBLANK_CALLBACK = 0x0C       # gMain.vblankCallback (include/main.h)
PIKACHU_NATIONAL = 25
SB2_DEX_OWNED, SB2_DEX_SEEN = 0x18 + 0x10, 0x18 + 0x44   # struct Pokedex em SaveBlock2 + 0x18
SB1_DEX_SEEN_COPIES = (0x5F8, 0x3A18)
CLIMAS = {   # nome: (gBattleWeather, BWV_*, partículas, callback das partículas)
    "chuva": (0x5, BWV_RAIN, 10, "SpriteCB_RainDrop"),
    "granizo": (0x180, BWV_HAIL, 8, "SpriteCB_Hail"),
    "areia": (0x18, BWV_SAND, 10, "SpriteCB_Sand"),
    "sol": (0x60, BWV_SUN, 0, None),
}
CALLBACKS = [cb for *_, cb in CLIMAS.values() if cb]
SPRITE_SIZE, MAX_SPRITES = 0x44, 64          # struct Sprite (include/sprite.h)
SPRITE_CALLBACK, SPRITE_IN_USE = 0x1C, 0x3E
SB2_OPTIONS_HI = 0x15                         # optionsBattleSceneOff = bit 2 (include/global.h)
SCENE_OFF_BIT = 1 << 2
SETTLE = 3


class BattleWeatherVisualScenario(WeatherScenario):
    # --- leituras ------------------------------------------------------------------
    def _vis(self) -> tuple[int, int]:
        base = self.game.syms.addr("gBattleWeatherVisual")
        return self.emu.read_u8(base + VIS_SHOWN), self.emu.read_u8(base + VIS_COUNT)

    def _particles(self) -> dict[str, int]:
        """Sprites vivos de cada callback do módulo."""
        sprites = self.game.syms.addr("gSprites")
        addrs = {self.game.syms.addr(cb) & ~1: cb for cb in CALLBACKS}
        out = dict.fromkeys(CALLBACKS, 0)
        for i in range(MAX_SPRITES):
            s = sprites + i * SPRITE_SIZE
            if self.emu.read_u16(s + SPRITE_IN_USE) & 1:
                cb = addrs.get(self.emu.read_u32(s + SPRITE_CALLBACK) & ~1)
                if cb:
                    out[cb] += 1
        return out

    def _set_battle_weather(self, value: int) -> None:
        self.emu.write(self.game.syms.addr("gBattleWeather"), value.to_bytes(2, "little"))
        self.emu.frames(SETTLE)

    def _expect(self, name: str) -> str:
        _, bwv, count, cb = CLIMAS[name]
        assert self._vis() == (bwv, count), f"{name}: gBattleWeatherVisual = {self._vis()}, esperava {(bwv, count)}"
        parts = self._particles()
        want = {c: (count if c == cb else 0) for c in CALLBACKS}
        assert parts == want, f"{name}: partículas {parts}, esperava {want}"
        return f"{name}: {count} partículas"

    # --- passos --------------------------------------------------------------------
    def _battle(self) -> str:
        self.box.set_party_mon(0, self.consts.species(LEAD_SPECIES), LEAD_LEVEL)
        self.driver = self._start_wild_battle()
        self.driver.wait_action_menu()
        self.emu.frames(30)
        assert self._vis() == (BWV_NONE, 0), f"sem clima: {self._vis()}"
        return "batalha selvagem aberta, sem clima e sem partículas"

    def _weather(self, name: str) -> str:
        self._set_battle_weather(CLIMAS[name][0])
        detail = self._expect(name)
        self._shot(f"batalha_clima_{name}")
        return detail

    def _move(self) -> str:
        self._set_battle_weather(CLIMAS["chuva"][0])
        d = self.driver
        d._choose_action(ACTION_FIGHT)
        self.ctl.wait_until(lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX), 300, "menu de golpes")
        d._choose_first_move_with_pp()
        anim_addr = self.game.syms.addr("gAnimScriptActive")
        during, frames = set(), 0
        for _ in range(1200):
            self.emu.frames(1)
            if self.emu.read_u8(anim_addr):
                frames += 1
                during.add(self._vis())
            if d.controller_func() == ACTION_FUNC:
                break
        self.emu.frames(SETTLE)
        assert frames > 0, "o turno não teve animação"
        assert during == {(BWV_NONE, 0)}, f"durante a animação: {during}"
        return f"{frames} quadros de animação sem clima; " + self._expect("chuva")

    def _swap(self) -> str:
        self._set_battle_weather(CLIMAS["areia"][0])
        before = self._expect("areia")
        self._set_battle_weather(CLIMAS["chuva"][0])
        return f"{before} → " + self._expect("chuva")

    def _fade(self) -> tuple[int, bool]:
        """(y, active) de gPaletteFade (include/palette.h: y:5 nos bits 6-10 do u16 em +4,
        active no bit 15 do u16 em +6)."""
        base = self.game.syms.addr("gPaletteFade")
        return (self.emu.read_u16(base + 4) >> 6) & 31, bool(self.emu.read_u16(base + 6) >> 15)

    def _tinted(self) -> bool:
        return bool(self.emu.read_u8(self.game.syms.addr("gBattleWeatherVisual") + VIS_SUN_APPLIED))

    def _bag(self) -> str:
        """Revisão, achado 2: no quadro em que o fade para preto acaba, antes de a BOLSA abrir, o
        clima (tom e partículas) não pode voltar."""
        self._set_battle_weather(CLIMAS["chuva"][0])
        d = self.driver
        d._choose_action(ACTION_BAG)
        dark = 0
        for _ in range(600):
            self.emu.frames(1)
            y, _ = self._fade()
            if y != 0:
                dark += 1
                assert self._vis()[0] == BWV_NONE and not self._tinted(), (
                    f"tela apagada (y = {y}) com o clima na tela: {self._vis()}, tom {self._tinted()}")
            if d.bag.ready():
                break
        assert dark > 0, "não vi o fade para preto da BOLSA"
        self.ctl.press_until(KEY_B, lambda: d.controller_func() == ACTION_FUNC, "volta da BOLSA")
        self.emu.frames(30)
        return f"{dark} quadros de tela apagada sem clima; BOLSA aberta e fechada; " + self._expect("chuva")

    def _move_cursor(self) -> str:
        """Revisão, achado 3: mexer o cursor no menu de golpes (fade 0→0) não recria o clima."""
        self._set_battle_weather(CLIMAS["areia"][0])
        base = self.game.syms.addr("gBattleWeatherVisual")
        ids = self.emu.read(base + VIS_SPRITE_IDS, 10)
        d = self.driver
        d._choose_action(ACTION_FIGHT)
        self.ctl.wait_until(lambda: d.controller_func().endswith(MOVE_FUNC_SUFFIX), 300, "menu de golpes")
        for key in (KEY_RIGHT, KEY_DOWN, KEY_LEFT, KEY_UP) * 2:
            self.emu.press(key, hold=2, release=2)
            for _ in range(8):
                self.emu.frames(1)
                assert self._vis() == (BWV_SAND, 10), f"cursor: {self._vis()}"
        assert self.emu.read(base + VIS_SPRITE_IDS, 10) == ids, "as partículas foram recriadas"
        self.ctl.press_until(KEY_B, lambda: d.controller_func() == ACTION_FUNC, "volta do menu de golpes")
        return "8 movimentos do cursor: as mesmas 10 partículas de areia o tempo todo"

    def _switch_in_tint(self) -> str:
        """Revisão, achado 5: Pokémon que entra (LoadPalette nos dois buffers) recebe o tom do sol
        no quadro seguinte. Simulado copiando Unfaded → Faded na paleta do batalhador 0."""
        self._set_battle_weather(CLIMAS["sol"][0])
        unf = self.game.syms.addr("gPlttBufferUnfaded") + BATTLER0_PAL * 32
        fad = self.game.syms.addr("gPlttBufferFaded") + BATTLER0_PAL * 32
        tinted = self.emu.read(fad, 32)
        assert tinted != self.emu.read(unf, 32), "o batalhador 0 não estava com o tom do sol"
        self.emu.write(fad, self.emu.read(unf, 32))
        self.emu.frames(2)
        assert self.emu.read(fad, 32) == tinted, "o tom não voltou para o batalhador que entrou"
        return "paleta do batalhador 0 sem o tom → tingida de novo em 2 quadros"

    def _capture_dex(self) -> str:
        """Revisão, achado 1: capturar espécie nova com chuva: na página da Pokédex (outro VBlank
        dentro do BattleMainCB2) não há partícula nem tom."""
        self.driver = self._start_wild_battle()
        self.driver.wait_action_menu()
        self._set_dex_owned(PIKACHU_NATIONAL, False)
        assert self.box.call(CMD_GIVE_ITEM, self.consts.item("ITEM_MASTER_BALL"), 1) == 1
        self._set_battle_weather(CLIMAS["chuva"][0])
        vblank_battle = self.game.syms.addr("VBlankCB_Battle") & ~1
        main = self.game.syms.addr("gMain")
        d, other = self.driver, [0]

        def watch() -> None:
            if self.emu.read_u32(main + MAIN_VBLANK_CALLBACK) & ~1 != vblank_battle:
                other[0] += 1
                assert self._vis()[0] == BWV_NONE and not self._tinted(), f"na Pokédex: {self._vis()}"
                assert not any(self._particles().values()), f"na Pokédex: {self._particles()}"

        d._open_bag_on_item(self.consts.item("ITEM_MASTER_BALL"))
        d.bag.use_selected()
        result = d._advance_until_menu_or_end("captura", 6000,
                                              stop=lambda: d._script_command() == NICKNAME_COMMAND,
                                              on_step=watch)
        assert result in ("stop", "end"), f"captura: {result}"
        assert other[0] > 0, "não vi a página da Pokédex"
        self.ctl.press_until(KEY_B, lambda: not self.game.in_battle(), "fim da batalha da captura", )
        return f"{other[0]} quadros na página da Pokédex sem clima"

    def _set_dex_owned(self, national: int, value: bool) -> None:
        byte, bit = (national - 1) // 8, (national - 1) % 8
        sb1, sb2 = self.game._sb1(), self.game._sb2()
        for addr in (sb2 + SB2_DEX_SEEN + byte, sb1 + SB1_DEX_SEEN_COPIES[0] + byte,
                     sb1 + SB1_DEX_SEEN_COPIES[1] + byte, sb2 + SB2_DEX_OWNED + byte):
            v = self.emu.read_u8(addr)
            self.emu.write(addr, bytes([(v | 1 << bit) if value else (v & ~(1 << bit) & 0xFF)]))

    def _scene_off(self) -> str:
        self._set_battle_weather(CLIMAS["chuva"][0])
        options = self.game._sb2() + SB2_OPTIONS_HI
        old = self.emu.read_u8(options)
        self.emu.write(options, bytes([old | SCENE_OFF_BIT]))
        self.emu.frames(SETTLE)
        try:
            assert self._vis() == (BWV_NONE, 0), f"animação desligada: {self._vis()}"
            assert not any(self._particles().values()), self._particles()
        finally:
            self.emu.write(options, bytes([old]))
            self.emu.frames(SETTLE)
        return "animação desligada: nada; religada: " + self._expect("chuva")

    def _end(self) -> str:
        self._set_battle_weather(CLIMAS["chuva"][0])
        self._leave_battle(self.driver, "chuva")
        assert self._vis()[0] == BWV_NONE, f"no campo: {self._vis()}"
        assert not any(self._particles().values()), f"no campo: {self._particles()}"
        return "fugiu com chuva; no campo nenhum sprite do módulo"

    def run(self) -> None:
        try:
            self._flow("clima_batalha: CONTINUAR com o save do modo rápido", self._start)
            self._flow("clima_batalha/abertura: batalha selvagem sem clima", self._battle)
            for name in CLIMAS:
                self._flow(f"clima_batalha/{name}: efeito contínuo",
                           lambda name=name: self._weather(name))
            self._flow("clima_batalha/golpe: some na animação e volta", self._move)
            self._flow("clima_batalha/troca_no_meio: areia → chuva sem sobras", self._swap)
            self._flow("clima_batalha/bolsa_e_volta: a chuva volta sem duplicar nem piscar", self._bag)
            self._flow("clima_batalha/cursor_golpes: o cursor do menu de golpes não recria o clima",
                       self._move_cursor)
            self._flow("clima_batalha/entra_tingido: o Pokémon que entra recebe o tom do sol",
                       self._switch_in_tint)
            self._flow("clima_batalha/cena_desligada: animação desligada esconde o clima", self._scene_off)
            self._flow("clima_batalha/fim_da_batalha: nada sobra no campo", self._end)
            self._flow("clima_batalha/captura_dex: a página da Pokédex fica sem clima", self._capture_dex)
        except Abort:
            pass


def run_full_battle_weather_visual(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    BattleWeatherVisualScenario(ctx_test).run()
