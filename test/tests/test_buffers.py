"""Estouro de buffer de string (Task T4): texto traduzível copiado para um buffer fixo
(esteira/buffers.py), medido em bytes + EOS contra o tamanho lido do C, sem piorar a base inglesa.

Os casos reais da rodada 1 viram teste: "Bolso de itens-chave" no gStringVar3[20] pelo
`bufferstdstring` (travava a encomenda do Viridian Mart) e "Cobertura" no mapName[25] do aviso
de mapa do terraço da Loja de Celadon.
"""

import shutil
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import buffers as bf
from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]
STRINGS = "src/strings.c"


@lru_cache(maxsize=1)
def _scan():
    return ct._scan(REPO_ROOT, ct.TRANSLATION_BASE)


@pytest.fixture(scope="module")
def ctx():
    """Contexto do repo real com a base inglesa (a hack-switch atual)."""
    ctx = bf.repo_context(str(REPO_ROOT))
    if ctx is None:
        pytest.skip(f"base inglesa indisponível ({_scan().base_note or 'sem .git'}): o critério da base não roda")
    return ctx


def _failures(ctx, needle: str = "", known=None) -> list[str]:
    return [r.detail for r in bf.check_buffers(REPO_ROOT, ctx=ctx, known=known)
            if r.status == "falha" and needle in r.detail]


def _base_with(ctx, changes: dict[tuple[str, str], str]) -> ct._Base:
    """A base real com alguns textos ingleses trocados."""
    texts = dict(ctx.base.texts)
    texts.update({k: (v,) for k, v in changes.items()})
    return ct._Base(texts, ctx.base.changed | {f for f, _l in changes}, ctx.base.present)


# --- medida --------------------------------------------------------------------------------------

def test_bytes_contam_acentuada_como_1_e_placeholder_pelo_charmap(ctx):
    assert bf.text_bytes("Poção$", ctx.env) == 5
    assert bf.text_bytes("Bolso de itens-chave", ctx.env) == 20
    # cópia crua: {STR_VAR_1} e {PLAYER} são 2 bytes (FD xx); o que vem depois do $ não é copiado
    assert bf.text_bytes("{PLAYER}: {STR_VAR_1}$lixo", ctx.env) == 2 + 2 + 2


def test_placeholders_expandidos_medem_o_pior_caso_da_t3(ctx):
    words = bf.EXPANDS["string"]
    # {PLAYER} 7 letras, {STR_VAR_1} 10 (VAR_SIZES), {COLOR} fica como está (3 bytes)
    assert bf.text_bytes("{PLAYER}: {STR_VAR_1}$", ctx.env, words) == 7 + 2 + 10
    assert bf.text_bytes("{COLOR RED}x$", ctx.env, words) == 3 + 1
    # DynamicPlaceholderTextUtil só expande o {DYNAMIC n}
    assert bf.text_bytes("{DYNAMIC 0x00}{PLAYER}$", ctx.env, bf.EXPANDS["dynamic"]) == 10 + 2


# --- tamanho lido do C ----------------------------------------------------------------------------

def test_tamanho_dos_buffers_lido_do_codigo(ctx):
    var3 = bf._resolve_buffer(bf.BufRef("gStringVar3"), ctx)
    assert (var3.size, var3.site) == (20, "src/string_util.c:6")
    assert bf._resolve_buffer(bf.BufRef("gStringVar1"), ctx).size == 32
    popup = bf._resolve_buffer(bf.BufRef("mapName", "src/map_name_popup.c", "MapNamePopupPrintMapNameOnWindow"), ctx)
    assert popup.size == 25 and popup.site.startswith("src/map_name_popup.c:")


def test_tamanho_muda_quando_o_c_muda(tmp_path, ctx):
    """Nada copiado à mão: outro string_util.c dá outro tamanho, inclusive por expressão de #define."""
    (tmp_path / "src").mkdir()
    (tmp_path / "include" / "constants").mkdir(parents=True)
    (tmp_path / "include" / "constants" / "global.h").write_text("#define POKEMON_NAME_LENGTH 10\n")
    (tmp_path / "src" / "string_util.c").write_text(
        "EWRAM_DATA u8 gStringVar1[32] = {};\n"
        "EWRAM_DATA u8 gStringVar2[POKEMON_NAME_LENGTH + 14] = {};\n"
        "EWRAM_DATA u8 gStringVar3[0x18] = {};\n")
    fake = bf.build_context(tmp_path, entries=[], base=None, env=ctx.env)
    assert bf._resolve_buffer(bf.BufRef("gStringVar2"), fake).size == 24
    assert bf._resolve_buffer(bf.BufRef("gStringVar3"), fake).size == 24


def test_eval_size():
    defines = {"A": "10", "B": "(A + 1) * 2"}
    assert bf.eval_size("B - 2", defines) == 20
    assert bf.eval_size("0x900", defines) == 2304
    assert bf.eval_size("sizeof(x)", defines) is None


# --- casos reais da rodada 1 ----------------------------------------------------------------------

def test_bolso_de_itens_chave_pelo_bufferstdstring_reprova(ctx):
    paths = [p for p in bf.script_paths(ctx) if p.what == "bufferstdstring STR_VAR_3, STDSTRING_KEY_ITEMS_POCKET"]
    assert any(p.site.startswith("data/scripts/obtain_item.inc:") for p in paths)
    assert all(p.buffer.name == "gStringVar3" and p.buffer.size == 20 for p in paths)
    bad = bf.with_texts(ctx, {(STRINGS, "gText_KeyItemsPocket"): "Bolso de itens-chave"})
    found = [f for f in _failures(bad, "gText_KeyItemsPocket") if "gStringVar3[20]" in f]
    assert len(found) == 1, found
    assert "21 bytes" in found[0] and "data/scripts/obtain_item.inc:" in found[0]
    assert _failures(bf.with_texts(ctx, {(STRINGS, "gText_KeyItemsPocket"): "Bolso Itens-chave"}),
                     "gText_KeyItemsPocket") == []


def test_terraco_cabe_e_cobertura_reprova_no_aviso_de_mapa(ctx):
    roof = [p for p in bf.popup_paths(ctx) if "CeladonCity_DepartmentStore_Roof" in p.what]
    assert len(roof) == 1 and roof[0].buffer.size == 25
    assert _failures(bf.with_texts(ctx, {(STRINGS, "gText_Rooftop2"): "Terraço"}), "mapName") == []
    found = _failures(bf.with_texts(ctx, {(STRINGS, "gText_Rooftop2"): "Cobertura"}), "gText_Rooftop2")
    assert found and "26 bytes" in found[0] and "mapName[25]" in found[0]
    assert "Loja de Celadon" not in found[0] or "MAPSEC_SPECIAL_AREA" in found[0]


def test_bufferitemname_com_nome_de_13_letras_cabe(ctx):
    item = "src/data/items.json"
    named = [p for p in bf.script_paths(ctx) if p.what.startswith("bufferitemname ")]
    assert named and min(p.buffer.size for p in named) == 20
    ok = bf.with_texts(ctx, {(item, "ITEM_POTION.name"): "ABCDEFGHIJKLM"})        # 13 letras + EOS = 14
    assert _failures(ok, "ITEM_POTION") == []
    too_long = bf.with_texts(ctx, {(item, "ITEM_POTION.name"): "ABCDEFGHIJKLMNOPQRST"})   # 20 + EOS
    found = _failures(too_long, "ITEM_POTION")
    assert found and any("gStringVar" in f for f in found)


def test_base_que_ja_estoura_nao_reprova_a_traducao_que_estoura_igual_ou_menos(ctx):
    key = (STRINGS, "gText_KeyItemsPocket")
    base = _base_with(ctx, {key: "KEY ITEMS POCKET, THE BIG ONE"})        # 29 + EOS = 30
    assert _failures(bf.with_texts(ctx, {key: "Bolso de itens-chave"}, base=base), "gText_KeyItemsPocket") == []
    found = _failures(bf.with_texts(ctx, {key: "Bolso de itens-chave bem grande!"}, base=base),
                      "gText_KeyItemsPocket")
    assert found and "33 bytes" in found[0] and "a base inglesa já ia a 30" in found[0]


def test_rotulo_novo_ou_sem_base_e_estrito(ctx):
    key = (STRINGS, "gText_KeyItemsPocket")
    texts = {k: v for k, v in ctx.base.texts.items() if k != key}          # o rótulo não existia
    base = ct._Base(texts, ctx.base.changed, ctx.base.present)
    found = _failures(bf.with_texts(ctx, {key: "Bolso de itens-chave"}, base=base), "gText_KeyItemsPocket")
    assert found and "base inglesa" not in found[0]
    strict = bf.with_texts(ctx, {key: "Bolso de itens-chave"}, base=None)
    assert _failures(strict, "gText_KeyItemsPocket")


def test_concatenacao_mede_a_soma(ctx):
    """Nível na tela da equipe: gStringVar1 = gText_Lv + até 3 algarismos (src/party_menu.c)."""
    lv = [p for p in bf.c_paths(ctx) if p.what.startswith("StringCopy(gStringVar1, gText_Lv)")]
    assert len(lv) == 1 and len(lv[0].parts) == 2
    fits = _failures(bf.with_texts(ctx, {(STRINGS, "gText_Lv"): "A" * 28}), "gStringVar1[32]")
    assert fits == []                                       # 28 + 3 + EOS = 32
    found = _failures(bf.with_texts(ctx, {(STRINGS, "gText_Lv"): "A" * 29}), "gStringVar1[32]")
    assert found and "33 bytes" in found[0] and "src/party_menu.c:" in found[0]


# --- inventário -------------------------------------------------------------------------------------

def test_toda_copia_de_texto_do_c_esta_no_inventario(ctx):
    """Cópia de texto traduzível que a varredura não mede sozinha (concatenação, destino ponteiro)
    precisa de uma entrada em DECLARED, medida ou isenta com o motivo."""
    pending = [f"{c.call.site} {c.call.func}: {c.call.text}" for c in bf.classify_calls(ctx) if c.status == "pendente"]
    assert pending == []


def test_toda_declaracao_casa_com_uma_chamada_e_resolve(ctx):
    classified = bf.classify_calls(ctx)
    problems = []
    for d in bf.DECLARED:
        if not any(d in c.declared for c in classified):
            problems.append(f"sem chamada: {d.file} {d.func} {d.src}")
        if not d.why:
            problems.append(f"sem motivo: {d.file} {d.func} {d.src}")
        if d.buffer is not None and bf._resolve_buffer(d.buffer, ctx) is None:
            problems.append(f"buffer não resolvido: {d.buffer}")
    for path in bf.c_paths(ctx, classified):
        if bf.measure_path(path, ctx) is None:
            problems.append(f"parte sem texto: {path.site} {path.what}")
    assert problems == []


def test_caminhos_de_script_cobrem_os_comandos_de_buffer(ctx):
    paths = bf.script_paths(ctx)
    cmds = {p.what.split()[0] for p in paths}
    assert {"bufferstdstring", "bufferitemname", "bufferitemnameplural", "buffermovename"} <= cmds
    assert all(bf.measure_path(p, ctx) for p in paths)


def test_repo_atual_sem_estouro_novo(ctx):
    assert _failures(ctx) == []


def test_estouro_conhecido_vira_aviso_e_some_quando_corrigido(ctx):
    """"Fruta Ocipêra" (13 letras) passa da linha de 27 bytes da bolsa de frutas (achado da T4 na
    hack-switch): fica em KNOWN_OVERFLOWS, como aviso, até a frente dona encurtar o nome."""
    wepear = ("src/data/items.json", "ITEM_WEPEAR_BERRY.name")
    found = _failures(ctx, "ITEM_WEPEAR_BERRY", known=[])
    assert found and "sListMenuStrbuf[27]" in found[0] and "28 bytes" in found[0]
    warnings = [r.detail for r in bf.check_buffers(REPO_ROOT, ctx=ctx) if r.status == "aviso"]
    assert any("ITEM_WEPEAR_BERRY" in w and "conhecido" in w for w in warnings)
    fixed = bf.with_texts(ctx, {wepear: "Fruta Wepear"})
    results = bf.check_buffers(REPO_ROOT, ctx=fixed)
    assert not [r for r in results if r.status == "falha"]
    assert any("não ocorre mais" in r.detail and "ITEM_WEPEAR_BERRY" in r.detail for r in results)


def test_fruta_na_bolsa_de_frutas_mede_so_os_nomes_de_fruta(ctx):
    """A lista da bolsa de frutas só tem frutas: um item comum de 13 letras não conta ali."""
    item = ("src/data/items.json", "ITEM_POTION.name")
    found = _failures(bf.with_texts(ctx, {item: "ABCDEFGHIJKLM"}), "sListMenuStrbuf")
    assert found == []


def test_check_text_roda_a_regra_de_buffer(monkeypatch):
    sentinel = ct.Result("texto/buffer", "falha", "sentinela")
    calls = []

    def fake(repo, entries, base, env):
        calls.append(base)
        return [sentinel]

    monkeypatch.setattr(bf, "check_buffers", fake)
    if shutil.which("git") is None or _scan().base is None:
        pytest.skip("sem git ou sem a base inglesa: a regra não roda")
    results = ct.check_text(str(REPO_ROOT), {"text": []}, english="desligado")
    assert sentinel in results and calls and calls[0] is not None
