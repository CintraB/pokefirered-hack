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

Ovos do Prof. Elm (Task 3, classe `OvosElm`, com os atalhos e a cena do `pos_liga`):

- `johto/ovos_elm/escolha`: a cena da Dex Nacional de verdade: o ovo raro e, depois dele, o menu com os 3 nomes;
  escolhido o CYNDAQUIL (2ª opção), é ele que vem; tela `johto_ovos_elm_menu` (por inicial);
- `johto/ovos_elm/hall`: o script da entrada no Hall (`CMD_CALL_SCRIPT`) deixa os dois ovos pendentes;
- `johto/ovos_elm/segunda`: na conversa, o raro primeiro e depois o menu só com CHIKORITA e TOTODILE; de novo, nada;
- `johto/ovos_elm/ultimo`: com 1 restante ele vem sem menu; depois dos 3, a vitória não deixa nada pendente;
- `johto/ovos_elm/pc`: equipe cheia, o ovo vai para o PC;
- `johto/ovos_elm/cheio`: equipe e PC cheios: aviso, nenhuma flag muda; com uma vaga, o mesmo menu e o ovo no PC;
- `johto/ovos_elm/save_antigo`: estágio 8 sem nenhuma flag do Elm: a conversa traz a 1ª oferta com os 3.

Snubbull do Fã-clube (Task 4, classe `FaClube`): o Presidente, depois do Vale Bicicleta, dá um Snubbull nv 20 se o 1º
da equipe tem amizade 200 ou mais (`GetLeadMonFriendship` >= 5):

- `johto/snubbull/sim`: amizade 255, equipe de 1: o Snubbull nv 20 entra na equipe e `FLAG_GOT_SNUBBULL` liga; tela
  `johto_snubbull` (a caixa "recebeu um Snubbull do Presidente");
- `johto/snubbull/limite`: 199 só ouve a dica e 200 já ganha;
- `johto/snubbull/baixa`: amizade 100: dica, nada muda; com 255 depois, ganha (a dica não trava nada);
- `johto/snubbull/segunda`: depois de ganhar, falar de novo não dá outro;
- `johto/snubbull/pc`: equipe cheia, o Snubbull vai para o PC;
- `johto/snubbull/cheio`: equipe e PC cheios: aviso e a flag NÃO liga; com uma vaga no PC, ele vem;
- `johto/snubbull/vale`: o Vale Bicicleta continua igual (pergunta, SIM, voucher) e o Snubbull só vem na conversa seguinte.

Sudowoodo do Caminho Verde (Task 5, classe `TrilhaVerde`): a "árvore estranha" no recanto (39, 10), ao norte do caminho
da Ilha Seis, é um Sudowoodo nv 35 em batalha selvagem comum (molde do Jirachi, música de selvagem):

- `johto/sudowoodo/dex`: sem a Dex Nacional fica escondido; com ela aparece em (39, 10); tela `johto_sudowoodo`;
- `johto/sudowoodo/passa`: com ele no lugar, o jogador anda da saída da Moita Estampada até a margem oeste (onde se
  surfa), passando logo abaixo dele, volta e entra na Moita de novo;
- `johto/sudowoodo/captura`: a fala, a batalha (SUDOWOODO nv 35, sem o tipo de lendário) e a Master Ball: some, não
  volta ao reentrar nem depois do Hall;
- `johto/sudowoodo/fuga`: fuga: some, não volta ao reentrar; o script do Hall (`CMD_CALL_SCRIPT`) o traz de volta;
- `johto/sudowoodo/vitoria`: derrotado: o mesmo da fuga.

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
from collections import Counter
from functools import cache

from .. import dexnav as dnv
from ..bag import MENU_CURSOR_POS, MENU_MAX_CURSOR, MENU_MIN_CURSOR
from ..battle import B_OUTCOME_CAUGHT, NICKNAME_COMMAND, BattleDriver
from ..breeding import header_defines
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_UP
from ..game import BOX_MON_SIZE, IN_BOX_COUNT
from ..hooks import CMD_DEXNAV_ROLL, CMD_GIVE_ITEM, CMD_ROLL_WILD, CMD_WARP, NO_RESULT, TEXT_SYMBOL, Mailbox
from ..paralelo import run_salt, seed_label, seed_rng
from . import REPO_ROOT, ScenarioContext
from .base import YESNO_TASK, Abort
from .full_post_league import (LAB, OAK_FRONT, OWNED_NEEDED, PALLET, PALLET_PLAYER, RARE_EGGS, SCENE_FRAMES,
                               SETTLE_FRAMES, TEXT_SEM_ESPACO, PostLeagueScenario)
from .pc_menu import MULTICHOICE_TASK
from .quick_catch_save import CatchSaveScenario

# Telas que o cenário grava em OUT/telas/ e que entram na comparação com as referências (esteira/refs.py).
# SCREEN_POINTS vão para o fim de SHARED_POINTS (COMUM/): o presente do Snubbull e o Sudowoodo no recanto do Caminho
# Verde. A do menu dos ovos do Elm muda com o inicial (a Poké Ball que o Carvalho deixou na mesa é a do outro inicial
# de cada vez), então é por inicial: STARTER_POINTS, em KEY_POINTS.
SCREEN_POINTS = ("johto_snubbull", "johto_sudowoodo")
STARTER_POINTS = ("johto_ovos_elm_menu",)

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
            # Task 3: os ovos do Prof. Elm (ver OvosElm)
            ovos = OvosElm(self.ctx, self.box)
            res = self.suite.run("johto/ovos_elm/escolha: na cena da Dex Nacional, depois do ovo raro, o CYNDAQUIL "
                                 "escolhido entre os 3", ovos.escolha)
            res.images.extend(ovos.telas)
            if res.status == "falha":
                raise Abort("johto/ovos_elm/escolha")
            self.suite.run("johto/ovos_elm/hall: nova vitória deixa o ovo do Elm pendente", ovos.hall)
            self.suite.run("johto/ovos_elm/segunda: o raro primeiro, depois o do Elm entre os 2 que faltam",
                           ovos.segunda)
            self.suite.run("johto/ovos_elm/ultimo: com 1 restante ele vem direto; depois, nada", ovos.ultimo)
            self.suite.run("johto/ovos_elm/pc: equipe cheia, o ovo vai para o PC", ovos.pc)
            self.suite.run("johto/ovos_elm/cheio: equipe e PC cheios, nada se perde", ovos.cheio)
            self.suite.run("johto/ovos_elm/save_antigo: depois da Dex Nacional sem ovo do Elm, a conversa oferece",
                           ovos.save_antigo)
            # Task 4: o Snubbull do Fã-clube (ver FaClube)
            clube = FaClube(self.ctx, self.box)
            res = self.suite.run("johto/snubbull/sim: amizade 255, o Snubbull nv 20 vem para a equipe", clube.sim)
            res.images.extend(clube.telas)
            self.suite.run("johto/snubbull/limite: 199 não ganha, 200 ganha", clube.limite)
            self.suite.run("johto/snubbull/baixa: amizade 100 só ouve a dica", clube.baixa)
            self.suite.run("johto/snubbull/segunda: depois de ganhar, não dá outro", clube.segunda)
            self.suite.run("johto/snubbull/pc: equipe cheia, o Snubbull vai para o PC", clube.pc)
            self.suite.run("johto/snubbull/cheio: equipe e PC cheios, nada se perde e a flag não liga", clube.cheio)
            self.suite.run("johto/snubbull/vale: o Vale Bicicleta continua igual", clube.vale)
            # Task 5: o Sudowoodo do Caminho Verde (ver TrilhaVerde)
            trilha = TrilhaVerde(self.ctx, self.box)
            res = self.suite.run("johto/sudowoodo/dex: a árvore estranha só aparece com a Dex Nacional", trilha.dex)
            res.images.extend(trilha.telas)
            if res.status == "falha":
                raise Abort("johto/sudowoodo/dex")
            self.suite.run("johto/sudowoodo/passa: com ele no lugar, o caminho obrigatório continua livre", trilha.passa)
            self.suite.run("johto/sudowoodo/captura: nv 35, batalha selvagem; capturado, some para sempre",
                           trilha.captura)
            self.suite.run("johto/sudowoodo/fuga: com fuga, some e só volta depois do Hall", trilha.fuga)
            self.suite.run("johto/sudowoodo/vitoria: derrotado, some e só volta depois do Hall", trilha.vitoria)
        except Abort:
            pass


ELM = ("CHIKORITA", "CYNDAQUIL", "TOTODILE")
HALL_SCRIPT = "EventScript_SetDefeatedEliteFourFlagsVars"   # a entrada no Hall (data/scripts/hall_of_fame.inc)
FALA_PRIMEIRA, FALA_OUTRA, FALA_RARO = "Prof. Elm, meu colega", "Chegou mais um Ovo", "outro Ovo raro"
STRING_VAR_BYTES = 20


class OvosElm(PostLeagueScenario):
    """Os ovos do Prof. Elm (Task 3), na mesma sessão do cenário, com os atalhos e a cena do `pos_liga`.

    A cena da Dex Nacional roda de verdade (o ovo raro e o 1º do Elm, escolhido no menu); a vitória seguinte na Liga
    é o script da entrada no Hall (`CMD_CALL_SCRIPT`), e cada conversa com o Carvalho aperta A em tudo, escolhe no menu
    dos ovos a espécie pedida e responde NÃO à oferta das novidades. Os ovos são contados na equipe e no PC."""

    def __init__(self, ctx: ScenarioContext, box: Mailbox):
        super().__init__(ctx)
        self.box = box
        self.telas: list[str] = []

    # --- leitura ---------------------------------------------------------------------------------------------------
    def _ovos(self) -> list[str]:
        """Espécies de todos os ovos, equipe e PC."""
        return [self._nome(s) for s in self._party_eggs() + [s for _, _, s in self._pc_eggs()]]

    def _nome(self, species_id: int) -> str:
        return self.consts.species_name(species_id).removeprefix("SPECIES_")

    def _elm_flags(self) -> dict[str, bool]:
        nomes = [f"FLAG_GOT_EGG_{n}" for n in ELM] + ["FLAG_ELM_EGG_PENDING", "FLAG_GOT_ELM_EGG"]
        return {n.removeprefix("FLAG_"): self._flag(n) for n in nomes}

    def _novos(self, antes: list[str]) -> list[str]:
        """Ovos que apareceram desde `antes` (multiconjunto: a posição na equipe ou no PC não importa)."""
        return sorted((Counter(self._ovos()) - Counter(antes)).elements())

    def _dados(self, *especies: str) -> None:
        """As flags de espécie do Elm ligadas são exatamente `especies`."""
        f = self._elm_flags()
        assert {n for n in ELM if f[f"GOT_EGG_{n}"]} == set(especies), f

    def _opcoes(self, n: int) -> list[str]:
        return [self.game.charmap.decode(self.emu.read(self.game.syms.addr(f"gStringVar{i + 1}"), STRING_VAR_BYTES))
                for i in range(n)]

    def _cursor(self, n: int) -> int:
        """&sMenu.cursorPos (src/menu.c) do menu de n opções aberto (há outro `sMenu` estático no ELF)."""
        found = [a for a in self.game.syms.addrs("sMenu")
                 if self.emu.read_u8(a + MENU_MIN_CURSOR) == 0 and self.emu.read_u8(a + MENU_MAX_CURSOR) == n - 1]
        assert len(found) == 1, f"não achei o sMenu do menu de {n} ({len(found)} candidatos)"
        return found[0] + MENU_CURSOR_POS

    # --- ações -----------------------------------------------------------------------------------------------------
    def _escolher(self, esperadas: tuple[str, ...], escolha: str, tela: str | None) -> None:
        """No menu dos ovos aberto: confere as opções, leva o cursor até `escolha` e aperta A."""
        self.emu.frames(8)
        opcoes = self._opcoes(len(esperadas))
        assert tuple(opcoes) == esperadas, f"opções {opcoes}, esperava {esperadas}"
        cursor, alvo = self._cursor(len(esperadas)), esperadas.index(escolha)
        assert self.emu.read_u8(cursor) == 0, f"o menu abriu com o cursor em {self.emu.read_u8(cursor)}"
        while self.emu.read_u8(cursor) != alvo:
            atual = self.emu.read_u8(cursor)
            self.ctl.press_until(KEY_DOWN, lambda c=atual: self.emu.read_u8(cursor) != c, "cursor do menu dos ovos",
                                 tries=3, wait=20)
        if tela:
            self.emu.frames(4)
            self.telas.append(self._shot(tela))
        self.ctl.press_until(KEY_A, lambda: MULTICHOICE_TASK not in self._tasks(), f"escolha de {escolha}")

    def _avancar(self, menu: tuple[str, ...] | None, escolha: str | None, until=None, tela: str | None = None,
                 what: str = "conversa com o Carvalho") -> list[str]:
        """A em tudo até `until()` (padrão: só o campo livre); o menu dos ovos, se abrir, tem de ser `menu` (None =
        não pode abrir) e recebe `escolha`; a oferta das novidades recebe NÃO. Devolve as falas, na ordem."""
        falas: list[str] = []
        abriu, spent = False, 0
        while not ((until is None or until()) and self._settled_idle()):
            if spent >= SCENE_FRAMES:
                raise self.ctl.timeout_error(what)
            msg = self._message()
            if not falas or falas[-1] != msg:
                falas.append(msg)
            tasks = self._tasks()
            if MULTICHOICE_TASK in tasks:
                assert menu is not None and not abriu, f"menu dos ovos inesperado: {self._opcoes(3)}"
                abriu = True
                self._escolher(menu, escolha, tela)
                continue
            self._press(KEY_B if YESNO_TASK in tasks and self._novidades_offer() else KEY_A)
            spent += 10
        assert abriu or menu is None, f"o menu dos ovos ({menu}) não abriu; falas {falas}"
        return falas

    def _falar(self, menu: tuple[str, ...] | None, escolha: str | None = None) -> list[str]:
        """Diante do Carvalho (warp para o laboratório, abaixo dele): fala e avança tudo."""
        self._warp(LAB, OAK_FRONT)
        self.ctl.wait_overworld_idle(600)
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Carvalho")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da fala do Carvalho")
        return self._avancar(menu, escolha)

    def _vitoria(self) -> None:
        """Uma nova vitória na Liga: o script da entrada no Hall (o EnterHallOfFame não roda: a flag do jogo zerado já
        está ligada, então para os ovos é a 2ª vitória em diante)."""
        self.box.call_script(self.game.syms.addr(HALL_SCRIPT))
        self.emu.frames(2)      # o script do Hall só tem specials: pode acabar no mesmo quadro
        self.ctl.wait_overworld_idle(600)

    def _voltar(self, nome: str) -> None:
        self.ctl.restore(nome)
        self.emu.frames(SETTLE_FRAMES)

    # --- casos -----------------------------------------------------------------------------------------------------
    def escolha(self) -> str:
        self._prepare(OWNED_NEEDED)
        assert not any(self._elm_flags().values()), f"flags do Elm ligadas antes da cena: {self._elm_flags()}"
        antes = self._ovos()
        self._warp(PALLET, PALLET_PLAYER)
        self.ctl.wait_until(self.ctl.script_active, 600, "início da cena do Oak")
        falas = self._avancar(ELM, "CYNDAQUIL", until=self._scene_done, tela="johto_ovos_elm_menu", what="cena pós-Liga")
        assert self.game.location() == self.consts.map(LAB), self.game.location()
        novos = self._novos(antes)
        raros = [n for n in novos if f"SPECIES_{n}" in RARE_EGGS]
        assert len(raros) == 1 and novos.count("CYNDAQUIL") == 1 and len(novos) == 2, f"ovos novos {novos}"
        i_raro = next(i for i, f in enumerate(falas) if "recebeu o Ovo!" in f)
        i_elm = next(i for i, f in enumerate(falas) if FALA_PRIMEIRA in f)
        assert i_raro < i_elm, f"o do Elm veio antes do raro: {falas}"
        assert any("recebeu o Ovo" in f and "CYNDAQUIL" in f for f in falas), falas
        self._dados("CYNDAQUIL")
        f = self._elm_flags()
        assert f["GOT_ELM_EGG"] and not f["ELM_EGG_PENDING"], f
        assert self._nat_dex_on(), f"Dex Nacional {self._nat_dex()}"
        self.ctl.checkpoint("johto_elm_1")
        return f"cena: ovo raro de {raros[0]}, depois o menu {list(ELM)} → CYNDAQUIL; flags {f}"

    def hall(self) -> str:
        self._voltar("johto_elm_1")
        assert not self._flag("FLAG_ELM_EGG_PENDING"), "pendente ligado antes da vitória"
        self._vitoria()
        assert self._flag("FLAG_ELM_EGG_PENDING"), "a vitória não deixou o ovo do Elm pendente"
        assert self._flag("FLAG_RARE_EGG_PENDING"), "a vitória não deixou o ovo raro pendente"
        self.ctl.checkpoint("johto_elm_hall")
        return "script do Hall: FLAG_ELM_EGG_PENDING e FLAG_RARE_EGG_PENDING ligadas"

    def segunda(self) -> str:
        self._voltar("johto_elm_hall")
        antes = self._ovos()
        falas = self._falar(("CHIKORITA", "TOTODILE"), "TOTODILE")
        i_raro = next(i for i, f in enumerate(falas) if FALA_RARO in f)
        i_elm = next(i for i, f in enumerate(falas) if FALA_OUTRA in f)
        assert i_raro < i_elm, f"o do Elm veio antes do raro: {falas}"
        novos = self._novos(antes)
        raro = [n for n in novos if n != "TOTODILE"]
        assert len(novos) == 2 and "TOTODILE" in novos and f"SPECIES_{raro[0]}" in RARE_EGGS, novos
        self._dados("CYNDAQUIL", "TOTODILE")
        assert not self._flag("FLAG_ELM_EGG_PENDING") and not self._flag("FLAG_RARE_EGG_PENDING")
        # entregue o pendente, a próxima conversa não dá mais nada
        self._falar(None)
        assert len(self._novos(antes)) == 2, self._novos(antes)
        self.ctl.checkpoint("johto_elm_2")
        return f"conversa: ovo raro de {raro[0]}, depois o menu [CHIKORITA, TOTODILE] → TOTODILE; de novo, nada"

    def ultimo(self) -> str:
        self._voltar("johto_elm_2")
        self._vitoria()
        assert self._flag("FLAG_ELM_EGG_PENDING")
        self.box.set_flag(self.consts.flag("FLAG_RARE_EGG_PENDING"), False)   # só o do Elm nesta conversa
        antes = self._ovos()
        falas = self._falar(None)
        assert self._novos(antes) == ["CHIKORITA"], self._novos(antes)
        assert any(FALA_OUTRA in f for f in falas), falas
        self._dados(*ELM)
        assert not self._flag("FLAG_ELM_EGG_PENDING")
        self._vitoria()
        assert not self._flag("FLAG_ELM_EGG_PENDING"), "pendente ligado sem espécie para dar"
        return "com 1 restante, CHIKORITA sem menu; depois da 3ª, a vitória não deixa nada pendente"

    def _so_elm_pendente(self) -> None:
        self._voltar("johto_elm_hall")
        self.box.set_flag(self.consts.flag("FLAG_RARE_EGG_PENDING"), False)
        self._set_party(6)

    def pc(self) -> str:
        self._so_elm_pendente()
        equipe, no_pc = self._party_eggs(), [s for _, _, s in self._pc_eggs()]
        self._falar(("CHIKORITA", "TOTODILE"), "CHIKORITA")
        assert self._party_eggs() == equipe and len(self.game.party()) == 6
        novos = Counter(s for _, _, s in self._pc_eggs()) - Counter(no_pc)
        assert [self._nome(s) for s in novos.elements()] == ["CHIKORITA"], self._pc_eggs()
        self._dados("CYNDAQUIL", "CHIKORITA")
        assert not self._flag("FLAG_ELM_EGG_PENDING")
        return "equipe cheia: o ovo de CHIKORITA vai para o PC, flag ligada, pendente apagado"

    def cheio(self) -> str:
        self._so_elm_pendente()
        assert self.box.fill_pc() == 14 * IN_BOX_COUNT
        antes = self._ovos()
        falas = self._falar(("CHIKORITA", "TOTODILE"), "TOTODILE")
        assert any(TEXT_SEM_ESPACO in f for f in falas), f"o Carvalho não avisou da falta de espaço: {falas}"
        assert self._ovos() == antes, self._ovos()
        self._dados("CYNDAQUIL")
        assert self._flag("FLAG_ELM_EGG_PENDING"), "o pendente se perdeu sem entregar o ovo"
        # abre uma vaga no PC: a mesma oferta, com as mesmas duas opções
        self.emu.write(self._box_addr(0, 0), bytes(BOX_MON_SIZE))
        self._falar(("CHIKORITA", "TOTODILE"), "TOTODILE")
        assert [self._nome(s) for _, _, s in self._pc_eggs()] == ["TOTODILE"], self._pc_eggs()
        self._dados("CYNDAQUIL", "TOTODILE")
        assert not self._flag("FLAG_ELM_EGG_PENDING")
        return "sem vaga: aviso, nenhuma flag muda; com 1 vaga no PC, o mesmo menu e o TOTODILE no PC"

    def save_antigo(self) -> str:
        self._voltar("johto_elm_1")
        # save de antes do POK-28 que já passou da Dex Nacional: ovo raro dado, nenhuma flag do Elm
        for nome in [f"FLAG_GOT_EGG_{n}" for n in ELM] + ["FLAG_ELM_EGG_PENDING", "FLAG_GOT_ELM_EGG"]:
            assert not self.box.set_flag(self.consts.flag(nome), False), nome
        assert self._flag("FLAG_GOT_RARE_EGG") and not self._flag("FLAG_RARE_EGG_PENDING")
        antes = self._ovos()
        falas = self._falar(ELM, "TOTODILE")
        assert any(FALA_PRIMEIRA in f for f in falas), f"a 1ª oferta não veio: {falas}"
        assert self._novos(antes) == ["TOTODILE"], self._novos(antes)
        self._dados("TOTODILE")
        assert self._flag("FLAG_GOT_ELM_EGG") and not self._flag("FLAG_ELM_EGG_PENDING")
        return "estágio 8 sem flag do Elm: a conversa traz a 1ª oferta com os 3 e entrega o TOTODILE"


FANCLUBE, FANCLUBE_FRENTE = "MAP_VERMILION_CITY_POKEMON_FAN_CLUB", (5, 5)   # abaixo do Presidente, em (5, 4)
FALA_SNUBBULL, FALA_DICA = "recebeu um Snubbull", "precisa gostar muito de você"


class FaClube(PostLeagueScenario):
    """O Snubbull do Presidente do Fã-clube (Task 4), na mesma sessão do cenário.

    Cada caso monta a equipe com o 1º na amizade pedida, leva o jogador diante do Presidente (com o Vale Bicicleta já
    dado, salvo no caso `vale`), aperta A em tudo (a pergunta do apelido recebe B = NÃO) e confere equipe, PC,
    flag e falas."""

    def __init__(self, ctx: ScenarioContext, box: Mailbox):
        super().__init__(ctx)
        self.box = box
        self.snubbull = self.consts.species("SPECIES_SNUBBULL")
        self.telas: list[str] = []

    # --- leitura ---------------------------------------------------------------------------------------------------
    def _na_equipe(self) -> list[int]:
        return [m.level for m in self.game.party() if m.species == self.snubbull]

    def _no_pc(self) -> int:
        return sum(1 for b in range(14) for m in self.game.box_mons(b) if m is not None and m.species == self.snubbull)

    def _estado(self) -> tuple[int, int, bool]:
        """(Snubbull na equipe, Snubbull no PC, FLAG_GOT_SNUBBULL)."""
        return len(self._na_equipe()), self._no_pc(), self._flag("FLAG_GOT_SNUBBULL")

    # --- ações -----------------------------------------------------------------------------------------------------
    def _equipe(self, amizade: int, tamanho: int = 1) -> None:
        """Equipe só de Rattata, com o 1º na `amizade` dada."""
        for slot in range(tamanho):
            self.box.set_party_mon(slot, self._sp("SPECIES_RATTATA"), 5, friendship=amizade if slot == 0 else 70)
        assert self.box.party_size(tamanho) == tamanho

    def _voltar(self, nome: str) -> None:
        self.ctl.restore(nome)
        self.emu.frames(SETTLE_FRAMES)

    def _falar(self, sim_ao_vale: bool = False, tela: str | None = None) -> list[str]:
        """Diante do Presidente: fala e avança tudo. A pergunta sim/não recebe A (SIM) só se `sim_ao_vale`; no mais
        (o apelido do Snubbull) recebe B. Com `tela`, fotografa a caixa "recebeu um Snubbull" (só para o relatório)."""
        self._warp(FANCLUBE, FANCLUBE_FRENTE)
        self.ctl.wait_overworld_idle(600)
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante do Presidente")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da fala do Presidente")
        falas: list[str] = []
        spent = 0
        while not self._settled_idle():
            if spent >= SCENE_FRAMES:
                raise self.ctl.timeout_error("conversa com o Presidente")
            msg = self._message()
            if not falas or falas[-1] != msg:
                falas.append(msg)
                if tela and FALA_SNUBBULL in msg and not self.telas:
                    self.emu.frames(4)
                    self.telas.append(self._shot(tela))
            self._press(KEY_A if sim_ao_vale or YESNO_TASK not in self._tasks() else KEY_B)
            spent += 10
        return falas

    def _dica(self, falas: list[str]) -> bool:
        return any(FALA_DICA in f for f in falas)

    def _ganhou(self, falas: list[str]) -> bool:
        return any(FALA_SNUBBULL in f for f in falas)

    # --- casos -----------------------------------------------------------------------------------------------------
    def sim(self) -> str:
        self.box.set_flag(self.consts.flag("FLAG_GOT_BIKE_VOUCHER"), True)
        self.box.set_flag(self.consts.flag("FLAG_GOT_SNUBBULL"), False)
        self._equipe(255)
        self.ctl.checkpoint("johto_fanclube_base")
        assert self._estado() == (0, 0, False), self._estado()
        falas = self._falar(tela="johto_snubbull")
        assert self._ganhou(falas) and not self._dica(falas), falas
        assert self._na_equipe() == [20] and len(self.game.party()) == 2, self.game.party()
        assert self._estado() == (1, 0, True), self._estado()
        self.ctl.checkpoint("johto_fanclube_sim")
        return "amizade 255: Snubbull nv 20 na equipe (2º), flag ligada"

    def limite(self) -> str:
        self._voltar("johto_fanclube_base")
        self._equipe(199)
        falas = self._falar()
        assert self._dica(falas) and not self._ganhou(falas), falas
        assert self._estado() == (0, 0, False), self._estado()
        self._voltar("johto_fanclube_base")
        self._equipe(200)
        falas = self._falar()
        assert self._ganhou(falas) and self._estado() == (1, 0, True), (falas, self._estado())
        return "199 só a dica; 200 ganha o Snubbull"

    def baixa(self) -> str:
        self._voltar("johto_fanclube_base")
        self._equipe(100)
        falas = self._falar()
        assert self._dica(falas) and not self._ganhou(falas), falas
        assert self._estado() == (0, 0, False) and len(self.game.party()) == 1, self._estado()
        self._equipe(255)    # a dica não trava nada: gostando mais, ele dá
        falas = self._falar()
        assert self._ganhou(falas) and self._estado() == (1, 0, True), (falas, self._estado())
        return "amizade 100: dica, nada muda; com 255 depois, ganha"

    def segunda(self) -> str:
        self._voltar("johto_fanclube_sim")
        falas = self._falar()
        assert not self._ganhou(falas) and not self._dica(falas), falas
        assert self._estado() == (1, 0, True) and len(self.game.party()) == 2, self._estado()
        return "depois de ganhar, a conversa não dá outro (nem repete a dica)"

    def pc(self) -> str:
        self._voltar("johto_fanclube_base")
        self._equipe(255, 6)
        falas = self._falar()
        assert self._ganhou(falas), falas
        assert self._estado() == (0, 1, True) and len(self.game.party()) == 6, self._estado()
        return "equipe cheia: o Snubbull vai para o PC, flag ligada"

    def cheio(self) -> str:
        self._voltar("johto_fanclube_base")
        self._equipe(255, 6)
        assert self.box.fill_pc() == 14 * IN_BOX_COUNT
        falas = self._falar()
        assert any("não há mais espaço" in f.lower() for f in falas), f"sem o aviso: {falas}"
        assert not self._ganhou(falas), falas
        assert self._estado() == (0, 0, False) and len(self.game.party()) == 6, self._estado()
        self.emu.write(self._box_addr(0, 0), bytes(BOX_MON_SIZE))     # abre uma vaga no PC
        falas = self._falar()
        assert self._ganhou(falas) and self._estado() == (0, 1, True), (falas, self._estado())
        return "sem vaga: aviso e flag desligada; com 1 vaga no PC, o Snubbull vem"

    def vale(self) -> str:
        self._voltar("johto_fanclube_base")
        bike = self.consts.item("ITEM_BIKE_VOUCHER")
        self.box.set_flag(self.consts.flag("FLAG_GOT_BIKE_VOUCHER"), False)
        self._equipe(255)
        assert self.game.bag_quantity(bike) == 0
        falas = self._falar(sim_ao_vale=True)
        assert any("Vale Bicicleta" in f for f in falas), falas
        assert not self._ganhou(falas) and self._estado() == (0, 0, False), (falas, self._estado())
        assert self.game.bag_quantity(bike) == 1 and self._flag("FLAG_GOT_BIKE_VOUCHER")
        falas = self._falar()
        assert self._ganhou(falas) and self._estado() == (1, 0, True), (falas, self._estado())
        assert self.game.bag_quantity(bike) == 1
        return "1ª conversa: pergunta, SIM, Vale Bicicleta e nada de Snubbull; a seguinte dá o Snubbull"


TRILHA = "MAP_SIX_ISLAND_GREEN_PATH"
SUDOWOODO_XY, DIANTE_SUDOWOODO = (39, 10), (39, 11)   # o recanto ao norte do caminho e o tile logo abaixo dele
SAIDA_MOITA, MARGEM_OESTE, PORTA_MOITA = (46, 11), (37, 15), (46, 10)
FALA_ARVORE, FALA_FUGIU = "árvore estranha", "saiu correndo"
OBJ_EVENTS, OBJ_EVENT_SIZE, OBJ_MAP_OFFSET = 16, 0x24, 7       # gObjectEvents[16]; coordenadas com MAP_OFFSET
BATTLE_TYPE_LEGENDARY, BATTLE_TYPE_WILD_SCRIPTED, BATTLE_TYPE_LEGENDARY_FRLG = 1 << 13, 1 << 17, 1 << 18


class TrilhaVerde(PostLeagueScenario):
    """O Sudowoodo do Caminho Verde (Task 5), na mesma sessão do cenário.

    A equipe é só um Mewtwo nv 100 (foge sempre e vence num golpe). Cada caso entra no mapa pelo atalho de warp (o
    ON_TRANSITION roda de verdade), fala com a "árvore" de baixo dela e leva a batalha selvagem até o fim; a volta pelo
    Hall é o script da entrada no Hall (`CMD_CALL_SCRIPT`)."""

    def __init__(self, ctx: ScenarioContext, box: Mailbox):
        super().__init__(ctx)
        self.box = box
        self.sudowoodo = self.consts.species("SPECIES_SUDOWOODO")
        self.gfx = header_defines(REPO_ROOT, "event_objects.h")["OBJ_EVENT_GFX_SUDOWOODO"]
        self.driver = BattleDriver(self.ctl)
        self.driver.move_policy = "best"
        self.telas: list[str] = []

    # --- leitura ---------------------------------------------------------------------------------------------------
    def _no_mapa(self) -> tuple[int, int] | None:
        """(x, y) do objeto ativo com o gráfico do Sudowoodo, ou None."""
        base = self.game.syms.addr("gObjectEvents")
        achados = []
        for i in range(OBJ_EVENTS):
            o = base + i * OBJ_EVENT_SIZE
            if self.emu.read_u8(o) & 1 and self.emu.read_u8(o + 5) == self.gfx:
                x, y = struct.unpack("<hh", self.emu.read(o + 0x10, 4))
                achados.append((x - OBJ_MAP_OFFSET, y - OBJ_MAP_OFFSET))
        assert len(achados) <= 1, achados
        return achados[0] if achados else None

    def _estado(self) -> tuple[tuple[int, int] | None, bool, bool]:
        """(posição do objeto, FLAG_HIDE_SUDOWOODO, FLAG_SUDOWOODO_FLEW_AWAY)."""
        return self._no_mapa(), self._flag("FLAG_HIDE_SUDOWOODO"), self._flag("FLAG_SUDOWOODO_FLEW_AWAY")

    def _na_equipe(self) -> list[int]:
        return [m.level for m in self.game.party() if m.species == self.sudowoodo]

    # --- ações -----------------------------------------------------------------------------------------------------
    def _entrar(self, xy: tuple[int, int] = DIANTE_SUDOWOODO) -> None:
        """Entra no Caminho Verde em `xy` pelo atalho de warp (o ON_TRANSITION decide se o Sudowoodo aparece)."""
        self._warp(TRILHA, xy)
        self.ctl.wait_overworld_idle(600)
        self.emu.frames(SETTLE_FRAMES)

    def _voltar(self, nome: str) -> None:
        self.ctl.restore(nome)
        self.emu.frames(SETTLE_FRAMES)

    def _vitoria(self) -> None:
        """Uma nova entrada no Hall (o script de verdade, como em OvosElm._vitoria)."""
        self.box.call_script(self.game.syms.addr(HALL_SCRIPT))
        self.emu.frames(2)
        self.ctl.wait_overworld_idle(600)

    def _falar(self) -> list[str]:
        """De baixo da árvore: olha para cima, fala e avança as falas até a batalha começar. Devolve as falas."""
        self._entrar()
        self.emu.hold(KEY_UP, 4)
        self.ctl.wait_until(self.nav._player_still, 60, "jogador parado diante da árvore")
        self._press(KEY_A)
        self.ctl.wait_until(self.ctl.script_active, 120, "início da fala da árvore")
        falas: list[str] = []
        spent = 0
        while not self.game.in_battle():
            if spent >= SCENE_FRAMES:
                raise self.ctl.timeout_error("fala da árvore até a batalha")
            msg = self._message()
            if not falas or falas[-1] != msg:
                falas.append(msg)
            self._press(KEY_A)
            spent += 10
        return falas

    def _batalha(self) -> str:
        """No menu de ação: confere espécie, nível e o tipo de batalha (selvagem comum, não a de lendário)."""
        self.driver.wait_action_menu()
        especie, nivel = self.driver.battler_species_level(1)
        assert (especie, nivel) == (self.sudowoodo, 35), (self._nome(especie), nivel)
        tipo = self.driver.battle_type_flags()
        assert tipo & BATTLE_TYPE_WILD_SCRIPTED, f"gBattleTypeFlags {tipo:#x}"
        assert not tipo & (BATTLE_TYPE_LEGENDARY | BATTLE_TYPE_LEGENDARY_FRLG), f"gBattleTypeFlags {tipo:#x}"
        return f"SUDOWOODO nv {nivel}, gBattleTypeFlags {tipo:#x}"

    def _nome(self, species_id: int) -> str:
        return self.consts.species_name(species_id).removeprefix("SPECIES_")

    def _ate_o_campo(self) -> list[str]:
        """Depois da batalha: A em tudo (B no apelido do capturado) até o campo ficar livre. Devolve as falas."""
        falas: list[str] = []
        spent = 0
        while not self._settled_idle():
            if spent >= SCENE_FRAMES:
                raise self.ctl.timeout_error("volta ao campo depois da batalha")
            if not self.game.in_battle():
                msg = self._message()
                if not falas or falas[-1] != msg:
                    falas.append(msg)
            self._press(KEY_B if self.driver._script_command() == NICKNAME_COMMAND else KEY_A)
            spent += 10
        return falas

    def _sumiu_ate_o_hall(self) -> str:
        """Fuga ou derrota: sumiu e não volta ao reentrar; o Hall o traz de volta ao mesmo lugar."""
        assert self._estado() == (None, True, True), self._estado()
        self._entrar()
        assert self._estado() == (None, True, True), f"voltou sem o Hall: {self._estado()}"
        self._vitoria()
        assert not self._flag("FLAG_SUDOWOODO_FLEW_AWAY"), "o Hall não apagou FLAG_SUDOWOODO_FLEW_AWAY"
        self._entrar()
        assert self._estado() == (SUDOWOODO_XY, False, False), f"depois do Hall: {self._estado()}"
        return "sumiu, não volta ao reentrar; depois do Hall, de volta em (39, 10)"

    # --- casos -----------------------------------------------------------------------------------------------------
    def dex(self) -> str:
        self.box.set_party_mon(0, self._sp("SPECIES_MEWTWO"), 100)
        assert self.box.party_size(1) == 1
        assert not self.box.set_flag(self.consts.flag("FLAG_SUDOWOODO_FLEW_AWAY"), False)
        # sem a Dex Nacional (IsNationalPokedexEnabled pede a flag, a var e o byte mágico: basta a flag)
        assert not self.box.set_flag(self.consts.flag("FLAG_SYS_NATIONAL_DEX"), False)
        assert not self._nat_dex_on()
        self._entrar()
        assert self._estado() == (None, True, False), f"sem a Dex Nacional: {self._estado()}"
        assert self.box.enable_national_dex()
        self._entrar()
        assert self._estado() == (SUDOWOODO_XY, False, False), f"com a Dex Nacional: {self._estado()}"
        assert not self._na_equipe()
        self.ctl.checkpoint("johto_sudowoodo_base")
        self._entrar((41, 12))          # um pouco de lado, para a foto mostrar o recanto e o caminho
        self.emu.frames(240)            # o aviso com o nome do mapa já saiu da tela
        self.telas.append(self._shot("johto_sudowoodo"))
        return "sem a Dex Nacional: escondido (flag ligada, nenhum objeto); com ela: em (39, 10)"

    def passa(self) -> str:
        """Com ele no lugar, anda da saída da Moita Estampada até a margem oeste (onde se surfa) passando logo abaixo
        dele, volta e entra na Moita de novo: o caminho obrigatório continua livre."""
        self._voltar("johto_sudowoodo_base")
        self._entrar(SAIDA_MOITA)
        assert self._no_mapa() == SUDOWOODO_XY
        trechos = [DIANTE_SUDOWOODO, MARGEM_OESTE, SAIDA_MOITA]
        for alvo in trechos:
            assert self.nav.walk_to(*alvo), f"não chegou a {alvo} (está em {self.game.player_xy()})"
            assert self._no_mapa() == SUDOWOODO_XY, "o Sudowoodo saiu do lugar"
        destino = self.nav.go_through_warp("up")
        moita = self.consts.map("MAP_SIX_ISLAND_PATTERN_BUSH")
        assert self.game.location() == moita, (self.game.location(), destino)
        return f"(46, 11) → (39, 11) → {MARGEM_OESTE} → (46, 11) → Moita Estampada, com ele em (39, 10)"

    def captura(self) -> str:
        self._voltar("johto_sudowoodo_base")
        master = self.consts.item("ITEM_MASTER_BALL")
        assert self.box.call(CMD_GIVE_ITEM, master, 1) == 1
        falas = self._falar()
        assert any(FALA_ARVORE in f for f in falas), falas
        batalha = self._batalha()
        assert self.driver.throw_ball(master), "a Master Ball não capturou"
        self._ate_o_campo()
        assert self.driver.outcome() == B_OUTCOME_CAUGHT, f"gBattleOutcome = {self.driver.outcome()}"
        assert self._na_equipe() == [35], self.game.party()
        assert self._estado() == (None, True, False), f"depois da captura: {self._estado()}"
        self._entrar()
        assert self._estado() == (None, True, False), f"reentrando: {self._estado()}"
        self._vitoria()
        self._entrar()
        assert self._estado() == (None, True, False), f"capturado, voltou depois do Hall: {self._estado()}"
        return f"{batalha}; capturado: some, não volta nem ao reentrar nem depois do Hall"

    def fuga(self) -> str:
        self._voltar("johto_sudowoodo_base")
        falas = self._falar()
        assert any(FALA_ARVORE in f for f in falas), falas
        batalha = self._batalha()
        assert self.driver.run_away(), "a fuga falhou"
        falas = self._ate_o_campo()
        assert any(FALA_FUGIU in f for f in falas), falas
        assert not self._na_equipe()
        return f"{batalha}; fuga: {self._sumiu_ate_o_hall()}"

    def vitoria(self) -> str:
        self._voltar("johto_sudowoodo_base")
        self._falar()
        batalha = self._batalha()
        assert self.driver.fight_to_end() == "win", f"gBattleOutcome = {self.driver.outcome()}"
        falas = self._ate_o_campo()
        assert any(FALA_FUGIU in f for f in falas), falas
        return f"{batalha}; derrotado: {self._sumiu_ate_o_hall()}"


def run_full_johto(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    JohtoScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only johto ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "johto", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
