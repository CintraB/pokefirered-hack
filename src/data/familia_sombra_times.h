// POK-51: times da Família Sombra por ocupação (incluído só por src/familia_sombra.c).
//
// Níveis do spec (§6.3): ocupação 1 = andares 1-3 de 50 a 54, andares 4-5 de 54 a 58, gêmeos 60; cada ocupação
// seguinte soma +6 em tudo. Cada membro segura um item que o fortalece (o item não vai para o jogador).
//
// Capangas visíveis (slots 1-9, 3 por andar): só espécies com sprite de chapéu (Task 2), e cada andar usa as
// paletas PALSLOT_NPC_1, _2 e _3 nesta ordem (o 4 fica para a Poké Bola do chão, OBJ_EVENT_GFX_ITEM_BALL):
//   posição 1 do andar (NPC_1): Misdreavus, Houndoom, Muk, Absol, Golem
//   posição 2 do andar (NPC_2): Sableye, Murkrow, Weezing, Cacturne
//   posição 3 do andar (NPC_3): Banette, Sneasel, Arbok, Shiftry
// Haunter, Houndour, Crobat, Mightyena e Crawdaunt (NPC_4) ficam no plantel (andares 4-5 e pedágio).

struct FamiliaMembro
{
    u16 species;
    u8 level;           // 0 no plantel: o nível vem de quem chama (pedágio, andares 4-5)
    u16 heldItem;
    u16 moves[MAX_MON_MOVES];
};

#define FAMILIA_CAPANGAS        9
#define FAMILIA_PLANTEL         6
#define FAMILIA_NIVEL_PASSO     6   // +6 em tudo a cada ocupação
#define FAMILIA_NIVEL_PEDAGIO_1 56  // ocupação 1: dentro dos andares 4-5 (54-58)
#define FAMILIA_NIVEL_PEDAGIO_2 58
#define FAMILIA_NIVEL_ANDAR_MIN 54  // ocupação 1: encontros dos andares 4-5 (sorteado entre MIN e MAX)
#define FAMILIA_NIVEL_ANDAR_MAX 58

#define MEMBRO(sp, lv, item, m1, m2, m3, m4) \
    {SPECIES_##sp, lv, ITEM_##item, {MOVE_##m1, MOVE_##m2, MOVE_##m3, MOVE_##m4}}

// Os 9 capangas visíveis: [ocupação - 1][slot - 1]; slot 1-3 = 1º andar, 4-6 = 2º, 7-9 = 3º.
static const struct FamiliaMembro sFamiliaCapangas[FAMILIA_OCUPACOES_TOTAL][FAMILIA_CAPANGAS] =
{
    // Ocupação 1: o Dom (fantasma, sombrio, veneno)
    {
        MEMBRO(MISDREAVUS, 50, SPELL_TAG,     SHADOW_BALL,  PSYCHIC,      THUNDERBOLT,  PAIN_SPLIT),
        MEMBRO(MURKROW,    50, SHARP_BEAK,    WING_ATTACK,  FAINT_ATTACK, SHADOW_BALL,  TAUNT),
        MEMBRO(ARBOK,      51, POISON_BARB,   SLUDGE_BOMB,  EARTHQUAKE,   CRUNCH,       GLARE),
        MEMBRO(MUK,        52, LEFTOVERS,     SLUDGE_BOMB,  FIRE_PUNCH,   THUNDER_PUNCH, CURSE),
        MEMBRO(WEEZING,    52, QUICK_CLAW,    SLUDGE_BOMB,  THUNDERBOLT,  FLAMETHROWER, WILL_O_WISP),
        MEMBRO(BANETTE,    53, SPELL_TAG,     SHADOW_BALL,  KNOCK_OFF,    THUNDERBOLT,  WILL_O_WISP),
        MEMBRO(ABSOL,      53, SCOPE_LENS,    SWORDS_DANCE, BITE,         SLASH,        SHADOW_BALL),
        MEMBRO(SABLEYE,    54, LEFTOVERS,     SHADOW_BALL,  FAINT_ATTACK, KNOCK_OFF,    CONFUSE_RAY),
        MEMBRO(SHIFTRY,    54, MIRACLE_SEED,  GIGA_DRAIN,   FAINT_ATTACK, EXTRASENSORY, FAKE_OUT),
    },
    // Ocupação 2: o Cobrador (pedra e sombrio)
    {
        MEMBRO(HOUNDOOM,   56, BLACK_GLASSES, FLAMETHROWER, CRUNCH,       SOLAR_BEAM,   SUNNY_DAY),
        MEMBRO(CACTURNE,   56, QUICK_CLAW,    NEEDLE_ARM,   FAINT_ATTACK, GIGA_DRAIN,   SPIKES),
        MEMBRO(SNEASEL,    57, BLACK_GLASSES, SLASH,        FAINT_ATTACK, ICE_BEAM,     QUICK_ATTACK),
        MEMBRO(GOLEM,      58, HARD_STONE,    EARTHQUAKE,   ROCK_SLIDE,   EXPLOSION,    BRICK_BREAK),
        MEMBRO(MURKROW,    58, SCOPE_LENS,    WING_ATTACK,  FAINT_ATTACK, SHADOW_BALL,  TAUNT),
        MEMBRO(ARBOK,      59, SHELL_BELL,    SLUDGE_BOMB,  EARTHQUAKE,   CRUNCH,       GLARE),
        MEMBRO(ABSOL,      59, CHOICE_BAND,   SLASH,        BITE,         SHADOW_BALL,  IRON_TAIL),
        MEMBRO(SABLEYE,    60, LEFTOVERS,     SHADOW_BALL,  FAINT_ATTACK, KNOCK_OFF,    CONFUSE_RAY),
        MEMBRO(SHIFTRY,    60, SITRUS_BERRY,  GIGA_DRAIN,   FAINT_ATTACK, EXTRASENSORY, SWORDS_DANCE),
    },
    // Ocupação 3: o Mercenário // parte 2 troca (plantel provisório gen 1-3, com sprite de chapéu)
    {
        MEMBRO(GOLEM,      62, HARD_STONE,    EARTHQUAKE,   ROCK_SLIDE,   EXPLOSION,    BRICK_BREAK),
        MEMBRO(WEEZING,    62, LEFTOVERS,     SLUDGE_BOMB,  THUNDERBOLT,  FLAMETHROWER, WILL_O_WISP),
        MEMBRO(ARBOK,      63, POISON_BARB,   SLUDGE_BOMB,  EARTHQUAKE,   CRUNCH,       GLARE),
        MEMBRO(HOUNDOOM,   64, BLACK_GLASSES, FLAMETHROWER, CRUNCH,       SOLAR_BEAM,   SUNNY_DAY),
        MEMBRO(CACTURNE,   64, MIRACLE_SEED,  NEEDLE_ARM,   FAINT_ATTACK, GIGA_DRAIN,   SPIKES),
        MEMBRO(SHIFTRY,    65, SITRUS_BERRY,  GIGA_DRAIN,   FAINT_ATTACK, EXTRASENSORY, SWORDS_DANCE),
        MEMBRO(ABSOL,      65, SCOPE_LENS,    SWORDS_DANCE, BITE,         SLASH,        SHADOW_BALL),
        MEMBRO(SABLEYE,    66, LEFTOVERS,     SHADOW_BALL,  FAINT_ATTACK, KNOCK_OFF,    CONFUSE_RAY),
        MEMBRO(SNEASEL,    66, QUICK_CLAW,    SLASH,        FAINT_ATTACK, ICE_BEAM,     QUICK_ATTACK),
    },
    // Ocupação 4: o Pesadelo // parte 2 troca (plantel provisório gen 1-3, com sprite de chapéu)
    {
        MEMBRO(MISDREAVUS, 68, SPELL_TAG,     SHADOW_BALL,  PSYCHIC,      THUNDERBOLT,  PAIN_SPLIT),
        MEMBRO(SABLEYE,    68, LEFTOVERS,     SHADOW_BALL,  FAINT_ATTACK, KNOCK_OFF,    CONFUSE_RAY),
        MEMBRO(BANETTE,    69, SPELL_TAG,     SHADOW_BALL,  KNOCK_OFF,    THUNDERBOLT,  WILL_O_WISP),
        MEMBRO(MUK,        70, LEFTOVERS,     SLUDGE_BOMB,  FIRE_PUNCH,   THUNDER_PUNCH, CURSE),
        MEMBRO(MURKROW,    70, SCOPE_LENS,    WING_ATTACK,  FAINT_ATTACK, SHADOW_BALL,  TAUNT),
        MEMBRO(SNEASEL,    71, BLACK_GLASSES, SLASH,        FAINT_ATTACK, ICE_BEAM,     QUICK_ATTACK),
        MEMBRO(ABSOL,      71, CHOICE_BAND,   SLASH,        BITE,         SHADOW_BALL,  IRON_TAIL),
        MEMBRO(WEEZING,    72, QUICK_CLAW,    SLUDGE_BOMB,  THUNDERBOLT,  FLAMETHROWER, WILL_O_WISP),
        MEMBRO(BANETTE,    72, SPELL_TAG,     SHADOW_BALL,  KNOCK_OFF,    THUNDERBOLT,  WILL_O_WISP),
    },
};

// Os gêmeos guarda-costas (dupla, 6º andar): [ocupação - 1][gêmeo]. Sem Earthquake: na dupla acertaria o irmão.
static const struct FamiliaMembro sFamiliaGemeos[FAMILIA_OCUPACOES_TOTAL][2] =
{
    {
        MEMBRO(MACHAMP, 60, BLACK_BELT,   CROSS_CHOP,  ROCK_SLIDE, BULK_UP,      FIRE_PUNCH),
        MEMBRO(MACHAMP, 60, SITRUS_BERRY, CROSS_CHOP,  ROCK_SLIDE, THUNDER_PUNCH, ICE_PUNCH),
    },
    {
        MEMBRO(RHYDON,  66, HARD_STONE,   ROCK_SLIDE,  MEGAHORN,   BRICK_BREAK,  SWORDS_DANCE),
        MEMBRO(RHYDON,  66, LEFTOVERS,    ROCK_SLIDE,  MEGAHORN,   IRON_TAIL,    TAKE_DOWN),
    },
    {
        // Gligar voa: o Earthquake do irmão não o acerta.
        MEMBRO(GLIGAR,  72, SOFT_SAND,    EARTHQUAKE,  AERIAL_ACE, IRON_TAIL,    SWORDS_DANCE),
        MEMBRO(GLIGAR,  72, QUICK_CLAW,   EARTHQUAKE,  AERIAL_ACE, FAINT_ATTACK, SLASH),
    },
    {
        MEMBRO(DUSCLOPS, 78, LEFTOVERS,   SHADOW_BALL, ICE_BEAM,   WILL_O_WISP,  CONFUSE_RAY),
        MEMBRO(DUSCLOPS, 78, SPELL_TAG,   SHADOW_BALL, ICE_BEAM,   PAIN_SPLIT,   CURSE),
    },
};

// Plantel de cada ocupação (encontros dos andares 4-5 e as 2 lutas do pedágio): o nível vem de quem chama
// (andares 4-5: FAMILIA_NIVEL_ANDAR_MIN..MAX + 6 por ocupação, FamiliaSombra_NivelSelvagem).
static const struct FamiliaMembro sFamiliaPlantel[FAMILIA_OCUPACOES_TOTAL][FAMILIA_PLANTEL] =
{
    // Ocupação 1: o Dom
    {
        MEMBRO(HAUNTER,   0, SPELL_TAG,     SHADOW_BALL,  THUNDERBOLT,  HYPNOSIS,     DREAM_EATER),
        MEMBRO(CROBAT,    0, SHARP_BEAK,    AERIAL_ACE,   SLUDGE_BOMB,  SHADOW_BALL,  CONFUSE_RAY),
        MEMBRO(HOUNDOOM,  0, BLACK_GLASSES, FLAMETHROWER, CRUNCH,       SOLAR_BEAM,   SUNNY_DAY),
        MEMBRO(WEEZING,   0, LEFTOVERS,     SLUDGE_BOMB,  THUNDERBOLT,  FLAMETHROWER, WILL_O_WISP),
        MEMBRO(MIGHTYENA, 0, BLACK_GLASSES, CRUNCH,       TAKE_DOWN,    IRON_TAIL,    SWAGGER),
        MEMBRO(CRAWDAUNT, 0, SCOPE_LENS,    CRABHAMMER,   CRUNCH,       ICE_BEAM,     SWORDS_DANCE),
    },
    // Ocupação 2: o Cobrador (pedra e sombrio)
    {
        MEMBRO(GOLEM,     0, HARD_STONE,    EARTHQUAKE,   ROCK_SLIDE,   EXPLOSION,    BRICK_BREAK),
        MEMBRO(SNEASEL,   0, QUICK_CLAW,    SLASH,        FAINT_ATTACK, ICE_BEAM,     QUICK_ATTACK),
        MEMBRO(MIGHTYENA, 0, CHOICE_BAND,   CRUNCH,       TAKE_DOWN,    IRON_TAIL,    SHADOW_BALL),
        MEMBRO(CRAWDAUNT, 0, SCOPE_LENS,    CRABHAMMER,   CRUNCH,       ICE_BEAM,     SWORDS_DANCE),
        MEMBRO(HOUNDOOM,  0, BLACK_GLASSES, FLAMETHROWER, CRUNCH,       SOLAR_BEAM,   SUNNY_DAY),
        MEMBRO(ABSOL,     0, SCOPE_LENS,    SWORDS_DANCE, BITE,         SLASH,        SHADOW_BALL),
    },
    // Ocupação 3: o Mercenário // parte 2 troca
    {
        MEMBRO(GOLEM,     0, HARD_STONE,    EARTHQUAKE,   ROCK_SLIDE,   EXPLOSION,    BRICK_BREAK),
        MEMBRO(CROBAT,    0, SHARP_BEAK,    AERIAL_ACE,   SLUDGE_BOMB,  SHADOW_BALL,  CONFUSE_RAY),
        MEMBRO(ARBOK,     0, POISON_BARB,   SLUDGE_BOMB,  EARTHQUAKE,   CRUNCH,       GLARE),
        MEMBRO(ABSOL,     0, SCOPE_LENS,    SWORDS_DANCE, BITE,         SLASH,        SHADOW_BALL),
        MEMBRO(CRAWDAUNT, 0, SCOPE_LENS,    CRABHAMMER,   CRUNCH,       ICE_BEAM,     SWORDS_DANCE),
        MEMBRO(SHIFTRY,   0, MIRACLE_SEED,  GIGA_DRAIN,   FAINT_ATTACK, EXTRASENSORY, FAKE_OUT),
    },
    // Ocupação 4: o Pesadelo // parte 2 troca
    {
        MEMBRO(HAUNTER,    0, SPELL_TAG,    SHADOW_BALL,  THUNDERBOLT,  HYPNOSIS,     DREAM_EATER),
        MEMBRO(BANETTE,    0, SPELL_TAG,    SHADOW_BALL,  KNOCK_OFF,    THUNDERBOLT,  WILL_O_WISP),
        MEMBRO(MISDREAVUS, 0, LEFTOVERS,    SHADOW_BALL,  PSYCHIC,      THUNDERBOLT,  PAIN_SPLIT),
        MEMBRO(SABLEYE,    0, LEFTOVERS,    SHADOW_BALL,  FAINT_ATTACK, KNOCK_OFF,    CONFUSE_RAY),
        MEMBRO(CROBAT,     0, SHARP_BEAK,   AERIAL_ACE,   SLUDGE_BOMB,  SHADOW_BALL,  CONFUSE_RAY),
        MEMBRO(MUK,        0, LEFTOVERS,    SLUDGE_BOMB,  FIRE_PUNCH,   THUNDER_PUNCH, CURSE),
    },
};

// O chefe de cada ocupação (6º andar, encontro estático sempre shiny e capturável; FamiliaSombra_IniciarChefe):
// nível 62 + 6 por ocupação, 4 golpes e item fixos.
static const struct FamiliaMembro sFamiliaChefes[FAMILIA_OCUPACOES_TOTAL] =
{
    // GENGAR, O DOM: Hipnose põe para dormir e Comedor de Sonhos cobra a conta (a IA só o usa com o alvo dormindo);
    // Bola Sombria é o golpe forte do tipo, e o Raio cobre os tipos Água e Voador. Talismã Fantasma reforça a
    // Bola Sombria.
    MEMBRO(GENGAR,    62, SPELL_TAG,    SHADOW_BALL,  HYPNOSIS,     DREAM_EATER,  THUNDERBOLT),
    // TYRANITAR, O COBRADOR: Dança do Dragão prepara o ataque e a velocidade; Deslize de Pedra e Mastigar com o
    // bônus do tipo, Terremoto para Aço e Fogo. Restos o mantêm de pé enquanto se prepara (a areia não o fere).
    MEMBRO(TYRANITAR, 68, LEFTOVERS,    ROCK_SLIDE,   CRUNCH,       EARTHQUAKE,   DRAGON_DANCE),
    // O Mercenário (terra/dragão) // parte 2 troca (Garchomp é gen 4): Flygon provisório, golpes de terra e dragão.
    MEMBRO(FLYGON,    74, SOFT_SAND,    EARTHQUAKE,   DRAGON_CLAW,  ROCK_SLIDE,   FIRE_BLAST),
    // O Pesadelo (fantasma/psíquico) // parte 2 troca (Darkrai é gen 4): Hypno provisório, o sono e o sonho.
    MEMBRO(HYPNO,     80, TWISTED_SPOON, PSYCHIC,     HYPNOSIS,     DREAM_EATER,  SHADOW_BALL),
};

#undef MEMBRO
