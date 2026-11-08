"""Modo completo: os 18 de Johto (POK-28), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`), com o aviso das conquistas em
silêncio. Cada caso leva o jogador ao mapa com `CMD_WARP`, acerta o relógio e força o encontro com o gerador real do
jogo (`TEST_CMD_DEXNAV_ROLL`: centenas de encontros de verdade num atalho só, e `TEST_CMD_ROLL_WILD`, que gera um
selvagem e, com `arg1 = 1`, começa a batalha). As expectativas saem de `src/data/wild_encounters*.json`.

Selvagens (Task 2):

- `johto/miltank_de_dia`: Prado da Ilha Cinco. De manhã e à tarde o Miltank sai (10%, nível 30-35); à noite nunca. No
  entardecer (tarde ou noite, meio a meio: 5%) ele aparece. Uma batalha de verdade no menu de ação confere espécie e
  nível;
- `johto/gligar_a_noite`: Cânion Sevault. À noite o Gligar sai (10%, nível 35-40); de manhã e à tarde nunca;
- `johto/chinchou_super_vara`: Rotas 19, 20, 21N e 21S. Super Vara: Chinchou 15% (nível 25-35) e Lanturn 4% (nível
  35-40); a Vara Velha e a Boa nunca dão nenhum dos dois;
- `johto/corsola_surf`: Resort Gorgeous, surfando: Corsola 30% (nível 30-35);
- `johto/girafarig_safari`: Zona Safári Oeste, na grama: Girafarig 4% (nível 25-30), a qualquer hora.

Estatística: o jogo sorteia de verdade, então cada conferência tem um tamanho de amostra (`AMOSTRAS`) escolhido para o
falso vermelho ficar abaixo de `FALSO_VERMELHO_MAX` (1e-6): "nenhum acerto em n sorteios" vale (1-p)^n, "menos de k
acertos" a soma binomial, e as faixas de porcentagem são de `SIGMAS` desvios-padrão (2 em 1 bilhão cada). As contas
estão em `p_nenhum`, `p_menos_de` e `p_fora_da_faixa`, e `test_johto_selvagens.py` as confere para cada linha de
`AMOSTRAS`. O tempo medido (~1 min) cabe nos 2 min, então a amostragem fica: ela prova o gerador real inteiro (slot,
horário, nível) em vez de uma cópia dele em Python. Cada execução semeia o RNG do jogo com o sal da execução
(`ESTEIRA_SEED`, ou sorteado; ele sai no detalhe do 1º passo), então as amostras variam de uma execução para outra e
um vermelho se reproduz com `ESTEIRA_SEED=0x...`.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only johto
"""

import json
import math
import struct
import sys
from functools import cache

from .. import dexnav as dnv
from ..hooks import CMD_DEXNAV_ROLL, CMD_ROLL_WILD, CMD_WARP, NO_RESULT, TEXT_SYMBOL, Mailbox
from ..paralelo import run_salt, seed_label, seed_rng
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

MAPS_DIR = REPO_ROOT / "data" / "maps"
WILD_JSON = REPO_ROOT / "src" / "data" / "wild_encounters.json"
DAY = 0
MANHA, TARDE, ENTARDECER, NOITE = 7 * 60, 12 * 60, 18 * 60, 22 * 60   # minutos do dia (período em dia_noite.py)
HORAS = {"manhã": MANHA, "tarde": TARDE, "entardecer": ENTARDECER, "noite": NOITE}
ROTAS = ("MAP_ROUTE19", "MAP_ROUTE20", "MAP_ROUTE21_NORTH", "MAP_ROUTE21_SOUTH")
AREA_GRAMA, AREA_AGUA, AREA_PEDRA, AREA_PESCA = 0, 1, 2, 3
SUPER_VARA = 2           # SUPER_ROD de include/constants/items.h
WARP_TIMEOUT = 900
ROLAGEM_QUADROS = 30     # quadros por encontro no teto do atalho DEXNAV_ROLL

FALSO_VERMELHO_MAX = 1e-6
SIGMAS = 6               # faixa de porcentagem: 6 desvios-padrão da binomial = 2e-9 de falso vermelho

# chave -> (chance do slot, nº de sorteios, mínimo de acertos exigido). "Presença" = pelo menos 1 acerto em n
# sorteios do atalho DEXNAV_ROLL; as chaves "*_nivel" são tentativas de CMD_ROLL_WILD (para no mínimo de acertos).
AMOSTRAS = {
    "miltank_dia": (0.10, 300, 1),              # manhã e tarde; o Meowth da noite tem a mesma chance
    "miltank_entardecer": (0.05, 400, 1),       # meio a meio com a noite: 10% x 1/2
    "miltank_nivel": (0.10, 400, 3),
    "gligar_noite": (0.10, 300, 1),             # a noite; o Meowth do dia tem a mesma chance
    "gligar_entardecer": (0.05, 400, 1),
    "gligar_nivel": (0.10, 400, 3),
    "chinchou": (0.15, 800, 1),                 # também a faixa de porcentagem (SIGMAS)
    "chinchou_nivel": (0.15, 600, 3),
    "lanturn": (0.04, 800, 1),
    "lanturn_nivel": (0.04, 2500, 3),
    "corsola": (0.30, 600, 1),                  # também a faixa de porcentagem (SIGMAS)
    "corsola_nivel": (0.30, 400, 3),
    "girafarig": (0.04, 800, 1),                # manhã e noite
    "girafarig_nivel": (0.04, 2500, 3),
}


def p_nenhum(p: float, n: int) -> float:
    """Chance de NENHUM acerto em n sorteios de chance p."""
    return (1 - p) ** n


def p_menos_de(k: int, p: float, n: int) -> float:
    """Chance de menos de k acertos em n sorteios de chance p (soma binomial)."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k))


def p_fora_da_faixa(sigmas: float = SIGMAS) -> float:
    """Chance de a contagem sair a mais de `sigmas` desvios-padrão da esperada (normal, bicaudal)."""
    return math.erfc(sigmas / math.sqrt(2))


def tolerancia_pp(p: float, n: int, sigmas: float = SIGMAS) -> float:
    """Meia-largura, em pontos percentuais, da faixa de `sigmas` desvios-padrão de n sorteios de chance p."""
    return 100 * sigmas * math.sqrt(p * (1 - p) / n)


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

    def _rolar(self, metodo: int, chave: str) -> dict[str, int]:
        """`AMOSTRAS[chave]` encontros do gerador real do mapa atual: nome da espécie -> vezes. Como `dexnav.rolar`, mas
        com mais tempo: cada encontro cria o Pokémon de verdade e, nos níveis altos do Cânion, leva bem mais de 6
        quadros."""
        n = AMOSTRAS[chave][1]
        distintas = self.box.call(CMD_DEXNAV_ROLL, metodo, n, timeout=ROLAGEM_QUADROS * n + 600)
        assert distintas != NO_RESULT, f"o mapa atual não tem {dnv.METODOS[metodo]}"
        dados = self.emu.read(self.game.syms.addr(TEXT_SYMBOL), distintas * 4)
        pares = struct.unpack(f"<{distintas * 2}H", dados)
        contagem = {self._nome(pares[i]): pares[i + 1] for i in range(0, len(pares), 2)}
        assert sum(contagem.values()) == n, contagem
        return contagem

    def _presente(self, especie: str, vistos: dict[str, int], chave: str, onde: str) -> int:
        n = AMOSTRAS[chave][1]
        assert vistos.get(especie, 0) >= AMOSTRAS[chave][2], (
            f"{onde}: nenhum {especie} em {n} encontros (a chance de isso acontecer sem erro é "
            f"{p_nenhum(AMOSTRAS[chave][0], n):.1e}): {vistos}")
        return vistos[especie]

    def _na_faixa(self, especie: str, vistos: dict[str, int], chave: str, onde: str) -> float:
        """A porcentagem de `especie` nos sorteios, dentro de `SIGMAS` desvios-padrão da chance do slot."""
        p, n, _ = AMOSTRAS[chave]
        pct = 100 * vistos.get(especie, 0) / n
        tol = tolerancia_pp(p, n)
        assert abs(pct - 100 * p) <= tol, f"{onde}: {especie} {pct:.1f}%, esperado {100 * p:g}% +- {tol:.1f} p.p."
        return pct

    def _niveis_de(self, especie: str, area: int, chave: str, vara: int = 0) -> tuple[int, int]:
        """(menor, maior) nível de `especie` em `CMD_ROLL_WILD` (o gerador real, sem batalha), parando no mínimo de
        acertos de `AMOSTRAS[chave]`; no máximo o nº de tentativas da chave."""
        p, tentativas, minimo = AMOSTRAS[chave]
        niveis = []
        for _ in range(tentativas):
            r = self.box.call(CMD_ROLL_WILD, area | vara << 8, 0)
            assert r != NO_RESULT, f"o mapa atual não tem a área {area}"
            if self._nome(r & 0xFFFF) == especie:
                niveis.append(r >> 16)
                if len(niveis) >= minimo:
                    return min(niveis), max(niveis)
        raise AssertionError(f"{especie}: só {len(niveis)} em {tentativas} encontros (área {area}); a chance de isso "
                             f"acontecer sem erro é {p_menos_de(minimo, p, tentativas):.1e}")

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
    def _niveis(map_id: str, kind: str) -> dict[str, tuple[int, int]]:
        """espécie -> (menor, maior) nível dos slots do `kind` da tabela FireRed do mapa."""
        out: dict[str, tuple[int, int]] = {}
        for m in _tabela(map_id)[kind]["mons"]:
            nome = m["species"].removeprefix("SPECIES_")
            lo, hi = out.get(nome, (255, 0))
            out[nome] = (min(lo, m["min_level"]), max(hi, m["max_level"]))
        return out

    # --- passos ----------------------------------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="johto_continue")
        self.box.conq_silencio(True)
        # a batalha de verdade sorteia qualquer espécie do mapa (até nv 54 no Cânion): um Mewtwo nv 100 na frente
        # garante a fuga (mais rápido que todas) em vez de o time do `captura` desmaiar
        self.box.set_party_mon(0, self.consts.species("SPECIES_MEWTWO"), 100)
        # sem isto, toda execução parte do mesmo estado do RNG e repete as mesmas amostras (e o mesmo acaso); com o sal
        # da execução (ESTEIRA_SEED, ou sorteado) cada uma sorteia outra sequência, e um vermelho se reproduz com a mesma
        salt = self.ctx.seed or run_salt()
        seed_rng(self.emu, self.game.syms, "johto", 0, salt)
        return f"CONTINUAR com o save do modo rápido; avisos das conquistas em silêncio; {seed_label(salt)}"

    def _miltank_de_dia(self) -> str:
        mapa = "MAP_FIVE_ISLAND_MEADOW"
        resumo = []
        for hora in ("manhã", "tarde", "noite", "entardecer"):
            self._teleport(mapa, HORAS[hora])
            chave = "miltank_entardecer" if hora == "entardecer" else "miltank_dia"
            vistos = self._rolar(dnv.LAND, chave)
            if hora == "noite":
                assert "MILTANK" not in vistos, f"à noite saiu Miltank: {vistos}"
                self._presente("MEOWTH", vistos, chave, hora)
            else:
                self._presente("MILTANK", vistos, chave, hora)
                assert "MEOWTH" not in vistos or hora == "entardecer", f"{hora}: Meowth no horário do Miltank {vistos}"
            resumo.append(f"{hora} Miltank {vistos.get('MILTANK', 0)}/{AMOSTRAS[chave][1]}")
        self._teleport(mapa, TARDE)
        mn, mx = self._niveis_de("MILTANK", AREA_GRAMA, "miltank_nivel")
        assert 30 <= mn and mx <= 35, (mn, mx)
        return ", ".join(resumo) + "; " + self._batalha_de_verdade(
            AREA_GRAMA, {**self._niveis(mapa, "land_mons"), "MILTANK": (30, 35)})

    def _gligar_a_noite(self) -> str:
        mapa = "MAP_SEVEN_ISLAND_SEVAULT_CANYON"
        resumo = []
        for hora in ("noite", "manhã", "tarde", "entardecer"):
            self._teleport(mapa, HORAS[hora])
            chave = "gligar_entardecer" if hora == "entardecer" else "gligar_noite"
            vistos = self._rolar(dnv.LAND, chave)
            if hora in ("manhã", "tarde"):
                assert "GLIGAR" not in vistos, f"{hora} saiu Gligar: {vistos}"
                self._presente("MEOWTH", vistos, chave, hora)
            else:
                self._presente("GLIGAR", vistos, chave, hora)
            resumo.append(f"{hora} Gligar {vistos.get('GLIGAR', 0)}/{AMOSTRAS[chave][1]}")
        self._teleport(mapa, NOITE)
        mn, mx = self._niveis_de("GLIGAR", AREA_GRAMA, "gligar_nivel")
        assert 35 <= mn and mx <= 40, (mn, mx)
        return ", ".join(resumo) + "; " + self._batalha_de_verdade(
            AREA_GRAMA, {**self._niveis(mapa, "land_mons"), "GLIGAR": (35, 40)})

    def _chinchou_super_vara(self) -> str:
        resumo = []
        for mapa in ROTAS:
            self._teleport(mapa, TARDE)
            for metodo in (dnv.OLD_ROD, dnv.GOOD_ROD):
                vistos = self._rolar(metodo, "chinchou")
                assert not {"CHINCHOU", "LANTURN"} & set(vistos), f"{mapa} {dnv.METODOS[metodo]}: {vistos}"
            vistos = self._rolar(dnv.SUPER_ROD, "chinchou")
            self._presente("CHINCHOU", vistos, "chinchou", f"{mapa} super vara")
            chinchou = self._na_faixa("CHINCHOU", vistos, "chinchou", f"{mapa} super vara")
            lanturn = self._rolar(dnv.SUPER_ROD, "lanturn")
            self._presente("LANTURN", lanturn, "lanturn", f"{mapa} super vara")
            cn, cx = self._niveis_de("CHINCHOU", AREA_PESCA, "chinchou_nivel", SUPER_VARA)
            ln, lx = self._niveis_de("LANTURN", AREA_PESCA, "lanturn_nivel", SUPER_VARA)
            assert 25 <= cn and cx <= 35, (mapa, "Chinchou", cn, cx)
            assert 35 <= ln and lx <= 40, (mapa, "Lanturn", ln, lx)
            resumo.append(f"{mapa[4:]}: Chinchou {chinchou:.1f}% nv{cn}-{cx}, Lanturn "
                          f"{100 * lanturn['LANTURN'] / AMOSTRAS['lanturn'][1]:.1f}% nv{ln}-{lx}")
        return "; ".join(resumo)

    def _corsola_surf(self) -> str:
        self._teleport("MAP_FIVE_ISLAND_RESORT_GORGEOUS", TARDE)
        vistos = self._rolar(dnv.WATER, "corsola")
        self._presente("CORSOLA", vistos, "corsola", "Resort Gorgeous")
        pct = self._na_faixa("CORSOLA", vistos, "corsola", "Resort Gorgeous")
        mn, mx = self._niveis_de("CORSOLA", AREA_AGUA, "corsola_nivel")
        assert 30 <= mn and mx <= 35, (mn, mx)
        return f"Corsola {pct:.1f}%, nível {mn}-{mx}"

    def _girafarig_safari(self) -> str:
        resumo = []
        for hora in ("manhã", "noite"):
            self._teleport("MAP_SAFARI_ZONE_WEST", HORAS[hora])
            vistos = self._rolar(dnv.LAND, "girafarig")
            resumo.append(f"{hora} {self._presente('GIRAFARIG', vistos, 'girafarig', hora)}/{AMOSTRAS['girafarig'][1]}")
        mn, mx = self._niveis_de("GIRAFARIG", AREA_GRAMA, "girafarig_nivel")
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
