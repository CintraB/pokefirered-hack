"""Revisão final de consistência da tradução PT-BR (task 11, correções de 24/10).

Trava as incoerências entre frentes que as regras por termo inglês não enxergam:

- I1: rótulos de fala em caixa mista ("Carvalho:", "Mãe:"...), nunca "CARVALHO:";
- I2: gêmeos e duplas em caixa mista nos textos (os `trainerName` de `trainers.h` seguem em CAIXA ALTA);
- I3: "tipo Terrestre" (forma cheia do glossário), nunca "tipo Terra";
- I4/M11: "Cidade de Vermilion", "Floresta de Viridian", "Caverna de Cerulean", "Porto de Vermilion" em
  fala e placa; a forma curta só no nome de mapa/região, no Arquivo Fama e no Quest Log (limites de letras);
- I5: "Poké Mart" sempre no masculino;
- M3: espécies em caixa mista no tutorial do Cara Pokémon, em `cable_club.inc` e nas fichas do Cassino;
- M1/M5/M6/M7/M8/M9/M10: forma cheia de item/golpe, revanche = fala do mapa, séries de falas, pergunta de
  salvar, PE, Equipe Rocket e Ajuda com uma redação só.

Cada trava é uma função sobre os textos extraídos pela checagem (`check_text._sources`); o teste de
mutação reintroduz o problema num texto real e exige que a função o acuse.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from esteira import check_text as ct

REPO_ROOT = Path(__file__).resolve().parents[2]
BREAK = re.compile(r"\\[nlp]")

# ---- extração ------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _entries() -> dict[tuple[str, str], str]:
    """(arquivo, rótulo) -> texto cru da 1ª variante (quebras `\\n`/`\\l`/`\\p` como no fonte)."""
    out: dict[tuple[str, str], str] = {}
    for e in ct._sources(REPO_ROOT):
        if hasattr(e, "texts") and e.texts:
            out[(e.file, e.label)] = e.texts[0]
    assert len(out) > 10000, "a extração de textos devolveu poucos textos"
    return out


def _flat(text: str) -> str:
    """Texto achatado: quebras viram espaço (as quebras são decisão do reflow)."""
    return BREAK.sub(" ", text)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _text(file: str, label: str) -> str:
    return _entries()[(file, label)]


# ---- I1: rótulos de fala em caixa mista ----------------------------------------------------

SPEECH_LABEL = re.compile(r"(?:^|\\[nlp$]|\})\s*([A-ZÀ-Ý][A-ZÀ-Ý .']{2,}): ")


# Textos que não são fala: os rótulos "ANTES:"/"AGORA:"/"SEM:"/"COM:" da linha de comparação dos cartões
# da tela de novidades (cartoes.json) ficam em maiúsculas de propósito, como no mockup aprovado.
NOT_SPEECH_FILES = ("src/data/novidades/cartoes.json",)


def caps_labels(entries: dict[tuple[str, str], str]) -> list[str]:
    return [f"{f}: {lbl}: {m.group(1)}:" for (f, lbl), t in entries.items() if f not in NOT_SPEECH_FILES
            for m in SPEECH_LABEL.finditer(t)]


def test_nenhum_rotulo_de_fala_em_maiuscula():
    assert caps_labels(_entries()) == []


def test_rotulos_de_fala_em_caixa_mista_existem():
    flat = {k: _flat(t) for k, t in _entries().items()}
    for label, files in {
        "Carvalho:": ("data/maps/PalletTown_ProfessorOaksLab/text.inc", "data/text/pokedex_rating.inc",
                      "src/battle_message.c", "src/strings.c", "data/maps/PokemonLeague_HallOfFame/text.inc"),
        "Mãe:": ("data/maps/PalletTown_PlayersHouse_1F/text.inc", "data/text/white_out.inc"),
        "Cara Pokémon:": ("data/text/pokedude.inc", "src/data/text/teachy_tv.h"),
        "Alto-falante:": ("data/text/safari_zone.inc",),
        "Fantasma:": ("src/battle_message.c",),
        "Locutor:": ("src/battle_message.c",),
    }.items():
        for f in files:
            assert any(label in t for (ff, _), t in flat.items() if ff == f), f"{label} não aparece em {f}"


def test_mutacao_rotulo_em_maiuscula_e_acusado():
    entries = dict(_entries())
    key = ("data/maps/PalletTown_ProfessorOaksLab/text.inc", "PalletTown_ProfessorOaksLab_Text_OakBePatientRival")
    assert "Carvalho:" in entries[key]
    entries[key] = entries[key].replace("Carvalho:", "CARVALHO:")
    assert caps_labels(entries) == [f"{key[0]}: {key[1]}: CARVALHO:"]
    key2 = ("src/battle_message.c", "sText_OutOfSafariBalls")
    entries = dict(_entries())
    entries[key2] = entries[key2].replace("Locutor:", "LOCUTOR:")      # depois de um {PLAY_SE ...}
    assert any("LOCUTOR:" in p for p in caps_labels(entries))


# ---- I2 / M4: gêmeos, duplas e nomes próprios em caixa mista -------------------------------

TWINS = ("Eli", "Anne", "Kiri", "Jan", "Kia", "Mik", "Jes", "Gia", "Mya", "Ron", "Jed", "Lea", "Lia", "Luc",
         "Lil", "Ian", "Teala")
TWIN_FILES = ("data/maps/Route8/text.inc", "data/maps/Route12/text.inc", "data/maps/Route14/text.inc",
              "data/maps/Route15/text.inc", "data/maps/Route16/text.inc", "data/maps/Route19/text.inc",
              "data/maps/Route21_South/text.inc", "data/maps/OneIsland_KindleRoad/text.inc",
              "data/text/trainers.inc", "data/scripts/cable_club.inc")
_TWIN_CAPS = re.compile(r"\b(" + "|".join(n.upper() for n in TWINS) + r")\b")
_SHOUT_CAPS = re.compile(r"\bCHEFE\b")


def caps_names(entries: dict[tuple[str, str], str]) -> list[str]:
    return [f"{f}: {lbl}: {m.group(1)}" for (f, lbl), t in entries.items() if f in TWIN_FILES + ("data/maps/CeladonCity_House1/text.inc",)
            for m in list(_TWIN_CAPS.finditer(BREAK.sub(" ", t))) + list(_SHOUT_CAPS.finditer(t))]


def test_gemeos_e_duplas_em_caixa_mista():
    assert caps_names(_entries()) == []


def test_gemeos_aparecem_em_caixa_mista_nos_dois_lugares():
    flat = {k: _flat(t) for k, t in _entries().items()}

    def has(file: str, frag: str) -> bool:
        return any(frag in t for (f, _), t in flat.items() if f == file)

    assert has("data/text/trainers.inc", "Eli: ") and has("data/text/trainers.inc", "Anne: ")
    assert has("data/maps/Route8/text.inc", "Eli: ")
    assert has("data/text/trainers.inc", "Kiri: Jan, ") and has("data/maps/Route14/text.inc", "Kiri: Jan, ")
    assert has("data/maps/OneIsland_KindleRoad/text.inc", "Kia: ") and has("data/text/trainers.inc", "Kia: ")
    assert has("data/maps/Route12/text.inc", "Jes: ") and has("data/text/trainers.inc", "a minha Gia")
    assert has("data/maps/Route16/text.inc", "O Jed é tão legal") and has("data/text/trainers.inc", "Ian, ")
    assert has("data/scripts/cable_club.inc", "Sou eu, a Teala,")
    assert has("data/maps/CeladonCity_House1/text.inc", "Chefe!")


def test_trainer_name_de_gemeos_continua_em_caixa_alta():
    """Decisão do dono (24/10): `trainerName` fica em maiúscula (converter muda naturezas)."""
    trainers = _read("src/data/trainers.h")
    for name in ("ELI & ANNE", "GIA & JES"):
        assert f'.trainerName = _("{name}")' in trainers


def test_mutacao_nome_de_gemeo_em_maiuscula_e_acusado():
    entries = dict(_entries())
    key = ("data/maps/Route16/text.inc", "Route16_Text_LeaPostBattle")
    assert "Jed" in entries[key] or "Lea" in entries[key]
    entries[key] = re.sub(r"\bJed\b", "JED", entries[key]).replace("Lea:", "LEA:")
    assert caps_names(entries), "o teste não acusou o nome em maiúscula"
    entries = dict(_entries())
    key = ("data/scripts/cable_club.inc", "CableClub_Text_FirstTimeRightThisWay")
    entries[key] = entries[key].replace("Teala", "TEALA")
    assert caps_names(entries) == [f"{key[0]}: {key[1]}: TEALA"]


# ---- I3: tipo Terrestre ---------------------------------------------------------------------

TIPO_TERRA = re.compile(r"\btipos?\s+(?:[A-Za-zÀ-ÿ]+\s+e\s+)?Terra\b")


def tipo_terra(entries: dict[tuple[str, str], str]) -> list[str]:
    return [f"{f}: {lbl}" for (f, lbl), t in entries.items() if TIPO_TERRA.search(_flat(t))]


def test_nenhum_tipo_terra():
    assert tipo_terra(_entries()) == []


def test_tipo_terrestre_nas_quatro_falas_de_ginasio():
    assert "dos tipos Pedra e Terrestre" in _flat(_text("data/maps/CeladonCity_Gym/text.inc", "CeladonCity_Gym_Text_BridgetPostBattle"))
    flat = {k: _flat(t) for k, t in _entries().items()}
    for f in ("data/maps/CinnabarIsland_Gym/text.inc", "data/maps/VermilionCity_Gym/text.inc",
              "data/maps/ViridianCity_Gym/text.inc"):
        assert any("tipo Terrestre" in t for (ff, _), t in flat.items() if ff == f), f
    # a Insígnia Terra e a Terra Dourada não são o tipo
    assert any("Insígnia Terra" in t for (ff, _), t in flat.items() if ff == "data/maps/ViridianCity_Gym/text.inc")


def test_mutacao_tipo_terra_e_acusado():
    entries = dict(_entries())
    key = ("data/maps/CeladonCity_Gym/text.inc", "CeladonCity_Gym_Text_BridgetPostBattle")
    entries[key] = entries[key].replace("Terrestre", "Terra")
    assert tipo_terra(entries) == [f"{key[0]}: {key[1]}"]
    entries = dict(_entries())
    key = ("data/maps/VermilionCity_Gym/text.inc", [k[1] for k in entries if k[0] == "data/maps/VermilionCity_Gym/text.inc"
                                                      and "tipo Terrestre" in _flat(entries[k])][0])
    entries[key] = entries[key].replace("tipo Terrestre", "tipo Terra")
    assert tipo_terra(entries) == [f"{key[0]}: {key[1]}"]


# ---- I4 / M11: lugares compostos com a forma cheia -----------------------------------------

# forma curta -> (forma cheia, arquivos onde a curta continua valendo: nome de mapa/região (18 letras), etiqueta
# de 84 px do Arquivo Fama e, só para a Floresta, o Quest Log, que copia o lugar para gStringVar2 (19 letras
# + fim; "Floresta de Viridian" tem 20, "Caverna de Cerulean" tem 19 e cabe)
SHORT_PLACES = {
    "Cidade Vermilion": ("Cidade de Vermilion", {"src/data/region_map/region_map_sections.json",
                                                 "data/text/fame_checker.inc"}),
    "Floresta Viridian": ("Floresta de Viridian", {"src/data/region_map/region_map_sections.json",
                                                   "src/data/text/quest_log.h"}),
    "Caverna Cerulean": ("Caverna de Cerulean", {"src/data/region_map/region_map_sections.json"}),
    "Porto Vermilion": ("Porto de Vermilion", set()),
}


def short_places(entries: dict[tuple[str, str], str]) -> list[str]:
    found = []
    for (f, lbl), t in entries.items():
        flat = _flat(t)
        for short, (_, allowed) in SHORT_PLACES.items():
            if re.search(rf"(?<![A-Za-zÀ-ÿ]){re.escape(short)}(?![A-Za-zÀ-ÿ])", flat) and f not in allowed:
                found.append(f"{f}: {lbl}: {short}")
    return found


def test_lugares_compostos_com_forma_cheia_em_fala_e_placa():
    assert short_places(_entries()) == []


def test_forma_cheia_dos_lugares_aparece_onde_estava_a_curta():
    entries = _entries()
    where = {
        "Cidade de Vermilion": ("data/maps/Route16/text.inc", "data/maps/Route5/text.inc", "data/maps/Route6/text.inc",
                                "data/maps/Route25/text.inc", "data/maps/Route25_SeaCottage/text.inc",
                                "data/maps/SSAnne_B1F_Room4/text.inc", "data/maps/SSAnne_CaptainsOffice/text.inc",
                                "data/maps/VermilionCity/text.inc", "data/text/trainers.inc", "src/data/items.json"),
        "Floresta de Viridian": ("data/maps/Route2_ViridianForest_SouthEntrance/text.inc", "data/maps/Route3/text.inc",
                                 "data/maps/Route6/text.inc", "data/maps/ViridianCity/text.inc",
                                 "data/maps/ViridianForest/text.inc", "data/text/trainers.inc"),
        "Caverna de Cerulean": ("data/maps/CeruleanCity/text.inc",),
        "Porto de Vermilion": ("data/maps/CinnabarIsland/text.inc", "data/maps/VermilionCity/text.inc"),
    }
    for full, files in where.items():
        for f in files:
            assert any(full in _flat(t) for (ff, _), t in entries.items() if ff == f), f"{full} não aparece em {f}"


def test_a_forma_curta_continua_no_nome_de_mapa_e_no_arquivo_fama():
    regiao = _read("src/data/region_map/region_map_sections.json")
    assert '"name": "Cidade Vermilion"' in regiao
    assert "Cidade Vermilion" in _read("data/text/fame_checker.inc")


def test_vermilion_na_rota_16_nao_mistura_as_duas_formas():
    texts = [_flat(t) for (f, _), t in _entries().items() if f == "data/maps/Route16/text.inc" and "Fuchsia" in t]
    assert texts and any("da Cidade de Fuchsia até a Cidade de Vermilion" in t for t in texts), texts


def test_mutacao_forma_curta_de_lugar_e_acusada():
    for short, (full, _) in SHORT_PLACES.items():
        entries = dict(_entries())
        keys = [k for k, t in entries.items() if full in _flat(t) and k[0] not in SHORT_PLACES[short][1]
                and k[0].endswith(".inc")]
        assert keys, full
        k = keys[0]
        entries[k] = entries[k].replace(full, short)
        assert f"{k[0]}: {k[1]}: {short}" in short_places(entries), short


# ---- Termos do glossário que não podem partir na quebra ------------------------------------

NO_SPLIT = ("Cidade de Vermilion", "Floresta de Viridian", "Caverna de Cerulean", "Porto de Vermilion", "Poké Mart",
            "Compartilhador de Exp.", "Dentes de Ouro", "Esmagamento de Pedras")


def split_terms(entries: dict[tuple[str, str], str], terms=NO_SPLIT) -> list[str]:
    found = []
    for term in terms:
        words = term.split(" ")
        pat = re.compile(r"(?<![A-Za-zÀ-ÿ])" + r"(?: |\\[nlp])".join(re.escape(w) for w in words) + r"s?(?![A-Za-zÀ-ÿ])")
        for (f, lbl), t in entries.items():
            for m in pat.finditer(t):
                if BREAK.search(m.group(0)):
                    found.append(f"{f}: {lbl}: {term}")
    return found


def test_nenhum_termo_do_glossario_partido_nos_textos_corrigidos():
    assert split_terms(_entries()) == []


def test_equipe_rocket_por_extenso_na_casa_da_cerulean():
    t = _flat(_text("data/maps/CeruleanCity_House2/text.inc", "CeruleanCity_House2_Text_RocketsStoleTMForDig"))
    assert "Aqueles miseráveis da Equipe Rocket!" in t
    assert split_terms(_entries(), ("Equipe Rocket",)) == [], "Equipe Rocket partida na quebra"


def test_mutacao_termo_partido_e_acusado():
    entries = dict(_entries())
    key = ("data/maps/VermilionCity/text.inc", "VermilionCity_Text_SSAnneVisitsOnceAYear")
    assert "Cidade de Vermilion" in entries[key]
    entries[key] = entries[key].replace("Cidade de Vermilion", "Cidade de\\nVermilion")
    assert split_terms(entries) == [f"{key[0]}: {key[1]}: Cidade de Vermilion"]


# ---- I5: o Poké Mart ------------------------------------------------------------------------

FEM_BEFORE_MART = re.compile(
    r"(?<![A-Za-zÀ-ÿ])(uma|numa|duma|da|na|nas|as|a|esta|nesta|essa|nessa|aquela|alguma|algumas|outra|outras|"
    r"toda|todas)\s+(?:Poké\s+)?Marts?(?![A-Za-zÀ-ÿ])", re.I)


def mart_feminino(entries: dict[tuple[str, str], str]) -> list[str]:
    return [f"{f}: {lbl}: {m.group(0)}" for (f, lbl), t in entries.items() for m in FEM_BEFORE_MART.finditer(_flat(t))]


def test_poke_mart_sempre_no_masculino():
    assert mart_feminino(_entries()) == []


def test_poke_mart_masculino_em_todo_o_jogo():
    flat = [_flat(t) for t in _entries().values()]
    joined = "\n".join(flat)
    for frag in ("num Poké Mart", "um Poké Mart", "este Poké Mart", "do Poké Mart", "nos Poké Marts",
                 "Um Poké Mart é identificado", "Alguns Marts têm"):
        assert frag in joined, frag
    assert re.search(r"no Poké Mart", joined)
    # a Ajuda, que tinha os dois gêneros no mesmo arquivo
    ajuda = [_flat(t) for (f, _), t in _entries().items() if f == "data/text/help_system.inc"]
    assert not any(re.search(r"\b(uma|nas) (Poké )?Marts?\b", t) for t in ajuda)


def test_glossario_registra_o_genero_do_poke_mart():
    termos = json.loads(_read("test/esteira/glossario.json"))["termos"]
    mart = [t for t in termos if t["en"] == "POKé MART"]
    assert len(mart) == 1 and "masculino" in mart[0]["obs"]


def test_mutacao_poke_mart_feminino_e_acusado():
    entries = dict(_entries())
    key = ("data/maps/Route1/text.inc", [k[1] for k in entries if k[0] == "data/maps/Route1/text.inc"
                                          and "num Poké Mart" in _flat(entries[k])][0])
    entries[key] = entries[key].replace("num Poké Mart", "numa Poké Mart")
    assert mart_feminino(entries) == [f"{key[0]}: {key[1]}: numa Poké Mart"]
    entries = dict(_entries())
    key = ("data/text/help_system.inc", "Help_Text_AnswerRanOutOfPotions")
    entries[key] = entries[key].replace("um Poké Mart", "uma\\nPoké Mart")      # quebra entre o artigo e o termo
    assert any("uma Poké Mart" in p for p in mart_feminino(entries))


# ---- M3: espécies em caixa mista -----------------------------------------------------------

SPECIES_FILES = ("data/text/pokedude.inc", "data/scripts/cable_club.inc", "src/strings.c")
# KYOGRE/GROUDON de `gExpandedPlaceholder_*` são placeholders de nome, não texto corrido
SPECIES_ALLOWED = {("src/strings.c", "gExpandedPlaceholder_Kyogre"), ("src/strings.c", "gExpandedPlaceholder_Groudon")}


@lru_cache(maxsize=1)
def _species_caps() -> re.Pattern:
    names = re.findall(r'_\("([A-Z]+)"\)', _read("src/data/text/species_names.h"))
    names = sorted({n for n in names if len(n) >= 3}, key=len, reverse=True)
    assert "RATTATA" in names and "DODRIO" in names and len(names) > 300
    return re.compile(r"(?<![A-Za-zÀ-ÿ{_])(" + "|".join(names) + r")(?![A-Za-zÀ-ÿ}_])")


def species_caps(entries: dict[tuple[str, str], str]) -> list[str]:
    pat = _species_caps()
    return [f"{f}: {lbl}: {m.group(1)}" for (f, lbl), t in entries.items()
            if f in SPECIES_FILES and (f, lbl) not in SPECIES_ALLOWED for m in pat.finditer(t)]


def test_especies_em_caixa_mista_nos_tres_arquivos():
    assert species_caps(_entries()) == []


def test_especies_aparecem_em_caixa_mista():
    flat = {k: _flat(t) for k, t in _entries().items()}

    def has(file: str, frag: str) -> bool:
        return any(frag in t for (f, _), t in flat.items() if f == file)

    assert has("data/text/pokedude.inc", "Rattata") and has("data/text/pokedude.inc", "Pidgey")
    assert has("data/text/pokedude.inc", "Oddish") and has("data/text/pokedude.inc", "Poliwag")
    assert has("data/text/pokedude.inc", "Butterfree")
    assert has("data/scripts/cable_club.inc", "Dodrio")
    for sp in ("Eevee", "Flareon", "Jolteon", "Vaporeon", "Abra", "Clefairy", "Dratini", "Scyther", "Porygon",
               "Pinsir"):
        assert has("src/strings.c", sp), sp


def test_mutacao_especie_em_maiuscula_e_acusada():
    for file, frag, up in (("data/text/pokedude.inc", "Rattata", "RATTATA"),
                           ("data/scripts/cable_club.inc", "Dodrio", "DODRIO"),
                           ("src/strings.c", "Clefairy", "CLEFAIRY")):
        entries = dict(_entries())
        key = next(k for k, t in entries.items() if k[0] == file and frag in t)
        entries[key] = entries[key].replace(frag, up)
        assert f"{key[0]}: {key[1]}: {up}" in species_caps(entries), up


# ---- M1: forma cheia de item e golpe em fala ------------------------------------------------

def test_forma_cheia_de_item_e_golpe_em_fala():
    # POK-34: o assistente dá o Ovo da Sorte no lugar do Exp. Share
    assert "Dei o Ovo da Sorte a um" in _flat(_text("data/text/pokedex_rating.inc", "PokedexRating_Text_LessThan60"))
    assert "entregou os Dentes de Ouro" in _flat(_text("data/maps/FuchsiaCity_WardensHouse/text.inc",
                                                       "FuchsiaCity_WardensHouse_Text_GaveGoldTeethToWarden"))
    assert "Quer usar Esmagamento de Pedras?" in _flat(_text("data/scripts/field_moves.inc", "Text_UseRockSmash"))
    flat = [_flat(t) for t in _entries().values()]
    assert not any("Compart. Exp." in t or "Dentes Ouro" in t for (f, _), t in
                   zip(_entries().keys(), flat) if f not in ("src/data/items.json",))


def test_glossario_registra_as_formas_cheias_de_golpe():
    termos = {t["en"]: t for t in json.loads(_read("test/esteira/glossario.json"))["termos"]}
    assert termos["COMET PUNCH"]["completo"] == "Soco de Cometa"
    assert termos["SAND TOMB"]["completo"] == "Fosso de Areia"
    assert termos["ROCK SMASH"]["completo"] == "Esmagamento de Pedras"
    assert termos["THE END"]["pt"] == "Fim" and "pendente" not in termos["THE END"]["obs"]
    assert termos["VERMILION PORT"]["pt"] == "Porto de Vermilion"


# ---- M5: a revanche segue a fala do mapa ----------------------------------------------------

REMATCH_PAIRS = (
    ("Route17_Text_BillyRematchIntro", "Route17/text.inc", "Route17_Text_BillyIntro"),
    ("Route21_North_Text_RonaldRematchIntro", "Route21_North/text.inc", "Route21_North_Text_RonaldIntro"),
    ("Route25_Text_DanRematchIntro", "Route25/text.inc", "Route25_Text_DanIntro"),
    ("Route25_Text_HaleyRematchIntro", "Route25/text.inc", "Route25_Text_HaleyIntro"),
    ("Route24_Text_ShaneRematchIntro", "Route24/text.inc", "Route24_Text_ShaneIntro"),
    ("OneIsland_KindleRoad_Text_BryceRematchIntro", "OneIsland_KindleRoad/text.inc",
     "OneIsland_KindleRoad_Text_BryceIntro"),
)


def rematch_diffs(entries: dict[tuple[str, str], str]) -> list[str]:
    return [rematch for rematch, mapfile, original in REMATCH_PAIRS
            if _flat(entries[("data/text/trainers.inc", rematch)]) != _flat(entries[(f"data/maps/{mapfile}", original)])]


def test_revanche_igual_a_fala_do_mapa():
    assert rematch_diffs(_entries()) == []


def test_mutacao_revanche_diferente_e_acusada():
    entries = dict(_entries())
    k = ("data/text/trainers.inc", "Route25_Text_DanRematchIntro")
    entries[k] = entries[k].replace("Meu pai", "O papai")
    assert rematch_diffs(entries) == ["Route25_Text_DanRematchIntro"]


# ---- M6 / M7 / M8 / M10: uma redação só ----------------------------------------------------

def test_falas_em_serie_com_uma_redacao_so():
    flat = {k: _flat(t) for k, t in _entries().items()}
    # irmãos do Mestre da Pesca (A2 x B2/C3): "Pegue isto e vá pescar, jovem!"
    for f, lbl in (("data/maps/FuchsiaCity_House2/text.inc", "FuchsiaCity_House2_Text_LikeYourStyleTakeThis"),
                   ("data/maps/Route12_FishingHouse/text.inc", "Route12_FishingHouse_Text_TakeThisAndFish"),
                   ("data/maps/VermilionCity_House1/text.inc", "VermilionCity_House1_Text_TakeThisAndFish")):
        assert flat[(f, lbl)].endswith("Pegue isto e vá pescar, jovem!$"), (f, lbl)
    # "How are the fish biting?"
    for f, lbl in (("data/maps/FuchsiaCity_House2/text.inc", "FuchsiaCity_House2_Text_HowAreTheFishBiting"),
                   ("data/maps/VermilionCity_House1/text.inc", "VermilionCity_House1_Text_HowAreTheFishBiting")):
        assert flat[(f, lbl)].endswith("Os peixes estão mordendo?$"), (f, lbl)
    assert not any("beliscando a isca" in t for t in flat.values())
    # bolsa cheia ao ganhar a MT
    assert flat[("data/maps/CinnabarIsland_Gym/text.inc", "CinnabarIsland_Gym_Text_MakeSpaceForThis")] \
        == flat[("data/maps/FuchsiaCity_Gym/text.inc", "FuchsiaCity_Gym_Text_MakeSpaceForThis")] \
        == "Abra espaço para isto, criança!$"
    # troca no jogo
    assert flat[("data/text/ingame_trade.inc", "Trade_Text_DoYouHaveMonWantToTradeForMon")].endswith(
        "Quer trocar pelo meu {STR_VAR_2}?$")
    assert "Quer trocar pelo meu {STR_VAR_2}?" in " ".join(
        t for (f, _), t in flat.items() if f == "data/maps/VermilionCity_House2/text.inc")


def test_pergunta_de_salvar_com_uma_redacao_so():
    flat = {k: _flat(t) for k, t in _entries().items()}
    sobrescrever = [t for (f, _), t in flat.items() if "Já existe um jogo salvo." in t]
    assert len(sobrescrever) == 2 and all(t.endswith("Quer gravar por cima?$") or t.endswith("Quer gravar por cima?") for t in sobrescrever), sobrescrever
    assert not any("Posso salvar" in t or "Posso gravar" in t or "sobrescrevê-lo" in t for t in flat.values())
    assert "O texto registrado mudou. Quer salvar o jogo?" in flat[("src/strings.c", "gText_RegisteredTextChanged_OKtoSave")]
    ajuda = flat[("data/text/help_system.inc", "Help_Text_HowToUseSave")]
    assert "arquivo de save" not in ajuda and "registrado no jogo salvo" in ajuda


def test_pontos_de_experiencia_da_torre_como_o_resto_do_jogo():
    joined = " ".join(_flat(x) for (f, _), x in _entries().items() if f == "data/maps/TrainerTower_Lobby/text.inc")
    assert "não rende PE nem dinheiro." in joined
    assert "Pontos de Exp." not in joined


def test_golpes_ocultos_da_ajuda_com_uma_redacao_so():
    a = _flat(_text("data/text/help_system.inc", "Help_Text_AnswerWhatAreHiddenMoves"))
    b = _flat(_text("data/text/help_system.inc", "Help_Text_DefineHMMove"))
    assert a == b


def test_mutacao_ajuda_diferente_e_acusada():
    a = _flat(_text("data/text/help_system.inc", "Help_Text_AnswerWhatAreHiddenMoves"))
    b = _flat(_text("data/text/help_system.inc", "Help_Text_DefineHMMove")).replace("Golpes ocultos", "Os golpes ocultos")
    assert a != b


# ---- Fix round 1: Quest Log, Passe 7 Cores e vocativo "cara" ---------------------------------

def test_quest_log_caverna_cheia_e_floresta_curta():
    """O Quest Log copia o lugar para gStringVar2 (19 letras + fim): a Caverna cabe na forma cheia."""
    caverna = _text("src/data/text/quest_log.h", "gText_QuestLog_CeruleanCave")
    floresta = _text("src/data/text/quest_log.h", "gText_QuestLog_ViridianForest")
    assert caverna == "Caverna de Cerulean" and len(caverna) <= 19
    assert floresta == "Floresta Viridian"          # "Floresta de Viridian" tem 20 letras e estoura o buffer
    assert len("Floresta de Viridian") > 19


def test_passe_7_cores_com_o_desenho_do_arco_iris():
    desc = _flat(_text("src/data/items.json", "ITEM_RAINBOW_PASS"))
    assert "Cidade de Vermilion e Ilhas Sevii." in desc and "desenho de arco-íris" in desc, desc


# vocativo "cara" (e "minha cara jovem") dirigido ao jogador marca gênero (Ruling 24); "um cara legal", "com cara de",
# "Cara Pokémon" e "Cara Feia" são outra coisa. A palavra do Easy Chat ("cara" = dude) fica de fora.
VOCATIVE_CARA = re.compile(r"(?:,\s*|^|[.!?…:]\s+)(?:[Mm]inha\s+)?[Cc]ara\b(?!\s+(?:Pokémon|Feia|de\b))")


def vocativo_cara(entries: dict[tuple[str, str], str]) -> list[str]:
    return [f"{f}: {lbl}" for (f, lbl), t in entries.items()
            if "easy_chat" not in f and VOCATIVE_CARA.search(_flat(t))]


def test_nenhum_vocativo_cara():
    assert vocativo_cara(_entries()) == []


def test_vocativos_cara_trocados_mantendo_o_tom():
    flat = {k: _flat(t) for k, t in _entries().items()}
    assert flat[("data/maps/Route14/text.inc", "Route14_Text_IsaacPostBattle")] == "Criar Pokémon é um saco, hein.$"
    assert "Não, sério, eu não entendo mesmo." in flat[("data/maps/ThreeIsland/text.inc", "ThreeIsland_Text_OughtToBeThankingUs")]
    assert flat[("data/maps/ThreeIsland/text.inc", "ThreeIsland_Text_Biker1PostBattle")].startswith("Poxa, sério…")
    assert flat[("data/maps/Route17/text.inc", "Route17_Text_BillyIntro")].endswith("A gente manda nas estradas!$")
    assert flat[("data/maps/SilphCo_11F/text.inc", "SilphCo_11F_Text_ThanksForSavingMeDearGirl")].startswith(
        "Presidente: Ah, que alívio!")


def test_mutacao_vocativo_cara_e_acusado():
    for file, label, old, new in (
            ("data/maps/Route14/text.inc", "Route14_Text_IsaacPostBattle", "saco, hein.", "saco, cara."),
            ("data/maps/ThreeIsland/text.inc", "ThreeIsland_Text_OughtToBeThankingUs", "Não, sério,", "Não, cara,"),
            ("data/maps/ThreeIsland/text.inc", "ThreeIsland_Text_Biker1PostBattle", "Poxa, sério", "Poxa, cara"),
            ("data/maps/SilphCo_11F/text.inc", "SilphCo_11F_Text_ThanksForSavingMeDearGirl", "Ah, que alívio!",
             "Ah, minha cara jovem!")):
        entries = dict(_entries())
        assert old in entries[(file, label)], (file, label)
        entries[(file, label)] = entries[(file, label)].replace(old, new)
        assert vocativo_cara(entries) == [f"{file}: {label}"], (file, label)
    # falsos positivos que o teste não pode acusar
    for ok in ("Eu sou um cara legal.", "Cara Pokémon: Ih…", "Está com cara de cansaço.", "Cara Feia"):
        assert not VOCATIVE_CARA.search(ok), ok
