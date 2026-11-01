// GERADO por tools/dexnav/gerar.py; não editar (python3 -I tools/dexnav/gerar.py; o teste roda --conferir)
// DexNav (POK-47): os mapas com encontro do FireRed (um por mapa: a Caverna Mutante tem 9 tabelas e 1 linha),
// nome PT-BR "lugar + andar" e região, na ordem da Pokédex AREA (Kanto, depois Sevii). O índice é o bit de
// "visitado" em gSaveBlock1Ptr->dexNav.visitedMaps: mapa novo no meio da ordem desloca os bits dos saves.

#define DEXNAV_MAPAS_GERADOS 124

static const u8 sDexNavNome_0[] = _("Cidade de Pallet");
static const u8 sDexNavNome_1[] = _("Cidade de Viridian");
static const u8 sDexNavNome_2[] = _("Cidade de Cerulean");
static const u8 sDexNavNome_3[] = _("Cidade Vermilion");
static const u8 sDexNavNome_4[] = _("Cidade de Celadon");
static const u8 sDexNavNome_5[] = _("Cidade de Fuchsia");
static const u8 sDexNavNome_6[] = _("Ilha Cinnabar");
static const u8 sDexNavNome_7[] = _("Rota 1");
static const u8 sDexNavNome_8[] = _("Rota 2");
static const u8 sDexNavNome_9[] = _("Rota 3");
static const u8 sDexNavNome_10[] = _("Rota 4");
static const u8 sDexNavNome_11[] = _("Rota 5");
static const u8 sDexNavNome_12[] = _("Rota 6");
static const u8 sDexNavNome_13[] = _("Rota 7");
static const u8 sDexNavNome_14[] = _("Rota 8");
static const u8 sDexNavNome_15[] = _("Rota 9");
static const u8 sDexNavNome_16[] = _("Rota 10");
static const u8 sDexNavNome_17[] = _("Rota 11");
static const u8 sDexNavNome_18[] = _("Rota 12");
static const u8 sDexNavNome_19[] = _("Rota 13");
static const u8 sDexNavNome_20[] = _("Rota 14");
static const u8 sDexNavNome_21[] = _("Rota 15");
static const u8 sDexNavNome_22[] = _("Rota 16");
static const u8 sDexNavNome_23[] = _("Rota 17");
static const u8 sDexNavNome_24[] = _("Rota 18");
static const u8 sDexNavNome_25[] = _("Rota 19");
static const u8 sDexNavNome_26[] = _("Rota 20");
static const u8 sDexNavNome_27[] = _("Rota 21 Norte");
static const u8 sDexNavNome_28[] = _("Rota 21 Sul");
static const u8 sDexNavNome_29[] = _("Rota 22");
static const u8 sDexNavNome_30[] = _("Rota 23");
static const u8 sDexNavNome_31[] = _("Rota 24");
static const u8 sDexNavNome_32[] = _("Rota 25");
static const u8 sDexNavNome_33[] = _("Floresta Viridian");
static const u8 sDexNavNome_34[] = _("Monte Lua 1F");
static const u8 sDexNavNome_35[] = _("Monte Lua B1F");
static const u8 sDexNavNome_36[] = _("Monte Lua B2F");
static const u8 sDexNavNome_37[] = _("S.S. Anne");
static const u8 sDexNavNome_38[] = _("Caverna do Diglett");
static const u8 sDexNavNome_39[] = _("Estrada da Vitória 1F");
static const u8 sDexNavNome_40[] = _("Estrada da Vitória 2F");
static const u8 sDexNavNome_41[] = _("Estrada da Vitória 3F");
static const u8 sDexNavNome_42[] = _("Mansão Pokémon 1F");
static const u8 sDexNavNome_43[] = _("Mansão Pokémon 2F");
static const u8 sDexNavNome_44[] = _("Mansão Pokémon 3F");
static const u8 sDexNavNome_45[] = _("Mansão Pokémon B1F");
static const u8 sDexNavNome_46[] = _("Zona Safári Centro");
static const u8 sDexNavNome_47[] = _("Zona Safári Leste");
static const u8 sDexNavNome_48[] = _("Zona Safári Norte");
static const u8 sDexNavNome_49[] = _("Zona Safári Oeste");
static const u8 sDexNavNome_50[] = _("Túnel de Pedra 1F");
static const u8 sDexNavNome_51[] = _("Túnel de Pedra B1F");
static const u8 sDexNavNome_52[] = _("Ilhas Seafoam 1F");
static const u8 sDexNavNome_53[] = _("Ilhas Seafoam B1F");
static const u8 sDexNavNome_54[] = _("Ilhas Seafoam B2F");
static const u8 sDexNavNome_55[] = _("Ilhas Seafoam B3F");
static const u8 sDexNavNome_56[] = _("Ilhas Seafoam B4F");
static const u8 sDexNavNome_57[] = _("Torre Pokémon 3F");
static const u8 sDexNavNome_58[] = _("Torre Pokémon 4F");
static const u8 sDexNavNome_59[] = _("Torre Pokémon 5F");
static const u8 sDexNavNome_60[] = _("Torre Pokémon 6F");
static const u8 sDexNavNome_61[] = _("Torre Pokémon 7F");
static const u8 sDexNavNome_62[] = _("Caverna Cerulean 1F");
static const u8 sDexNavNome_63[] = _("Caverna Cerulean 2F");
static const u8 sDexNavNome_64[] = _("Caverna Cerulean B1F");
static const u8 sDexNavNome_65[] = _("Usina Elétrica");
static const u8 sDexNavNome_66[] = _("Estrada Fagulha");
static const u8 sDexNavNome_67[] = _("Praia do Tesouro");
static const u8 sDexNavNome_68[] = _("Ilha Um");
static const u8 sDexNavNome_69[] = _("Monte Brasa");
static const u8 sDexNavNome_70[] = _("M. Brasa Cume 1F");
static const u8 sDexNavNome_71[] = _("M. Brasa Cume 2F");
static const u8 sDexNavNome_72[] = _("M. Brasa Cume 3F");
static const u8 sDexNavNome_73[] = _("M. Brasa Rubi 1F");
static const u8 sDexNavNome_74[] = _("M. Brasa Rubi B1F");
static const u8 sDexNavNome_75[] = _("M. Brasa Rubi B2F");
static const u8 sDexNavNome_76[] = _("M. Brasa Rubi B3F");
static const u8 sDexNavNome_77[] = _("M. Brasa Escada B1F");
static const u8 sDexNavNome_78[] = _("M. Brasa Escada B2F");
static const u8 sDexNavNome_79[] = _("Cabo Extremo");
static const u8 sDexNavNome_80[] = _("Ponte da União");
static const u8 sDexNavNome_81[] = _("Porto da Ilha Três");
static const u8 sDexNavNome_82[] = _("Bosque das Frutas");
static const u8 sDexNavNome_83[] = _("Ilha Quatro");
static const u8 sDexNavNome_84[] = _("Caverna Gélida Entr.");
static const u8 sDexNavNome_85[] = _("Caverna Gélida 1F");
static const u8 sDexNavNome_86[] = _("Caverna Gélida B1F");
static const u8 sDexNavNome_87[] = _("Caverna Gélida Fundo");
static const u8 sDexNavNome_88[] = _("Recanto Esplêndido");
static const u8 sDexNavNome_89[] = _("Labirinto Aquático");
static const u8 sDexNavNome_90[] = _("Prado Ilha Cinco");
static const u8 sDexNavNome_91[] = _("Pilar Memorial");
static const u8 sDexNavNome_92[] = _("Ilha Cinco");
static const u8 sDexNavNome_93[] = _("Caverna Perdida 1");
static const u8 sDexNavNome_94[] = _("Caverna Perdida 2");
static const u8 sDexNavNome_95[] = _("Caverna Perdida 3");
static const u8 sDexNavNome_96[] = _("Caverna Perdida 4");
static const u8 sDexNavNome_97[] = _("Caverna Perdida 5");
static const u8 sDexNavNome_98[] = _("Caverna Perdida 6");
static const u8 sDexNavNome_99[] = _("Caverna Perdida 7");
static const u8 sDexNavNome_100[] = _("Caverna Perdida 8");
static const u8 sDexNavNome_101[] = _("Caverna Perdida 9");
static const u8 sDexNavNome_102[] = _("Caverna Perdida 10");
static const u8 sDexNavNome_103[] = _("Caverna Perdida 11");
static const u8 sDexNavNome_104[] = _("Caverna Perdida 12");
static const u8 sDexNavNome_105[] = _("Caverna Perdida 13");
static const u8 sDexNavNome_106[] = _("Caverna Perdida 14");
static const u8 sDexNavNome_107[] = _("Ilha Proscrita");
static const u8 sDexNavNome_108[] = _("Caminho Verde");
static const u8 sDexNavNome_109[] = _("Caminho da Água");
static const u8 sDexNavNome_110[] = _("Vale das Ruínas");
static const u8 sDexNavNome_111[] = _("Moita Estampada");
static const u8 sDexNavNome_112[] = _("Caverna Mutante");
static const u8 sDexNavNome_113[] = _("Torre do Treinador");
static const u8 sDexNavNome_114[] = _("Entrada do Cânion");
static const u8 sDexNavNome_115[] = _("Cânion Sevault");
static const u8 sDexNavNome_116[] = _("Ruínas de Tanoby");
static const u8 sDexNavNome_117[] = _("Câmara Monean");
static const u8 sDexNavNome_118[] = _("Câmara Liptoo");
static const u8 sDexNavNome_119[] = _("Câmara Weepth");
static const u8 sDexNavNome_120[] = _("Câmara Dilford");
static const u8 sDexNavNome_121[] = _("Câmara Scufib");
static const u8 sDexNavNome_122[] = _("Câmara Rixy");
static const u8 sDexNavNome_123[] = _("Câmara Viapois");

const struct DexNavMap gDexNavMaps[DEXNAV_MAP_COUNT] =
{
    { MAP_GROUP(MAP_PALLET_TOWN), MAP_NUM(MAP_PALLET_TOWN), DEXNAV_REGION_KANTO, sDexNavNome_0 }, // 0
    { MAP_GROUP(MAP_VIRIDIAN_CITY), MAP_NUM(MAP_VIRIDIAN_CITY), DEXNAV_REGION_KANTO, sDexNavNome_1 }, // 1
    { MAP_GROUP(MAP_CERULEAN_CITY), MAP_NUM(MAP_CERULEAN_CITY), DEXNAV_REGION_KANTO, sDexNavNome_2 }, // 2
    { MAP_GROUP(MAP_VERMILION_CITY), MAP_NUM(MAP_VERMILION_CITY), DEXNAV_REGION_KANTO, sDexNavNome_3 }, // 3
    { MAP_GROUP(MAP_CELADON_CITY), MAP_NUM(MAP_CELADON_CITY), DEXNAV_REGION_KANTO, sDexNavNome_4 }, // 4
    { MAP_GROUP(MAP_FUCHSIA_CITY), MAP_NUM(MAP_FUCHSIA_CITY), DEXNAV_REGION_KANTO, sDexNavNome_5 }, // 5
    { MAP_GROUP(MAP_CINNABAR_ISLAND), MAP_NUM(MAP_CINNABAR_ISLAND), DEXNAV_REGION_KANTO, sDexNavNome_6 }, // 6
    { MAP_GROUP(MAP_ROUTE1), MAP_NUM(MAP_ROUTE1), DEXNAV_REGION_KANTO, sDexNavNome_7 }, // 7
    { MAP_GROUP(MAP_ROUTE2), MAP_NUM(MAP_ROUTE2), DEXNAV_REGION_KANTO, sDexNavNome_8 }, // 8
    { MAP_GROUP(MAP_ROUTE3), MAP_NUM(MAP_ROUTE3), DEXNAV_REGION_KANTO, sDexNavNome_9 }, // 9
    { MAP_GROUP(MAP_ROUTE4), MAP_NUM(MAP_ROUTE4), DEXNAV_REGION_KANTO, sDexNavNome_10 }, // 10
    { MAP_GROUP(MAP_ROUTE5), MAP_NUM(MAP_ROUTE5), DEXNAV_REGION_KANTO, sDexNavNome_11 }, // 11
    { MAP_GROUP(MAP_ROUTE6), MAP_NUM(MAP_ROUTE6), DEXNAV_REGION_KANTO, sDexNavNome_12 }, // 12
    { MAP_GROUP(MAP_ROUTE7), MAP_NUM(MAP_ROUTE7), DEXNAV_REGION_KANTO, sDexNavNome_13 }, // 13
    { MAP_GROUP(MAP_ROUTE8), MAP_NUM(MAP_ROUTE8), DEXNAV_REGION_KANTO, sDexNavNome_14 }, // 14
    { MAP_GROUP(MAP_ROUTE9), MAP_NUM(MAP_ROUTE9), DEXNAV_REGION_KANTO, sDexNavNome_15 }, // 15
    { MAP_GROUP(MAP_ROUTE10), MAP_NUM(MAP_ROUTE10), DEXNAV_REGION_KANTO, sDexNavNome_16 }, // 16
    { MAP_GROUP(MAP_ROUTE11), MAP_NUM(MAP_ROUTE11), DEXNAV_REGION_KANTO, sDexNavNome_17 }, // 17
    { MAP_GROUP(MAP_ROUTE12), MAP_NUM(MAP_ROUTE12), DEXNAV_REGION_KANTO, sDexNavNome_18 }, // 18
    { MAP_GROUP(MAP_ROUTE13), MAP_NUM(MAP_ROUTE13), DEXNAV_REGION_KANTO, sDexNavNome_19 }, // 19
    { MAP_GROUP(MAP_ROUTE14), MAP_NUM(MAP_ROUTE14), DEXNAV_REGION_KANTO, sDexNavNome_20 }, // 20
    { MAP_GROUP(MAP_ROUTE15), MAP_NUM(MAP_ROUTE15), DEXNAV_REGION_KANTO, sDexNavNome_21 }, // 21
    { MAP_GROUP(MAP_ROUTE16), MAP_NUM(MAP_ROUTE16), DEXNAV_REGION_KANTO, sDexNavNome_22 }, // 22
    { MAP_GROUP(MAP_ROUTE17), MAP_NUM(MAP_ROUTE17), DEXNAV_REGION_KANTO, sDexNavNome_23 }, // 23
    { MAP_GROUP(MAP_ROUTE18), MAP_NUM(MAP_ROUTE18), DEXNAV_REGION_KANTO, sDexNavNome_24 }, // 24
    { MAP_GROUP(MAP_ROUTE19), MAP_NUM(MAP_ROUTE19), DEXNAV_REGION_KANTO, sDexNavNome_25 }, // 25
    { MAP_GROUP(MAP_ROUTE20), MAP_NUM(MAP_ROUTE20), DEXNAV_REGION_KANTO, sDexNavNome_26 }, // 26
    { MAP_GROUP(MAP_ROUTE21_NORTH), MAP_NUM(MAP_ROUTE21_NORTH), DEXNAV_REGION_KANTO, sDexNavNome_27 }, // 27
    { MAP_GROUP(MAP_ROUTE21_SOUTH), MAP_NUM(MAP_ROUTE21_SOUTH), DEXNAV_REGION_KANTO, sDexNavNome_28 }, // 28
    { MAP_GROUP(MAP_ROUTE22), MAP_NUM(MAP_ROUTE22), DEXNAV_REGION_KANTO, sDexNavNome_29 }, // 29
    { MAP_GROUP(MAP_ROUTE23), MAP_NUM(MAP_ROUTE23), DEXNAV_REGION_KANTO, sDexNavNome_30 }, // 30
    { MAP_GROUP(MAP_ROUTE24), MAP_NUM(MAP_ROUTE24), DEXNAV_REGION_KANTO, sDexNavNome_31 }, // 31
    { MAP_GROUP(MAP_ROUTE25), MAP_NUM(MAP_ROUTE25), DEXNAV_REGION_KANTO, sDexNavNome_32 }, // 32
    { MAP_GROUP(MAP_VIRIDIAN_FOREST), MAP_NUM(MAP_VIRIDIAN_FOREST), DEXNAV_REGION_KANTO, sDexNavNome_33 }, // 33
    { MAP_GROUP(MAP_MT_MOON_1F), MAP_NUM(MAP_MT_MOON_1F), DEXNAV_REGION_KANTO, sDexNavNome_34 }, // 34
    { MAP_GROUP(MAP_MT_MOON_B1F), MAP_NUM(MAP_MT_MOON_B1F), DEXNAV_REGION_KANTO, sDexNavNome_35 }, // 35
    { MAP_GROUP(MAP_MT_MOON_B2F), MAP_NUM(MAP_MT_MOON_B2F), DEXNAV_REGION_KANTO, sDexNavNome_36 }, // 36
    { MAP_GROUP(MAP_SSANNE_EXTERIOR), MAP_NUM(MAP_SSANNE_EXTERIOR), DEXNAV_REGION_KANTO, sDexNavNome_37 }, // 37
    { MAP_GROUP(MAP_DIGLETTS_CAVE_B1F), MAP_NUM(MAP_DIGLETTS_CAVE_B1F), DEXNAV_REGION_KANTO, sDexNavNome_38 }, // 38
    { MAP_GROUP(MAP_VICTORY_ROAD_1F), MAP_NUM(MAP_VICTORY_ROAD_1F), DEXNAV_REGION_KANTO, sDexNavNome_39 }, // 39
    { MAP_GROUP(MAP_VICTORY_ROAD_2F), MAP_NUM(MAP_VICTORY_ROAD_2F), DEXNAV_REGION_KANTO, sDexNavNome_40 }, // 40
    { MAP_GROUP(MAP_VICTORY_ROAD_3F), MAP_NUM(MAP_VICTORY_ROAD_3F), DEXNAV_REGION_KANTO, sDexNavNome_41 }, // 41
    { MAP_GROUP(MAP_POKEMON_MANSION_1F), MAP_NUM(MAP_POKEMON_MANSION_1F), DEXNAV_REGION_KANTO, sDexNavNome_42 }, // 42
    { MAP_GROUP(MAP_POKEMON_MANSION_2F), MAP_NUM(MAP_POKEMON_MANSION_2F), DEXNAV_REGION_KANTO, sDexNavNome_43 }, // 43
    { MAP_GROUP(MAP_POKEMON_MANSION_3F), MAP_NUM(MAP_POKEMON_MANSION_3F), DEXNAV_REGION_KANTO, sDexNavNome_44 }, // 44
    { MAP_GROUP(MAP_POKEMON_MANSION_B1F), MAP_NUM(MAP_POKEMON_MANSION_B1F), DEXNAV_REGION_KANTO, sDexNavNome_45 }, // 45
    { MAP_GROUP(MAP_SAFARI_ZONE_CENTER), MAP_NUM(MAP_SAFARI_ZONE_CENTER), DEXNAV_REGION_KANTO, sDexNavNome_46 }, // 46
    { MAP_GROUP(MAP_SAFARI_ZONE_EAST), MAP_NUM(MAP_SAFARI_ZONE_EAST), DEXNAV_REGION_KANTO, sDexNavNome_47 }, // 47
    { MAP_GROUP(MAP_SAFARI_ZONE_NORTH), MAP_NUM(MAP_SAFARI_ZONE_NORTH), DEXNAV_REGION_KANTO, sDexNavNome_48 }, // 48
    { MAP_GROUP(MAP_SAFARI_ZONE_WEST), MAP_NUM(MAP_SAFARI_ZONE_WEST), DEXNAV_REGION_KANTO, sDexNavNome_49 }, // 49
    { MAP_GROUP(MAP_ROCK_TUNNEL_1F), MAP_NUM(MAP_ROCK_TUNNEL_1F), DEXNAV_REGION_KANTO, sDexNavNome_50 }, // 50
    { MAP_GROUP(MAP_ROCK_TUNNEL_B1F), MAP_NUM(MAP_ROCK_TUNNEL_B1F), DEXNAV_REGION_KANTO, sDexNavNome_51 }, // 51
    { MAP_GROUP(MAP_SEAFOAM_ISLANDS_1F), MAP_NUM(MAP_SEAFOAM_ISLANDS_1F), DEXNAV_REGION_KANTO, sDexNavNome_52 }, // 52
    { MAP_GROUP(MAP_SEAFOAM_ISLANDS_B1F), MAP_NUM(MAP_SEAFOAM_ISLANDS_B1F), DEXNAV_REGION_KANTO, sDexNavNome_53 }, // 53
    { MAP_GROUP(MAP_SEAFOAM_ISLANDS_B2F), MAP_NUM(MAP_SEAFOAM_ISLANDS_B2F), DEXNAV_REGION_KANTO, sDexNavNome_54 }, // 54
    { MAP_GROUP(MAP_SEAFOAM_ISLANDS_B3F), MAP_NUM(MAP_SEAFOAM_ISLANDS_B3F), DEXNAV_REGION_KANTO, sDexNavNome_55 }, // 55
    { MAP_GROUP(MAP_SEAFOAM_ISLANDS_B4F), MAP_NUM(MAP_SEAFOAM_ISLANDS_B4F), DEXNAV_REGION_KANTO, sDexNavNome_56 }, // 56
    { MAP_GROUP(MAP_POKEMON_TOWER_3F), MAP_NUM(MAP_POKEMON_TOWER_3F), DEXNAV_REGION_KANTO, sDexNavNome_57 }, // 57
    { MAP_GROUP(MAP_POKEMON_TOWER_4F), MAP_NUM(MAP_POKEMON_TOWER_4F), DEXNAV_REGION_KANTO, sDexNavNome_58 }, // 58
    { MAP_GROUP(MAP_POKEMON_TOWER_5F), MAP_NUM(MAP_POKEMON_TOWER_5F), DEXNAV_REGION_KANTO, sDexNavNome_59 }, // 59
    { MAP_GROUP(MAP_POKEMON_TOWER_6F), MAP_NUM(MAP_POKEMON_TOWER_6F), DEXNAV_REGION_KANTO, sDexNavNome_60 }, // 60
    { MAP_GROUP(MAP_POKEMON_TOWER_7F), MAP_NUM(MAP_POKEMON_TOWER_7F), DEXNAV_REGION_KANTO, sDexNavNome_61 }, // 61
    { MAP_GROUP(MAP_CERULEAN_CAVE_1F), MAP_NUM(MAP_CERULEAN_CAVE_1F), DEXNAV_REGION_KANTO, sDexNavNome_62 }, // 62
    { MAP_GROUP(MAP_CERULEAN_CAVE_2F), MAP_NUM(MAP_CERULEAN_CAVE_2F), DEXNAV_REGION_KANTO, sDexNavNome_63 }, // 63
    { MAP_GROUP(MAP_CERULEAN_CAVE_B1F), MAP_NUM(MAP_CERULEAN_CAVE_B1F), DEXNAV_REGION_KANTO, sDexNavNome_64 }, // 64
    { MAP_GROUP(MAP_POWER_PLANT), MAP_NUM(MAP_POWER_PLANT), DEXNAV_REGION_KANTO, sDexNavNome_65 }, // 65
    { MAP_GROUP(MAP_ONE_ISLAND_KINDLE_ROAD), MAP_NUM(MAP_ONE_ISLAND_KINDLE_ROAD), DEXNAV_REGION_SEVII, sDexNavNome_66 }, // 66
    { MAP_GROUP(MAP_ONE_ISLAND_TREASURE_BEACH), MAP_NUM(MAP_ONE_ISLAND_TREASURE_BEACH), DEXNAV_REGION_SEVII, sDexNavNome_67 }, // 67
    { MAP_GROUP(MAP_ONE_ISLAND), MAP_NUM(MAP_ONE_ISLAND), DEXNAV_REGION_SEVII, sDexNavNome_68 }, // 68
    { MAP_GROUP(MAP_MT_EMBER_EXTERIOR), MAP_NUM(MAP_MT_EMBER_EXTERIOR), DEXNAV_REGION_SEVII, sDexNavNome_69 }, // 69
    { MAP_GROUP(MAP_MT_EMBER_SUMMIT_PATH_1F), MAP_NUM(MAP_MT_EMBER_SUMMIT_PATH_1F), DEXNAV_REGION_SEVII, sDexNavNome_70 }, // 70
    { MAP_GROUP(MAP_MT_EMBER_SUMMIT_PATH_2F), MAP_NUM(MAP_MT_EMBER_SUMMIT_PATH_2F), DEXNAV_REGION_SEVII, sDexNavNome_71 }, // 71
    { MAP_GROUP(MAP_MT_EMBER_SUMMIT_PATH_3F), MAP_NUM(MAP_MT_EMBER_SUMMIT_PATH_3F), DEXNAV_REGION_SEVII, sDexNavNome_72 }, // 72
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_1F), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_1F), DEXNAV_REGION_SEVII, sDexNavNome_73 }, // 73
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_B1F), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_B1F), DEXNAV_REGION_SEVII, sDexNavNome_74 }, // 74
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_B2F), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_B2F), DEXNAV_REGION_SEVII, sDexNavNome_75 }, // 75
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_B3F), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_B3F), DEXNAV_REGION_SEVII, sDexNavNome_76 }, // 76
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_B1F_STAIRS), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_B1F_STAIRS), DEXNAV_REGION_SEVII, sDexNavNome_77 }, // 77
    { MAP_GROUP(MAP_MT_EMBER_RUBY_PATH_B2F_STAIRS), MAP_NUM(MAP_MT_EMBER_RUBY_PATH_B2F_STAIRS), DEXNAV_REGION_SEVII, sDexNavNome_78 }, // 78
    { MAP_GROUP(MAP_TWO_ISLAND_CAPE_BRINK), MAP_NUM(MAP_TWO_ISLAND_CAPE_BRINK), DEXNAV_REGION_SEVII, sDexNavNome_79 }, // 79
    { MAP_GROUP(MAP_THREE_ISLAND_BOND_BRIDGE), MAP_NUM(MAP_THREE_ISLAND_BOND_BRIDGE), DEXNAV_REGION_SEVII, sDexNavNome_80 }, // 80
    { MAP_GROUP(MAP_THREE_ISLAND_PORT), MAP_NUM(MAP_THREE_ISLAND_PORT), DEXNAV_REGION_SEVII, sDexNavNome_81 }, // 81
    { MAP_GROUP(MAP_THREE_ISLAND_BERRY_FOREST), MAP_NUM(MAP_THREE_ISLAND_BERRY_FOREST), DEXNAV_REGION_SEVII, sDexNavNome_82 }, // 82
    { MAP_GROUP(MAP_FOUR_ISLAND), MAP_NUM(MAP_FOUR_ISLAND), DEXNAV_REGION_SEVII, sDexNavNome_83 }, // 83
    { MAP_GROUP(MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE), MAP_NUM(MAP_FOUR_ISLAND_ICEFALL_CAVE_ENTRANCE), DEXNAV_REGION_SEVII, sDexNavNome_84 }, // 84
    { MAP_GROUP(MAP_FOUR_ISLAND_ICEFALL_CAVE_1F), MAP_NUM(MAP_FOUR_ISLAND_ICEFALL_CAVE_1F), DEXNAV_REGION_SEVII, sDexNavNome_85 }, // 85
    { MAP_GROUP(MAP_FOUR_ISLAND_ICEFALL_CAVE_B1F), MAP_NUM(MAP_FOUR_ISLAND_ICEFALL_CAVE_B1F), DEXNAV_REGION_SEVII, sDexNavNome_86 }, // 86
    { MAP_GROUP(MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK), MAP_NUM(MAP_FOUR_ISLAND_ICEFALL_CAVE_BACK), DEXNAV_REGION_SEVII, sDexNavNome_87 }, // 87
    { MAP_GROUP(MAP_FIVE_ISLAND_RESORT_GORGEOUS), MAP_NUM(MAP_FIVE_ISLAND_RESORT_GORGEOUS), DEXNAV_REGION_SEVII, sDexNavNome_88 }, // 88
    { MAP_GROUP(MAP_FIVE_ISLAND_WATER_LABYRINTH), MAP_NUM(MAP_FIVE_ISLAND_WATER_LABYRINTH), DEXNAV_REGION_SEVII, sDexNavNome_89 }, // 89
    { MAP_GROUP(MAP_FIVE_ISLAND_MEADOW), MAP_NUM(MAP_FIVE_ISLAND_MEADOW), DEXNAV_REGION_SEVII, sDexNavNome_90 }, // 90
    { MAP_GROUP(MAP_FIVE_ISLAND_MEMORIAL_PILLAR), MAP_NUM(MAP_FIVE_ISLAND_MEMORIAL_PILLAR), DEXNAV_REGION_SEVII, sDexNavNome_91 }, // 91
    { MAP_GROUP(MAP_FIVE_ISLAND), MAP_NUM(MAP_FIVE_ISLAND), DEXNAV_REGION_SEVII, sDexNavNome_92 }, // 92
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM1), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM1), DEXNAV_REGION_SEVII, sDexNavNome_93 }, // 93
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM2), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM2), DEXNAV_REGION_SEVII, sDexNavNome_94 }, // 94
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM3), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM3), DEXNAV_REGION_SEVII, sDexNavNome_95 }, // 95
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM4), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM4), DEXNAV_REGION_SEVII, sDexNavNome_96 }, // 96
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM5), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM5), DEXNAV_REGION_SEVII, sDexNavNome_97 }, // 97
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM6), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM6), DEXNAV_REGION_SEVII, sDexNavNome_98 }, // 98
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM7), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM7), DEXNAV_REGION_SEVII, sDexNavNome_99 }, // 99
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM8), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM8), DEXNAV_REGION_SEVII, sDexNavNome_100 }, // 100
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM9), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM9), DEXNAV_REGION_SEVII, sDexNavNome_101 }, // 101
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM10), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM10), DEXNAV_REGION_SEVII, sDexNavNome_102 }, // 102
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM11), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM11), DEXNAV_REGION_SEVII, sDexNavNome_103 }, // 103
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM12), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM12), DEXNAV_REGION_SEVII, sDexNavNome_104 }, // 104
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM13), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM13), DEXNAV_REGION_SEVII, sDexNavNome_105 }, // 105
    { MAP_GROUP(MAP_FIVE_ISLAND_LOST_CAVE_ROOM14), MAP_NUM(MAP_FIVE_ISLAND_LOST_CAVE_ROOM14), DEXNAV_REGION_SEVII, sDexNavNome_106 }, // 106
    { MAP_GROUP(MAP_SIX_ISLAND_OUTCAST_ISLAND), MAP_NUM(MAP_SIX_ISLAND_OUTCAST_ISLAND), DEXNAV_REGION_SEVII, sDexNavNome_107 }, // 107
    { MAP_GROUP(MAP_SIX_ISLAND_GREEN_PATH), MAP_NUM(MAP_SIX_ISLAND_GREEN_PATH), DEXNAV_REGION_SEVII, sDexNavNome_108 }, // 108
    { MAP_GROUP(MAP_SIX_ISLAND_WATER_PATH), MAP_NUM(MAP_SIX_ISLAND_WATER_PATH), DEXNAV_REGION_SEVII, sDexNavNome_109 }, // 109
    { MAP_GROUP(MAP_SIX_ISLAND_RUIN_VALLEY), MAP_NUM(MAP_SIX_ISLAND_RUIN_VALLEY), DEXNAV_REGION_SEVII, sDexNavNome_110 }, // 110
    { MAP_GROUP(MAP_SIX_ISLAND_PATTERN_BUSH), MAP_NUM(MAP_SIX_ISLAND_PATTERN_BUSH), DEXNAV_REGION_SEVII, sDexNavNome_111 }, // 111
    { MAP_GROUP(MAP_SIX_ISLAND_ALTERING_CAVE), MAP_NUM(MAP_SIX_ISLAND_ALTERING_CAVE), DEXNAV_REGION_SEVII, sDexNavNome_112 }, // 112
    { MAP_GROUP(MAP_SEVEN_ISLAND_TRAINER_TOWER), MAP_NUM(MAP_SEVEN_ISLAND_TRAINER_TOWER), DEXNAV_REGION_SEVII, sDexNavNome_113 }, // 113
    { MAP_GROUP(MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE), MAP_NUM(MAP_SEVEN_ISLAND_SEVAULT_CANYON_ENTRANCE), DEXNAV_REGION_SEVII, sDexNavNome_114 }, // 114
    { MAP_GROUP(MAP_SEVEN_ISLAND_SEVAULT_CANYON), MAP_NUM(MAP_SEVEN_ISLAND_SEVAULT_CANYON), DEXNAV_REGION_SEVII, sDexNavNome_115 }, // 115
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS), DEXNAV_REGION_SEVII, sDexNavNome_116 }, // 116
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_MONEAN_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_117 }, // 117
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_LIPTOO_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_LIPTOO_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_118 }, // 118
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_WEEPTH_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_WEEPTH_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_119 }, // 119
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_DILFORD_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_120 }, // 120
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_SCUFIB_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_SCUFIB_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_121 }, // 121
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_RIXY_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_RIXY_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_122 }, // 122
    { MAP_GROUP(MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER), MAP_NUM(MAP_SEVEN_ISLAND_TANOBY_RUINS_VIAPOIS_CHAMBER), DEXNAV_REGION_SEVII, sDexNavNome_123 }, // 123
};
