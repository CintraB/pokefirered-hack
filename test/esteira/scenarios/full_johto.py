"""Modo completo: os 18 de Johto (POK-28), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`), com o aviso das conquistas em
silêncio. Cada caso leva o jogador ao mapa com `CMD_WARP`, acerta o relógio e força o encontro com o gerador real do
jogo (`TEST_CMD_DEXNAV_ROLL`: centenas de encontros de verdade num atalho só, e `TEST_CMD_ROLL_WILD`, que gera um
selvagem e, com `arg1 = 1`, começa a batalha). As expectativas saem de `src/data/wild_encounters*.json`.

Selvagens (Task 2):

- `johto/miltank_de_dia`: Prado da Ilha Cinco. De manhã e à tarde o Miltank sai (10%, nível 30-35); à noite nunca. No
  entardecer (tarde ou noite, meio a meio) ele aparece. Uma batalha de verdade no menu de ação confere espécie e nível;
- `johto/gligar_a_noite`: Cânion Sevault. À noite o Gligar sai (10%, nível 35-40); de manhã e à tarde nunca;
- `johto/chinchou_super_vara`: Rotas 19, 20, 21N e 21S. Super Vara: Chinchou 15% (nível 25-35) e Lanturn 4% (nível
  35-40); a Vara Velha e a Boa nunca dão nenhum dos dois;
- `johto/corsola_surf`: Resort Gorgeous, surfando: Corsola 30% (nível 30-35);
- `johto/girafarig_safari`: Zona Safári Oeste, na grama: Girafarig 4% (nível 25-30), a qualquer hora.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only johto
"""

import json
import struct
import sys
from functools import cache

from .. import dexnav as dnv
from ..hooks import CMD_DEXNAV_ROLL, CMD_ROLL_WILD, CMD_WARP, NO_RESULT, TEXT_SYMBOL, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

MAPS_DIR = REPO_ROOT / "data" / "maps"
WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
DAY = 0
MANHA, TARDE, ENTARDECER, NOITE = 7 * 60, 12 * 60, 18 * 60, 22 * 60   # minutos do dia (período em dia_noite.py)
HORAS = {"manhã": MANHA, "tarde": TARDE, "entardecer": ENTARDECER, "noite": NOITE}
ROLAGENS = 300            # encontros por conferência no atalho (P(falhar) = 0,9^300 ~ 2e-14 para um slot de 10%)
ROLAGENS_RARO = 800       # slots de 4%: 0,96^800 ~ 6e-15
TENTATIVAS_NIVEL = 400    # CMD_ROLL_WILD até sair a espécie, para ler o nível
SLOT_SUPER_VARA = {"Chinchou": 15, "Lanturn": 4}
ROTAS = ("MAP_ROUTE19", "MAP_ROUTE20", "MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH")
AREA_GRAMA, AREA_AGUA, AREA_PEDRA, AREA_PESCA = 0, 1, 2, 3
SUPER_VARA = 2           # SUPER_ROD de include/constants/items.h
WARP_TIMEOUT = 900
ROLAGEM_QUADROS = 30      # quadros por encontro no teto do atalho DEXNAV_ROLL


@cache
def _warp_xy(map_id: str) -> tuple[int, int]:
    """Onde pôr o jogador no mapa: o 1º warp (onde se chega ao entrar por ele) ou, se o mapa não tem warps (Rotas 21
    Norte e Sul, só mar), o centro do layout. O gerador de encontros só olha o mapa, não o tile."""
    layouts = {lay["id"]: lay for lay in json.loads((REPO_ROOT / "data" / "layouts" / "layouts.json")
                                                    .read_text(encoding="utf-8"))["layouts"] if "id" in lay}
    for path in MAPS_DIR.glob("*/map.json"):
        m = json.loads(path.read_text(encoding="utf-8"))
        if m["id"] == map_id:
            if m["warp_events"]:
                w = m["warp_events"][0]
                return w["x"], w["y"]
            lay = layouts[m["layout"]]
            return lay["width"] // 2, lay["height"] // 2
    raise KeyError(map_id)


@cache
def _tabela(map_id: str) -> dict:
    """A tabela `_FireRed` do mapa em wild_encounters.json."""
    for g in json.loads(WILD_JSON.read_text(encoding="utf-8"))["wild_encounter_groups"]:
        for e in g["encounters"]:
            if e["map"] == map_id and "FireRed" in e["base_label"]:
                return e
    raise KeyError(map_id)


class JohtoScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None

    # --- utilidades ------------------------------------------------------------------------------------------------
    def _nome(self, species_id: int) -> str:
        return self.consts.species_name(species_id).removeprefix("SPECIES_")

    def _teleport(self, map_id: str, minuto: int) -> None:
        self.box.set_clock(DAY, minuto)
        group, num = self.consts.map(map_id)
        x, y = _warp_xy(map_id)
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), WARP_TIMEOUT, f"warp para {map_id}")
        self.ctl.wait_overworld_idle(WARP_TIMEOUT)
        self.emu.frames(30)

    def _rolar(self, metodo: int, n: int) -> dict[str, int]:
        """`n` encontros do gerador real do mapa atual: nome da espécie -> vezes. Como `dexnav.rolar`, mas com mais
        tempo: cada encontro cria o Pokémon de verdade e, nos níveis altos do Cânion, leva bem mais de 6 quadros."""
        distintas = self.box.call(CMD_DEXNAV_ROLL, metodo, n, timeout=ROLAGEM_QUADROS * n + 600)
        assert distintas != NO_RESULT, f"o mapa atual não tem {dnv.METODOS[metodo]}"
        dados = self.emu.read(self.game.syms.addr(TEXT_SYMBOL), distintas * 4)
        pares = struct.unpack(f"<{distintas * 2}H", dados)
        contagem = {self._nome(pares[i]): pares[i + 1] for i in range(0, len(pares), 2)}
        assert sum(contagem.values()) == n, contagem
        return contagem

    def _nivel_de(self, especie: str, area: int, vara: int = 0) -> tuple[int, int]:
        """(menor, maior) nível visto em `CMD_ROLL_WILD` até sair `especie` 12 vezes (no máximo TENTATIVAS_NIVEL)."""
        niveis, tentativas = [], 0
        while len(niveis) < 12:
            assert tentativas < TENTATIVAS_NIVEL, (f"{especie}: só {len(niveis)} em {TENTATIVAS_NIVEL} encontros "
                                                   f"(área {area})")
            tentativas += 1
            r = self.box.call(CMD_ROLL_WILD, area | vara << 8, 0)
            assert r != NO_RESULT, f"o mapa atual não tem a área {area}"
            if self._nome(r & 0xFFFF) == especie:
                niveis.append(r >> 16)
        return min(niveis), max(niveis)

    def _batalha_de_verdade(self, area: int, validos: dict[str, tuple[int, int]], vara: int = 0) -> str:
        """Um encontro que começa a batalha (CMD_ROLL_WILD arg1 = 1): no menu de ação, o inimigo é o que o atalho
        devolveu, de uma espécie e nível possíveis do mapa."""
        r = self.box.call(CMD_ROLL_WILD, area | vara << 8, 1, timeout=1200)
        assert r != NO_RESULT, f"o mapa atual não tem a área {area}"
        especie, nivel = self._nome(r & 0xFFFF), r >> 16
        self.ctl.wait_until(self.game.in_battle, 1200, "a batalha selvagem começar")
        self.driver.wait_action_menu()
        batalha = self.driver.battler_species_level(1)
        assert (self._nome(batalha[0]), batalha[1]) == (especie, nivel), (batalha, especie, nivel)
        assert especie in validos and validos[especie][0] <= nivel <= validos[especie][1], (especie, nivel, validos)
        self._end_battle(f"fuga do {especie} selvagem")
        return f"batalha: {especie} nv{nivel}"

    @staticmethod
    def _niveis(map_id: str, kind: str, so_especies: set[str] | None = None) -> dict[str, tuple[int, int]]:
        """espécie -> (menor, maior) nível dos slots do `kind` da tabela FireRed do mapa."""
        out: dict[str, tuple[int, int]] = {}
        for m in _tabela(map_id)[kind]["mons"]:
            nome = m["species"].removeprefix("SPECIES_")
            if so_especies is not None and nome not in so_especies:
                continue
            lo, hi = out.get(nome, (255, 0))
            out[nome] = (min(lo, m["min_level"]), max(hi, m["max_level"]))
        return out

    # --- passos ----------------------------------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="johto_continue")
        self.box.conq_silencio(True)
        return "CONTINUAR com o save do modo rápido; avisos das conquistas em silêncio"

    def _miltank_de_dia(self) -> str:
        mapa = "MAP_FIVE_ISLAND_MEADOW"
        resumo = []
        for hora in ("manhã", "tarde", "noite", "entardecer"):
            self._teleport(mapa, HORAS[hora])
            vistos = self._rolar(dnv.LAND, ROLAGENS)
            if hora == "noite":
                assert "MILTANK" not in vistos, f"à noite saiu Miltank: {vistos}"
                assert "MEOWTH" in vistos, vistos
            else:
                assert "MILTANK" in vistos, f"{hora}: nenhum Miltank em {ROLAGENS} encontros: {vistos}"
                assert "MEOWTH" not in vistos or hora == "entardecer", f"{hora}: Meowth no horário do Miltank {vistos}"
            resumo.append(f"{hora} Miltank {vistos.get('MILTANK', 0)}/{ROLAGENS}")
        self._teleport(mapa, TARDE)
        mn, mx = self._nivel_de("MILTANK", AREA_GRAMA)
        assert 30 <= mn and mx <= 35, (mn, mx)
        return ", ".join(resumo) + "; " + self._batalha_de_verdade(
            AREA_GRAMA, {**self._niveis(mapa, "land_mons"), "MILTANK": (30, 35)})

    def _gligar_a_noite(self) -> str:
        mapa = "MAP_SEVEN_ISLAND_SEVAULT_CANYON"
        resumo = []
        for hora in ("noite", "manhã", "tarde", "entardecer"):
            self._teleport(mapa, HORAS[hora])
            vistos = self._rolar(dnv.LAND, ROLAGENS)
            if hora in ("manhã", "tarde"):
                assert "GLIGAR" not in vistos, f"{hora} saiu Gligar: {vistos}"
            else:
                assert "GLIGAR" in vistos, f"{hora}: nenhum Gligar em {ROLAGENS} encontros: {vistos}"
            resumo.append(f"{hora} Gligar {vistos.get('GLIGAR', 0)}/{ROLAGENS}")
        self._teleport(mapa, NOITE)
        mn, mx = self._nivel_de("GLIGAR", AREA_GRAMA)
        assert 35 <= mn and mx <= 40, (mn, mx)
        return ", ".join(resumo) + "; " + self._batalha_de_verdade(
            AREA_GRAMA, {**self._niveis(mapa, "land_mons"), "GLIGAR": (35, 40)})

    def _chinchou_super_vara(self) -> str:
        resumo = []
        for mapa in ROTAS:
            self._teleport(mapa, TARDE)
            for metodo in (dnv.OLD_ROD, dnv.GOOD_ROD):
                vistos = self._rolar(metodo, ROLAGENS)
                assert not {"CHINCHOU", "LANTURN"} & set(vistos), f"{mapa} {dnv.METODOS[metodo]}: {vistos}"
            vistos = self._rolar(dnv.SUPER_ROD, ROLAGENS_RARO)
            assert "CHINCHOU" in vistos and "LANTURN" in vistos, f"{mapa} super vara: {vistos}"
            chinchou = 100 * vistos["CHINCHOU"] / ROLAGENS_RARO
            assert 15 - 5 <= chinchou <= 15 + 5, f"{mapa}: Chinchou {chinchou:.1f}% (esperado 15%)"
            resumo.append(f"{mapa[4:]}: Chinchou {chinchou:.1f}% Lanturn {100 * vistos['LANTURN'] / ROLAGENS_RARO:.1f}%")
        self._teleport(ROTAS[0], TARDE)
        mn, mx = self._nivel_de("CHINCHOU", AREA_PESCA, SUPER_VARA)
        assert 25 <= mn and mx <= 35, (mn, mx)
        return "; ".join(resumo) + f"; Chinchou nv{mn}-{mx}"

    def _corsola_surf(self) -> str:
        mapa = "MAP_FIVE_ISLAND_RESORT_GORGEOUS"
        self._teleport(mapa, TARDE)
        vistos = self._rolar(dnv.WATER, ROLAGENS)
        assert "CORSOLA" in vistos, vistos
        pct = 100 * vistos["CORSOLA"] / ROLAGENS
        assert 30 - 10 <= pct <= 30 + 10, f"Corsola {pct:.1f}% (esperado 30%)"
        mn, mx = self._nivel_de("CORSOLA", AREA_AGUA)
        assert 30 <= mn and mx <= 35, (mn, mx)
        return f"Corsola {pct:.1f}%, nível {mn}-{mx}"

    def _girafarig_safari(self) -> str:
        mapa = "MAP_SAFARI_ZONE_WEST"
        resumo = []
        for hora in ("manhã", "noite"):
            self._teleport(mapa, HORAS[hora])
            vistos = self._rolar(dnv.LAND, ROLAGENS_RARO)
            assert "GIRAFARIG" in vistos, f"{hora}: nenhum Girafarig em {ROLAGENS_RARO}: {vistos}"
            resumo.append(f"{hora} {vistos['GIRAFARIG']}/{ROLAGENS_RARO}")
        mn, mx = self._nivel_de("GIRAFARIG", AREA_GRAMA)
        assert 25 <= mn and mx <= 30, (mn, mx)
        return "Girafarig " + ", ".join(resumo) + f", nível {mn}-{mx}"

    def run(self) -> None:
        try:
            self._flow("johto: CONTINUAR com o save do modo rápido", self._start)
            self.suite.run("johto/miltank_de_dia: Prado da Ilha Cinco, só de manhã e à tarde", self._miltank_de_dia)
            self.suite.run("johto/gligar_a_noite: Cânion Sevault, só à noite", self._gligar_a_noite)
            self.suite.run("johto/chinchou_super_vara: Rotas 19 a 21, Chinchou e Lanturn só na Super Vara",
                           self._chinchou_super_vara)
            self.suite.run("johto/corsola_surf: Resort Gorgeous", self._corsola_surf)
            self.suite.run("johto/girafarig_safari: Zona Safári Oeste", self._girafarig_safari)
        except Abort:
            pass


def run_full_johto(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    JohtoScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only johto ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "johto", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
