"""POK-45 sem emulador: os 6 golpes novos de Fada (MOVE_* 355–360), com os dados da Gen 6.

Dados de batalha, nome e descrição PT-BR, animação, Draining Kiss curando 75%, Disarming Voice
como golpe de som e os learnsets X/Y de tools/gen6/gen6.json (por nível e de ovo). Nenhuma outra
linha dos learnsets muda em relação à base deste pacote (hack-switch 759447339, SHA fixo).
"""

import json
import re
import shutil
import subprocess

import pytest

from esteira import check_text as ct
from esteira.reflow import line_widths
from esteira.scenarios import REPO_ROOT

GEN6 = json.loads((REPO_ROOT / "tools" / "gen6" / "gen6.json").read_text(encoding="utf-8"))
BASE = "759447339662d5680268db3f3b38f44f44ecd88c"   # hack-switch na criação desta branch (SHA fixo)
# POK-54: espécies da Gen 4 acrescentadas depois da base, sem golpe de Fada (conferidas em test_especies_novas.py)
EXTRAS_POK54_LEARNSETS = {"sGibleLevelUpLearnset", "sGabiteLevelUpLearnset", "sGarchompLevelUpLearnset",
                          "sDarkraiLevelUpLearnset"}
EXTRAS_POK54_OVOS = {"SPECIES_GIBLE"}


def _ler(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _git_show(caminho: str) -> str:
    if shutil.which("git") is None:
        pytest.skip("precisa do git")
    return subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{BASE}:{caminho}"], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


NOVOS = ["MOVE_MOONBLAST", "MOVE_PLAY_ROUGH", "MOVE_DAZZLING_GLEAM", "MOVE_DRAINING_KISS",
         "MOVE_FAIRY_WIND", "MOVE_DISARMING_VOICE"]
P, M, K, C = "FLAG_PROTECT_AFFECTED", "FLAG_MIRROR_MOVE_AFFECTED", "FLAG_KINGS_ROCK_AFFECTED", "FLAG_MAKES_CONTACT"

# golpe: (efeito, poder, precisão, PP, chance, alvo, flags, categoria)
ESPERADO = {
    "MOVE_MOONBLAST": ("EFFECT_SPECIAL_ATTACK_DOWN_HIT", 95, 100, 15, 30, "MOVE_TARGET_SELECTED", {P, M}, "SPECIAL"),
    "MOVE_PLAY_ROUGH": ("EFFECT_ATTACK_DOWN_HIT", 90, 90, 10, 10, "MOVE_TARGET_SELECTED", {C, P, M, K}, "PHYSICAL"),
    "MOVE_DAZZLING_GLEAM": ("EFFECT_HIT", 80, 100, 10, 0, "MOVE_TARGET_BOTH", {P, M}, "SPECIAL"),
    "MOVE_DRAINING_KISS": ("EFFECT_ABSORB", 50, 100, 10, 0, "MOVE_TARGET_SELECTED", {C, P, M}, "SPECIAL"),
    "MOVE_FAIRY_WIND": ("EFFECT_HIT", 40, 100, 30, 0, "MOVE_TARGET_SELECTED", {P, M, K}, "SPECIAL"),
    "MOVE_DISARMING_VOICE": ("EFFECT_ALWAYS_HIT", 40, 0, 15, 0, "MOVE_TARGET_BOTH", {P, M, K}, "SPECIAL"),
}


def _constantes_dos_golpes() -> dict[str, int]:
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"^#define (MOVES?_\w+) (\d+)$", _ler("include/constants/moves.h"), re.M)}


def _entradas() -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"^    \[(MOVE_\w+)\] =\s*\{(.*?)^    \},",
                                                        _ler("src/data/battle_moves.h"), re.M | re.S)}


def _campo(corpo: str, nome: str) -> str:
    return re.search(rf"\.{nome} = ([^,]+),", corpo).group(1).strip()


def test_constantes():
    k = _constantes_dos_golpes()
    assert [k[n] for n in NOVOS] == list(range(355, 361))
    assert k["MOVES_COUNT"] == 363  # + Dragon Rush e Dark Void no fim (POK-54)


def test_dados_gen6():
    entradas = _entradas()
    for nome, (efeito, poder, prec, pp, chance, alvo, flags, cat) in ESPERADO.items():
        corpo = entradas[nome]
        achado = (_campo(corpo, "effect"), int(_campo(corpo, "power")), int(_campo(corpo, "accuracy")),
                  int(_campo(corpo, "pp")), int(_campo(corpo, "secondaryEffectChance")), _campo(corpo, "target"),
                  {f.strip() for f in _campo(corpo, "flags").split("|")}, _campo(corpo, "category"))
        assert achado == (efeito, poder, prec, pp, chance, alvo, flags, f"MOVE_CATEGORY_{cat}"), nome
        assert _campo(corpo, "type") == "TYPE_FAIRY", nome
        assert _campo(corpo, "priority") == "0", nome
        assert GEN6["categories"][nome] == cat and GEN6["types"][nome] == "TYPE_FAIRY", nome


def test_nomes_e_descricoes():
    nomes = dict(re.findall(r"\[(MOVE_\w+)\]\s*=\s*_\(\"([^\"]*)\"\)", _ler("src/data/text/move_names.h")))
    ponteiros = dict(re.findall(r"\[(MOVE_\w+)\s*-\s*1\]\s*=\s*(gMoveDescription_\w+)", _ler("src/move_descriptions.c")))
    descricoes = {m.group(1): m.group(2) for m in re.finditer(
        r"const u8 (gMoveDescription_\w+)\[\] = _\(\"((?:[^\"\\]|\\.)*)\"\);", _ler("src/move_descriptions.c"))}
    rotulos = set()
    for nome in NOVOS:
        assert nome in nomes and 0 < len(nomes[nome]) <= 12, nome
        assert nome in ponteiros and ponteiros[nome] in descricoes, nome
        texto = descricoes[ponteiros[nome]]
        linhas = texto.split("\\n")
        assert len(linhas) <= 4 and max(line_widths(texto)) <= 15 * 8 - 7, (nome, texto)
        rotulos |= {nome, ponteiros[nome]}
    entradas = [e for e in ct._sources(REPO_ROOT) if isinstance(e, ct._Entry) and e.label in rotulos]
    assert len(entradas) == 12
    assert ct.english_report(str(REPO_ROOT), entradas) == {}


def test_animacoes():
    texto = _ler("data/battle_anim_scripts.s")
    tabela = re.search(r"gBattleAnims_Moves::\n(.*?)\n\n", texto, re.S).group(1)
    alvos = re.findall(r"^\t\.4byte (\w+)", tabela, re.M)
    assert len(alvos) == 361
    assert alvos[-6:] == [n.replace("MOVE_", "Move_") for n in NOVOS]
    for n in NOVOS:
        assert re.search(rf"^{n.replace('MOVE_', 'Move_')}:\n", texto, re.M), n


def _funcao(texto: str, assinatura: str) -> str:
    return re.search(rf"{re.escape(assinatura)}\n\{{(.*?)\n\}}", texto, re.S).group(1)


def test_draining_kiss_75():
    corpo = _funcao(_ler("src/battle_script_commands.c"), "static void Cmd_negativedamage(void)")
    assert re.search(r"gCurrentMove == MOVE_DRAINING_KISS", corpo)
    assert "gHpDealt * 3 / 4" in corpo
    assert "gHpDealt / 2" in corpo                      # Absorb, Mega Drain, Giga Drain, Dream Eater: 50%
    for golpe in ("MOVE_ABSORB", "MOVE_MEGA_DRAIN", "MOVE_GIGA_DRAIN"):
        assert golpe not in corpo


def test_disarming_voice_som():
    tabela = re.search(r"sSoundMovesTable\[\] =\s*\{(.*?)\};", _ler("src/battle_util.c"), re.S).group(1)
    assert "MOVE_DISARMING_VOICE" in tabela
    assert tabela.strip().endswith("SOUND_MOVES_END")


# --- learnsets -----------------------------------------------------------------------------

def _learnsets(texto: str) -> dict[str, list[tuple[int, str]]]:
    return {m.group(1): [(int(lv), mv) for lv, mv in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", m.group(2))]
            for m in re.finditer(r"static const u16 (s\w+LevelUpLearnset)\[\] = \{(.*?)\};", texto, re.S)}


def _ponteiros() -> dict[str, str]:
    return dict(re.findall(r"\[(SPECIES_\w+)\] = (s\w+LevelUpLearnset)", _ler("src/data/pokemon/level_up_learnset_pointers.h")))


def _ovos(texto: str) -> dict[str, list[str]]:
    return {f"SPECIES_{m.group(1)}": re.findall(r"MOVE_\w+", m.group(2))
            for m in re.finditer(r"egg_moves\((\w+),(.*?)\)", texto, re.S)}


def _levelup_esperado() -> set[tuple[str, int, str]]:
    """Regra do pacote: golpe repetido na mesma espécie no X/Y fica só no nível > 1 (o nível 1 do X/Y é o
    relembrar da evolução); se só houver o nível 1, fica o 1."""
    esperado = set()
    for especie, lista in GEN6["levelup"].items():
        for golpe in {g for _, g in lista}:
            niveis = sorted({lv for lv, g in lista if g == golpe})
            if len(niveis) > 1:
                niveis = [lv for lv in niveis if lv > 1]
            esperado |= {(especie, lv, golpe) for lv in niveis}
    return esperado


def test_learnsets_gen6():
    atuais, base, ponteiros = _learnsets(_ler("src/data/pokemon/level_up_learnsets.h")), \
        _learnsets(_git_show("src/data/pokemon/level_up_learnsets.h")), _ponteiros()
    assert set(atuais) - EXTRAS_POK54_LEARNSETS == set(base)
    assert not [g for nome in EXTRAS_POK54_LEARNSETS for _, g in atuais[nome] if g in NOVOS]
    atuais = {k: v for k, v in atuais.items() if k not in EXTRAS_POK54_LEARNSETS}
    for nome, lista in atuais.items():
        assert [x for x in lista if x[1] not in NOVOS] == base[nome], nome          # nada mais mudou
        niveis = [lv for lv, _ in lista]
        assert niveis == sorted(niveis), nome                                       # ordem crescente
    achado = {(esp, lv, g) for esp, arr in ponteiros.items() for lv, g in atuais.get(arr, []) if g in NOVOS}
    # espécies que compartilham o array (ex.: Unown/Castform/Deoxys) não entram aqui; o achado é exato
    esperado = _levelup_esperado()
    assert esperado and achado == esperado
    assert ("SPECIES_GARDEVOIR", 85, "MOVE_MOONBLAST") in esperado and ("SPECIES_MAWILE", 60, "MOVE_PLAY_ROUGH") in esperado
    assert ("SPECIES_MAWILE", 1, "MOVE_FAIRY_WIND") in esperado and ("SPECIES_MAWILE", 1, "MOVE_PLAY_ROUGH") not in esperado


def test_golpes_de_ovo_gen6():
    atuais, base = _ovos(_ler("src/data/pokemon/egg_moves.h")), _ovos(_git_show("src/data/pokemon/egg_moves.h"))
    assert set(atuais) - EXTRAS_POK54_OVOS == set(base)
    assert not [g for esp in EXTRAS_POK54_OVOS for g in atuais[esp] if g in NOVOS]
    atuais = {k: v for k, v in atuais.items() if k not in EXTRAS_POK54_OVOS}
    for especie, lista in atuais.items():
        assert [g for g in lista if g not in NOVOS] == base[especie], especie
        assert len(lista) <= 10, especie                                            # EGG_MOVES_ARRAY_COUNT
    achado = {(esp, g) for esp, lista in atuais.items() for g in lista if g in NOVOS}
    esperado = {(esp, g) for esp, lista in GEN6["egg"].items() for g in lista}
    assert esperado and achado == esperado


# --- Task 4b: moveset padrão e IA com Soundproof ---------------------------------------------

def _moveset_padrao(learnset: list[tuple[int, str]], nivel: int) -> list[str]:
    """Espelho de GiveBoxMonInitialMoveset (src/pokemon.c): percorre o learnset até passar do nível;
    golpe já conhecido é pulado; com 4 golpes, apaga o primeiro e põe o novo no fim."""
    golpes: list[str] = []
    for lv, golpe in learnset:
        if lv > nivel:
            break
        if golpe in golpes:
            continue
        if len(golpes) == 4:
            golpes.pop(0)
        golpes.append(golpe)
    return golpes


def test_golpes_novos_nivel1_nao_mudam_moveset_padrao():
    atuais = _learnsets(_ler("src/data/pokemon/level_up_learnsets.h"))
    base = _learnsets(_git_show("src/data/pokemon/level_up_learnsets.h"))
    com_nivel1 = {nome for nome, lista in atuais.items() if any(lv == 1 and g in NOVOS for lv, g in lista)}
    assert {"sClefableLevelUpLearnset", "sWigglytuffLevelUpLearnset", "sJynxLevelUpLearnset",
            "sLinooneLevelUpLearnset"} <= com_nivel1
    for nome in com_nivel1:
        # golpes novos de nível > 1 (Gen 6 pura, de propósito) ficam fora; aqui só pesa o de nível 1
        lista = [(lv, g) for lv, g in atuais[nome] if not (g in NOVOS and lv > 1)]
        bloco1 = [g for lv, g in lista if lv == 1]
        novos1 = [g for g in bloco1 if g in NOVOS]
        assert bloco1[:len(novos1)] == novos1, nome          # o novo vem antes dos outros de nível 1
        for nivel in range(1, 101):
            velho, novo = _moveset_padrao(base[nome], nivel), _moveset_padrao(lista, nivel)
            if len(velho) == 4:
                assert novo == velho, (nome, nivel)          # nada sai do moveset padrão
            else:
                # base com menos de 4 golpes (Clefairy, Persian, Mawile): o novo só ocupa a vaga vazia
                assert [g for g in novo if g not in novos1] == velho, (nome, nivel)


def test_ia_soundproof_cobre_todos_os_golpes_de_som():
    tabela = re.search(r"sSoundMovesTable\[\] =\s*\{(.*?)\};", _ler("src/battle_util.c"), re.S).group(1)
    som = [g for g in re.findall(r"MOVE_\w+", tabela)]
    assert {"MOVE_HYPER_VOICE", "MOVE_DISARMING_VOICE"} <= set(som)
    ia = re.search(r"^AI_CheckBadMove_CheckSoundproof::\n(.*?)\n\n", _ler("data/battle_ai_scripts.s"), re.M | re.S).group(1)
    linhas = ia.splitlines()
    assert linhas[:2] == ["\tget_ability AI_TARGET", "\tif_not_equal ABILITY_SOUNDPROOF, AI_CheckBadMove_CheckEffect"]
    assert linhas[2:] == [f"\tif_move {g}, Score_Minus10" for g in som]
