"""Tela de novidades do Prof. Carvalho, Task 1: os cartões, o gerador e a medida dos textos (sem emulador).

Os tópicos e cartões moram num JSON único (`src/data/novidades/cartoes.json`); o make o converte em
`src/data/novidades_cartoes.h` (só `const`) com `tools/novidades/gen_cartoes.py`, no padrão do
`tools/wild_leafgreen/gen_swaps.py`. As larguras/linhas das janelas do cartão são constantes de
`include/novidades.h` (a Task 3 desenha as janelas com elas); a checagem de texto da esteira
(`esteira.check_text`) lê essas mesmas constantes e mede cada texto do JSON na janela dele.
"""

import importlib.util
import json
import re
import subprocess
import sys

import pytest

from esteira import check_text as ct
from esteira.scenarios import REPO_ROOT

JSON_REL = "src/data/novidades/cartoes.json"
JSON_PATH = REPO_ROOT / JSON_REL
HEADER_H = REPO_ROOT / "include" / "novidades.h"
GEN_SCRIPT = REPO_ROOT / "tools" / "novidades" / "gen_cartoes.py"
RULES_MK = REPO_ROOT / "json_data_rules.mk"
GITIGNORE = REPO_ROOT / ".gitignore"
GENERATED_REL = "src/data/novidades_cartoes.h"

TOPICOS_DO_SPEC = ["Ritmo de jogo", "Shiny", "Evoluções", "Resumo do Pokémon", "Creche", "Dia e noite",
                   "Clima", "Pokédex e captura", "Lendários", "Pós-Liga", "Melhorias modernas", "Sobre a hack"]
CAMPOS_DE_TEXTO = ("title", "before", "after", "body")


def _dados() -> dict:
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def _topicos() -> list[dict]:
    return _dados()["topics"]


def _topico(nome: str) -> dict:
    return next(t for t in _topicos() if t["name"] == nome)


def _constantes() -> dict[str, int]:
    """`#define NOVIDADES_X <número>` de include/novidades.h."""
    text = HEADER_H.read_text(encoding="utf-8")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define NOVIDADES_(\w+)\s+(\d+)\b", text, re.M)}


def _gen_module():
    spec = importlib.util.spec_from_file_location("gen_cartoes", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plano(texto: str) -> str:
    """Texto do cartão numa linha só (quebras viram espaço), para procurar frases."""
    return re.sub(r"\s+", " ", texto)


def _cartoes():
    for t in _topicos():
        for i, c in enumerate(t["cards"], 1):
            yield t, i, c


# --- tópicos e cartões ------------------------------------------------------------------------

def test_doze_topicos_na_ordem_do_spec():
    assert [t["name"] for t in _topicos()] == TOPICOS_DO_SPEC
    assert _constantes()["TOPIC_COUNT"] == 12 == len(_topicos())


def test_conquistas_e_diario_no_fim_de_melhorias_modernas():
    """POK-44: a grade 4x3 já está cheia (12 tópicos); os dois cartões entram no fim de "Melhorias modernas",
    como os do POK-43/45, e citam o caminho (SELECT no cartão do menu START; SELECT de novo para o diário)."""
    cartoes = _topico("Melhorias modernas")["cards"]
    assert [c["title"] for c in cartoes[-6:-4]] == ["Conquistas e prêmios", "Diário da jornada"]   # POK-42/46/47/48 depois
    conquistas, diario = (_plano(c["body"]) for c in cartoes[-6:-4])
    ativas = sum(1 for c in json.loads((REPO_ROOT / "src/data/conquistas/conquistas.json").read_text(encoding="utf-8"))
                 ["conquistas"] if c.get("ativa", True))
    assert "cartão" in conquistas and "SELECT" in conquistas and f"{ativas} conquistas" in conquistas
    assert "SELECT" in diario and "MVP" in diario


def test_revanches_por_degrau_no_fim_de_melhorias_modernas():
    """POK-42: como os do POK-43/45 e do POK-44, o cartão entra no fim de "Melhorias modernas" (grade cheia) e cita a
    guarda da Liga, os níveis de Normal a 100 e o que vale para o Explorador VS."""
    cartao = _topico("Melhorias modernas")["cards"][-4]   # POK-46, 47 e 48 depois
    assert cartao["title"] == "Revanches por degrau" and cartao["itemId"] == "ITEM_VS_SEEKER"
    corpo = _plano(cartao["body"])
    for trecho in ("Hall da Fama", "guarda da Liga", "Normal", "Nível 100", "Elite 4", "Explorador VS", "times de 6",
                   "IVs altos"):
        assert trecho in corpo, trecho


def test_chefes_mais_espertos_no_fim_de_melhorias_modernas():
    """POK-46: o cartão entra no fim de "Melhorias modernas" (grade cheia) e diz quem são os chefes (as revanches só do
    Nível 80 para cima) e o que mudou: troca antes do golpe super efetivo, quem entra e as curas."""
    cartao = _topico("Melhorias modernas")["cards"][-3]   # POK-47 e 48 depois
    assert cartao["title"] == "Chefes mais espertos" and cartao["itemId"] == "ITEM_FULL_RESTORE"
    corpo = _plano(cartao["body"])
    for trecho in ("Líderes", "Elite 4", "rival", "Nível 80", "golpe super efetivo", "quem entra", "poções e curas"):
        assert trecho in corpo, trecho


def test_dexnav_no_fim_de_melhorias_modernas():
    """POK-47: o cartão entra no fim de "Melhorias modernas" (grade cheia), com o ícone do item novo, e diz como abrir
    (menu START ou SELECT) e o que a tela tem, com os nomes do rodapé da tela ("SELECT mapas", "START busca")."""
    cartao = _topico("Melhorias modernas")["cards"][-2]   # POK-48 depois
    assert cartao["title"] == "DexNav" and cartao["itemId"] == "ITEM_DEXNAV"
    corpo = _plano(cartao["body"])
    for trecho in ("menu START", "SELECT, registrando o item", "jeito de encontrar", "chance real", "níveis",
                   "falta capturar", "SELECT mapas", "START busca", "Pokémon visto"):
        assert trecho in corpo, trecho
    rodape = (REPO_ROOT / "src/strings.c").read_text(encoding="utf-8")
    assert '_("SELECT mapas")' in rodape and '_("START busca")' in rodape


def test_seguidor_no_fim_de_melhorias_modernas():
    """POK-48/53: o cartão entra no fim de "Melhorias modernas" (grade cheia), com um dos seguidores na imagem, diz
    quem segue (os 386, com os grandes, as letras do Unown e as fêmeas), quando some e onde desligar (a linha Seguidor
    das OPÇÕES)."""
    cartao = _topico("Melhorias modernas")["cards"][-1]
    assert cartao["title"] == "Pokémon seguidor" and cartao["speciesBefore"] == "SPECIES_PIKACHU"
    corpo = _plano(cartao["body"])
    for trecho in ("1º da equipe", "todos os 386", "grandes como Wailord e Lugia", "letra do Unown", "fêmeas",
                   "bicicleta", "Surf", "OPÇÕES", "Seguidor"):
        assert trecho in corpo, trecho
    strings = (REPO_ROOT / "src/strings.c").read_text(encoding="utf-8")
    assert '_("Seguidor")' in strings


def test_cada_topico_tem_cartao():
    for t in _topicos():
        assert t["cards"], f"tópico sem cartão: {t['name']}"
        for i, c in enumerate(t["cards"], 1):
            assert c.get("title") and c.get("body"), f"{t['name']} #{i}: cartão sem título ou texto"


def test_ids_dos_topicos_sao_identificadores_unicos():
    ids = [t["id"] for t in _topicos()]
    assert all(re.fullmatch(r"[a-z][a-z0-9_]*", i) for i in ids)
    assert len(set(ids)) == len(ids)


def test_miticos_revelacao_logo_depois_das_pistas():
    cartoes = _topico("Lendários")["cards"]
    pistas = [i for i, c in enumerate(cartoes) if "pistas" in c["title"].lower()]
    assert len(pistas) == 1
    i = pistas[0]
    assert "Quer saber onde estão? Veja o próximo cartão." in _plano(cartoes[i]["body"])
    assert i + 1 < len(cartoes), "o cartão das pistas é o último: falta a revelação"
    revelacao = _plano(cartoes[i + 1]["body"])
    for lugar in ("Mansão Pokémon", "Bosque das Frutas", "Tanoby"):
        assert lugar in revelacao, f"a revelação não cita {lugar}"
    # nada de spoiler no cartão das pistas
    assert not any(lugar in _plano(cartoes[i]["body"]) for lugar in ("Mansão", "Bosque", "Tanoby"))


def test_revelacao_traz_as_condicoes_dos_tres_miticos():
    cartoes = _topico("Lendários")["cards"]
    i = next(i for i, c in enumerate(cartoes) if "pistas" in c["title"].lower())
    texto = _plano(cartoes[i + 1]["body"])
    for termo in ("Mew", "Mewtwo", "Celebi", "manhã", "Ilhas Sevii", "Jirachi", "noite", "céu limpo", "Deoxys"):
        assert termo in texto, termo


def test_amuleto_cita_151():
    amuleto = [c for c in _topico("Shiny")["cards"] if "Amuleto Brilhante" in c["title"]]
    assert len(amuleto) == 1
    assert "151" in amuleto[0]["body"]
    assert "Prof. Carvalho" in _plano(amuleto[0]["body"])
    assert "151" in _plano(_topico("Pós-Liga")["cards"][0]["body"])


def test_feebas_pescavel_e_escama_prisma():
    cartao = next(c for c in _topico("Evoluções")["cards"] if "Feebas" in c["title"] or "Prisma" in c["title"])
    texto = _plano(cartao["body"])
    for termo in ("Feebas", "Milotic", "Escama Prisma", "Supervara", "Ilha Quatro"):
        assert termo in texto, termo
    assert cartao["speciesBefore"] == "SPECIES_FEEBAS" and cartao["speciesAfter"] == "SPECIES_MILOTIC"


def test_pedra_solar_e_itens_de_celadon():
    cartoes = [_plano(c["body"]) for c in _topico("Evoluções")["cards"]]
    solar = next(t for t in cartoes if "Pedra Solar" in t)
    assert "¥5.000" in solar and "Celadon" in solar and "4º andar" in solar
    itens = next(t for t in cartoes if "Dente Abissal" in t and "Melhora" in t and "Celadon" in t)
    for item in ("Pedra do Rei", "Revestimento Metálico", "Escama de Dragão", "Escama Abissal"):
        assert item in itens, item


def test_evolucoes_por_troca_um_cartao_por_caso():
    titulos = " | ".join(c["title"] for c in _topico("Evoluções")["cards"])
    for nome in ("Kadabra", "Machoke", "Graveler", "Haunter", "Onix", "Scyther", "Seadra", "Porygon",
                 "Clamperl", "Slowpoke", "Poliwhirl", "Celadon", "Espeon", "Prisma"):
        assert nome in titulos, nome
    por_troca = {c["speciesBefore"]: c for c in _topico("Evoluções")["cards"] if c.get("before")}
    assert por_troca["SPECIES_KADABRA"]["before"] == "ANTES: troca"
    assert por_troca["SPECIES_KADABRA"]["after"] == "AGORA: Nv. 37"
    # o cartão que o Review Focus 2 cita: duas espécies grandes lado a lado
    onix = por_troca["SPECIES_ONIX"]
    assert onix["speciesAfter"] == "SPECIES_STEELIX"
    assert "Revestimento Metálico" in _plano(onix["body"]) and "não é gasto" in _plano(onix["body"])


def test_fatos_dos_hacks_pos_liga_lendarios_e_dex():
    todos = {t["name"]: " ".join(_plano(c["body"]) for c in t["cards"]) for t in _topicos()}
    pos = todos["Pós-Liga"]
    assert all(e in pos for e in ("Ovo raro", "a cada vitória na Liga", "até os 3", "Larvitar", "Bagon", "Beldum", "¥45.000"))
    lend = todos["Lendários"]
    assert "Entei" in lend and "Raikou" in lend and "Suicune" in lend
    assert "capturar ou derrotar" in lend and "próxima entrada no Hall da Fama" in lend
    assert "primeira vez" in lend and "Bilhete" in lend
    dex = todos["Pokédex e captura"]
    assert "LeafGreen" in dex and "FireRed" in dex
    assert all(e in dex for e in ("Zona de Safári", "Bulbasaur", "Charmander", "Squirtle", "Leste", "Norte",
                                  "Oeste", "surfando", "Caverna Mutante", "a cada dia", "Monte Lua", "Fóssil Domo",
                                  "Fóssil Hélice"))


def test_hack7_clima_relogio_creche_e_resumo():
    todos = {t["name"]: " ".join(_plano(c["body"]) for c in t["cards"]) for t in _topicos()}
    assert all(e in todos["Dia e noite"] for e in ("Manhã", "tarde", "entardecer", "noite", "Hoothoot", "START"))
    assert all(e in todos["Clima"] for e in ("chuva", "neve", "areia", "cinzas", "granizo"))
    assert all(e in todos["Creche"] for e in ("IVs", "natureza", "Pedra Eterna", "Nó do Destino", "Poder"))
    assert all(e in todos["Resumo do Pokémon"] for e in ("EVOLUÇÃO", "corações", "255", "220", "IV", "EVs", "Poder Oculto"))
    assert "IVs/EVs" in " ".join(c["title"] for c in _topico("Resumo do Pokémon")["cards"])
    assert "1 em 8.192" in " ".join(c.get("before", "") for c in _topico("Shiny")["cards"])
    assert "1 em 4.096" in " ".join(c.get("after", "") for c in _topico("Shiny")["cards"])


def test_imagens_dos_cartoes_sao_coerentes():
    especies = (REPO_ROOT / "include" / "constants" / "species.h").read_text(encoding="utf-8")
    itens = (REPO_ROOT / "include" / "constants" / "items.h").read_text(encoding="utf-8")
    for t in _topicos():
        assert re.search(rf"^#define {t['iconItemId']}\s", itens, re.M), f"{t['name']}: {t['iconItemId']}"
        assert t.get("iconCustom", 0) in (0, 1, 2, 3, 4)
    for t, i, c in _cartoes():
        onde = f"{t['name']} #{i}"
        assert bool(c.get("before")) == bool(c.get("after")), f"{onde}: ANTES e AGORA vêm juntos"
        if c.get("speciesAfter"):
            assert c.get("speciesBefore"), f"{onde}: espécie 'depois' sem 'antes'"
        if c.get("itemId"):
            assert not c.get("speciesBefore"), f"{onde}: imagem é item OU espécie"
            assert re.search(rf"^#define {c['itemId']}\s", itens, re.M), f"{onde}: {c['itemId']}"
        for campo in ("speciesBefore", "speciesAfter"):
            if c.get(campo):
                assert re.search(rf"^#define {c[campo]}\s", especies, re.M), f"{onde}: {c[campo]}"


def test_textos_sem_marca_de_genero_do_jogador():
    padrao = re.compile(r"\b(obrigad[oa]|bem-vind[oa]|sozinh[oa]|pronto|preparad[oa]|treinador|campe[ãa]o)\b", re.I)
    for t, i, c in _cartoes():
        for campo in CAMPOS_DE_TEXTO:
            achado = padrao.search(_plano(c.get(campo, "")))
            assert not achado, f"{t['name']} #{i} {campo}: '{achado.group(0)}' marca gênero"


def test_quebras_de_linha_nao_partem_termos():
    termos = ("Prof. Carvalho", "Amuleto Brilhante", "Escama Prisma", "Escama Abissal", "Escama de Dragão",
              "Dente Abissal", "Revestimento Metálico", "Pedra do Rei", "Pedra Solar", "Pedra Eterna",
              "Nó do Destino", "Zona de Safári", "Hall da Fama", "Liga Pokémon", "Ilha Quatro", "Ilhas Sevii",
              "Mansão Pokémon", "Bosque das Frutas", "Ruínas de Tanoby", "Caverna Mutante", "Loja de Celadon",
              "Pokédex Nacional", "Poder Oculto", "Ovo raro", "Nv. 37", "Monte Lua", "Fóssil Domo",
              "Fóssil Hélice", "laboratório da Ilha Cinnabar")
    for t, i, c in _cartoes():
        for campo in CAMPOS_DE_TEXTO:
            texto = c.get(campo, "")
            for termo in termos:
                if termo in _plano(texto):
                    assert termo in texto, f"{t['name']} #{i} {campo}: quebra no meio de '{termo}'"


def test_termo_criado_esta_no_glossario():
    glossario = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    termo = next(x for x in glossario["termos"] if x["pt"] == "Escama Abissal")
    assert termo["fonte"] == "criado" and termo["categoria"] == "item"


# --- o header gerado --------------------------------------------------------------------------

def test_header_gerado_bate_com_json():
    texto = _gen_module().render(JSON_PATH)
    dados = _topicos()
    # cada texto do JSON vira um _("...") com as quebras como \n literal
    esperados = []
    for t in dados:
        esperados.append(t["name"])
        for c in t["cards"]:
            esperados += [c[k] for k in CAMPOS_DE_TEXTO if c.get(k)]
    gerados = re.findall(r'^static const u8 sNovidadesText_\w+\[\] = _\("(.*)"\);$', texto, re.M)
    assert gerados == [e.replace("\n", "\\n") for e in esperados]
    # a ordem e a contagem dos tópicos e dos cartões
    for t in dados:
        bloco = re.search(rf"static const struct NovidadesCard sNovidadesCards_{t['id']}\[\] =\n\{{\n(.*?)\n\}};",
                          texto, re.S)
        assert bloco, t["id"]
        assert len(re.findall(r"^    \{$", bloco.group(1), re.M)) == len(t["cards"])
    assert re.findall(r"\.cards = (sNovidadesCards_\w+),", texto) == [f"sNovidadesCards_{t['id']}" for t in dados]
    assert texto.count("const struct NovidadesTopic gNovidadesTopics[] =") == 1
    assert "ARRAY_COUNT(gNovidadesTopics) == NOVIDADES_TOPIC_COUNT" in texto
    # campos vazios ficam de fora (NULL/0 por padrão); espécies e itens como constantes
    assert ".before = NULL" not in texto and ".speciesBefore = 0" not in texto
    onix = re.search(r"\.speciesBefore = SPECIES_ONIX,\n\s+\.speciesAfter = SPECIES_STEELIX,", texto)
    assert onix
    assert len(re.findall(r"\.speciesBefore = SPECIES_", texto)) == sum(1 for _, _, c in _cartoes() if c.get("speciesBefore"))
    assert len(re.findall(r"\.itemId = ITEM_", texto)) == sum(1 for _, _, c in _cartoes() if c.get("itemId"))
    assert re.findall(r"\.iconItemId = (ITEM_\w+),", texto) == [t["iconItemId"] for t in dados]
    assert re.findall(r"\.iconCustom = (\d),", texto) == [str(t.get("iconCustom", 0)) for t in dados]


def test_header_gerado_e_so_const_sem_ewram():
    texto = _gen_module().render(JSON_PATH)
    assert "EWRAM_DATA" not in texto
    assert not re.search(r"^(?!static const|const|STATIC_ASSERT|//|\s|\{|\}|$|#)", texto, re.M)
    assert "DO NOT MODIFY" in texto and "tools/novidades/gen_cartoes.py" in texto


def test_cli_gera_o_mesmo_header(tmp_path):
    saida = tmp_path / "novidades_cartoes.h"
    subprocess.run([sys.executable, "-I", str(GEN_SCRIPT), str(JSON_PATH), str(saida)], check=True)
    assert saida.read_text(encoding="utf-8") == _gen_module().render(JSON_PATH)


def test_gerador_recusa_json_malformado(tmp_path):
    ruim = tmp_path / "ruim.json"
    base = _dados()
    base["topics"][0]["cards"][0]["body"] = 'aspas " e barra \\ soltas'
    ruim.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError):
        _gen_module().render(ruim)
    base = _dados()
    base["topics"][0]["cards"][0]["speciesAfter"] = "SPECIES_ONIX"   # 'depois' sem 'antes'
    base["topics"][0]["cards"][0].pop("speciesBefore", None)
    ruim.write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(ValueError):
        _gen_module().render(ruim)


def test_header_do_c_declara_as_estruturas_do_plano():
    h = HEADER_H.read_text(encoding="utf-8")
    card = re.sub(r"//.*", "", re.search(r"struct NovidadesCard\s*\{(.*?)\};", h, re.S).group(1))
    assert [re.sub(r"\s+", " ", f.strip()) for f in card.split(";") if f.strip()] == [
        "const u8 *title", "const u8 *before", "const u8 *after", "const u8 *body",
        "u16 speciesBefore", "u16 speciesAfter", "u16 itemId"]
    topic = re.sub(r"//.*", "", re.search(r"struct NovidadesTopic\s*\{(.*?)\};", h, re.S).group(1))
    assert [re.sub(r"\s+", " ", f.strip()) for f in topic.split(";") if f.strip()] == [
        "const u8 *name", "u16 iconItemId", "u8 iconCustom", "const struct NovidadesCard *cards", "u8 cardCount"]
    assert "extern const struct NovidadesTopic gNovidadesTopics[];" in h
    assert "EWRAM_DATA" not in h


def test_constantes_de_janela_no_header():
    c = _constantes()
    for nome in ("TITLE_WIDTH_PX", "BEFORE_AFTER_WIDTH_PX", "BODY_WIDTH_PX", "BODY_LINES", "TOPIC_NAME_WIDTH_PX",
                 "BODY_LINE_HEIGHT_PX"):
        assert c.get(nome, 0) > 0, nome
    assert c["TITLE_WIDTH_PX"] <= 240 and c["BODY_WIDTH_PX"] <= 240
    assert 2 * c["BEFORE_AFTER_WIDTH_PX"] <= 240, "os dois blocos ANTES/AGORA têm de caber lado a lado"
    # a tela inteira (160 px): barra 16 + imagem 64 + linha ANTES/AGORA + corpo
    assert 16 + 64 + c["BODY_LINE_HEIGHT_PX"] + c["BODY_LINES"] * c["BODY_LINE_HEIGHT_PX"] <= 160


def test_make_gera_o_header_e_o_git_ignora():
    regra = RULES_MK.read_text(encoding="utf-8")
    assert "AUTO_GEN_TARGETS += $(DATA_SRC_SUBDIR)/novidades_cartoes.h" in regra
    assert re.search(r"^\$\(DATA_SRC_SUBDIR\)/novidades_cartoes\.h: \$\(DATA_SRC_SUBDIR\)/novidades/cartoes\.json "
                     r"tools/novidades/gen_cartoes\.py\n\tpython3 tools/novidades/gen_cartoes\.py \$< \$@$",
                     regra, re.M)
    assert re.search(r"^\$\(C_BUILDDIR\)/novidades_data\.o: c_dep \+= \$\(DATA_SRC_SUBDIR\)/novidades_cartoes\.h$",
                     regra, re.M)
    assert GENERATED_REL in GITIGNORE.read_text(encoding="utf-8").splitlines()
    unidade = (REPO_ROOT / "src" / "novidades_data.c").read_text(encoding="utf-8")
    assert '#include "data/novidades_cartoes.h"' in unidade   # o header compila de verdade no build


# --- a medida dos textos na esteira -----------------------------------------------------------

@pytest.fixture(scope="module")
def entradas():
    return {e.label: e for e in ct._sources(REPO_ROOT) if not isinstance(e, ct.Result) and e.file == JSON_REL}


def test_esteira_registra_todos_os_textos_dos_cartoes(entradas):
    esperados = set()
    for t in _topicos():
        esperados.add(f"{t['id']}.name")
        for i, c in enumerate(t["cards"], 1):
            esperados |= {f"{t['id']}.{i}.{k}" for k in CAMPOS_DE_TEXTO if c.get(k)}
    assert set(entradas) == esperados
    assert entradas["ritmo.name"].texts == ("Ritmo de jogo",)
    # a quebra de linha entra como `\n` literal, como no .string/_("") do jogo
    assert any("\\n" in e.texts[0] for e in entradas.values())
    assert GENERATED_REL not in {f for f, _ in ct._source_files(REPO_ROOT)}   # o header gerado repete o JSON


def test_janelas_da_esteira_usam_as_constantes_do_header(entradas):
    c = _constantes()
    esperado = {
        "name": (c["TOPIC_NAME_WIDTH_PX"], "normal", 1),
        "title": (c["TITLE_WIDTH_PX"], "normal", 1),
        "before": (c["BEFORE_AFTER_WIDTH_PX"], "small", 1),
        "after": (c["BEFORE_AFTER_WIDTH_PX"], "small", 1),
        "body": (c["BODY_WIDTH_PX"], "small", c["BODY_LINES"]),
    }
    vistos = set()
    for label in entradas:
        regra = ct.rule_for(JSON_REL, label)
        campo = label.rsplit(".", 1)[1]
        assert (regra.px, regra.font, regra.lines) == esperado[campo], label
        vistos.add(campo)
    assert vistos == set(esperado)


def test_regras_citam_a_linha_da_constante_no_header(entradas):
    linhas = HEADER_H.read_text(encoding="utf-8").splitlines()
    for label in ("ritmo.name", "ritmo.1.title", "shiny.1.before", "shiny.1.after", "ritmo.1.body"):
        regra = ct.rule_for(JSON_REL, label)
        citados = re.findall(r"include/novidades\.h:(\d+)", regra.source)
        assert citados, label
        for n in citados:
            assert linhas[int(n) - 1].startswith("#define NOVIDADES_"), (label, n)


def test_textos_cabem_nas_janelas(entradas):
    """Largura, linhas, charmap, inglês e glossário de todos os cartões, pela checagem completa da esteira."""
    assert len(entradas) > 100, "a esteira não leu os textos dos cartões"
    achados = [r for r in ct.check_text(str(REPO_ROOT), {}) if JSON_REL in r.detail]
    assert not achados, "\n".join(f"{r.name}: {r.detail}" for r in achados)


def test_medida_acusa_texto_que_nao_cabe():
    """Controle negativo: a regra está de fato ligada (largura, linhas, título, ANTES/AGORA e inglês)."""
    env = ct._load_env(REPO_ROOT)
    c = _constantes()
    larga = "M" * 60
    corpo = ct.rule_for(JSON_REL, "ritmo.1.body")
    assert [p[0] for p in ct._analyze(larga, False, corpo, env)] == [ct.RULE_WIDTH]
    seis = "\\n".join(["curto"] * (c["BODY_LINES"] + 1))
    assert [p[0] for p in ct._analyze(seis, False, corpo, env)] == [ct.RULE_LINES]
    assert [p[0] for p in ct._analyze("curto\\nlinha dois", False, ct.rule_for(JSON_REL, "ritmo.1.title"), env)] == [
        ct.RULE_LINES]
    assert any(p[0] == ct.RULE_WIDTH for p in ct._analyze(
        "ANTES: troca + Revestimento Metálico", False, ct.rule_for(JSON_REL, "evolucoes.5.before"), env))
    ingles = ct._Entry(JSON_REL, "ritmo.1.body", ("You can walk and run faster than before.",), False)
    assert ct._english_words(ingles, set())


def test_pior_cartao_usa_a_janela_quase_toda():
    """Guarda contra janela folgada demais: o corpo mais cheio passa de 3 linhas e de 85% da largura."""
    env = ct._load_env(REPO_ROOT)
    c = _constantes()
    medidas = [ct.measure(card["body"].replace("\n", "\\n"), env, "small") for _, _, card in _cartoes()]
    assert max(m.lines for m in medidas) >= c["BODY_LINES"] - 1
    assert max(m.widest for m in medidas) >= 0.85 * c["BODY_WIDTH_PX"]
