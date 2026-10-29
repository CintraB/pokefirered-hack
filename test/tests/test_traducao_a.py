"""Frente A da tradução: diálogos dos mapas (`data/maps/*/text.inc`), grupo a grupo.

Para os arquivos de cada grupo já traduzido: nenhum inglês sobrando (função de relatório de inglês
da checagem de texto), nenhum achado das regras de texto da esteira (`controle`, `glossario`,
largura, linhas, letras, charmap) e os rótulos iguais aos da base inglesa. Task seguinte da frente:
acrescentar o grupo em `GRUPOS`.
"""

import json
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]

# grupo -> pastas de mapa (text.inc) traduzidas
GRUPOS = {
    "A1": [
        "CeladonCity", "CeladonCity_Condominiums_1F", "CeladonCity_Condominiums_2F",
        "CeladonCity_Condominiums_3F", "CeladonCity_Condominiums_Roof", "CeladonCity_Condominiums_RoofRoom",
        "CeladonCity_DepartmentStore_1F", "CeladonCity_DepartmentStore_2F", "CeladonCity_DepartmentStore_3F",
        "CeladonCity_DepartmentStore_4F", "CeladonCity_DepartmentStore_5F", "CeladonCity_DepartmentStore_Roof",
        "CeladonCity_GameCorner", "CeladonCity_GameCorner_PrizeRoom", "CeladonCity_Gym", "CeladonCity_Hotel",
        "CeladonCity_House1", "CeladonCity_PokemonCenter_1F", "CeladonCity_Restaurant", "CeruleanCave_B1F",
        "CeruleanCity", "CeruleanCity_BikeShop", "CeruleanCity_Gym", "CeruleanCity_House1", "CeruleanCity_House2",
        "CeruleanCity_House3", "CeruleanCity_House4", "CeruleanCity_House5", "CeruleanCity_Mart",
        "CeruleanCity_PokemonCenter_1F", "CinnabarIsland", "CinnabarIsland_Gym",
    ],
    "A2": [
        "CinnabarIsland_Mart", "CinnabarIsland_PokemonCenter_1F", "CinnabarIsland_PokemonLab_Entrance",
        "CinnabarIsland_PokemonLab_ExperimentRoom", "CinnabarIsland_PokemonLab_Lounge",
        "CinnabarIsland_PokemonLab_ResearchRoom", "DiglettsCave_NorthEntrance",
        "DiglettsCave_SouthEntrance", "FiveIsland", "FiveIsland_House1", "FiveIsland_House2",
        "FiveIsland_LostCave_Room1", "FiveIsland_LostCave_Room10", "FiveIsland_LostCave_Room4",
        "FiveIsland_Meadow", "FiveIsland_MemorialPillar", "FiveIsland_PokemonCenter_1F",
        "FiveIsland_ResortGorgeous", "FiveIsland_ResortGorgeous_House", "FiveIsland_RocketWarehouse",
        "FiveIsland_WaterLabyrinth", "FourIsland", "FourIsland_House1", "FourIsland_IcefallCave_Back",
        "FourIsland_LoreleisHouse", "FourIsland_Mart", "FourIsland_PokemonCenter_1F", "FuchsiaCity",
        "FuchsiaCity_Gym", "FuchsiaCity_House1", "FuchsiaCity_House2", "FuchsiaCity_House3",
        "FuchsiaCity_Mart", "FuchsiaCity_PokemonCenter_1F", "FuchsiaCity_SafariZone_Entrance",
        "FuchsiaCity_SafariZone_Office", "FuchsiaCity_WardensHouse", "IndigoPlateau_PokemonCenter_1F",
        "LavenderTown",
    ],
    "A3": [
        "LavenderTown_House1", "LavenderTown_House2", "LavenderTown_Mart", "LavenderTown_PokemonCenter_1F",
        "LavenderTown_VolunteerPokemonHouse", "MtEmber_Exterior", "MtEmber_RubyPath_B3F", "MtMoon_1F", "MtMoon_B2F",
        "OneIsland", "OneIsland_House1", "OneIsland_House2", "OneIsland_KindleRoad",
        "OneIsland_KindleRoad_EmberSpa", "OneIsland_PokemonCenter_1F", "OneIsland_TreasureBeach", "PalletTown",
        "PalletTown_PlayersHouse_1F", "PalletTown_PlayersHouse_2F", "PalletTown_ProfessorOaksLab",
    ],
}
FILES = [f"data/maps/{m}/text.inc" for maps in GRUPOS.values() for m in maps]

# Inglês que a checagem conta mas é legítimo: (arquivo, palavras, textos) -> motivo.
# Vazio desde a B3: "TO" (Treinador Original, glossário OT -> TO) deixou de contar na própria regra.
ENGLISH_EXCEPTIONS = {}


@pytest.fixture(scope="module")
def results():
    if shutil.which("git") is None:
        pytest.skip("sem git")
    return ct.check_text(str(REPO_ROOT), {"text": []}, english="desligado")


def test_base_inglesa_disponivel(results):
    """Sem a base, `controle` e `glossario` não rodam (o aviso não cita arquivo): não pode ficar verde calado."""
    assert [r.detail for r in results if "base inglesa indisponível" in r.detail] == []


def _mine(results, rule=None):
    # achado conhecido de regra nova (check_text.KNOWN_FINDINGS, T4) é aviso que a frente corrige depois
    return [r for r in results if r.status != "ok" and any(f in r.detail for f in FILES)
            and not (r.status == "aviso" and "(conhecido:" in r.detail)
            and (rule is None or r.name == f"texto/{rule}")]


@pytest.mark.parametrize("rule", ["largura", "linhas", "letras", "charmap", "terminador", "controle", "glossario"])
def test_nenhum_achado_das_regras_nos_arquivos_da_frente(results, rule):
    assert [f"{r.detail}" for r in _mine(results, rule)] == []


def test_nenhum_achado_de_texto_nos_arquivos_da_frente(results):
    # qualquer outra regra de texto, com os arquivos da frente no detalhe
    assert [f"{r.name}: {r.detail}" for r in _mine(results)] == []


def test_nenhum_ingles_sobrando():
    report = ct.english_report(str(REPO_ROOT))
    left = {}
    for f in FILES:
        c = report.get(f)
        if c is None:
            continue
        if (c.words, c.texts) == ENGLISH_EXCEPTIONS.get(f):
            continue
        left[f] = (c.words, c.texts, c.examples)
    assert left == {}


def test_excecao_do_to_continua_sendo_so_a_sigla():
    """A única exceção do relatório de inglês é a sigla TO (Treinador Original)."""
    text = (REPO_ROOT / "data/maps/CeladonCity_DepartmentStore_3F/text.inc").read_text(encoding="utf-8")
    block = text[text.index("OTStandsForOriginalTrainer::"):]
    block = block[:block.index("$")]
    words = ct._plain_words(block.replace(".string", " "))
    assert [w for w in words if w.lower() in ct.ENGLISH_WORDS] == ["TO", "TO"]


# rótulos que os hacks acrescentaram depois da base da tradução (não são rótulos renomeados)
ROTULOS_DOS_HACKS = {"PalletTown_ProfessorOaksLab_Text_OakAnotherRareEgg",      # Hack 8: ovo raro por vitória
                     "PalletTown_ProfessorOaksLab_Text_OakOfferNovidadesFirst",  # tela de novidades (Task 5)
                     "PalletTown_ProfessorOaksLab_Text_OakNovidadesAnytime",
                     "PalletTown_ProfessorOaksLab_Text_OakOfferNovidades",
                     "MtMoon_B2F_Text_TakeTheOtherFossilToo",                    # Hack 8: dois fósseis no Monte Lua
                     "FourIsland_Text_DaycareManIncubator"}                      # POK-37: a creche dá a Incubadora
# rótulos da base que um hack tirou de propósito (o texto deixou de existir)
ROTULOS_REMOVIDOS_DOS_HACKS = {"MtMoon_B2F_Text_ThenThisFossilIsMine"}           # Hack 8: o Miguel não leva mais o outro fóssil


@lru_cache(maxsize=None)
def _base_labels(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"],
                         capture_output=True)
    if out.returncode != 0:
        return None
    return re.findall(r"^(\w+)::", out.stdout.decode("utf-8"), re.M)


@pytest.mark.parametrize("rel", FILES)
def test_rotulos_iguais_aos_da_base(rel):
    if shutil.which("git") is None:
        pytest.skip("sem git")
    base = _base_labels(rel)
    if base is None:
        pytest.skip("sem o commit base da tradução")
    now = [lbl for lbl in re.findall(r"^(\w+)::", (REPO_ROOT / rel).read_text(encoding="utf-8"), re.M)
           if lbl not in ROTULOS_DOS_HACKS]
    assert now == [lbl for lbl in base if lbl not in ROTULOS_REMOVIDOS_DOS_HACKS]


@pytest.mark.parametrize("rel", FILES)
def test_sem_termos_ingleses_em_caixa_alta(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    # nomes de golpe/item do jogo inglês que não podem sobrar em caixa alta no diálogo
    text = re.sub(r"{[^}]*}", "", text)
    for old in ("POKéMON", "TRAINER", "GYM", "BADGE", "TEAM ROCKET", "POKé BALL", "BERRY", "STORE", "LEADER"):
        assert old not in re.sub(r"@.*", "", text), (rel, old)


# Regras de 20/10: jogador sem gênero marcado; termos do glossário exatos; nomes não partidos na quebra
PLAYER_GENDERED = ("Fique quieto", "muito bruto", "parceiro,", "ocupado demais", "perdedor", "Aspirante a campeão",
                   "Seja bem-vindo", "Bem-vindo",
                   # padrões que escaparam na C1 + o Treinador referido ao jogador
                   "você é bom", "ganancioso", "campeão em formação", "tão bruto", "ser discreto",
                   "habilidade como", "ser um Treinador",
                   # A2: adjetivos/particípios dirigidos ao jogador
                   "frustrado", "jovem amigo", "esmagado", "Você é pesado", "criança Treinadora")
WRONG_FORMS = ("Esconderijo da Equipe Rocket",
               # decisões do Cintra de 20/10: forma cheia em fala; títulos de jogo no original
               "Superrepel.", "Cura Queimad.", "Vale Bicicl.", "Guarda Esp.", "Expl. Sônica", "Rajada Fogo",
               "Esmaga Pedra", "Atq. Esp.", "Def. Esp.", "Vermelho e Verde",
               # A2: forma cheia de golpe em fala; nomes do glossário
               "Raio Congel.", "P. Corporal", "Zona do Safári", "Safari Zone",
               # A3: forma cheia do item em fala; Oak vira Carvalho; nomes de lugar do glossário
               "Mapa Cidade", "Passe Arco-íris", "Prof. Oak", "Professor Oak", "OAK", "Monte Ember", "Ilha Kindle",
               "Ilha 1", "Ilha One",
               # fix 1 da A3: "menu" minúsculo no meio da frase (glossário); "Visto daqui" concorda com "o Monte"
               "o Menu", "no Menu", "Vista daqui, o Monte")
NAMES_NOT_SPLIT = ("Equipe Rocket", "GAME FREAK", "Loja de Celadon", "Pó de Fruta", "Canto Direto",
                   "Sistema de Armazenamento de Pokémon", "Centro Pokémon", "Loja de Bicicletas",
                   "Cura Queimadura", "Vale Bicicleta", "Guarda Especial", "Explosão Sônica", "Rajada de Fogo",
                   "Esmagamento de Pedras", "Ataque Especial", "Defesa Especial", "Red e Green",
                   # A2: golpe em forma cheia, títulos e nomes que não estão (ou estão sem flexão) no glossário
                   "Pancada Corporal", "Raio Congelante", "Sr. Fuji", "Dr. Fuji", "Máquina de Ressurreição",
                   "Ovo de Pokémon", "Ovos de Pokémon", "Pokédex Nacional", "Elite Quatro", "Liga Pokémon",
                   "Srta. Selphy", "Chefe Giovanni", "Casa de Voluntários Pokémon",
                   # termo criado pela frente B (registrado no glossário dela; aqui só para a quebra)
                   "Mestre da Pesca",
                   # A3: termos criados (também no glossário) e nomes compostos fora dele
                   "Campeão da Liga Pokémon", "Cidade de Goldenrod", "Ginásio de Pewter", "Treinador Pokémon",
                   "Treinadores Pokémon", "Poké Flauta", "Passe Triplo", "Passe 7 Cores", "Fóssil Hélice", "Fóssil Domo",
                   "Mapa da Cidade", "Armazém Rocket", "Estrada Fagulha", "Monte Brasa", "Spa da Brasa",
                   "Goldeen precisa de lenha")


def _flat(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    body = "".join(re.findall(r'\.string "(.*)"', text))
    return body


@pytest.mark.parametrize("rel", FILES)
def test_jogador_sem_genero_e_termos_exatos(rel):
    body = _flat(rel)
    # Hack 8: o Miguel (homem) fala de si mesmo; "ganancioso" aí não é adjetivo dirigido ao jogador
    body = body.replace("Eu não sou ganancioso", "")
    for bad in PLAYER_GENDERED + WRONG_FORMS:
        assert bad not in body, (rel, bad)


def _multiword_terms():
    """Todo termo PT de duas ou mais palavras do glossário de máquina, mais os nomes acima."""
    data = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    names = {t["pt"] for t in data["termos"] if " " in t["pt"]} | set(NAMES_NOT_SPLIT)
    # "Centros Pokémon", "Insígnias Rocha": plural simples com "s" na última palavra de cada trecho
    plurals = set()
    for name in names:
        words = name.split(" ")
        for j, w in enumerate(words):
            if w[-1:].isalpha() and not w.endswith("s"):
                plurals.add(" ".join(words[:j] + [w + "s"] + words[j + 1:]))
    return sorted(names | plurals)


TERMS = _multiword_terms()


# Nome que não cabe numa linha (278 px) e quebra num ponto só, decidido à mão (placa de Pallet): nome -> posição do espaço
SPLIT_ALLOWED = {"Laboratório de Pesquisa Pokémon do Prof. Carvalho": len("Laboratório de Pesquisa")}


@pytest.mark.parametrize("rel", FILES)
def test_nomes_nao_sao_partidos_na_quebra(rel):
    body = _flat(rel)
    found = []
    for name in TERMS:
        for i, ch in enumerate(name):
            if ch == " " and i != SPLIT_ALLOWED.get(name):
                for br in ("\\n", "\\l"):
                    if name[:i] + br + name[i + 1:] in body:
                        found.append(name)
    assert found == [], rel


@pytest.mark.parametrize("rel", FILES)
def test_fim_de_arquivo_igual_ao_da_base(rel):
    """O fim do arquivo (linha em branco final) é o da versão inglesa."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    base = out.stdout.decode("utf-8")
    now = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert len(now) - len(now.rstrip("\n")) == len(base) - len(base.rstrip("\n"))


# Regra de 20/10: a esteira mede {STR_VAR_n}/{B_BUFF*}/{B_COPY_VAR_*} como 0 px; aqui eles valem 10 "M" (largos)
VARIABLE_PLACEHOLDER = re.compile(r"\{(?:STR_VAR_\d|B_BUFF\d|B_COPY_VAR_\d)\}")
DIALOG_PX = 208


@pytest.fixture(scope="module")
def env():
    return ct._load_env(REPO_ROOT)


@pytest.mark.parametrize("rel", FILES)
def test_linhas_com_placeholder_variavel_cabem_com_10_letras_largas(rel, env):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    too_wide = []
    for m in re.finditer(r'^(\w+)::\n((?:[ \t]+\.string ".*"\n?)+)', text, re.M):
        raw = "".join(re.findall(r'\.string "(.*)"', m.group(2)))
        if not VARIABLE_PLACEHOLDER.search(raw):
            continue
        measured = ct.measure(VARIABLE_PLACEHOLDER.sub("MMMMMMMMMM", raw), env, "normal")
        if measured.widest > DIALOG_PX:
            too_wide.append(f"{m.group(1)}: {measured.widest} px")
    assert too_wide == []


def test_ha_texto_com_placeholder_variavel_no_grupo():
    """Garante que a checagem acima tem o que medir (se um dia não houver, o teste avisa)."""
    n = sum(bool(VARIABLE_PLACEHOLDER.search((REPO_ROOT / rel).read_text(encoding="utf-8"))) for rel in FILES)
    assert n >= 1


# Buffers (gStringVar1/2/3: 20 bytes, 19 letras): nomes de item que os scripts do grupo copiam com
# bufferitemname (fósseis do laboratório de Cinnabar) têm de caber no campo do item (13 letras).
def test_nomes_de_item_bufferizados_pelos_scripts_do_grupo_cabem():
    items = {i["itemId"]: i["english"]
             for i in json.loads((REPO_ROOT / "src/data/items.json").read_text(encoding="utf-8"))["items"]}
    found = []
    for rel in FILES:
        scripts = (REPO_ROOT / rel).with_name("scripts.inc")
        if not scripts.exists():
            continue
        for item in re.findall(r"bufferitemname\s+STR_VAR_\d,\s*(ITEM_\w+)", scripts.read_text(encoding="utf-8")):
            found.append(item)
            assert len(items[item]) <= 13, (item, items[item])
    assert "ITEM_HELIX_FOSSIL" in found and "ITEM_OLD_AMBER" in found


# Gênero do jogador, padrão genérico (fix da A2): "você" (ou {PLAYER}) + verbo de ligação + adjetivo/particípio
# masculino (-o, -ado, -ido, -oso, -udo), como "Você ser rápido" ou "você está pronto". A lista exata
# `PLAYER_GENDERED` só serve contra regressão; esta pega o que ainda não foi visto. Gerúndio (-ndo) não conta;
# palavra-alvo com 3+ letras e que não seja intensificador (evita "está no Ginásio", "é do tipo", "está muito feliz").
_COPULA = r"(?:é|está|estava|era|foi|ser|estar|ficar|fica|ficou|parece|estiver|for|seja)"
_INTENSIFIERS = r"(?:muito|bem|tão|mais|menos|meio|bastante|realmente|sempre)"
GENDERED_ADJ = re.compile(
    rf"(?<!\w)(?:[Vv]ocê|{{PLAYER}})\s+(?:não\s+)?{_COPULA}\s+(?:{_INTENSIFIERS}\s+)?"
    rf"(?!{_INTENSIFIERS}\b)(?!\w*ndo\b)(\w{{3,}}(?:o|ado|ido|oso|udo))\b")
# palavra terminada em -o que segue "você é/está/..." sem marcar o gênero do jogador (palavra -> motivo)
GENDERED_ADJ_OK: dict[str, str] = {}


def _one_line(body):
    """Texto do `.string` achatado: as quebras literais (barra + n, l ou p) viram espaço; só {PLAYER} sobra entre chaves."""
    body = re.sub(r"\{[^}]*\}", lambda m: "{PLAYER}" if m.group(0) == "{PLAYER}" else " ", body)
    return re.sub(re.escape(chr(92)) + "[nlp]", " ", body)


def _sentences(rel):
    return _one_line(_flat(rel))


@pytest.mark.parametrize("rel", FILES)
def test_nenhum_adjetivo_masculino_dirigido_ao_jogador(rel):
    text = _sentences(rel)
    found = [m.group(0) for m in GENDERED_ADJ.finditer(text) if m.group(1) not in GENDERED_ADJ_OK]
    assert found == [], rel


@pytest.mark.parametrize("raw", [
    "Então! Você ser rápido e me dar isso!",
    "Você está pronto?",
    r"Você ser\nrápido",                    # quebra de linha entre o verbo e o adjetivo
    r"Você está\pmuito cansado",            # quebra de caixa + intensificador
    "{PLAYER} está pronto",                 # {PLAYER} em 3ª pessoa
    "Sim, {PLAYER} foi esperto",
])
def test_padrao_de_genero_acha_adjetivo_masculino(raw):
    """Mutações: o 'Você ser rápido' que passou pela A2 e as formas que o primeiro regex deixava passar."""
    assert GENDERED_ADJ.search(_one_line(raw)), raw


@pytest.mark.parametrize("raw", [
    "Você está fazendo algo e você andar logo",
    "Você está no Ginásio",
    "você é do tipo Água",
    "Você foi ao centro",
    "Você está muito feliz",
    "Você é tão forte",
])
def test_padrao_de_genero_nao_acusa_falso_positivo(raw):
    assert not GENDERED_ADJ.search(_one_line(raw)), raw


# ---- A3 (rodada 3) --------------------------------------------------------------------------------------------
# Regras de 21/10 que valem aqui: vocativo dirigido ao jogador ("cara", "amigo"...) e insulto "Seu X!"/"Ora, seu!"
# marcam gênero (Ruling 24); "o personagem principal"/"o protagonista" também. Procuramos no texto achatado
# (`_one_line`: quebras viram espaço), como o regex de adjetivo acima.
VOCATIVE = re.compile(
    r"(?:^|[.!?…] |, )(?:[Cc]ara|[Aa]migo|[Aa]miga|[Pp]arceir[oa]|[Gg]aroto|[Gg]arota|[Mm]oleque|[Mm]oleca|[Rr]apaz|"
    r"[Mm]ocinha|[Mm]eu caro|[Mm]inha cara)(?=[,.!?…])")
INSULT = re.compile(r"(?:[Oo]ra, |(?:^|[.!?…,] ))[Ss](?:eu|ua)(?: [A-Za-zÀ-ÿ]+)?[!?]|[Oo]ra, seu\b")
MAIN_CHARACTER = ("personagem principal", "protagonista", "vocês todos")


A3_FILES = [f"data/maps/{m}/text.inc" for m in GRUPOS["A3"]]
# (A1/A2 ficam de fora: a fala dividida por gênero do jogador, como "Obrigado, rapaz!"/"Obrigado, mocinha!" do
# Diretor, tem rótulos próprios por gênero e fala de propósito com cada um)


@pytest.mark.parametrize("rel", A3_FILES)
def test_sem_vocativo_nem_insulto_que_marca_o_genero_do_jogador(rel):
    text = _sentences(rel)
    found = [m.group(0) for m in VOCATIVE.finditer(text)] + [m.group(0) for m in INSULT.finditer(text)]
    found += [w for w in MAIN_CHARACTER if w in text.lower()]
    assert found == [], rel


@pytest.mark.parametrize("raw", [
    "Ei, cara! Você viu isso?",
    "Calma, amigo.",
    "Cara, que susto!",
    r"Olha só\n, parceiro!",
    "Boa sorte, garota!",
    "Ora, seu!",
    "Fora daqui, seu idiota!",
    "Seu bobo!",
    "Ouça, sua pestinha!",
    "Ah, o personagem principal chegou",
    "Vocês todos pomposos",
])
def test_padroes_de_vocativo_e_insulto_acham_o_que_marca_o_genero(raw):
    """Mutações: o que escapou na B2 ("Seu ratinho!", "Ora, seu!") e na C2 ("cara"/"amigo")."""
    text = _one_line(raw)
    assert (VOCATIVE.search(text) or INSULT.search(text) or any(w in text.lower() for w in MAIN_CHARACTER)), raw


@pytest.mark.parametrize("raw", [
    "Meu amigo Celio mandou o barco",
    "o cara que me deu o fora",
    "Dê um oi ao rapaz por mim!",
    "O seu jeito de batalhar me lembra alguém",
    "Que sorte a sua!",
    "Um amigo do Celio.",
])
def test_padroes_de_vocativo_e_insulto_nao_acusam_falso_positivo(raw):
    text = _one_line(raw)
    assert not (VOCATIVE.search(text) or INSULT.search(text)), raw


# Termos que a A3 criou (glossário "criado") têm de estar registrados e aparecer nas falas
TERMS_A3 = {
    "NAME RATER": ("Avaliador de Apelidos", "data/maps/LavenderTown_House2/text.inc"),
    "POKéMON FAN MAGAZINE": ("Revista Fã de Pokémon", "data/maps/LavenderTown_VolunteerPokemonHouse/text.inc"),
    "POKéMON INSIDER": ("Pokémon por Dentro", "data/maps/LavenderTown_VolunteerPokemonHouse/text.inc"),
    "POKéMON FAN": ("Fã de Pokémon", "data/maps/LavenderTown_VolunteerPokemonHouse/text.inc"),
    "KNOT ISLAND": ("Ilha do Nó", "data/maps/OneIsland/text.inc"),
    "POKéMON NET CENTER": ("Centro de Rede Pokémon", "data/maps/OneIsland/text.inc"),
    "NETWORK MACHINE": ("Máquina de Rede", "data/maps/OneIsland_PokemonCenter_1F/text.inc"),
    "OAK'S POKéMON SEMINAR": ("Seminário Pokémon do Prof. Carvalho", "data/maps/PalletTown_ProfessorOaksLab/text.inc"),
    "OAK POKéMON RESEARCH LAB": ("Laboratório de Pesquisa Pokémon do Prof. Carvalho", "data/maps/PalletTown/text.inc"),
    "GOLDENROD CITY": ("Cidade de Goldenrod", "data/maps/OneIsland_PokemonCenter_1F/text.inc"),
    "POKéMON LEAGUE HQ": ("Sede da Liga Pokémon", "data/maps/PalletTown_ProfessorOaksLab/text.inc"),
}


@pytest.mark.parametrize("en", sorted(TERMS_A3))
def test_termo_criado_na_a3_esta_no_glossario_e_na_fala(en):
    glossary = json.loads((REPO_ROOT / "test" / "esteira" / "glossario.json").read_text(encoding="utf-8"))
    entries = [t for t in glossary["termos"] if t["en"] == en]
    pt, rel = TERMS_A3[en]
    assert len(entries) == 1 and entries[0]["pt"] == pt and entries[0]["fonte"] == "criado"
    assert entries[0].get("frente") == "A3"
    assert pt in _sentences(rel)


# Termos que a A3 recebeu prontos de outras frentes: a fala usa exatamente o que está decidido
def test_senha_do_armazem_fica_inteira_numa_linha():
    """"Goldeen precisa de lenha." (1ª senha, definida na A2) não pode ser partida entre linhas nem trocada."""
    strings = re.findall(r'\.string "(.*)"', (REPO_ROOT / "data/maps/MtEmber_Exterior/text.inc").read_text(encoding="utf-8"))
    assert any("“Goldeen precisa de lenha.”" in s for s in strings)


def test_senha_e_a_mesma_da_a2():
    outras = (REPO_ROOT / "data/maps/FiveIsland_Meadow/text.inc").read_text(encoding="utf-8")
    assert "“Goldeen precisa de lenha.”" in outras


def test_falas_do_carvalho_usam_o_rotulo_do_glossario():
    for rel in ("data/maps/PalletTown/text.inc", "data/maps/PalletTown_ProfessorOaksLab/text.inc",
                "data/maps/PalletTown_PlayersHouse_1F/text.inc"):
        body = _flat(rel)
        assert "OAK:" not in body and "Oak:" not in body, rel
    assert "Carvalho: " in _flat("data/maps/PalletTown_ProfessorOaksLab/text.inc")


@pytest.mark.parametrize("rel", A3_FILES)
def test_texto_japones_sem_uso_fica_como_na_base(rel):
    """Os `.string` em japonês (sobras sem tradução inglesa) não são traduzidos: ficam como na base."""
    if shutil.which("git") is None:
        pytest.skip("sem git")
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{ct.TRANSLATION_BASE}:{rel}"], capture_output=True)
    if out.returncode != 0:
        pytest.skip("sem o commit base da tradução")
    kana = re.compile("[぀-ヿ]")

    def japanese(text):
        return {m.group(1): m.group(2) for m in re.finditer(r'^(\w+)::\n((?:[ \t]+\.string ".*"\n?)+)', text, re.M)
                if kana.search(m.group(2))}

    assert japanese((REPO_ROOT / rel).read_text(encoding="utf-8")) == japanese(out.stdout.decode("utf-8"))


# Unidades: o jogo passou a usar metro/quilo; nada de pés, polegadas, libras, milhas...
IMPERIAL = re.compile(r"\b(?:inch(?:es)?|polegadas?|libras?|lbs?\.?|feet|foot|milhas?|jardas?|onças?)\b"
                      r"|\d\s*(?:ft|pés?|pol\.?)(?!\w)", re.I)


@pytest.mark.parametrize("rel", FILES)
def test_sem_unidade_imperial(rel):
    assert IMPERIAL.findall(_sentences(rel)) == []
