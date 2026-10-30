"""Modo completo: clima sempre visível na batalha (POK-15), na build de teste.

O módulo src/battle_weather_visual.c mostra o clima da batalha o tempo todo: gotas de chuva,
pedrinhas de granizo e grãos de areia (sprites) ou o tom quente do sol, e esconde tudo durante as
animações. O estado fica em gBattleWeatherVisual (include/battle_weather_visual.h). Sessão própria
da ROM de teste a partir do .sav do `captura` (`save_from="captura"`); a batalha é selvagem pelo
atalho START_WILD_BATTLE (Pikachu nível 5, Magikarp nível 50 na frente para o turno não derrubar
ninguém) e o clima é escrito direto em gBattleWeather:

- `clima_batalha/<clima>` (chuva, granizo, areia, sol): estado e número de partículas certos, só
  partículas do clima atual (tela `clima_<clima>`);
- `clima_batalha/golpe`: com chuva, um turno de Splash: nada do clima durante a animação, as 10
  gotas de volta depois;
- `clima_batalha/troca_no_meio`: areia → chuva sem grão de areia sobrando;
- `clima_batalha/bolsa_e_volta`: com chuva, abre a BOLSA e fecha: 10 gotas, não 20;
- `clima_batalha/cena_desligada`: "Animação de batalha" desligada → nada;
- `clima_batalha/fim_da_batalha`: foge com chuva → no campo, nenhum sprite do módulo.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only clima_batalha
"""

from ..battle import ACTION_BAG, ACTION_FIGHT, ACTION_FUNC, MOVE_FUNC_SUFFIX
from ..emu import KEY_B
from . import ScenarioContext
from .base import Abort
from .full_weather import LEAD_LEVEL, LEAD_SPECIES, WeatherScenario

# include/battle_weather_visual.h
BWV_NONE, BWV_RAIN, BWV_HAIL, BWV_SAND, BWV_SUN = range(5)
VIS_SHOWN, VIS_COUNT = 0, 1
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
        self._shot(f"clima_{name}")
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

    def _bag(self) -> str:
        self._set_battle_weather(CLIMAS["chuva"][0])
        d = self.driver
        d._choose_action(ACTION_BAG)
        d.bag.wait_ready()
        self.ctl.press_until(KEY_B, lambda: d.controller_func() == ACTION_FUNC, "volta da BOLSA")
        self.emu.frames(30)
        return "BOLSA aberta e fechada; " + self._expect("chuva")

    def _scene_off(self) -> str:
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
            self._flow("clima_batalha/bolsa_e_volta: a chuva volta sem duplicar", self._bag)
            self._flow("clima_batalha/cena_desligada: animação desligada esconde o clima", self._scene_off)
            self._flow("clima_batalha/fim_da_batalha: nada sobra no campo", self._end)
        except Abort:
            pass


def run_full_battle_weather_visual(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    BattleWeatherVisualScenario(ctx_test).run()
