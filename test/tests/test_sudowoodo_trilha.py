"""POK-28, Task 5: a "árvore estranha" do Caminho Verde (Ilha Seis) é um Sudowoodo nv 35.

Molde do Jirachi (`SevenIsland_TanobyRuins`): o objeto nasce escondido e o ON_TRANSITION só o mostra com a Dex
Nacional ligada, sem ter fugido e sem o Sudowoodo capturado. Derrotado ou com fuga, ele some até a próxima entrada no
Hall da Fama (`EventScript_ResetLegendaries`); capturado, some para sempre. A batalha é a selvagem comum (música e
transição de selvagem, como o Snorlax da Rota 12), e não a de lendário.

O gráfico é o do seguidor (`sFollowerPicTable_Sudowoodo` e `sFollowerPal_Sudowoodo`, de `follower_species.h`), sem
arte nova, com a paleta no slot especial dos objetos (10), como o S.S. Anne e a Estrela de Jirachi.

O cenário `johto` (`test/esteira/scenarios/full_johto.py`, casos `johto/sudowoodo/*`) roda o fluxo de verdade.
"""

import json
import re
import struct

from esteira.scenarios import REPO_ROOT

MAPA = "data/maps/SixIsland_GreenPath"
P = "SixIsland_GreenPath_"
SUDOWOODO_XY = (39, 10)        # o recuo de terra ao norte do caminho, a oeste da placa (40, 10)
LARGURA = 72


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _block(label: str, rel: str = f"{MAPA}/scripts.inc") -> str:
    """Corpo do rótulo `label::` até o próximo rótulo global (sem os comentários `@` do seguinte)."""
    src = _read(rel)
    start = src.index(f"{label}::")
    m = re.search(r"^\w+::", src[start + len(label) + 2:], re.M)
    corpo = src[start:start + len(label) + 2 + (m.start() if m else len(src))]
    return re.sub(r"(?:^@[^\n]*\n)+\Z", "", corpo, flags=re.M)


def _defines(rel: str) -> dict[str, int]:
    return {n: int(v, 0) for n, v in re.findall(r"^#define (\w+)\s+(0x[0-9A-Fa-f]+|\d+)\b", _read(rel), re.M)}


def _objeto() -> dict:
    objs = [o for o in json.loads(_read(f"{MAPA}/map.json"))["object_events"]
            if o.get("script") == f"{P}EventScript_Sudowoodo"]
    assert len(objs) == 1, objs
    return objs[0]


def _celula(x: int, y: int) -> tuple[int, int, int]:
    """(colisão, elevação, comportamento) do tile, como o jogo lê (map.bin + atributos dos tilesets)."""
    data = (REPO_ROOT / "data/layouts/SixIsland_GreenPath/map.bin").read_bytes()
    v = struct.unpack_from("<H", data, (y * LARGURA + x) * 2)[0]
    metatile = v & 0x3FF
    if metatile < 0x280:
        attrs, idx = "data/tilesets/primary/general/metatile_attributes.bin", metatile
    else:
        attrs, idx = "data/tilesets/secondary/sevii_islands_67/metatile_attributes.bin", metatile - 0x280
    beh = struct.unpack_from("<I", (REPO_ROOT / attrs).read_bytes(), idx * 4)[0] & 0x1FF
    return (v >> 10) & 3, v >> 12, beh


def test_flags_na_faixa_livre_sem_colisao():
    d = _defines("include/constants/flags.h")
    assert d["FLAG_HIDE_SUDOWOODO"] == 0x4DF and d["FLAG_SUDOWOODO_FLEW_AWAY"] == 0x4E0
    assert "FLAG_0x4DF" not in d and "FLAG_0x4E0" not in d
    valores = [v for n, v in d.items() if n.startswith("FLAG_")]
    assert valores.count(0x4DF) == 1 and valores.count(0x4E0) == 1
    assert d["FLAG_0x4E1"] == 0x4E1                 # a próxima continua livre


def test_hall_da_fama_traz_de_volta():
    reset = _block("EventScript_ResetLegendaries", "data/scripts/hall_of_fame.inc")
    assert "clearflag FLAG_SUDOWOODO_FLEW_AWAY" in reset
    assert "FLAG_HIDE_SUDOWOODO" not in reset        # quem decide se aparece é o ON_TRANSITION


def test_objeto_no_recuo_sem_bloquear():
    o = _objeto()
    assert o["flag"] == "FLAG_HIDE_SUDOWOODO"
    assert o["local_id"] == "LOCALID_GREEN_PATH_SUDOWOODO"
    assert o["graphics_id"] == "OBJ_EVENT_GFX_SUDOWOODO"
    assert (o["x"], o["y"], o["elevation"]) == (*SUDOWOODO_XY, 3)
    assert o["movement_type"] == "MOVEMENT_TYPE_FACE_DOWN" and o["trainer_type"] == "TRAINER_TYPE_NONE"
    # entra no fim (o da Jaclyn não muda de LOCALID)
    objs = json.loads(_read(f"{MAPA}/map.json"))["object_events"]
    assert [x["script"] for x in objs] == [f"{P}EventScript_Jaclyn", f"{P}EventScript_Sudowoodo"]
    x, y = SUDOWOODO_XY
    assert _celula(x, y) == (0, 3, 0)                # terra comum, sem colisão, elevação 3
    # recuo: só se chega a ele por baixo (39, 11); os outros vizinhos são parede, então ele não está em passagem
    assert _celula(x, y + 1) == (0, 3, 0)
    for vx, vy in ((x, y - 1), (x + 1, y)):
        assert _celula(vx, vy)[0] != 0, (vx, vy)
    assert _celula(x - 1, y)[:2] == (0, 3)           # o outro tile do recuo (38, 10), também sem saída


def test_rota_obrigatoria_continua_livre():
    """Da saída da Moita Estampada (45/46, 11) até a margem oeste (37, 14..16, onde se surfa) com o Sudowoodo no lugar:
    as linhas 11 e 12 e a escada de pedra (38/39, 13) passam ao sul dele."""
    import esteira.nav as nav

    grupos = json.loads(_read("data/maps/map_groups.json"))
    grupo, num = next((g, grupos[nome].index("SixIsland_GreenPath")) for g, nome in enumerate(grupos["group_order"])
                      if "SixIsland_GreenPath" in grupos[nome])
    grid = nav.load_map_grid(REPO_ROOT, grupo, num)
    bloqueado = {SUDOWOODO_XY}
    for saida in ((45, 11), (46, 11)):
        for margem in ((37, 14), (37, 15), (37, 16)):
            assert nav.find_route(grid, saida, margem, bloqueado) is not None, (saida, margem)
    # e a placa (40, 10) continua legível de baixo
    assert nav.find_route(grid, (45, 11), (40, 11), bloqueado) is not None


def test_aparece_so_depois_da_dex_nacional():
    scripts = _read(f"{MAPA}/scripts.inc")
    assert re.search(rf"map_script MAP_SCRIPT_ON_TRANSITION, {P}OnTransition\b", scripts)
    assert re.search(rf"map_script MAP_SCRIPT_ON_RESUME, {P}OnResume\b", scripts)
    b = _block(f"{P}EventScript_TryShowSudowoodo")
    linhas = [l.strip() for l in b.splitlines()[1:] if l.strip()]
    assert linhas[0] == "setflag FLAG_HIDE_SUDOWOODO"               # escondido por padrão
    assert linhas[-2:] == ["clearflag FLAG_HIDE_SUDOWOODO", "return"]
    assert "goto_if_set FLAG_SUDOWOODO_FLEW_AWAY, EventScript_Return" in b
    assert "specialvar VAR_RESULT, IsNationalPokedexEnabled" in b
    assert "goto_if_eq VAR_RESULT, FALSE, EventScript_Return" in b
    assert "setvar VAR_0x8004, SPECIES_SUDOWOODO" in b and "IsSpeciesCaught" in b
    assert "goto_if_eq VAR_RESULT, TRUE, EventScript_Return" in b


def test_conversa_e_batalha_selvagem_nv35():
    b = _block(f"{P}EventScript_Sudowoodo")
    assert "goto_if_questlog EventScript_ReleaseEnd" in b
    # reconfere na conversa o que não depende do mapa (objeto velho de um save gravado aqui)
    assert "goto_if_set FLAG_SUDOWOODO_FLEW_AWAY, EventScript_ReleaseEnd" in b
    assert "IsNationalPokedexEnabled" in b
    assert b.index("IsSpeciesCaught") < b.index(f"msgbox {P}Text_StrangeTree")
    assert "goto_if_eq VAR_RESULT, TRUE, EventScript_ReleaseEnd" in b
    assert b.index(f"msgbox {P}Text_StrangeTree") < b.index("playmoncry SPECIES_SUDOWOODO")
    assert "setwildbattle SPECIES_SUDOWOODO, 35" in b
    # batalha selvagem comum (música e transição de selvagem), como o Snorlax; não a de lendário
    assert "dowildbattle" in b and "StartLegendaryBattle" not in b and "seteventmon" not in b
    assert b.index("setflag FLAG_SYS_SPECIAL_WILD_BATTLE") < b.index("dowildbattle") < b.index(
        "clearflag FLAG_SYS_SPECIAL_WILD_BATTLE")
    for saida in ("B_OUTCOME_WON", "B_OUTCOME_RAN", "B_OUTCOME_PLAYER_TELEPORTED", "B_OUTCOME_MON_FLED"):
        assert re.search(rf"goto_if_eq VAR_RESULT, {saida}, {P}EventScript_SudowoodoRanOff\b", b), saida
    assert "setflag FLAG_SUDOWOODO_FLEW_AWAY" not in b      # capturado (ou derrota do jogador) não liga a fuga


def test_fuga_some_ate_o_hall_e_captura_some_para_sempre():
    fuga = _block(f"{P}EventScript_SudowoodoRanOff")
    assert "setflag FLAG_SUDOWOODO_FLEW_AWAY" in fuga
    assert "removeobject LOCALID_GREEN_PATH_SUDOWOODO" in fuga
    assert f"msgbox {P}Text_SudowoodoRanOff" in fuga
    assert fuga.index("setflag") < fuga.index("removeobject")
    remover = _block(f"{P}EventScript_TryRemoveSudowoodo")
    assert "goto_if_ne VAR_RESULT, B_OUTCOME_CAUGHT, EventScript_Return" in remover
    assert "removeobject LOCALID_GREEN_PATH_SUDOWOODO" in remover
    assert "call_if_set FLAG_SYS_SPECIAL_WILD_BATTLE" in _block(f"{P}OnResume")


def test_textos():
    texto = _read(f"{MAPA}/text.inc")
    for rotulo in ("Text_StrangeTree", "Text_SudowoodoRanOff"):
        corpo = _block(f"{P}{rotulo}", f"{MAPA}/text.inc")
        bruto = "".join(re.findall(r'\.string "(.*?)"', corpo))
        assert bruto.endswith("$"), rotulo
        assert all(c.count("\\n") <= 1 for c in bruto.split("\\p")), rotulo
    arvore = re.sub(r"\\[nlp]", " ", "".join(re.findall(r'\.string "(.*?)"', _block(f"{P}Text_StrangeTree",
                                                                                     f"{MAPA}/text.inc")))).lower()
    assert "árvore estranha" in arvore and "mexeu" in arvore
    assert "SUDOWOODO" in _block(f"{P}Text_SudowoodoRanOff", f"{MAPA}/text.inc")
    assert not re.search(r"\b(the|tree|weird|ran)\b", texto.lower()), "texto em inglês"


def test_grafico_do_seguidor_sem_arte_nova():
    d = _defines("include/constants/event_objects.h")
    # depois do bloco da Família Sombra (o id vai para o save: nada antes dele muda de número)
    familia = [v for n, v in d.items() if n.startswith("OBJ_EVENT_GFX_") and v < 240 and n != "OBJ_EVENT_GFX_SUDOWOODO"]
    assert max(familia) == 192
    assert d["OBJ_EVENT_GFX_SUDOWOODO"] == 193 and d["NUM_OBJ_EVENT_GFX"] == 194
    pointers = _read("src/data/object_events/object_event_graphics_info_pointers.h")
    assert re.search(r"\[OBJ_EVENT_GFX_SUDOWOODO\]\s*=\s*&gObjectEventGraphicsInfo_Sudowoodo,", pointers)
    info = re.search(r"gObjectEventGraphicsInfo_Sudowoodo = \{(.*?)\n\};",
                     _read("src/data/object_events/object_event_graphics_info.h"), re.S).group(1)
    assert ".images = sFollowerPicTable_Sudowoodo," in info and ".anims = sAnimTable_Follower," in info
    assert ".paletteTag = OBJ_EVENT_PAL_TAG_SUDOWOODO," in info
    # slot especial (10): os slots de NPC 1-4 ficam com as paletas comuns (Jaclyn e os vizinhos); o seguidor é o 11
    assert ".paletteSlot = PALSLOT_NPC_SPECIAL," in info
    assert ".width = 32," in info and ".height = 32," in info and ".size = 512," in info
    movimento = _read("src/event_object_movement.c")
    assert re.search(r"#define OBJ_EVENT_PAL_TAG_SUDOWOODO\s+0x111D\b", movimento)
    assert re.search(r"\{sFollowerPal_Sudowoodo,\s*OBJ_EVENT_PAL_TAG_SUDOWOODO\}", movimento)
    # a paleta não está nos conjuntos de reflexo especiais: não grava no slot do seguidor (ele continua no mapa)
    reflexos = re.search(r"gSpecialObjectReflectionPaletteSets\[\] = \{(.*?)\};", movimento, re.S).group(1)
    assert "SUDOWOODO" not in reflexos
    assert movimento.index('#include "data/object_events/follower_species.h"') < movimento.index(
        '#include "data/object_events/object_event_graphics_info.h"')
