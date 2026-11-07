"""Seguidores (POK-48), Task 2: o seguidor nunca vai para o save nem para o Quest Log, o bit da opção e o estado em
EWRAM (sem emulador: lê o C como texto).

- `test_save_pula_seguidor`: o laço que copia `gObjectEvents` para `gSaveBlock1Ptr->objectEvents` (load_save.c) e o que
  grava os objetos da cena do Quest Log (quest_log_objects.c) pulam o slot de `Follower_IsFollowerObject`; o replay
  (`QL_LoadObjects`) também não recria um seguidor gravado.
- `test_bit_opcao`: `u16 optionsFollowerOff:1` no bitfield de 0x15 do SaveBlock2, logo depois de `regionMapZoom` (0 = Sim:
  save antigo abre ligado), com `STATIC_ASSERT` de offset e tamanho do SaveBlock2 em follower.c.
- `test_ewram_seguidor`: `struct FollowerState` em EWRAM com `STATIC_ASSERT(sizeof(...) <= 16)`.
- `test_localid_reservado`: `OBJ_EVENT_ID_FOLLOWER` = 0xFE e nenhum mapa chega perto (localId = índice + 1 do template,
  no máximo OBJECT_EVENT_TEMPLATES_COUNT = 64).
"""

import json
import re

from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
INCLUDE = REPO_ROOT / "include"


def _ler(caminho):
    return caminho.read_text(encoding="utf-8")


def _funcao(texto: str, nome: str) -> str:
    """Corpo de `nome(...)` { ... } (chaves balanceadas)."""
    m = re.search(rf"^\w[\w\s\*]*\b{nome}\s*\([^;{{]*\)\s*\{{", texto, re.M)
    assert m, f"função {nome} não encontrada"
    i, prof = m.end(), 1
    while prof:
        prof += {"{": 1, "}": -1}.get(texto[i], 0)
        i += 1
    return texto[m.end():i - 1]


def _sem_comentarios(texto: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", texto, flags=re.S)


def test_save_pula_seguidor():
    load_save = _sem_comentarios(_ler(SRC / "load_save.c"))
    corpo = _funcao(load_save, "SaveObjectEvents")
    assert "Follower_IsFollowerObject(&gObjectEvents[i])" in corpo, corpo
    assert "gSaveBlock1Ptr->objectEvents[i] = gObjectEvents[i]" in corpo, corpo
    assert '#include "follower.h"' in load_save

    ql = _sem_comentarios(_ler(SRC / "quest_log_objects.c"))
    assert '#include "follower.h"' in ql
    grava = _funcao(ql, "QL_RecordObjects")
    assert "Follower_IsFollowerObject(&gObjectEvents[i])" in grava, grava
    # o registro do seguidor vai zerado (inativo), não com os campos do objeto
    assert re.search(r"Follower_IsFollowerObject\(&gObjectEvents\[i\]\)\)\s*\{[^}]*CpuFill", grava), grava
    replay = _funcao(ql, "QL_LoadObjects")
    assert "OBJ_EVENT_ID_FOLLOWER" in replay, replay


def test_bit_opcao():
    glob = _sem_comentarios(_ler(INCLUDE / "global.h"))
    sb2 = glob[glob.index("struct SaveBlock2\n"):]
    sb2 = sb2[:sb2.index("};")]
    campos = re.findall(r"u16\s+(\w+):(\d+);", sb2)
    nomes = [n for n, _ in campos]
    assert nomes == ["optionsTextSpeed", "optionsWindowFrameType", "optionsSound", "optionsBattleStyle",
                     "optionsBattleSceneOff", "regionMapZoom", "optionsFollowerOff"], campos
    bits = [int(b) for _, b in campos]
    assert sum(bits) <= 16 and dict(campos)["optionsFollowerOff"] == "1"
    # 3 + 5 bits em 0x14; o seguidor é o 5º bit de 0x15 (bit 12 do u16): o byte que a esteira lê
    assert sum(bits[:6]) == 12

    follower_c = _sem_comentarios(_ler(SRC / "follower.c"))
    assert re.search(r"STATIC_ASSERT\(offsetof\(struct SaveBlock2, pokedex\) == 0x18,", follower_c)
    assert re.search(r"STATIC_ASSERT\(sizeof\(struct SaveBlock2\) == 0xF24,", follower_c)
    corpo = _funcao(follower_c, "Follower_IsEnabled")
    assert "!gSaveBlock2Ptr->optionsFollowerOff" in corpo, corpo


def test_ewram_seguidor():
    follower_c = _sem_comentarios(_ler(SRC / "follower.c"))
    assert re.search(r"STATIC_ASSERT\(sizeof\(struct FollowerState\) <= 16,", follower_c)
    ewram = re.findall(r"EWRAM_DATA\s+(?:static\s+)?([\w ]+?)\s+(\w+)(\[[^\]]*\])?\s*=", follower_c)
    assert ewram == [("struct FollowerState", "sFollowerState", "")], ewram


def test_localid_reservado():
    h = _ler(INCLUDE / "follower.h")
    assert re.search(r"#define OBJ_EVENT_ID_FOLLOWER\s+0xFE\b", h)
    maior = 0
    for mapa in (REPO_ROOT / "data" / "maps").glob("*/map.json"):
        dados = json.loads(mapa.read_text(encoding="utf-8"))
        maior = max(maior, len(dados.get("object_events", [])))
    assert maior <= 64 < 0xFE, maior


def test_telas_do_cenario_no_fim_de_shared_points():
    """As fotos do cenário `seguidor` (o 1º é sempre CHARMANDER: não dependem do inicial) vão para COMUM/."""
    from esteira import refs
    from esteira.scenarios import full_seguidor as cen
    fim = (len(refs.SHARED_POINTS) - len(refs.POKERUS_POINTS) - len(refs.FAMILIA_POINTS)
           - len(refs.CASAS_POINTS))   # depois deles, só os do Pokérus (POK-50) e do POK-51
    assert refs.SHARED_POINTS[fim - len(cen.SCREEN_POINTS):fim] == cen.SCREEN_POINTS
    assert len(set(refs.SHARED_POINTS)) == len(refs.SHARED_POINTS)
    texto = (REPO_ROOT / "test" / "esteira" / "scenarios" / "full_seguidor.py").read_text(encoding="utf-8")
    for ponto in cen.SCREEN_POINTS:
        assert f'self._shot("{ponto}")' in texto, ponto


def test_paleta_so_objetos_visiveis():
    """Só um objeto visível (sem a flag de esconder) do slot 10 com reflexo no 11 impede o seguidor; um escondido que um
    script mostra depois tira o seguidor em LoadSpecialObjectReflectionPalette."""
    eom = _sem_comentarios(_ler(SRC / "event_object_movement.c"))
    corpo = _funcao(eom, "IsFollowerPaletteSlotInUse")
    assert "FlagGet(gSaveBlock1Ptr->objectEventTemplates[i].flagId)" in corpo, corpo
    carga = _funcao(eom, "LoadSpecialObjectReflectionPalette")
    assert re.search(r"gReflectionEffectPaletteMap\[slot\] == PALSLOT_FOLLOWER\)\s*Follower_Remove\(\);", carga), carga
