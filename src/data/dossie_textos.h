// O dossiê da Família Sombra (POK-54, Task 9): as páginas da tela de src/dossie.c.
//
// Fonte da lore: docs/superpowers/specs/2026-11-06-casas-familia-sombra-design.md §8 (enriquecida) e o epílogo
// "Depois". Medidas em include/dossie.h; a checagem de texto da esteira mede cada texto aqui com elas
// (test/esteira/check_text.py) e test/tests/test_dossie.py confere a 1ª linha da lore, que é mais estreita.
// Quebras de linha só com `\n`. O título do chefe aparece sempre junto da espécie e em vermelho
// ({COLOR RED} ... {COLOR DARK_GRAY}: os índices 4 e 2 da paleta da pasta). A fonte não tem travessão: "-".

// --- capa e abas --------------------------------------------------------------------------------------------------
static const u8 sDossieAba_Policia[] = _("POLÍCIA DE KANTO");
static const u8 sDossieAba_Ficha1[] = _("FICHA 1 DE 4");
static const u8 sDossieAba_Ficha2[] = _("FICHA 2 DE 4");
static const u8 sDossieAba_Ficha3[] = _("FICHA 3 DE 4");
static const u8 sDossieAba_Ficha4[] = _("FICHA 4 DE 4");
static const u8 sDossieFolha_Prefixo[] = _("FOLHA ");
static const u8 sDossieCapa_Rota[] = _("ROTA 23");
static const u8 sDossieCapa_Arquivo[] = _("Arquivo: Oficial Jenny");

// --- títulos, gêmeos e rosas ----------------------------------------------------------------------------------------
static const u8 sDossieTitulo_Dom[] = _("GENGAR, O DOM");
static const u8 sDossieTitulo_Cobrador[] = _("TYRANITAR, O COBRADOR");
static const u8 sDossieTitulo_Mercenario[] = _("GARCHOMP, O MERCENÁRIO");
static const u8 sDossieTitulo_Pesadelo[] = _("DARKRAI, O PESADELO");
static const u8 sDossieTitulo_Depois[] = _("DEPOIS DO CASO");

static const u8 sDossieGemeos_Dom[] = _("Gêmeos: 2 Machamp");
static const u8 sDossieGemeos_Cobrador[] = _("Gêmeos: 2 Rhydon");
static const u8 sDossieGemeos_Mercenario[] = _("Gêmeos: 2 Gligar");
static const u8 sDossieGemeos_Pesadelo[] = _("Gêmeos: 2 Dusclops");

static const u8 sDossieRosa_Dom[] = _("Rosa vermelha");
static const u8 sDossieRosa_Cobrador[] = _("Rosa dourada");
static const u8 sDossieRosa_Mercenario[] = _("Rosa azul");
static const u8 sDossieRosa_Pesadelo[] = _("Rosa negra");

// --- a lore (1ª linha ao lado da foto, as outras embaixo) -----------------------------------------------------------
static const u8 sDossieTexto_Dom1[] = _(
    "Quando a Equipe Rocket\n"
    "caiu, um fantasma juntou os Pokémon\n"
    "abandonados num prédio esquecido da\n"
    "Rota 23. Ali nasceu a Família Sombra,\n"
    "e ele virou {COLOR RED}GENGAR, O DOM{COLOR DARK_GRAY}.");
static const u8 sDossieTexto_Dom2[] = _(
    "Ninguém chegava ao Dom\n"
    "sem a revista dos gêmeos Machamp. No\n"
    "sexto andar ele ouvia pedidos,\n"
    "concedia favores e cobrava lealdade;\n"
    "quem pedia saía devendo.");
static const u8 sDossieTexto_Dom3[] = _(
    "Na lapela, a rosa\n"
    "vermelha de uma menina de Lavender\n"
    "cujo Pokémon ele salvou. “Um favor de\n"
    "hoje é uma dívida de amanhã.” Quem\n"
    "pagava o pedágio subia em paz.");

static const u8 sDossieTexto_Cobrador1[] = _(
    "Veio do Monte Prateado\n"
    "com dois Rhydon que não falavam, só\n"
    "batiam. {COLOR RED}TYRANITAR, O COBRADOR{COLOR DARK_GRAY}\n"
    "recolhia as dívidas que o Dom\n"
    "perdoava, sem pressa e sem desconto.");
static const u8 sDossieTexto_Cobrador2[] = _(
    "Quando o Dom caiu, tomou\n"
    "a cadeira sem pedir licença e trocou a\n"
    "rosa vermelha por uma dourada, da cor\n"
    "do pedágio. Sob ele a Família ficou\n"
    "mais rica - e mais cruel.");

static const u8 sDossieTexto_Mercenario1[] = _(
    "Com Kanto perdido, a\n"
    "Família quebrou a própria regra e\n"
    "mandou buscar alguém de fora. De\n"
    "Sinnoh chegou {COLOR RED}GARCHOMP, O MERCENÁRIO{COLOR DARK_GRAY},\n"
    "com dois Gligar das cavernas de lá.");
static const u8 sDossieTexto_Mercenario2[] = _(
    "Não perguntava o motivo,\n"
    "só o preço. Nunca beijou a mão de\n"
    "ninguém: não era família, era contrato.\n"
    "Uma oferta dele não se recusava; se\n"
    "pagava, adiantado.");
static const u8 sDossieTexto_Mercenario3[] = _(
    "Usava uma rosa azul,\n"
    "colhida na neve de onde veio.\n"
    "Guardava cada pagamento num cofre,\n"
    "para o dia de voltar para casa. Esse\n"
    "dia nunca chegou.");

static const u8 sDossieTexto_Pesadelo1[] = _(
    "Os bilhetes mais antigos\n"
    "falam de uma sombra por trás do Dom,\n"
    "o padrinho do padrinho:\n"
    "{COLOR RED}DARKRAI, O PESADELO{COLOR DARK_GRAY}. Nunca subiu as\n"
    "escadas; governava pelos sonhos.");
static const u8 sDossieTexto_Pesadelo2[] = _(
    "Quem dormia no prédio\n"
    "acordava devendo. Nas reuniões das\n"
    "famílias, a cadeira dele ficava vazia.\n"
    "Dois Dusclops vigiavam a porta entre o\n"
    "sono e a vigília.");
static const u8 sDossieTexto_Pesadelo3[] = _(
    "Só quando todos caíram o\n"
    "Pesadelo apareceu. Sua rosa é negra,\n"
    "como a noite em que ninguém acorda.\n"
    "Com ele, a Família Sombra termina.");

static const u8 sDossieTexto_Depois[] = _(
    "A polícia fechou o prédio da Rota 23\n"
    "para sempre. Os Pokémon da Família\n"
    "foram para o Centro de Reabilitação de\n"
    "Celadon; muitos ganharam treinadores\n"
    "novos e uma casa de verdade. A rosa\n"
    "vermelha do Dom voltou para a menina\n"
    "de Lavender, que a guarda num vaso\n"
    "perto da janela.");

// --- os chefes e as páginas -----------------------------------------------------------------------------------------
struct DossieChefe
{
    const u8 *aba;
    const u8 *gemeos;
    const u8 *rosa;
};

// Índice = chefe - 1 (a ordem das ocupações: Dom, Cobrador, Mercenário, Pesadelo)
static const struct DossieChefe sDossieChefes[4] = {
    {sDossieAba_Ficha1, sDossieGemeos_Dom, sDossieRosa_Dom},
    {sDossieAba_Ficha2, sDossieGemeos_Cobrador, sDossieRosa_Cobrador},
    {sDossieAba_Ficha3, sDossieGemeos_Mercenario, sDossieRosa_Mercenario},
    {sDossieAba_Ficha4, sDossieGemeos_Pesadelo, sDossieRosa_Pesadelo},
};

static const struct DossiePagina sDossiePaginas[] = {
    {DOSSIE_CAPA, 1, 1, NULL, sDossieCapa_Arquivo},
    {1, 1, 3, sDossieTitulo_Dom, sDossieTexto_Dom1},
    {1, 2, 3, sDossieTitulo_Dom, sDossieTexto_Dom2},
    {1, 3, 3, sDossieTitulo_Dom, sDossieTexto_Dom3},
    {2, 1, 2, sDossieTitulo_Cobrador, sDossieTexto_Cobrador1},
    {2, 2, 2, sDossieTitulo_Cobrador, sDossieTexto_Cobrador2},
    {3, 1, 3, sDossieTitulo_Mercenario, sDossieTexto_Mercenario1},
    {3, 2, 3, sDossieTitulo_Mercenario, sDossieTexto_Mercenario2},
    {3, 3, 3, sDossieTitulo_Mercenario, sDossieTexto_Mercenario3},
    {4, 1, 3, sDossieTitulo_Pesadelo, sDossieTexto_Pesadelo1},
    {4, 2, 3, sDossieTitulo_Pesadelo, sDossieTexto_Pesadelo2},
    {4, 3, 3, sDossieTitulo_Pesadelo, sDossieTexto_Pesadelo3},
    {DOSSIE_DEPOIS, 1, 1, sDossieTitulo_Depois, sDossieTexto_Depois},
};
