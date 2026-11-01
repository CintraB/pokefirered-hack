"""DexNav (POK-47) na ROM de teste: as entradas que o C enumera e o confronto com o sorteio real.

`entradas` lê `DexNav_GetMapEntries` pelos atalhos TEST_CMD_DEXNAV_ENTRY/RATE; `rolar` roda o gerador real de
encontro do mapa atual N vezes (TEST_CMD_DEXNAV_ROLL, sem batalha) e lê a contagem em gTestText;
`comparar` diz quais espécies ficaram fora da tolerância. `visitado`/`zerar_visitados` leem e mexem no bit de
"visitado" de `gSaveBlock1Ptr->dexNav` (SaveBlock1 + 0x3A94: u32 magic, u8 visitedMaps[16]).
Usado pelo `dexnav/chances_reais` (cenário dexnav) e pela verificação da Task 1.
"""

import struct

from . import hooks

# DEXNAV_METHOD_* e DEXNAV_PERIOD_* (include/dexnav.h)
LAND, WATER, OLD_ROD, GOOD_ROD, SUPER_ROD, ROCK = range(6)
METODOS = ("grama", "surf", "vara velha", "vara boa", "super vara", "quebra-pedra")
MANHA, TARDE, NOITE, TARDE_NOITE = range(4)   # período do TEST_CMD_DEXNAV_RATE (3 = média da tarde e da noite)
MAGIC = 0x31564E44                             # DEXNAV_MAGIC, "DNV1"
SB1_DEXNAV = 0x3A94                            # offsetof(struct SaveBlock1, dexNav)
TALLY_MAX = 384 // 4                           # TEST_DEXNAV_TALLY_MAX


def entradas(box: hooks.Mailbox, mapa: int) -> list[dict]:
    """[{especie, metodo, periodos, chances: [manhã, tarde, noite, tarde-noite] (‰), min, max}] do mapa."""
    out = []
    for i in range(64):
        r = box.call(hooks.CMD_DEXNAV_ENTRY, mapa, i)
        if r == hooks.NO_RESULT:
            break
        e = {"especie": r & 0xFFFF, "metodo": (r >> 16) & 0xFF, "periodos": r >> 24, "chances": []}
        for p in (MANHA, TARDE, NOITE, TARDE_NOITE):
            t = box.call(hooks.CMD_DEXNAV_RATE, mapa, i | p << 8)
            assert t != hooks.NO_RESULT, (mapa, i, p)
            e["chances"].append(t & 0xFFFF)
            e["min"], e["max"] = (t >> 16) & 0xFF, t >> 24
        out.append(e)
    return out


def rolar(box: hooks.Mailbox, metodo: int, n: int) -> dict[int, int]:
    """Espécie -> vezes em `n` encontros do gerador real no mapa atual (pode levar uns quadros)."""
    # cada encontro cria o Pokémon de verdade (CreateMon): 2 a 5 quadros por encontro (mais nos níveis altos)
    distintas = box.call(hooks.CMD_DEXNAV_ROLL, metodo, n, timeout=6 * n + 120)
    assert distintas != hooks.NO_RESULT, f"o mapa atual não tem {METODOS[metodo]}"
    addr = box.ctl.game.syms.addr(hooks.TEXT_SYMBOL)
    dados = box.emu.read(addr, distintas * 4)
    pares = struct.unpack(f"<{distintas * 2}H", dados)
    contagem = {pares[i]: pares[i + 1] for i in range(0, len(pares), 2)}
    assert sum(contagem.values()) == n, contagem
    return contagem


def comparar(esperado: dict[int, int], contagem: dict[int, int], n: int, tolerancia_pp: float = 3.0) -> list[tuple]:
    """(espécie, chance enumerada %, frequência real %) de cada espécie fora de ±tolerância (ou que apareceu sem estar
    na enumeração); lista vazia = bateu."""
    fora = []
    for especie in set(esperado) | set(contagem):
        chance = esperado.get(especie, 0) / 10
        freq = 100 * contagem.get(especie, 0) / n
        if abs(chance - freq) > tolerancia_pp or (chance == 0) != (contagem.get(especie, 0) == 0):
            fora.append((especie, chance, round(freq, 2)))
    return fora


def _area(emu, syms) -> int:
    return emu.read_u32(syms.addr("gSaveBlock1Ptr")) + SB1_DEXNAV


def magic(emu, syms) -> int:
    return emu.read_u32(_area(emu, syms))


def visitado(emu, syms, mapa: int) -> bool:
    byte = emu.read(_area(emu, syms) + 4 + mapa // 8, 1)[0]
    return bool(byte >> (mapa % 8) & 1)


def visitados(emu, syms, total: int = 124) -> list[int]:
    bits = emu.read(_area(emu, syms) + 4, 16)
    return [i for i in range(total) if bits[i // 8] >> (i % 8) & 1]


def zerar_visitados(emu, syms) -> None:
    """Só na ROM de teste/pytest: nenhum mapa visitado (o marcador fica)."""
    emu.write(_area(emu, syms) + 4, bytes(16))
