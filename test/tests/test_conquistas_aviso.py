"""Conquistas e diário de batalhas (POK-44), Task 6: o aviso que pausa o jogo, a entrega do prêmio e a esteira.

O aviso nasce num ponto só do campo (`ProcessPlayerFieldInput`, logo depois de `TryRunOnFrameMapScript`), roda por um
script de campo (`EventScript_AvisoConquista`: lockall + special + waitstate) e entrega o prêmio na bolsa, senão no PC
de itens; sem espaço nos dois, o prêmio fica pendente e o aviso diz isso. Este arquivo lê o C, o script e os textos
como texto; o comportamento no emulador fica no cenário `conquistas` (grupos `aviso/*` e `premio/*`) e nos roteiros
rápidos, que dispensam os avisos que aparecem (`dispensar_avisos`).
"""

import json
import re

from PIL import Image

from esteira import check_text, hooks
from esteira.scenarios import REPO_ROOT

SRC = REPO_ROOT / "src"
AVISO_C = SRC / "conquistas_aviso.c"
CONQ_C = SRC / "conquistas.c"
CONQ_H = REPO_ROOT / "include" / "conquistas.h"
STRINGS_C = SRC / "strings.c"
SCRIPT = REPO_ROOT / "data" / "scripts" / "conquistas.inc"
SPECIALS = REPO_ROOT / "data" / "specials.inc"
EVENT_SCRIPTS = REPO_ROOT / "data" / "event_scripts.s"
EVENT_SCRIPTS_H = REPO_ROOT / "include" / "event_scripts.h"
JSON_PATH = SRC / "data" / "conquistas" / "conquistas.json"
ITEMS_JSON = SRC / "data" / "items.json"
GFX = REPO_ROOT / "graphics" / "conquistas"
ESTEIRA = REPO_ROOT / "test" / "esteira"
CENARIO = ESTEIRA / "scenarios" / "full_conquistas.py"
LARGURA_JANELA = 26 * 8   # janela de 26 tiles, texto em x = 0


def _ler(caminho) -> str:
    return caminho.read_text(encoding="utf-8")


def _corpo(fonte: str, nome: str) -> str:
    """Corpo da função C `nome` (da `{` da definição até a `}` na coluna 0)."""
    m = re.search(rf"^[\w *]+\b{nome}\([^;{{]*\)\n\{{\n(.*?)^\}}", fonte, re.S | re.M)
    assert m, f"função {nome} não encontrada"
    return m.group(1)


def _sem_comentarios(fonte: str) -> str:
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", fonte, flags=re.S)


# --- um ponto de chamada, as guardas e o script ----------------------------------------------------------------
def test_aviso_um_so_ponto_de_chamada():
    chamadas = []
    for arq in SRC.glob("*.c"):
        fonte = _sem_comentarios(_ler(arq))
        for m in re.finditer(r"\bConquistas_TentarAviso\s*\(\s*\)", fonte):
            linha = fonte[fonte.rfind("\n", 0, m.start()) + 1:fonte.find("\n", m.end())]
            if not re.match(r"^bool8 Conquistas_TentarAviso", linha):   # a definição
                chamadas.append(arq.name)
    assert chamadas == ["field_control_avatar.c"], chamadas
    corpo = _corpo(_ler(SRC / "field_control_avatar.c"), "ProcessPlayerFieldInput")
    frame = corpo.index("TryRunOnFrameMapScript() == TRUE")
    # no quadro em que o passo termina, o passo (gatilho de chão, warp, encontro, GAME_STAT_STEPS) vem antes do aviso
    aviso = corpo.index("if (!input->tookStep && Conquistas_TentarAviso() == TRUE)")
    assert frame < aviso, "o aviso tem de vir depois do script de quadro do mapa"
    entre = corpo[frame:aviso]
    assert entre.count("return TRUE;") == 1 and "if (" not in entre.replace("if (TryRunOnFrameMapScript", ""), (
        "o aviso vem logo depois de TryRunOnFrameMapScript")
    assert "return TRUE;" in corpo[aviso:aviso + 160]


def test_guardas_do_aviso():
    corpo = _corpo(_ler(AVISO_C), "Conquistas_TentarAviso")
    for guarda in ("gQuestLogState == QL_STATE_PLAYBACK", "InUnionRoom()", "gReceivedRemoteLinkPlayers",
                   "gPlayerAvatar.tileTransitionState == T_TILE_TRANSITION", "gConquistasSilencio",
                   "(gMain.vblankCounter2 & 31) == 0", "Conquistas_ChecarEstado()", "Conquistas_AvisosPendentes()",
                   "adiadoNoMapa", "ScriptContext_SetupScript(EventScript_AvisoConquista)"):
        assert guarda in corpo, guarda
    # as guardas vêm antes da checagem cadenciada e o silêncio só existe na ROM de teste
    assert corpo.index("T_TILE_TRANSITION") < corpo.index("Conquistas_ChecarEstado()")
    assert re.search(r"#if TESTBUILD\s*\n\s*if \(gConquistasSilencio\)", corpo)
    assert corpo.index("0xFFFF") > corpo.index("adiadoNoMapa"), "mapa diferente do adiado zera adiadoNoMapa"


def test_special_no_fim_e_script():
    specials = _ler(SPECIALS)
    # no fim, depois de todos os da base; a Task 7 acrescentou o da tela logo depois e o POK-42 o da Liga
    nomes = [n for n in re.findall(r"def_special (\w+)", specials.split("gSpecialsEnd::")[0])
             if not n.startswith(("FamiliaSombra_", "MestreGolpes_", "GetKrabby", "CompareKrabby", "SalaTrofeus_"))]  # POK-51 vem depois
    finais = nomes[nomes.index("Conquistas_MostrarAviso"):]
    assert finais == ["Conquistas_MostrarAviso", "Conquistas_AbrirTelaDoScript", "ShouldUseLeagueRematchTeams",
                      "BufferRematchTierName", "ShowRematchTierMenu"], finais
    script = _ler(SCRIPT)
    m = re.search(r"^EventScript_AvisoConquista::\n(.*?)\n\n", script + "\n\n", re.S | re.M)
    assert m, "EventScript_AvisoConquista não encontrado"
    comandos = [linha.strip() for linha in m.group(1).splitlines() if linha.strip()]
    # sem task livre o special devolve FALSE e o script não espera (senão o waitstate travaria); com a janela, o
    # waitfanfare depois do waitstate (como no Std_ObtainItem): o aviso fecha com a fanfarra ainda tocando, e um
    # menu ou uma porta nesse meio (ResetTasks) mataria o Task_Fanfare com a música do mapa pausada
    assert comandos == ["goto_if_questlog EventScript_ReleaseEnd", "lockall",
                        "specialvar VAR_RESULT, Conquistas_MostrarAviso",
                        "goto_if_eq VAR_RESULT, FALSE, EventScript_AvisoConquistaSemTask",
                        "waitstate", "waitfanfare", "releaseall", "end"], comandos
    assert comandos.index("waitfanfare") == comandos.index("waitstate") + 1
    corpo = _corpo(_ler(AVISO_C), "Conquistas_MostrarAviso")
    assert corpo.index("TASK_NONE") < corpo.index("AllocZeroed"), "confere a task antes de alocar e entregar"
    assert '.include "data/scripts/conquistas.inc"' in _ler(EVENT_SCRIPTS)
    assert "extern const u8 EventScript_AvisoConquista[];" in _ler(EVENT_SCRIPTS_H)


def test_interface():
    h = _ler(CONQ_H)
    for proto in ("bool8 Conquistas_TentarAviso(void);", "bool8 Conquistas_MostrarAviso(void);",
                  "extern u8 gConquistasAvisoAtivo;"):
        assert proto in h, proto
    # o comentário do Diario_ListarEmOrdem voltou para a linha dele
    listar = next(linha for linha in h.splitlines() if "Diario_ListarEmOrdem" in linha)
    treinador = next(linha for linha in h.splitlines() if "Diario_TreinadorDoEvento" in linha)
    assert "em ordem crescente" in listar and "em ordem crescente" not in treinador, (listar, treinador)


def test_ewram_so_o_byte_do_aviso_e_o_silencio():
    fonte = _ler(AVISO_C)
    ewram = re.findall(r"EWRAM_DATA\s+[\w ]+?\b(\w+)\s*(?:=|;|\[)", fonte)
    assert sorted(ewram) == ["gConquistasAvisoAtivo", "gConquistasSilencio"], ewram
    silencio = fonte.index("gConquistasSilencio")
    assert fonte.rfind("#if TESTBUILD", 0, silencio) > fonte.rfind("#endif", 0, silencio), "silêncio fora do TESTBUILD"
    for arq in SRC.glob("*.c"):
        if arq.name in ("conquistas_aviso.c", "test_hooks.c"):
            continue
        assert "gConquistasSilencio" not in _ler(arq), arq.name


def test_janela_animacao_e_fanfarra():
    fonte = _ler(AVISO_C)
    template = re.search(r"sAvisoWindowTemplate\s*=\s*\{(.*?)\};", fonte, re.S).group(1)
    campos = dict(re.findall(r"\.(\w+)\s*=\s*(\w+)", template))
    assert (campos["width"], campos["height"], campos["baseBlock"], campos["bg"]) == ("26", "4", "0x198", "0"), campos
    assert "DrawStdWindowFrame(" in fonte and "ClearStdWindowAndFrameToTransparent(" in fonte
    assert "PlayFanfare(MUS_OBTAIN_ITEM)" in fonte
    assert re.search(r"#define AVISO_MIN_QUADROS\s+30\b", fonte) and re.search(r"#define AVISO_MAX_QUADROS\s+180\b", fonte)
    # o offset do BG0 que a animação mexe volta a 0 e a janela sai do BG0 ao fechar
    assert "ChangeBgY(0, 0, BG_COORD_SET)" in fonte and "RemoveWindow(" in fonte
    assert "ScriptContext_Enable()" in fonte and "gConquistasAvisoAtivo = 0" in fonte
    assert "IsMapNamePopupTaskActive()" in fonte, "o popup do nome do mapa também mexe no BG0VOFS"


def test_entrega_bolsa_pc_ou_pendente():
    corpo = _corpo(_ler(CONQ_C), "Conquistas_EntregarPremio")
    bolsa, pc = corpo.index("AddBagItem("), corpo.index("AddPCItem(")
    assert bolsa < pc
    assert corpo.index("Conquistas_SetEntregue(") > pc and corpo.index("Conquistas_SetDegrauEntregue(") > pc, (
        "só marca entregue depois de entregar")


def test_icone_solto_por_tag():
    """O AddItemIconObject monta o SpriteTemplate na pilha: o ícone é solto pela tag, nunca pelo sprite->template."""
    fonte = _ler(AVISO_C)
    corpo = _corpo(fonte, "EsconderSprites")
    assert "DestroySpriteAndFreeResources" not in _sem_comentarios(fonte)
    for chamada in ("FreeSpriteTilesByTag(TAG_AVISO_ICONE)", "FreeSpritePaletteByTag(TAG_AVISO_ICONE)",
                    "FreeSpriteTilesByTag(TAG_AVISO_ESTRELA)", "FreeSpritePaletteByTag(TAG_AVISO_ESTRELA)"):
        assert chamada in corpo, chamada


def test_fila_nao_trava_no_que_nao_cabe():
    corpo = _corpo(_ler(AVISO_C), "Conquistas_MostrarAviso")
    assert corpo.index("Conquistas_ProximoQueCabe(") < corpo.index("Conquistas_ProximoPendente(")


def test_checagem_cadenciada_sem_decifrar_os_ovos():
    fonte = _ler(CONQ_C)
    checar = _corpo(fonte, "Conquistas_ChecarEstado")
    assert re.search(r"LerTime\(&time, .*FALSE\)", checar), "a checagem cadenciada pede a leitura sem os ovos"
    varrer = _corpo(fonte, "VarrerTimeEPC")
    assert "TRUE" in varrer


# --- textos e larguras --------------------------------------------------------------------------------------------
def _textos() -> dict[str, str]:
    fonte = _ler(STRINGS_C)
    return {m.group(1): "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2)))
            for m in re.finditer(r"const u8 (gText_ConqAviso_\w+)\[\]\s*=\s*_\((.*?)\);", fonte, re.S)}


def _medir(texto: str) -> int:
    env = check_text._load_env(REPO_ROOT)
    return check_text.measure(texto + "$", env).widest


def test_textos_do_aviso_existem_e_tem_regra():
    t = _textos()
    for nome in ("Titulo", "Premio", "NaBolsa", "NoPc", "Cheios", "ResumoAntes", "ResumoUma", "ResumoVarias",
                 "Premios", "Separador", "Depois"):
        assert f"gText_ConqAviso_{nome}" in t, nome
    regra = check_text.rule_for("src/strings.c", "gText_ConqAviso_Titulo")
    assert regra is not None and regra.px == LARGURA_JANELA and regra.lines == 1, regra
    h = _ler(REPO_ROOT / "include" / "strings.h")
    for nome in t:
        assert f"extern const u8 {nome}[];" in h, nome


# O plural de cada prêmio da tabela que sai com 2 ou mais, conferido um a um (src/conquistas_aviso.c, NomeDoPremio).
PLURAIS = {
    "ITEM_POKE_BALL": "Poké Bolas",
    "ITEM_GREAT_BALL": "Grandes Bolas",
    "ITEM_ULTRA_BALL": "Ultra Bolas",
    "ITEM_SUPER_POTION": "Superpoções",
    "ITEM_HYPER_POTION": "Hiperpoções",
    "ITEM_MAX_REPEL": "Repel. Máximos",
    "ITEM_PP_MAX": "PP Máximos",
    "ITEM_RARE_CANDY": "Doces Raros",
}
# abreviados: o mesmo no singular e no plural ("3 Reviver Máx.", "3 Superrepel.")
INVARIAVEIS = {"ITEM_MAX_REVIVE", "ITEM_SUPER_REPEL"}


def _tabela_de_plurais() -> dict[str, str]:
    """sPluraisDoPremio do C, com o texto de cada rótulo (strings.c): item -> plural."""
    fonte = _ler(AVISO_C)
    corpo = re.search(r"sPluraisDoPremio\[\]\s*=\s*\{(.*?)\n\};", fonte, re.S).group(1)
    t = _textos()
    return {item: t[rotulo] for item, rotulo in re.findall(r"\{\s*(ITEM_\w+),\s*(gText_ConqAviso_Plural\w+)\s*\}", corpo)}


def _nome_do_premio(p: dict, itens: dict[str, str], t: dict[str, str]) -> str:
    """O nome que o aviso mostra: o plural da tabela com 2 ou mais, senão o nome do item (como NomeDoPremio)."""
    if p["qtd"] >= 2:
        return _tabela_de_plurais().get(p["item"], itens[p["item"]])
    return itens[p["item"]]


def test_plural_do_premio():
    """Todo prêmio com 2 ou mais sai no plural ("5 Poké Bolas", "3 Superpoções"); os abreviados ficam iguais.
    A tabela do C é exatamente a conferida aqui, sem sobra."""
    fonte = _ler(AVISO_C)
    corpo = _corpo(fonte, "NomeDoPremio")
    assert "qtd >= 2" in corpo and "ItemId_GetName(item)" in corpo
    assert "NomeDoPremio(p->item, p->qtd)" in _corpo(fonte, "MontarConquista")
    tabela = _tabela_de_plurais()
    assert tabela == PLURAIS, tabela
    itens = {i["itemId"]: i["english"] for i in json.loads(_ler(ITEMS_JSON))["items"]}
    vistos = {}
    for c in json.loads(_ler(JSON_PATH))["conquistas"]:
        for p in c["premios"]:
            if p["qtd"] >= 2:
                assert p["item"] in PLURAIS or p["item"] in INVARIAVEIS, f"{c['id']}: {p['item']} sem plural conferido"
                vistos[p["item"]] = _nome_do_premio(p, itens, _textos())
    assert set(vistos) == set(PLURAIS) | INVARIAVEIS, sorted(vistos)   # nenhuma entrada morta na tabela
    for item in INVARIAVEIS:
        assert vistos[item] == itens[item] and itens[item].endswith("."), (item, vistos[item])
    assert vistos["ITEM_POKE_BALL"] == "Poké Bolas" and vistos["ITEM_SUPER_POTION"] == "Superpoções"
    # o plural fica no texto do aviso (linha2[64]): o maior prêmio montado cabe no buffer
    assert max(len(n) for n in PLURAIS.values()) <= 14


def test_larguras_montadas():
    """Cada linha que o aviso monta cabe nos 208 px: título + nome (com cada degrau), prêmio + destino de cada prêmio
    e as linhas do resumo com 2 algarismos."""
    t = _textos()
    itens = {i["itemId"]: i["english"] for i in json.loads(_ler(ITEMS_JSON))["items"]}
    dados = json.loads(_ler(JSON_PATH))
    largas = []
    for c in dados["conquistas"]:
        for valor in c.get("degraus") or [None]:
            nome = c["nome"].replace("{N}", str(valor))
            largas.append(t["gText_ConqAviso_Titulo"] + nome)
        for p in c["premios"]:
            for destino in ("NaBolsa", "NoPc"):
                largas.append(f"{t['gText_ConqAviso_Premio']}{p['qtd']} {_nome_do_premio(p, itens, t)}"
                              f"{t[f'gText_ConqAviso_{destino}']}")
    largas.append(t["gText_ConqAviso_Cheios"])
    largas.append(t["gText_ConqAviso_ResumoAntes"] + "99" + t["gText_ConqAviso_ResumoVarias"])
    largas.append(t["gText_ConqAviso_ResumoAntes"] + "1" + t["gText_ConqAviso_ResumoUma"])
    sep = t["gText_ConqAviso_Separador"]
    largas.append(t["gText_ConqAviso_Premios"] + "99" + t["gText_ConqAviso_NaBolsa"] + sep + "99"
                  + t["gText_ConqAviso_NoPc"])
    # com prêmio pendente a linha perde o "Prêmios: " (src/conquistas_aviso.c, MontarResumo)
    largas.append("99" + t["gText_ConqAviso_NaBolsa"] + sep + "99" + t["gText_ConqAviso_NoPc"] + sep + "99"
                  + t["gText_ConqAviso_Depois"])
    medidas = {texto: _medir(texto) for texto in largas}
    grandes = {k: v for k, v in medidas.items() if v > LARGURA_JANELA}
    assert not grandes, grandes


# --- gráfico ---------------------------------------------------------------------------------------------------
def test_grafico_do_aviso():
    png = Image.open(GFX / "aviso.png")
    assert png.mode == "P" and png.size == (16, 32), (png.mode, png.size)
    assert max(png.tobytes()) < 16
    pal = (GFX / "aviso.pal").read_bytes()
    assert pal.startswith(b"JASC-PAL\r\n0100\r\n16\r\n") and pal.count(b"\r\n") == 19, pal[:40]
    assert 'INCBIN_U32("graphics/conquistas/aviso.4bpp")' in _ler(AVISO_C)
    assert 'INCBIN_U16("graphics/conquistas/aviso.gbapal")' in _ler(AVISO_C)


# --- atalhos e esteira -------------------------------------------------------------------------------------------
def test_atalhos():
    assert hooks.CMD_CONQ_SILENCIO == 0xBC and hooks.CMD_ENCHER_BOLSO == 0xBD
    assert callable(hooks.Mailbox.conq_silencio) and callable(hooks.Mailbox.encher_bolso)
    corpo = _ler(SRC / "test_hooks.c")
    assert "case TEST_CMD_CONQ_SILENCIO:" in corpo and "case TEST_CMD_ENCHER_BOLSO:" in corpo


def test_esteira_convive_com_o_aviso():
    base = _ler(ESTEIRA / "scenarios" / "base.py")
    assert "def dispensar_avisos(ctx" in base and "gConquistasAvisoAtivo" in base
    assert "conq_silencio(True)" in base
    # as sessões da ROM de teste ficam em silêncio; os roteiros da jogável dispensam o aviso
    main = _ler(ESTEIRA / "__main__.py")
    assert main.count("conq_silencio = ") >= 2, "sessões de teste (inline/paralelo e assistir)"
    for arq, onde in (("quick_opening.py", "_rival_battle"), ("quick_catch_save.py", "_catch"),
                      ("travel.py", "_after_battle"), ("full_forest_brock.py", "_challenge_brock")):
        fonte = _ler(ESTEIRA / "scenarios" / arq)
        m = re.search(rf"def {onde}\(.*?(?=\n    def |\Z)", fonte, re.S)
        assert m and "dispensar_avisos(" in m.group(0), (arq, onde)
    cenario = _ler(CENARIO)
    assert "conq_silencio(False)" in cenario
    for grupo in ("aviso/aparece_e_entrega", "aviso/fanfarra_devolve_bgm", "aviso/espera_fim_da_batalha", "aviso/fila", "aviso/degrau",
                  "premio/bolsa_cheia_vai_ao_pc", "premio/tudo_cheio_fica_pendente", "premio/fila_nao_trava",
                  "aviso/passo_antes", "aviso/resumo_retro"):
        assert f'"{grupo}"' in cenario, grupo
    # o grupo da derrota desliga o Hall da Fama antes: a asserção do slot do rival separa as duas guardas
    corpo = re.search(r"def _derrota_nao_conta\(.*?(?=\n    def )", cenario, re.S).group(0)
    assert corpo.index('_flag("FLAG_SYS_GAME_CLEAR", False)') < corpo.index("start_trainer_battle")
