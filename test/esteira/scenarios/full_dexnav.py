"""Modo completo: DexNav (POK-47), na build de teste.

Sessão própria da ROM de teste a partir do .sav do `captura` (`save_from="captura"`), com o aviso das conquistas em
silêncio. A preparação (`_start`, savestate `dexnav_base`) deixa tudo que a tela mostra igual em toda execução, seja
qual for o inicial ou o Pokémon capturado no `captura`: relógio no dia 0 ao meio-dia (tarde; Caverna Mutante no
conjunto 0), a Pokédex reescrita na RAM (capturados: Bulbasaur, Pidgey e os 7 de Viridian, que fica completa; só
vistos: Rattata, Oddish, Spinarak e Mew), os mapas visitados (Cidade de Viridian, Rotas 1, 12 e 22 e Estrada Fagulha), o último
mapa com encontro (Rota 1) e a trava de Tanoby fechada. As expectativas saem de `tools/dexnav/gerar.py` (o espelho
Python das regras de encontro), não do C.

- `dexnav/entradas_c_python` (R2): `DexNav_GetMapEntries` (atalhos 0xE0/0xE1) == `gerar.enumerar` nos 124 mapas
  (espécie, jeito, períodos, chance de cada período, a da tarde-noite e níveis);
- `dexnav/chances_reais` (R4): o gerador real de encontro (TEST_CMD_DEXNAV_ROLL, 2000 sorteios) contra a chance
  enumerada, com tolerância em desvios-padrão da binomial (`dexnav.comparar`): Rota 1 à tarde, à noite e na
  tarde-noite (mistura 50/50), Mansão 1F (metade LeafGreen) e Super Vara em Viridian;
- `dexnav/caverna_mutante`: dia 22, entrar põe a var no conjunto 4 e o C, o Python e o sorteio real batem (Teddiursa);
  no dia 23, ainda dentro, continua o conjunto 4 (a var só muda ao entrar); de fora, o DexNav já mostra o conjunto 5
  (Aipom), e entrar de novo põe a var em 5 e o sorteio bate com ele;
- `dexnav/tanoby`: câmara Monean trancada: 0 entradas, o gerador real sem encontro e, aberta de dentro, o modo mapa com
  0 espécies (topo "?/?" apagado, foto `dexnav_tanoby_trancada`); liberada: Unown 100% no C, no Python e no sorteio
  real;
- `dexnav/extra_tarde_noite`: de manhã, na Rota 24, as espécies só da tarde e da noite viram "+N à tarde/noite";
- `dexnav/abre_start`: no quarto (sem encontro) o menu Start tem DEXNAV logo abaixo de POKéDEX (8 linhas; foto
  `dexnav_menu_start`); na Rota 1 o DEXNAV abre o modo mapa e B volta ao menu Start com o cursor no DEXNAV;
- `dexnav/mapa_sem_encontro`: no quarto, abre a lista na Rota 1 (o último mapa com encontro) e B volta ao menu;
- `dexnav/marcas`: Rota 1 à tarde: as linhas (Pidgey ●, Rattata ◐, Sentret ?) na ordem da chance, contadores 1/4,
  a linha "+1 à noite" (Hoothoot) e os períodos (foto `dexnav_mapa`); com os 4 capturados, 4/4 (foto do mapa
  completo, para os olhos);
- `dexnav/abas` (R6): a Estrada Fagulha aberta pela lista tem as 4 abas; R dá a volta, L volta; em cada aba o número
  de Pokémon e os contadores; na VARAS, rolada até o fim: as 9 linhas nas 3 seções na ordem, o topo rolado e de volta
  a 0, contadores e sem linha extra;
- `dexnav/lista`: SELECT abre a lista de Kanto na Rota 1 (foto `dexnav_lista`); todas as linhas das duas regiões
  (mapa, visitado, capturados, total) e os completos de cada região (Viridian completa);
- `dexnav/nao_visitado` (R11): A num mapa não visitado (Rota 24) não abre; a câmara Monean visitada com Tanoby
  trancada é "?/?" (visitada e total 0) e A não abre; liberada, mostra 0/1 e abre; A num resultado da busca não
  visitado não abre;
- `dexnav/busca_so_vistos`: START abre a escolha na espécie selecionada no mapa (Pidgey); as linhas são só as espécies
  vistas com encontro, na ordem da Pokédex Nacional, com o número de mapas de cada uma (sem o Mew, visto sem
  encontro, nem o Hoothoot, que nunca foi visto);
- `dexnav/busca_resultado` (R11): os 9 mapas do Oddish na ordem real (primeiro os de agora, depois por chance; empate
  na ordem dos mapas), com jeito, períodos, visitado e o horário mostrado (foto `dexnav_busca_resultado`); e o Spinarak
  (R14): fora do horário, a maior chance de um período só com o nome dele (Rota 2: "36% noite", não a média de manhã e
  noite; foto `dexnav_busca_dois_horarios`);
- `dexnav/navegacao` (R10): mapa → lista → mapa → busca → resultado → mapa (Rota 12, na linha do Oddish) e B em cadeia
  até o campo, cada tela de volta com a seleção de antes; SELECT volta à lista que está na pilha;
- `dexnav/select`: REGISTRAR na bolsa, SELECT no campo abre o DexNav e B volta ao campo com o controle livre;
- `dexnav/bolsa`: USAR na bolsa abre o DexNav e B volta à bolsa no mesmo bolso e posição;
- `dexnav/bolso_cheio`: sem o item e com o bolso de itens-chave cheio, salvar e CONTINUAR não trava nem dá o item, e
  o menu Start ainda abre o DEXNAV;
- `dexnav/save_antigo`: área do DexNav zerada (save de antes do DexNav), salvar e CONTINUAR: zerado
  (FLAG_SYS_GAME_CLEAR) = os 124 visitados; não zerado = nenhum, e daí em diante só os novos.

Telas comparadas (SHARED_POINTS): dexnav_mapa, dexnav_lista, dexnav_busca_resultado, dexnav_menu_start.

Uso, a partir de test/ (a pasta OUT precisa do captura.sav de um `rapido`/`completo`):
    python3 -m esteira completo --rom R --elf E --out OUT --only dexnav
Numa janela, em tempo real: `make test-watch CENARIO=dexnav`.
"""

import importlib.util
import json
import re
import struct
import sys
from functools import cache

from .. import dexnav as dnv
from ..bag import BAG_CONTEXT_TASK, BAG_CURSOR_POS, BAG_ITEMS_ABOVE, BAG_POCKET, Bag
from ..emu import KEY_A, KEY_B, KEY_DOWN, KEY_L, KEY_LEFT, KEY_R, KEY_RIGHT, KEY_SELECT, KEY_START, KEY_UP
from ..field_menu import MENU_TIMEOUT, STARTMENU_BAG, STARTMENU_DEXNAV, STARTMENU_POKEDEX
from ..game import SB1_BAG_POCKETS
from ..breeding import header_defines
from ..hooks import CMD_DEXNAV_ROLL, CMD_WARP, NO_RESULT, Mailbox
from . import REPO_ROOT, ScenarioContext
from .base import Abort
from .quick_catch_save import CatchSaveScenario

# Telas comparadas com a referência (test/referencias/COMUM/: a Pokédex e os visitados são os da preparação)
SCREEN_POINTS = ("dexnav_mapa", "dexnav_lista", "dexnav_busca_resultado", "dexnav_menu_start")

GERAR = REPO_ROOT / "tools" / "dexnav" / "gerar.py"
POKEDEX_H = REPO_ROOT / "include" / "constants" / "pokedex.h"
MAPS_DIR = REPO_ROOT / "data" / "maps"

CLOCK = (0, 12 * 60)          # dia 0, 12:00 (tarde): clima limpo; a Caverna Mutante de fora fica no conjunto do dia
MUTANTE = 0                   # GetAlteringCaveSetForScript = dia % 9
MANHA, DIA, NOITE = 1, 2, 4   # DEXNAV_PERIOD_* (include/dexnav.h)
TARDE_NOITE = DIA | NOITE     # DexNav_CurrentPeriodBit na tarde-noite (TIME_EVENING)
MODO_MAPA, MODO_LISTA, MODO_BUSCA = 0, 1, 2
ESCOLHA, RESULTADO = 0, 1     # DEXNAV_SEARCH_*
KANTO, SEVII = 0, 1
MARCA_CAPTURADO, MARCA_VISTO, MARCA_NUNCA = 0, 1, 2
ABA_DO_METODO = (0, 1, 2, 2, 2, 3)   # sAbaDoMetodo: GRAMA, SURFAR, VARAS (3 varas), PEDRA
LAST_MAP_NONE = 0xFF

# struct DexNavSave em SaveBlock1 + 0x3A94: u32 magic, u8 visitedMaps[16], u8 lastMapIndex, u8 unused[43]
DEXNAV_AREA, DEXNAV_AREA_SIZE, DEXNAV_LAST = dnv.SB1_DEXNAV, 64, 0x14
# Pokédex: SaveBlock2.pokedex.owned/seen e as duas cópias de seen no SaveBlock1 (as três precisam bater)
SB2_DEX_OWNED, SB2_DEX_SEEN = 0x28, 0x5C
SB1_DEX_SEEN_COPIES = (0x5F8, 0x3A18)
DEX_BYTES = 52
SB1_REGISTERED_ITEM = 0x296
ITEMMENUACTION_REGISTER = 2

# A Pokédex da preparação (nomes de NATIONAL_DEX_*)
CAPTURADOS = ("BULBASAUR", "PIDGEY", "PSYDUCK", "POLIWAG", "POLIWHIRL", "SLOWPOKE", "GOLDEEN", "MAGIKARP",
              "GYARADOS")   # os 7 de Viridian (surf e varas): Viridian completa
SO_VISTOS = ("RATTATA", "ODDISH", "SPINARAK", "MEW")   # Mew: visto, sem encontro em mapa nenhum
VISITADOS = ("MAP_VIRIDIAN_CITY", "MAP_ROUTE1", "MAP_ROUTE12", "MAP_ROUTE22", "MAP_ONE_ISLAND_KINDLE_ROAD")
ULTIMO = "MAP_ROUTE1"

ROUTE1_XY = (12, 20)
QUARTO = "MAP_PALLET_TOWN_PLAYERS_HOUSE_2F"
NAO_VISITADO = "MAP_ROUTE24"
CAMARA = "MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER"
ABAS_MAPA = "MAP_ONE_ISLAND_KINDLE_ROAD"
BUSCA = "ODDISH"
BUSCA_DOIS_HORARIOS = "SPINARAK"   # Rota 2: manhã 4% e noite 36% (R14)
BUSCA_ABRE = "MAP_ROUTE12"
EXTRA_TARDE_NOITE = "MAP_ROUTE24"   # de manhã, a grama tem espécies só da tarde e da noite
MANHA_MINUTO = 7 * 60
MUTANTE_MAPA = "MAP_SIX_ISLAND_ALTERING_CAVE"
MUTANTE_DIAS = (22, 23)       # conjuntos 4 (Teddiursa) e 5 (Aipom): o de fora no dia 23 difere da var de dentro
NUM_CONJUNTOS_MUTANTE = 9     # NUM_ALTERING_CAVE_TABLES (gerar.NUM_CONJUNTOS_MUTANTE)
SB1_VARS, VAR_BASE = 0x1000, 0x4000   # u16 vars[] em SaveBlock1
VARS = header_defines(REPO_ROOT, "vars.h")

ROLAGENS = 2000               # sorteios por linha do chances_reais
TELA_TIMEOUT = 600            # a lista e a busca varrem os 124 mapas antes (~15 quadros)
ASSENTA = 8                   # quadros depois da entrada pronta, antes de ler/fotografar


@cache
def _gerar():
    """tools/dexnav/gerar.py carregado pelo caminho (como em test_dexnav_dados.py)."""
    spec = importlib.util.spec_from_file_location("dexnav_gerar_cenario", GERAR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@cache
def _nacional() -> dict[str, int]:
    """NATIONAL_DEX_X -> número, do 1º enum de include/constants/pokedex.h (NONE = 0)."""
    texto = POKEDEX_H.read_text(encoding="utf-8")
    bloco = texto[texto.index("enum {"):texto.index("};")]
    nomes = re.findall(r"^\s*NATIONAL_DEX_(\w+),", bloco, re.M)
    return {n: i for i, n in enumerate(nomes)}


@cache
def _warp_xy(map_id: str) -> tuple[int, int]:
    """O 1º warp do mapa (onde o jogador chega ao entrar por ele)."""
    for path in MAPS_DIR.glob("*/map.json"):
        m = json.loads(path.read_text(encoding="utf-8"))
        if m["id"] == map_id:
            w = m["warp_events"][0]
            return w["x"], w["y"]
    raise KeyError(map_id)


def taxa(chances: list[int], bits: int) -> int:
    """DexNav_RateForPeriods: a média arredondada das colunas dos períodos em `bits`."""
    cols = [chances[i] for i in range(3) if bits >> i & 1]
    return (sum(cols) + len(cols) // 2) // len(cols) if cols else 0


def linha_resultado(chances: list[int], periodos: int, bits: int) -> tuple[bool, int, int]:
    """Uma linha do resultado da busca (ColherResultados, src/dexnav.c): (aparece agora, chance ‰, períodos do horário
    mostrado). Agora: a chance de agora (`taxa` com os bits de agora: a tarde-noite é a média) e todos os períodos em
    que aparece. Fora do horário: a maior chance de um período só e esse período (os empatados juntos); nunca a média
    de horários diferentes (R14)."""
    if periodos & bits:
        return True, taxa(chances, bits), periodos
    maior = max(chances[i] for i in range(3) if periodos >> i & 1)
    return False, maior, sum(1 << i for i in range(3) if periodos >> i & 1 and chances[i] == maior)


class DexNavScenario(CatchSaveScenario):
    def __init__(self, ctx: ScenarioContext):
        super().__init__(ctx)
        self.box: Mailbox | None = None
        self.g = _gerar()
        self.mapas = self.g.mapas()
        self.idx = {m["id"]: i for i, m in enumerate(self.mapas)}
        self.nac = _nacional()
        self.capturados = {self.nac[n] for n in CAPTURADOS}
        self.vistos = self.capturados | {self.nac[n] for n in SO_VISTOS}
        self.visitados = {self.idx[m] for m in VISITADOS}
        self._esperado: dict[tuple[int, bool], list[dict]] = {}
        self._dia = CLOCK[0]
        assert self.g.NUM_CONJUNTOS_MUTANTE == NUM_CONJUNTOS_MUTANTE and self.g.MUTANTE == MUTANTE_MAPA

    # --- expectativas (gerar.py) -----------------------------------------------------------------------------------
    def _nac_de(self, especie: str) -> int:
        return self.nac[especie.removeprefix("SPECIES_")]

    def _entradas(self, mapa: int, tanoby: bool = False) -> list[dict]:
        """gerar.enumerar do mapa `mapa` (índice), com a espécie em número (`id`) e na Pokédex (`nac`)."""
        chave = (mapa, tanoby)
        if chave not in self._esperado:
            out = []
            for e in self.g.enumerar(self.mapas[mapa]["id"], conjunto_mutante=MUTANTE, tanoby_liberado=tanoby):
                out.append(dict(e, id=self.consts.species(e["especie"]), nac=self._nac_de(e["especie"])))
            self._esperado[chave] = out
        return self._esperado[chave]

    def _marca(self, nac: int) -> int:
        if nac in self.capturados:
            return MARCA_CAPTURADO
        return MARCA_VISTO if nac in self.vistos else MARCA_NUNCA

    def _contar(self, entradas: list[dict]) -> tuple[int, int]:
        """(capturados, total) das espécies distintas de `entradas`."""
        nacs = {e["nac"] for e in entradas}
        return len(nacs & self.capturados), len(nacs)

    def _aba(self, mapa: int, aba: int, bits: int) -> dict:
        """O que a aba mostra no período `bits`: linhas (espécie, jeito), por chance em cada jeito; a linha extra (quantas
        espécies só de outro período e os períodos delas) e os contadores da aba."""
        es = [e for e in self._entradas(mapa) if ABA_DO_METODO[e["metodo"]] == aba]
        linhas = []
        for m in range(6):
            agora = [e for e in es if e["metodo"] == m and e["periodos"] & bits]
            agora.sort(key=lambda e: -taxa(e["chances"], bits))
            linhas += [(e["id"], m, self._marca(e["nac"])) for e in agora]
        aparecem = {e["id"] for e in es if e["periodos"] & bits}
        fora = [e for e in es if e["id"] not in aparecem]
        periodos = 0
        for e in fora:
            periodos |= e["periodos"]
        cap, tot = self._contar(es)
        return {"linhas": linhas, "extra": len({e["id"] for e in fora}), "periodos_extra": periodos,
                "capturados": cap, "total": tot}

    def _abas(self, mapa: int) -> list[int]:
        return sorted({ABA_DO_METODO[e["metodo"]] for e in self._entradas(mapa)})

    def _linha_lista(self, mapa: int) -> tuple[int, int, int, int]:
        cap, tot = self._contar(self._entradas(mapa))
        return mapa, int(mapa in self.visitados), cap, tot

    def _completos(self, regiao: int) -> tuple[int, int]:
        mapas = [i for i, m in enumerate(self.mapas) if m["regiao"] == regiao]
        completos = 0
        for i in mapas:
            cap, tot = self._contar(self._entradas(i))
            completos += i in self.visitados and tot != 0 and cap == tot
        return completos, len(mapas)

    def _mapas_da_especie(self) -> dict[int, int]:
        """Nº nacional -> em quantos mapas a espécie aparece (qualquer jeito e período)."""
        out: dict[int, int] = {}
        for i in range(len(self.mapas)):
            for nac in {e["nac"] for e in self._entradas(i)}:
                out[nac] = out.get(nac, 0) + 1
        return out

    def _resultado(self, especie: str, bits: int) -> list[tuple[int, int, int, int]]:
        """As linhas do resultado da busca: (mapa, jeito, períodos, visitado | períodos do horário mostrado << 4), uma
        seção por jeito; em cada uma os de agora primeiro, depois por chance (empate: a ordem dos mapas)."""
        res = []
        for i in range(len(self.mapas)):
            for e in self._entradas(i):
                if e["especie"] == f"SPECIES_{especie}":
                    agora, chance, mostrados = linha_resultado(e["chances"], e["periodos"], bits)
                    res.append((i, e["metodo"], e["periodos"], int(i in self.visitados) | mostrados << 4, agora,
                                chance))
        out = []
        for m in range(6):
            secao = sorted((r for r in res if r[1] == m), key=lambda r: (not r[4], -r[5]))
            out += [r[:4] for r in secao]
        return out

    # --- RAM ---------------------------------------------------------------------------------------------------------
    def _sb(self, n: int) -> int:
        return self.emu.read_u32(self.game.syms.addr(f"gSaveBlock{n}Ptr"))

    def _escrever_pokedex(self, capturados: set[int], vistos: set[int]) -> None:
        def bits(nums: set[int]) -> bytes:
            raw = bytearray(DEX_BYTES)
            for n in nums:
                raw[(n - 1) // 8] |= 1 << ((n - 1) % 8)
            return bytes(raw)
        sb1, sb2 = self._sb(1), self._sb(2)
        self.emu.write(sb2 + SB2_DEX_OWNED, bits(capturados))
        for addr in (sb2 + SB2_DEX_SEEN, sb1 + SB1_DEX_SEEN_COPIES[0], sb1 + SB1_DEX_SEEN_COPIES[1]):
            self.emu.write(addr, bits(vistos))

    def _visitar(self, mapas: set[int], ultimo: int) -> None:
        raw = bytearray(16)
        for i in mapas:
            raw[i // 8] |= 1 << (i % 8)
        area = self._sb(1) + DEXNAV_AREA
        self.emu.write(area + 4, bytes(raw))
        self.emu.write(area + DEXNAV_LAST, bytes([ultimo]))

    def _marcar_visitado(self, mapa: int, on: bool = True) -> None:
        addr = self._sb(1) + DEXNAV_AREA + 4 + mapa // 8
        v = self.emu.read_u8(addr)
        self.emu.write(addr, bytes([(v | 1 << (mapa % 8)) if on else (v & ~(1 << (mapa % 8)) & 0xFF)]))

    def _ultimo(self) -> int:
        return self.emu.read_u8(self._sb(1) + DEXNAV_AREA + DEXNAV_LAST)

    def _flag(self, name: str, on: bool) -> None:
        assert self.box.set_flag(self.consts.flag(name), on) == on, name

    def _teleport(self, map_id: str, xy: tuple[int, int] | None = None) -> None:
        group, num = self.consts.map(map_id)
        x, y = xy or _warp_xy(map_id)
        self.box.call(CMD_WARP, group | num << 8, x | y << 16)
        self.ctl.wait_until(lambda: self.game.location() == (group, num), 600, f"warp para {map_id}")
        self.ctl.wait_overworld_idle(900)
        self.emu.frames(30)

    def _qtd_dexnav(self) -> int:
        dexnav = self.consts.item("ITEM_DEXNAV")
        return sum(q for it, q in self.game.bag_pocket(1) if it == dexnav)

    # --- a tela ------------------------------------------------------------------------------------------------------
    def _tela(self, what: int = 0) -> dict | None:
        return self.box.dexnav_tela(what)

    def _pronta(self, what: str = "DexNav pronto") -> None:
        self.ctl.wait_until(lambda: (self._tela(1) or {}).get("pronta") == 1, TELA_TIMEOUT, what)
        self.emu.frames(ASSENTA)

    def _tecla(self, key: int, what: str = "DexNav pronto depois da tecla") -> None:
        self.emu.press(key, hold=2, release=4)
        self._pronta(what)

    def _abrir(self) -> int | None:
        """Abre pelo atalho (script de campo) no mapa atual e espera a entrada."""
        mapa = self.box.open_dexnav()
        self.ctl.wait_until(lambda: self._tela() is not None, 120, "DexNav aberto")
        self._pronta("DexNav aberto e pronto")
        return mapa

    def _fechar(self) -> None:
        """B até sair do DexNav (de qualquer tela da pilha)."""
        for _ in range(12):
            if self._tela() is None:
                return
            self.emu.press(KEY_B, hold=2, release=4)
            self.ctl.wait_until(lambda: self._tela() is None or (self._tela(1) or {}).get("pronta") == 1,
                                TELA_TIMEOUT, "DexNav depois do B")
        assert self._tela() is None, "o DexNav não fechou com B"

    def _estado(self) -> tuple[int, int, int, int]:
        """(modo, aba, mapa, pilha)."""
        s0, s5 = self._tela(0), self._tela(5)
        return s0["modo"], s0["aba"], s0["mapa"], s5["pilha"]

    def _cursor(self) -> tuple[int, int]:
        s = self._tela(4)
        return s["cursor"], s["linhas"]

    def _mover_para(self, alvo: int) -> None:
        """Seleção na linha escolhível `alvo` (contando só as que se escolhem)."""
        for _ in range(400):
            cur, _n = self._cursor()
            if cur == alvo:
                return
            self._tecla(KEY_DOWN if alvo > cur else KEY_UP, "cursor do DexNav")
        raise self.ctl.timeout_error(f"cursor do DexNav na linha {alvo}")

    def _linhas(self) -> list[dict]:
        """A linha selecionada (what 7) de cada linha escolhível, de cima para baixo."""
        self._mover_para(0)
        _cur, n = self._cursor()
        out = []
        for k in range(n):
            if k:
                self._mover_para(k)
            out.append(self._tela(7))
        return out

    def _ir_ate(self, pred, what: str) -> dict:
        """Desce (do começo) até a linha selecionada satisfazer `pred(what 7)`."""
        self._mover_para(0)
        _cur, n = self._cursor()
        for k in range(n):
            if k:
                self._mover_para(k)
            linha = self._tela(7)
            if pred(linha):
                return linha
        raise AssertionError(f"linha não encontrada: {what}")

    # --- passos ------------------------------------------------------------------------------------------------------
    def _start(self) -> str:
        self.box = Mailbox(self.ctl)
        self._title_to_continue("tela de título da build de teste", shot="dexnav_continue")
        self.box.conq_silencio(True)
        self.box.set_clock(*CLOCK)
        self._flag("FLAG_SYS_UNLOCKED_TANOBY_RUINS", False)
        self._escrever_pokedex(self.capturados, self.vistos)
        self._visitar(self.visitados, self.idx[ULTIMO])
        assert dnv.magic(self.emu, self.game.syms) == dnv.MAGIC, "o save do captura não tem o marcador do DexNav"
        assert dnv.visitados(self.emu, self.game.syms) == sorted(self.visitados)
        self.ctl.checkpoint("dexnav_base")
        return (f"CONTINUAR; relógio no dia 0 12:00, Pokédex: {len(self.capturados)} capturados e "
                f"{len(self.vistos) - len(self.capturados)} só vistos, visitados {sorted(self.visitados)}, último "
                f"{self.idx[ULTIMO]}; savestate dexnav_base")

    def _restore(self) -> None:
        self.ctl.restore("dexnav_base")
        self.emu.frames(12)

    def _entradas_c_python(self) -> str:
        self._restore()
        diferentes, entradas = [], 0
        for i in range(len(self.mapas)):
            c = dnv.entradas(self.box, i)
            py = self._entradas(i)
            entradas += len(c)
            got = [(e["especie"], e["metodo"], e["periodos"], e["chances"][:3], e["min"], e["max"]) for e in c]
            want = [(e["id"], e["metodo"], e["periodos"], e["chances"], e["min"], e["max"]) for e in py]
            tn = [e["chances"][3] for e in c]
            tn_want = [taxa(e["chances"], TARDE_NOITE) for e in py]
            if got != want or tn != tn_want:
                diferentes.append(f"{self.mapas[i]['id']}: C {got} {tn} != Python {want} {tn_want}")
        assert not diferentes, f"{len(diferentes)} mapas diferentes: " + " | ".join(diferentes[:3])
        return f"124 mapas, {entradas} entradas: C == gerar.enumerar (Tanoby trancada, Caverna Mutante no conjunto 0)"

    def _var(self, nome: str) -> int:
        return self.emu.read_u16(self._sb(1) + SB1_VARS + (VARS[nome] - VAR_BASE) * 2)

    def _rolar(self, map_id: str, xy, minuto: int, bits: int, metodo: int, entradas: list[dict] | None = None,
               dia: int = 0, warp: bool = True) -> str:
        """O gerador real do mapa (ROLAGENS vezes) contra a chance do gerar.py (`entradas`, padrão: o mapa no estado da
        preparação), com a tolerância em σ de `dnv.comparar`."""
        self.box.set_clock(dia, minuto)
        if warp:
            self._teleport(map_id, xy)
        if entradas is None:
            entradas = self._entradas(self.idx[map_id])
        esperado = {e["id"]: taxa(e["chances"], bits) for e in entradas
                    if e["metodo"] == metodo and e["periodos"] & bits}
        contagem = dnv.rolar(self.box, metodo, ROLAGENS)
        fora = dnv.comparar(esperado, contagem, ROLAGENS)
        nome = lambda s: self.consts.species_name(s).removeprefix("SPECIES_")   # noqa: E731
        assert not fora, (f"{map_id} {dnv.METODOS[metodo]} às {minuto // 60}h: fora da tolerância "
                          f"(espécie, chance %, real %, tolerância p.p.): "
                          f"{[(nome(s), c, f, t) for s, c, f, t in fora]}")
        return (f"{map_id} {dnv.METODOS[metodo]} {minuto // 60}h: "
                + ", ".join(f"{nome(s)} {esperado.get(s, 0) / 10:g}→{100 * contagem.get(s, 0) / ROLAGENS:.1f}"
                            for s in sorted(esperado, key=lambda s: -esperado[s])))

    def _chances_reais(self) -> str:
        self._restore()
        partes = [
            self._rolar("MAP_ROUTE1", ROUTE1_XY, 12 * 60, DIA, dnv.LAND),
            self._rolar("MAP_ROUTE1", ROUTE1_XY, 22 * 60, NOITE, dnv.LAND),
            self._rolar("MAP_ROUTE1", ROUTE1_XY, 18 * 60, TARDE_NOITE, dnv.LAND),
            self._rolar("MAP_POKEMON_MANSION_1F", None, 12 * 60, DIA, dnv.LAND),
            self._rolar("MAP_VIRIDIAN_CITY", None, 12 * 60, DIA, dnv.SUPER_ROD),
        ]
        return f"{ROLAGENS} sorteios, tolerância {dnv.SIGMAS} σ: " + "; ".join(partes)

    def _conjunto_mutante(self) -> tuple[list[dict], list[dict]]:
        """(C, Python) das entradas da Caverna Mutante agora."""
        cave = self.idx[MUTANTE_MAPA]
        return dnv.entradas(self.box, cave), self._entradas_mutante(self._conjunto_esperado())

    def _conjunto_esperado(self) -> int:
        """Dentro da caverna, a var do encontro; de fora, o conjunto do dia (o que ela recebe ao entrar)."""
        if self.game.location() == self.consts.map(MUTANTE_MAPA):
            return self._var("VAR_ALTERING_CAVE_WILD_SET")
        return self._dia % NUM_CONJUNTOS_MUTANTE

    def _entradas_mutante(self, conjunto: int) -> list[dict]:
        return [dict(e, id=self.consts.species(e["especie"]), nac=self._nac_de(e["especie"]))
                for e in self.g.enumerar(MUTANTE_MAPA, conjunto_mutante=conjunto)]

    def _bate_c_python(self, c: list[dict], py: list[dict], what: str) -> list[str]:
        got = [(e["especie"], e["metodo"], e["periodos"], e["chances"][:3], e["min"], e["max"]) for e in c]
        want = [(e["id"], e["metodo"], e["periodos"], e["chances"], e["min"], e["max"]) for e in py]
        assert got == want, f"{what}: C {got} != Python {want}"
        return [self.consts.species_name(e["especie"]).removeprefix("SPECIES_") for e in c]

    def _caverna_mutante(self) -> str:
        """Dia 22 (conjunto 4): entrar põe a var em 4 e o sorteio real bate com o conjunto 4. No dia 23, ainda dentro
        (var 4), o DexNav continua no conjunto 4 e o sorteio também; de fora, o DexNav já mostra o conjunto 5 (o do
        dia), e entrar de novo põe a var em 5 e o sorteio bate com ele."""
        self._restore()
        partes = []
        self._dia = MUTANTE_DIAS[0]
        self.box.set_clock(self._dia, 12 * 60)
        self._teleport(MUTANTE_MAPA)
        var = self._var("VAR_ALTERING_CAVE_WILD_SET")
        assert var == self._dia % NUM_CONJUNTOS_MUTANTE, f"dia {self._dia}: var {var}"
        c, py = self._conjunto_mutante()
        especies = self._bate_c_python(c, py, f"dentro, dia {self._dia}")
        partes.append(f"dia {self._dia} dentro (var {var}): {especies}; "
                      + self._rolar(MUTANTE_MAPA, None, 12 * 60, DIA, dnv.LAND, py, dia=self._dia, warp=False))
        # dia seguinte, sem sair: a var não muda, o DexNav e o sorteio continuam no conjunto de antes
        self._dia = MUTANTE_DIAS[1]
        self.box.set_clock(self._dia, 12 * 60)
        assert self._var("VAR_ALTERING_CAVE_WILD_SET") == var
        c, py_dentro = self._conjunto_mutante()
        assert py_dentro == py
        especies = self._bate_c_python(c, py_dentro, f"dentro, dia {self._dia}")
        partes.append(f"dia {self._dia} ainda dentro (var {var}): {especies}; "
                      + self._rolar(MUTANTE_MAPA, None, 12 * 60, DIA, dnv.LAND, py_dentro, dia=self._dia, warp=False))
        # de fora: o conjunto do dia, diferente do da var
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        c, py_fora = self._conjunto_mutante()
        assert py_fora != py, "o conjunto de fora devia ser outro"
        especies = self._bate_c_python(c, py_fora, f"fora, dia {self._dia}")
        partes.append(f"dia {self._dia} de fora: {especies}")
        # entrar de novo: a var vira o conjunto do dia, e o sorteio bate com o que o DexNav mostrava de fora
        self._teleport(MUTANTE_MAPA)
        var = self._var("VAR_ALTERING_CAVE_WILD_SET")
        assert var == self._dia % NUM_CONJUNTOS_MUTANTE, f"dia {self._dia}: var {var}"
        c, py = self._conjunto_mutante()
        assert py == py_fora
        self._bate_c_python(c, py, f"dentro de novo, dia {self._dia}")
        partes.append(f"entrando (var {var}): "
                      + self._rolar(MUTANTE_MAPA, None, 12 * 60, DIA, dnv.LAND, py, dia=self._dia, warp=False))
        return "; ".join(partes)

    def _tanoby(self) -> str:
        """Câmara Monean: trancada, nem o DexNav nem o gerador real têm encontro; liberada, Unown 100% nos dois."""
        self._restore()
        camara = self.idx[CAMARA]
        self._flag("FLAG_SYS_UNLOCKED_TANOBY_RUINS", False)
        self._teleport(CAMARA)
        assert dnv.entradas(self.box, camara) == [] == self._entradas(camara, tanoby=False)
        raw = self.box.call(CMD_DEXNAV_ROLL, dnv.LAND, 10, timeout=200)
        assert raw == NO_RESULT, f"trancada: o gerador real achou encontro ({raw:#x})"
        # aberto de dentro: o modo mapa sem espécie (o topo mostra "?/?" apagado, como a lista)
        assert self._abrir() == camara
        s0, s2 = self._tela(0), self._tela(2)
        assert (s0["modo"], s0["mapa"], s2["total_mapa"], s2["capturados_mapa"]) == (MODO_MAPA, camara, 0, 0), (s0, s2)
        self._shot("dexnav_tanoby_trancada")
        self._fechar()
        self.ctl.wait_overworld_idle(600)
        self._flag("FLAG_SYS_UNLOCKED_TANOBY_RUINS", True)
        py = self._entradas(camara, tanoby=True)
        especies = self._bate_c_python(dnv.entradas(self.box, camara), py, "liberada")
        assert especies == ["UNOWN"] and py[0]["chances"] == [1000, 1000, 1000], (especies, py)
        rolagem = self._rolar(CAMARA, None, 12 * 60, DIA, dnv.LAND, py, warp=False)
        return (f"trancada: 0 entradas, o gerador real sem encontro e, aberto de dentro, o mapa com 0 espécies (topo "
                f"\"?/?\", foto dexnav_tanoby_trancada); liberada: {especies} 100% e {rolagem}")

    def _extra_tarde_noite(self) -> str:
        """De manhã, na Rota 24, as espécies que só aparecem à tarde e à noite (DAY | NIGHT) formam a linha
        "+N à tarde/noite" (antes caía em "em outros horários")."""
        self._restore()
        rota24 = self.idx[EXTRA_TARDE_NOITE]
        self.box.set_clock(0, MANHA_MINUTO)
        self._marcar_visitado(rota24)
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_SELECT)
        self._lista_ate(rota24)
        self._tecla(KEY_A)
        esp = self._aba(rota24, 0, MANHA)
        assert esp["periodos_extra"] == DIA | NOITE and esp["extra"] > 0, esp
        detalhe = self._conferir_aba(rota24, 0, MANHA)
        self._shot("dexnav_extra_tarde_noite")
        self._fechar()
        return f"Rota 24 às {MANHA_MINUTO // 60}h: +{esp['extra']} à tarde/noite (períodos {DIA | NOITE}); {detalhe}"

    def _cursor_menu_em(self, entrada: int) -> None:
        menu = self.menu
        alvo = menu.entries().index(entrada)
        addr = self.game.syms.addr("sStartMenuCursorPos")
        for _ in range(10):
            cur = self.emu.read_u8(addr)
            if cur == alvo:
                return
            self.ctl.press_until(KEY_DOWN if alvo > cur else KEY_UP, lambda: self.emu.read_u8(addr) != cur,
                                 "cursor do menu Start")
        raise self.ctl.timeout_error("cursor do menu Start no DEXNAV")

    def _start_dexnav_e_volta(self) -> tuple[int, int, int, int]:
        """Menu Start → DEXNAV; devolve o estado da tela pronta, B até o menu Start voltar com o cursor no DEXNAV."""
        menu = self.menu
        menu.choose(STARTMENU_DEXNAV)
        self.ctl.wait_until(lambda: self._tela() is not None, TELA_TIMEOUT, "DexNav pelo menu Start")
        self._pronta()
        estado = self._estado()
        self._fechar()
        self.ctl.wait_until(menu.accepting_input, MENU_TIMEOUT, "menu Start de volta")
        cursor = self.emu.read_u8(self.game.syms.addr("sStartMenuCursorPos"))
        assert cursor == menu.entries().index(STARTMENU_DEXNAV), f"cursor do menu Start em {cursor}"
        return estado

    def _abre_start(self) -> str:
        self._restore()
        self._teleport(QUARTO)
        menu = self.menu
        menu.open_start_menu()
        entradas = menu.entries()
        assert entradas[:2] == [STARTMENU_POKEDEX, STARTMENU_DEXNAV] and len(entradas) == 8, entradas
        self._cursor_menu_em(STARTMENU_DEXNAV)
        self.emu.frames(20)
        self._shot("dexnav_menu_start")
        menu.close_start_menu()
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        menu.open_start_menu()
        estado = self._start_dexnav_e_volta()
        assert estado == (MODO_MAPA, 0, self.idx["MAP_ROUTE1"], 0), estado
        menu.close_start_menu()
        return (f"menu Start com {len(entradas)} linhas, DEXNAV logo abaixo de POKéDEX (foto dexnav_menu_start); na "
                f"Rota 1 abre o modo mapa (modo, aba, mapa, pilha = {estado}) e B volta ao menu no DEXNAV")

    def _mapa_sem_encontro(self) -> str:
        self._restore()
        self._teleport(QUARTO)
        assert self._ultimo() == self.idx[ULTIMO], self._ultimo()
        menu = self.menu
        menu.open_start_menu()
        estado = self._start_dexnav_e_volta()
        assert estado == (MODO_LISTA, KANTO, self.idx[ULTIMO], 0), estado
        menu.close_start_menu()
        assert self.box.open_dexnav() is None, "o atalho achou encontro no quarto"
        self.ctl.wait_until(lambda: (self._tela(1) or {}).get("pronta") == 1, TELA_TIMEOUT, "lista pelo atalho")
        estado2 = self._estado()
        assert estado2 == estado, estado2
        self._fechar()
        self.ctl.wait_overworld_idle(600)
        return (f"no quarto (sem encontro), lastMapIndex {self._ultimo()}: o DexNav abre na lista na Rota 1 "
                f"{estado}, pelo menu Start e pelo atalho; B volta ao menu Start e ao campo")

    def _conferir_aba(self, mapa: int, aba: int, bits: int, rolar: bool = False) -> str:
        esp = self._aba(mapa, aba, bits)
        s0, s1, s2, s3 = (self._tela(w) for w in range(4))
        assert (s0["modo"], s0["aba"], s0["mapa"]) == (MODO_MAPA, aba, mapa), s0
        assert s1["mons"] == len(esp["linhas"]), f"aba {aba}: {s1['mons']} Pokémon, esperava {len(esp['linhas'])}"
        assert (s2["capturados_aba"], s2["total_aba"]) == (esp["capturados"], esp["total"]), s2
        assert (s3["extra"], s3["periodos_extra"], s3["periodos"]) == (esp["extra"], esp["periodos_extra"], bits), s3
        assert s1["topo"] == 0, f"aba nova com topo {s1['topo']}"
        detalhe = f"aba {aba}: {len(esp['linhas'])} Pokémon, {esp['capturados']}/{esp['total']}"
        if rolar:
            linhas = self._linhas()
            topo = self._tela(1)["topo"]
            got = [(l["baixo16"], l["d"], l["c"]) for l in linhas]
            assert got == esp["linhas"], f"aba {aba}: linhas {got}, esperava {esp['linhas']}"
            assert topo > 0, "a lista não rolou até a última linha"
            self._mover_para(0)
            assert self._tela(1)["topo"] == 0, "de volta à 1ª linha, o topo não voltou a 0"
            detalhe += f", linhas na ordem, topo {topo} na última e 0 de volta"
        return detalhe

    def _marcas(self) -> str:
        self._restore()
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        rota1 = self.idx["MAP_ROUTE1"]
        assert self._abrir() == rota1
        self._shot("dexnav_mapa")
        esp = self._aba(rota1, 0, DIA)
        s1, s2 = self._tela(1), self._tela(2)
        assert s1["abas"] == 1, f"abas {s1['abas']:#x}: a Rota 1 só tem GRAMA"
        cap, tot = self._contar(self._entradas(rota1))
        assert (s2["capturados_mapa"], s2["total_mapa"]) == (cap, tot) == (1, 4), s2
        detalhe = self._conferir_aba(rota1, 0, DIA)
        linhas = [(l["baixo16"], l["d"], l["c"]) for l in self._linhas()]
        assert linhas == esp["linhas"], f"linhas {linhas}, esperava {esp['linhas']}"
        marcas = [m for _s, _m, m in linhas]
        assert marcas == [MARCA_CAPTURADO, MARCA_VISTO, MARCA_NUNCA], marcas
        assert esp["extra"] == 1 and esp["periodos_extra"] == NOITE
        self._fechar()
        self.ctl.wait_overworld_idle(600)
        # os 4 capturados: 4/4 (o "100%" e a coroa, para os olhos)
        todos = self.capturados | {e["nac"] for e in self._entradas(rota1)}
        self._escrever_pokedex(todos, self.vistos | todos)
        self._abrir()
        s2 = self._tela(2)
        assert (s2["capturados_mapa"], s2["total_mapa"], s2["capturados_aba"], s2["total_aba"]) == (4, 4, 4, 4), s2
        self._shot("dexnav_mapa_completo")
        self._fechar()
        return (f"Rota 1 à tarde: Pidgey ●, Rattata ◐, Sentret ? (por chance), {cap}/{tot}, +1 à noite; {detalhe}; "
                f"com os 4 capturados, 4/4 (foto dexnav_mapa_completo)")

    def _lista_ate(self, mapa: int) -> dict:
        return self._ir_ate(lambda l: l["a"] == mapa, f"mapa {mapa} na lista")

    def _abrir_estrada(self) -> int:
        """Da Rota 1, SELECT → Sevii → A na Estrada Fagulha (visitada): o modo mapa dela, pilha 2."""
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_SELECT)
        self._tecla(KEY_R)
        mapa = self.idx[ABAS_MAPA]
        self._lista_ate(mapa)
        self._tecla(KEY_A)
        assert self._estado() == (MODO_MAPA, 0, mapa, 2), self._estado()
        return mapa

    def _abas_check(self) -> str:
        self._restore()
        mapa = self._abrir_estrada()
        abas = self._abas(mapa)
        assert abas == [0, 1, 2, 3], abas
        assert self._tela(1)["abas"] == 0b1111, self._tela(1)
        partes = [self._conferir_aba(mapa, 0, DIA)]
        seq = []
        for key, aba in ((KEY_R, 1), (KEY_R, 2), (KEY_R, 3), (KEY_R, 0), (KEY_L, 3), (KEY_L, 2)):
            self._tecla(key)
            seq.append(self._tela(0)["aba"])
            assert seq[-1] == aba, f"{'R' if key == KEY_R else 'L'} foi para a aba {seq[-1]}, esperava {aba}"
            if aba == 2 and key == KEY_L:
                self._shot("dexnav_aba_varas")
                partes.append(self._conferir_aba(mapa, aba, DIA, rolar=True))
                self._mover_para(self._cursor()[1] - 1)
                self._shot("dexnav_aba_varas_rolada")
                self._mover_para(0)
            elif seq.count(aba) == 1:
                partes.append(self._conferir_aba(mapa, aba, DIA))
        self._fechar()
        return f"Estrada Fagulha: abas {abas}, R/L {seq}; " + "; ".join(partes)

    def _lista(self) -> str:
        self._restore()
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_SELECT)
        rota1 = self.idx["MAP_ROUTE1"]
        assert self._estado() == (MODO_LISTA, KANTO, rota1, 1), self._estado()
        assert (self._tela(7)["a"], self._tela(7)["b"]) == (rota1, 1)
        self._shot("dexnav_lista")
        detalhes = []
        for regiao, key in ((KANTO, None), (SEVII, KEY_R)):
            if key is not None:
                self._tecla(key)
                assert self._tela(0)["aba"] == regiao
            s5 = self._tela(5)
            esp = self._completos(regiao)
            assert (s5["completos"], s5["total"]) == esp, f"região {regiao}: {s5}, esperava {esp}"
            got = [(l["a"], l["b"], l["c"], l["d"]) for l in self._linhas()]
            want = [self._linha_lista(i) for i, m in enumerate(self.mapas) if m["regiao"] == regiao]
            assert got == want, f"região {regiao}: " + str([(g, w) for g, w in zip(got, want) if g != w][:4])
            detalhes.append(f"{'Kanto' if regiao == KANTO else 'Sevii'} {len(got)} mapas, {esp[0]} completos")
        self._tecla(KEY_L)
        assert self._tela(0)["aba"] == KANTO
        self._fechar()
        return ("SELECT abre a lista de Kanto na Rota 1 (foto dexnav_lista); todas as linhas (mapa, visitado, "
                "capturados, total) batem: " + ", ".join(detalhes))

    def _nao_visitado(self) -> str:
        self._restore()
        camara = self.idx[CAMARA]
        self._marcar_visitado(camara)
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_SELECT)
        rota24 = self.idx[NAO_VISITADO]
        linha = self._lista_ate(rota24)
        assert linha["b"] == 0, linha
        self._tecla(KEY_A)
        assert self._estado() == (MODO_LISTA, KANTO, rota24, 1), f"A no não visitado: {self._estado()}"
        self._tecla(KEY_R)
        linha = self._lista_ate(camara)
        assert (linha["b"], linha["d"]) == (1, 0), f"câmara trancada: {linha} (visitada e total 0 = ?/? cinza)"
        self._shot("dexnav_lista_tanoby")
        self._tecla(KEY_A)
        assert self._estado() == (MODO_LISTA, SEVII, camara, 1), f"A na câmara trancada: {self._estado()}"
        # resultado da busca num mapa não visitado
        self._tecla(KEY_START)
        self._ir_ate(lambda l: l["baixo16"] == self.consts.species(f"SPECIES_{BUSCA}"), BUSCA)
        self._tecla(KEY_A)
        linha = self._ir_ate(lambda l: l["a"] == rota24, "Rota 24 no resultado")
        assert linha["d"] & 1 == 0, linha   # bit 0: visitado
        self._tecla(KEY_A)
        assert self._estado()[:2] == (MODO_BUSCA, RESULTADO), f"A no resultado não visitado: {self._estado()}"
        self._fechar()
        self.ctl.wait_overworld_idle(600)
        # liberada, a câmara mostra a espécie (0/1) e abre
        self._flag("FLAG_SYS_UNLOCKED_TANOBY_RUINS", True)
        self._abrir()
        self._tecla(KEY_SELECT)
        self._tecla(KEY_R)
        linha = self._lista_ate(camara)
        assert (linha["b"], linha["c"], linha["d"]) == (1, 0, 1), f"câmara liberada: {linha}"
        self._tecla(KEY_A)
        assert self._estado() == (MODO_MAPA, 0, camara, 2), f"A na câmara liberada: {self._estado()}"
        self._fechar()
        return ("A na Rota 24 (não visitada) e na câmara Monean trancada (visitada, total 0 = ?/?, foto "
                "dexnav_lista_tanoby) não abre; A na Rota 24 no resultado do Oddish não abre; liberada, a câmara "
                "mostra 0/1 e abre")

    def _escolha_esperada(self) -> list[tuple[int, int]]:
        especie_de = {v: k for k, v in self.nac.items()}
        mapas = self._mapas_da_especie()
        return [(self.consts.species(f"SPECIES_{especie_de[n]}"), mapas[n]) for n in sorted(self.vistos)
                if mapas.get(n)]

    def _busca_so_vistos(self) -> str:
        self._restore()
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_START)
        s0 = self._tela(0)
        assert (s0["modo"], s0["aba"]) == (MODO_BUSCA, ESCOLHA), s0
        pidgey = self.consts.species("SPECIES_PIDGEY")
        assert self._tela(7)["baixo16"] == pidgey, f"a escolha abriu em {self._tela(7)}, esperava o Pidgey do mapa"
        got = [(l["baixo16"], l["alto16"]) for l in self._linhas()]
        want = self._escolha_esperada()
        assert got == want, f"escolha {got}, esperava {want}"
        fora = {self.consts.species("SPECIES_MEW"), self.consts.species("SPECIES_HOOTHOOT")}
        assert not fora & {s for s, _ in got}
        self._fechar()
        nomes = [self.consts.species_name(s).removeprefix("SPECIES_") for s, _ in got]
        return (f"a escolha abre no Pidgey (o selecionado no mapa) e lista só os vistos com encontro, na ordem da "
                f"Pokédex: {nomes} (com os mapas de cada um); sem Mew (sem encontro) nem Hoothoot (nunca visto)")

    def _ir_ao_resultado(self) -> None:
        """Da escolha da busca aberta: A no Oddish."""
        self._ir_ate(lambda l: l["baixo16"] == self.consts.species(f"SPECIES_{BUSCA}"), BUSCA)
        self._tecla(KEY_A)

    def _busca_resultado(self) -> str:
        self._restore()
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        self._tecla(KEY_START)
        self._ir_ao_resultado()
        s0, s6 = self._tela(0), self._tela(6)
        want = self._resultado(BUSCA, DIA)
        assert (s0["modo"], s0["aba"]) == (MODO_BUSCA, RESULTADO), s0
        assert (s6["especie"], s6["resultados"]) == (self.consts.species(f"SPECIES_{BUSCA}"), len(want)), s6
        self._shot("dexnav_busca_resultado")
        got = [(l["a"], l["b"], l["c"], l["d"]) for l in self._linhas()]
        assert got == want, f"resultado {got}, esperava {want}"
        agora = [m for m, _j, p, _v in want if p & DIA]
        assert agora == [m for m, *_ in want[:len(agora)]], "os de agora não vieram primeiro"
        # R14: fora do horário, a maior chance de um período só e o nome desse período (Spinarak na Rota 2: manhã 4%
        # e noite 36% → "36% noite", não a média "20% manhã/noite")
        self._tecla(KEY_B)
        alvo = self.consts.species(f"SPECIES_{BUSCA_DOIS_HORARIOS}")
        self._ir_ate(lambda l: l["baixo16"] == alvo, BUSCA_DOIS_HORARIOS)
        self._tecla(KEY_A)
        want2 = self._resultado(BUSCA_DOIS_HORARIOS, DIA)
        got2 = [(l["a"], l["b"], l["c"], l["d"]) for l in self._linhas()]
        assert got2 == want2, f"resultado do {BUSCA_DOIS_HORARIOS} {got2}, esperava {want2}"
        rota2 = self.idx["MAP_ROUTE2"]
        linha = next(r for r in got2 if r[0] == rota2)
        assert (linha[2], linha[3] >> 4) == (MANHA | NOITE, NOITE), f"Rota 2: {linha} (períodos, mostrados)"
        self._shot("dexnav_busca_dois_horarios")
        self._fechar()
        return (f"{BUSCA}: {len(got)} mapas na ordem (mapa, jeito, períodos, visitado | mostrados << 4) {got}: os "
                f"{len(agora)} de agora primeiro, depois os da noite, cada grupo por chance; "
                f"{BUSCA_DOIS_HORARIOS}: {got2}, Rota 2 (manhã/noite) mostrada como noite (36%), a maior de um período")

    def _passo(self, key: int, esperado: tuple, what: str) -> tuple:
        self._tecla(key)
        estado = self._estado()
        assert estado == esperado, f"{what}: {estado}, esperava {esperado}"
        return estado

    def _navegacao(self) -> str:
        self._restore()
        rota1, rota12 = self.idx["MAP_ROUTE1"], self.idx[BUSCA_ABRE]
        oddish = self.consts.species(f"SPECIES_{BUSCA}")
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        self._abrir()
        assert self._estado() == (MODO_MAPA, 0, rota1, 0)
        self._passo(KEY_SELECT, (MODO_LISTA, KANTO, rota1, 1), "SELECT: lista")
        self._passo(KEY_A, (MODO_MAPA, 0, rota1, 2), "A na Rota 1: mapa")
        # na busca, o "mapa" do estado continua o da tela de onde se veio (a Rota 1)
        self._passo(KEY_START, (MODO_BUSCA, ESCOLHA, rota1, 3), "START: escolha")
        self._ir_ao_resultado()
        assert self._estado() == (MODO_BUSCA, RESULTADO, rota1, 4), self._estado()
        linha = self._ir_ate(lambda l: l["a"] == rota12, "Rota 12 no resultado")
        cursor_res = self._cursor()[0]
        assert linha["d"] & 1 == 1, linha
        self._passo(KEY_A, (MODO_MAPA, 0, rota12, 5), "A na Rota 12: mapa")
        assert self._tela(7)["baixo16"] == oddish, f"o mapa abriu na linha {self._tela(7)}, esperava o Oddish"
        # B em cadeia: cada tela volta como estava
        self._passo(KEY_B, (MODO_BUSCA, RESULTADO, rota1, 4), "B: resultado")
        assert self._cursor()[0] == cursor_res and self._tela(7)["a"] == rota12, \
            "o resultado não voltou na linha da Rota 12"
        self._passo(KEY_B, (MODO_BUSCA, ESCOLHA, rota1, 3), "B: escolha")
        assert self._tela(7)["baixo16"] == oddish, "a escolha não voltou no Oddish"
        self._passo(KEY_B, (MODO_MAPA, 0, rota1, 2), "B: mapa da Rota 1")
        self._passo(KEY_B, (MODO_LISTA, KANTO, rota1, 1), "B: lista")
        self._passo(KEY_B, (MODO_MAPA, 0, rota1, 0), "B: o mapa do começo")
        self.emu.press(KEY_B, hold=2, release=4)
        self.ctl.wait_until(lambda: self._tela() is None, TELA_TIMEOUT, "B sai do DexNav")
        self.ctl.wait_overworld_idle(600)
        assert self.game.callback2() == "CB2_Overworld", self.game.callback2()
        # SELECT com a lista na pilha volta até ela
        self._abrir()
        self._passo(KEY_SELECT, (MODO_LISTA, KANTO, rota1, 1), "SELECT: lista")
        self._passo(KEY_START, (MODO_BUSCA, ESCOLHA, rota1, 2), "START: escolha")
        self._passo(KEY_SELECT, (MODO_LISTA, KANTO, rota1, 1), "SELECT volta à lista da pilha")
        self._fechar()
        return ("mapa → SELECT lista → A mapa → START escolha → A resultado → A Rota 12 (na linha do Oddish), pilha "
                "0..5; B em cadeia: resultado (na Rota 12), escolha (no Oddish), mapa, lista, mapa, campo; SELECT com "
                "a lista na pilha volta a ela (pilha 1)")

    def _escolher_acao(self, bag: Bag, acao: int) -> list[int]:
        in_context = lambda: BAG_CONTEXT_TASK in self.game.active_tasks()   # noqa: E731
        self.ctl.press_until(KEY_A, in_context, "menu do item")
        acoes = bag.context_actions()
        idx = acoes.index(acao)
        cursor = bag._menu_cursor_addr(len(acoes))
        for _ in range(len(acoes)):
            cur = self.emu.read_u8(cursor)
            if cur == idx:
                break
            self.ctl.press_until(KEY_DOWN if idx > cur else KEY_UP, lambda: self.emu.read_u8(cursor) != cur, "cursor")
        self.ctl.press_until(KEY_A, lambda: not in_context(), f"ação {acao}")
        return acoes

    def _bolsa_pos(self) -> tuple[int, int, int]:
        st = self.game.syms.addr("gBagMenuState")
        p = self.emu.read_u16(st + BAG_POCKET)
        return p, self.emu.read_u16(st + BAG_CURSOR_POS + 2 * p), self.emu.read_u16(st + BAG_ITEMS_ABOVE + 2 * p)

    def _select(self) -> str:
        self._restore()
        dexnav = self.consts.item("ITEM_DEXNAV")
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        menu, bag = self.menu, Bag(self.ctl)
        menu.open_start_menu()
        menu.choose(STARTMENU_BAG)
        bag.wait_ready()
        bag.select(dexnav)
        acoes = self._escolher_acao(bag, ITEMMENUACTION_REGISTER)
        self.emu.frames(30)
        registrado = self.emu.read_u16(self._sb(1) + SB1_REGISTERED_ITEM)
        assert registrado == dexnav, f"registrado {registrado} (ações {acoes})"
        bag.wait_ready()
        self.ctl.press_until(KEY_B, lambda: not bag.ready(), "bolsa fechada")
        self.ctl.wait_until(menu.accepting_input, MENU_TIMEOUT, "menu Start depois da bolsa")
        menu.close_start_menu()
        self.ctl.press_until(KEY_SELECT, lambda: self._tela() is not None, "SELECT abre o DexNav", tries=5, wait=60)
        self._pronta()
        estado = self._estado()
        assert estado == (MODO_MAPA, 0, self.idx["MAP_ROUTE1"], 0), estado
        self._fechar()
        self.ctl.wait_overworld_idle(600)
        assert self.game.callback2() == "CB2_Overworld" and not menu.start_menu_open(), self.game.callback2()
        travado = self.emu.read_u8(self.game.syms.addr("sLockFieldControls"))
        xy = self.game.player_xy()
        for tecla in (KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP):
            self.emu.hold(tecla, 24)
            self.emu.frames(16)
            if self.game.player_xy() != xy:
                break
        assert travado == 0 and self.game.player_xy() != xy, f"controle preso: lock {travado}, {xy}"
        return (f"REGISTRAR (ações {acoes}) → registeredItem {registrado}; SELECT no campo abre o DexNav {estado}; B "
                f"volta ao campo sem menu e o jogador anda ({xy} → {self.game.player_xy()})")

    def _bolsa(self) -> str:
        self._restore()
        dexnav = self.consts.item("ITEM_DEXNAV")
        self._teleport("MAP_ROUTE1", ROUTE1_XY)
        menu, bag = self.menu, Bag(self.ctl)
        menu.open_start_menu()
        menu.choose(STARTMENU_BAG)
        bag.wait_ready()
        bag.select(dexnav)
        antes = self._bolsa_pos()
        bag.use_selected()
        self.ctl.wait_until(lambda: self._tela() is not None, TELA_TIMEOUT, "DexNav pela bolsa")
        self._pronta()
        estado = self._estado()
        assert estado == (MODO_MAPA, 0, self.idx["MAP_ROUTE1"], 0), estado
        self._fechar()
        bag.wait_ready()
        depois = self._bolsa_pos()
        assert antes == depois, f"a bolsa voltou em {depois}, saiu de {antes}"
        self.ctl.press_until(KEY_B, lambda: not bag.ready(), "bolsa fechada")
        self.ctl.wait_until(menu.accepting_input, MENU_TIMEOUT, "menu Start depois da bolsa")
        menu.close_start_menu()
        return f"USAR abre o DexNav {estado}; B volta à bolsa no mesmo bolso e posição {antes}"

    def _salvar_e_continuar(self, shot: str) -> None:
        status = self.menu.save_game()
        assert status == 1, f"gSaveAttemptStatus = {status}"
        self.emu.flush_save()
        self.emu.reset()
        self._title_to_continue("tela de título depois do reset", shot=shot)
        self.box.conq_silencio(True)
        self.emu.frames(30)

    def _bolso_cheio(self) -> str:
        self._restore()
        dexnav = self.consts.item("ITEM_DEXNAV")
        sb1 = self._sb(1)
        off, count = SB1_BAG_POCKETS[1]
        base = sb1 + off
        slots = [(self.emu.read_u16(base + 4 * i), self.emu.read_u16(base + 4 * i + 2)) for i in range(count)]
        ficam = [s for s in slots if s[0] and s[0] != dexnav]
        self.emu.write(base, b"".join(struct.pack("<HH", *s) for s in ficam) + bytes(4 * (count - len(ficam))))
        if self.emu.read_u16(sb1 + SB1_REGISTERED_ITEM) == dexnav:
            self.emu.write(sb1 + SB1_REGISTERED_ITEM, b"\0\0")
        assert self._qtd_dexnav() == 0
        self.box.encher_bolso(self.consts.item("ITEM_BICYCLE"))
        chave = [i for i, it in enumerate(json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))
                                          ["items"]) if it["pocket"] == "POCKET_KEY_ITEMS"]
        presentes = {it for it, _ in self.game.bag_pocket(1)}
        livre = next(i for i in chave if i not in presentes and i != dexnav)
        for i in range(count):   # o atalho pode ter posto o DexNav entre os itens: troca por outro
            if self.emu.read_u16(base + 4 * i) == dexnav:
                self.emu.write(base + 4 * i, struct.pack("<H", livre))
        cheio = len(self.game.bag_pocket(1))
        assert cheio == count and self._qtd_dexnav() == 0, f"bolso {cheio}/{count}, DexNav {self._qtd_dexnav()}"
        self._teleport(QUARTO)
        self._salvar_e_continuar("dexnav_bolso_cheio_continue")
        assert self.game.callback2() == "CB2_Overworld", self.game.callback2()
        assert self._qtd_dexnav() == 0, f"o DexNav entrou no bolso cheio ({self._qtd_dexnav()})"
        menu = self.menu
        menu.open_start_menu()
        assert STARTMENU_DEXNAV in menu.entries(), menu.entries()
        estado = self._start_dexnav_e_volta()
        menu.close_start_menu()
        return (f"bolso de itens-chave {cheio}/{count} sem o DexNav; salvar e CONTINUAR sem travar e sem o item; o "
                f"menu Start abre o DEXNAV {estado}")

    def _save_antigo(self) -> str:
        detalhes = []
        for zerado in (True, False):
            self._restore()
            self._flag("FLAG_SYS_GAME_CLEAR", zerado)
            self.emu.write(self._sb(1) + DEXNAV_AREA, bytes(DEXNAV_AREA_SIZE))
            self._teleport(QUARTO)
            assert dnv.magic(self.emu, self.game.syms) == 0
            self._salvar_e_continuar(f"dexnav_save_antigo_{int(zerado)}")
            magic = dnv.magic(self.emu, self.game.syms)
            vis = dnv.visitados(self.emu, self.game.syms)
            assert magic == dnv.MAGIC, f"marcador {magic:#x} depois do CONTINUAR"
            assert self._ultimo() == LAST_MAP_NONE, self._ultimo()
            if zerado:
                assert vis == list(range(len(self.mapas))), f"zerado: {len(vis)} visitados"
                self._abrir()
                s0, s7 = self._tela(0), self._tela(7)
                assert s0["modo"] == MODO_LISTA and s7["b"] == 1, (s0, s7)
                self._fechar()
                detalhes.append(f"zerado: marcador, os {len(vis)} visitados, último 0xFF, a lista abre num visitado")
            else:
                assert vis == [], f"não zerado: {vis}"
                self._teleport("MAP_ROUTE1", ROUTE1_XY)
                vis = dnv.visitados(self.emu, self.game.syms)
                assert vis == [self.idx["MAP_ROUTE1"]] and self._ultimo() == self.idx["MAP_ROUTE1"], vis
                detalhes.append(f"não zerado: marcador, nenhum visitado; na Rota 1, só ela ({vis})")
        return "; ".join(detalhes)

    def run(self) -> None:
        try:
            self._flow("dexnav: CONTINUAR e preparação", self._start)
            run = self.suite.run
            run("dexnav/entradas_c_python: DexNav_GetMapEntries == gerar.enumerar nos 124 mapas", self._entradas_c_python)
            run("dexnav/chances_reais: o sorteio real bate com a chance mostrada (tolerância em σ)", self._chances_reais)
            run("dexnav/caverna_mutante: dentro, a var do encontro; de fora, o conjunto do dia", self._caverna_mutante)
            run("dexnav/tanoby: câmara trancada sem encontro; liberada, Unown 100%", self._tanoby)
            run("dexnav/extra_tarde_noite: de manhã, \"+N à tarde/noite\" para as espécies da tarde e da noite",
                self._extra_tarde_noite)
            run("dexnav/abre_start: DEXNAV no menu Start abre o mapa e volta ao menu", self._abre_start)
            run("dexnav/mapa_sem_encontro: sem encontro, abre a lista no último mapa com encontro",
                self._mapa_sem_encontro)
            run("dexnav/marcas: capturado/visto/nunca visto batendo com a Pokédex, contadores e +N", self._marcas)
            run("dexnav/abas: L/R trocam as abas e a VARAS rolada mostra tudo na ordem", self._abas_check)
            run("dexnav/lista: a lista de mapas com progresso e completos por região", self._lista)
            run("dexnav/nao_visitado: não visitado e Tanoby trancada não abrem", self._nao_visitado)
            run("dexnav/busca_so_vistos: a busca só oferece Pokémon vistos com encontro", self._busca_so_vistos)
            run("dexnav/busca_resultado: os mapas da espécie na ordem (agora antes, depois chance)",
                self._busca_resultado)
            run("dexnav/navegacao: pilha mapa → lista → mapa → busca → resultado → mapa e B em cadeia", self._navegacao)
            run("dexnav/select: registrado no SELECT, abre do campo e volta ao campo", self._select)
            run("dexnav/bolsa: USAR na bolsa abre e volta à bolsa na mesma posição", self._bolsa)
            # os dois últimos salvam e reiniciam
            run("dexnav/bolso_cheio: sem o item e com o bolso cheio, o menu Start ainda abre", self._bolso_cheio)
            run("dexnav/save_antigo: save sem marcador, zerado e não zerado", self._save_antigo)
        except Abort:
            pass


def run_full_dexnav(ctx_test: ScenarioContext) -> None:
    """Roda o cenário na build de teste recém-ligada com o .sav do modo rápido (ver módulo)."""
    DexNavScenario(ctx_test).run()


def main(argv: list[str] | None = None) -> int:
    """Atalho para `python3 -m esteira completo --only dexnav ARGS`."""
    from ..__main__ import main as cli_main
    return cli_main(["completo", "--only", "dexnav", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    sys.exit(main())
