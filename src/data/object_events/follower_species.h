// Gerado por tools/seguidores/converter.py a partir do pacote HGSS do Veekun; não editar à mão.
// Uma entrada por espécie, indexada pelo número da Pokédex nacional - 1: folha de 8 quadros (sul, norte, oeste,
// leste; 2 cada) de 32x32, ou 64x64 nos grandes (`large`), paleta normal e paleta shiny com o mesmo mapeamento
// de índices. Variantes: fêmea (`female`) e as 28 letras do Unown (`forms`, ordem de GetUnownLetterByPersonality).

static const u16 sFollowerPic_Bulbasaur[] = INCBIN_U16("graphics/object_events/pics/seguidores/bulbasaur.4bpp");
static const u16 sFollowerPal_Bulbasaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bulbasaur.gbapal");
static const u16 sFollowerPalShiny_Bulbasaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bulbasaur_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Bulbasaur[] = {
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 0),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 1),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 2),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 3),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 4),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 5),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 6),
    overworld_frame(sFollowerPic_Bulbasaur, 4, 4, 7),
};

static const u16 sFollowerPic_Ivysaur[] = INCBIN_U16("graphics/object_events/pics/seguidores/ivysaur.4bpp");
static const u16 sFollowerPal_Ivysaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ivysaur.gbapal");
static const u16 sFollowerPalShiny_Ivysaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ivysaur_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ivysaur[] = {
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 0),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 1),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 2),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 3),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 4),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 5),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 6),
    overworld_frame(sFollowerPic_Ivysaur, 4, 4, 7),
};

static const u16 sFollowerPic_Venusaur[] = INCBIN_U16("graphics/object_events/pics/seguidores/venusaur.4bpp");
static const u16 sFollowerPal_Venusaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venusaur.gbapal");
static const u16 sFollowerPalShiny_Venusaur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venusaur_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Venusaur[] = {
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 0),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 1),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 2),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 3),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 4),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 5),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 6),
    overworld_frame(sFollowerPic_Venusaur, 4, 4, 7),
};

static const u16 sFollowerPic_Venusaur_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/venusaur_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_Venusaur_F[] = {
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 0),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 1),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 2),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 3),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 4),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 5),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 6),
    overworld_frame(sFollowerPic_Venusaur_F, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerFemale_Venusaur = {
    .species = SPECIES_VENUSAUR,
    .large = FALSE,
    .formCount = 0,
    .images = sFollowerPicTable_Venusaur_F,
    .palette = sFollowerPal_Venusaur,
    .shinyPalette = sFollowerPalShiny_Venusaur,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Charmander[] = INCBIN_U16("graphics/object_events/pics/seguidores/charmander.4bpp");
static const u16 sFollowerPal_Charmander[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charmander.gbapal");
static const u16 sFollowerPalShiny_Charmander[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charmander_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Charmander[] = {
    overworld_frame(sFollowerPic_Charmander, 4, 4, 0),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 1),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 2),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 3),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 4),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 5),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 6),
    overworld_frame(sFollowerPic_Charmander, 4, 4, 7),
};

static const u16 sFollowerPic_Charmeleon[] = INCBIN_U16("graphics/object_events/pics/seguidores/charmeleon.4bpp");
static const u16 sFollowerPal_Charmeleon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charmeleon.gbapal");
static const u16 sFollowerPalShiny_Charmeleon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charmeleon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Charmeleon[] = {
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 0),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 1),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 2),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 3),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 4),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 5),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 6),
    overworld_frame(sFollowerPic_Charmeleon, 4, 4, 7),
};

static const u16 sFollowerPic_Charizard[] = INCBIN_U16("graphics/object_events/pics/seguidores/charizard.4bpp");
static const u16 sFollowerPal_Charizard[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charizard.gbapal");
static const u16 sFollowerPalShiny_Charizard[] = INCBIN_U16("graphics/object_events/palettes/seguidores/charizard_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Charizard[] = {
    overworld_frame(sFollowerPic_Charizard, 4, 4, 0),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 1),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 2),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 3),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 4),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 5),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 6),
    overworld_frame(sFollowerPic_Charizard, 4, 4, 7),
};

static const u16 sFollowerPic_Squirtle[] = INCBIN_U16("graphics/object_events/pics/seguidores/squirtle.4bpp");
static const u16 sFollowerPal_Squirtle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/squirtle.gbapal");
static const u16 sFollowerPalShiny_Squirtle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/squirtle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Squirtle[] = {
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 0),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 1),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 2),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 3),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 4),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 5),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 6),
    overworld_frame(sFollowerPic_Squirtle, 4, 4, 7),
};

static const u16 sFollowerPic_Wartortle[] = INCBIN_U16("graphics/object_events/pics/seguidores/wartortle.4bpp");
static const u16 sFollowerPal_Wartortle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wartortle.gbapal");
static const u16 sFollowerPalShiny_Wartortle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wartortle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wartortle[] = {
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 0),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 1),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 2),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 3),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 4),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 5),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 6),
    overworld_frame(sFollowerPic_Wartortle, 4, 4, 7),
};

static const u16 sFollowerPic_Blastoise[] = INCBIN_U16("graphics/object_events/pics/seguidores/blastoise.4bpp");
static const u16 sFollowerPal_Blastoise[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blastoise.gbapal");
static const u16 sFollowerPalShiny_Blastoise[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blastoise_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Blastoise[] = {
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 0),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 1),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 2),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 3),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 4),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 5),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 6),
    overworld_frame(sFollowerPic_Blastoise, 4, 4, 7),
};

static const u16 sFollowerPic_Caterpie[] = INCBIN_U16("graphics/object_events/pics/seguidores/caterpie.4bpp");
static const u16 sFollowerPal_Caterpie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/caterpie.gbapal");
static const u16 sFollowerPalShiny_Caterpie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/caterpie_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Caterpie[] = {
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 0),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 1),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 2),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 3),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 4),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 5),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 6),
    overworld_frame(sFollowerPic_Caterpie, 4, 4, 7),
};

static const u16 sFollowerPic_Metapod[] = INCBIN_U16("graphics/object_events/pics/seguidores/metapod.4bpp");
static const u16 sFollowerPal_Metapod[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metapod.gbapal");
static const u16 sFollowerPalShiny_Metapod[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metapod_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Metapod[] = {
    overworld_frame(sFollowerPic_Metapod, 4, 4, 0),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 1),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 2),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 3),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 4),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 5),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 6),
    overworld_frame(sFollowerPic_Metapod, 4, 4, 7),
};

static const u16 sFollowerPic_Butterfree[] = INCBIN_U16("graphics/object_events/pics/seguidores/butterfree.4bpp");
static const u16 sFollowerPal_Butterfree[] = INCBIN_U16("graphics/object_events/palettes/seguidores/butterfree.gbapal");
static const u16 sFollowerPalShiny_Butterfree[] = INCBIN_U16("graphics/object_events/palettes/seguidores/butterfree_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Butterfree[] = {
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 0),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 1),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 2),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 3),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 4),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 5),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 6),
    overworld_frame(sFollowerPic_Butterfree, 4, 4, 7),
};

static const u16 sFollowerPic_Weedle[] = INCBIN_U16("graphics/object_events/pics/seguidores/weedle.4bpp");
static const u16 sFollowerPal_Weedle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weedle.gbapal");
static const u16 sFollowerPalShiny_Weedle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weedle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Weedle[] = {
    overworld_frame(sFollowerPic_Weedle, 4, 4, 0),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 1),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 2),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 3),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 4),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 5),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 6),
    overworld_frame(sFollowerPic_Weedle, 4, 4, 7),
};

static const u16 sFollowerPic_Kakuna[] = INCBIN_U16("graphics/object_events/pics/seguidores/kakuna.4bpp");
static const u16 sFollowerPal_Kakuna[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kakuna.gbapal");
static const u16 sFollowerPalShiny_Kakuna[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kakuna_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kakuna[] = {
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 0),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 1),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 2),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 3),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 4),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 5),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 6),
    overworld_frame(sFollowerPic_Kakuna, 4, 4, 7),
};

static const u16 sFollowerPic_Beedrill[] = INCBIN_U16("graphics/object_events/pics/seguidores/beedrill.4bpp");
static const u16 sFollowerPal_Beedrill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beedrill.gbapal");
static const u16 sFollowerPalShiny_Beedrill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beedrill_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Beedrill[] = {
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 0),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 1),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 2),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 3),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 4),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 5),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 6),
    overworld_frame(sFollowerPic_Beedrill, 4, 4, 7),
};

static const u16 sFollowerPic_Pidgey[] = INCBIN_U16("graphics/object_events/pics/seguidores/pidgey.4bpp");
static const u16 sFollowerPal_Pidgey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgey.gbapal");
static const u16 sFollowerPalShiny_Pidgey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgey_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pidgey[] = {
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 0),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 1),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 2),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 3),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 4),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 5),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 6),
    overworld_frame(sFollowerPic_Pidgey, 4, 4, 7),
};

static const u16 sFollowerPic_Pidgeotto[] = INCBIN_U16("graphics/object_events/pics/seguidores/pidgeotto.4bpp");
static const u16 sFollowerPal_Pidgeotto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgeotto.gbapal");
static const u16 sFollowerPalShiny_Pidgeotto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgeotto_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pidgeotto[] = {
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 0),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 1),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 2),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 3),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 4),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 5),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 6),
    overworld_frame(sFollowerPic_Pidgeotto, 4, 4, 7),
};

static const u16 sFollowerPic_Pidgeot[] = INCBIN_U16("graphics/object_events/pics/seguidores/pidgeot.4bpp");
static const u16 sFollowerPal_Pidgeot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgeot.gbapal");
static const u16 sFollowerPalShiny_Pidgeot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pidgeot_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pidgeot[] = {
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 0),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 1),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 2),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 3),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 4),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 5),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 6),
    overworld_frame(sFollowerPic_Pidgeot, 4, 4, 7),
};

static const u16 sFollowerPic_Rattata[] = INCBIN_U16("graphics/object_events/pics/seguidores/rattata.4bpp");
static const u16 sFollowerPal_Rattata[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rattata.gbapal");
static const u16 sFollowerPalShiny_Rattata[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rattata_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Rattata[] = {
    overworld_frame(sFollowerPic_Rattata, 4, 4, 0),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 1),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 2),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 3),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 4),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 5),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 6),
    overworld_frame(sFollowerPic_Rattata, 4, 4, 7),
};

static const u16 sFollowerPic_Raticate[] = INCBIN_U16("graphics/object_events/pics/seguidores/raticate.4bpp");
static const u16 sFollowerPal_Raticate[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raticate.gbapal");
static const u16 sFollowerPalShiny_Raticate[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raticate_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Raticate[] = {
    overworld_frame(sFollowerPic_Raticate, 4, 4, 0),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 1),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 2),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 3),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 4),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 5),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 6),
    overworld_frame(sFollowerPic_Raticate, 4, 4, 7),
};

static const u16 sFollowerPic_Spearow[] = INCBIN_U16("graphics/object_events/pics/seguidores/spearow.4bpp");
static const u16 sFollowerPal_Spearow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spearow.gbapal");
static const u16 sFollowerPalShiny_Spearow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spearow_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Spearow[] = {
    overworld_frame(sFollowerPic_Spearow, 4, 4, 0),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 1),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 2),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 3),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 4),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 5),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 6),
    overworld_frame(sFollowerPic_Spearow, 4, 4, 7),
};

static const u16 sFollowerPic_Fearow[] = INCBIN_U16("graphics/object_events/pics/seguidores/fearow.4bpp");
static const u16 sFollowerPal_Fearow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/fearow.gbapal");
static const u16 sFollowerPalShiny_Fearow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/fearow_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Fearow[] = {
    overworld_frame(sFollowerPic_Fearow, 4, 4, 0),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 1),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 2),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 3),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 4),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 5),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 6),
    overworld_frame(sFollowerPic_Fearow, 4, 4, 7),
};

static const u16 sFollowerPic_Ekans[] = INCBIN_U16("graphics/object_events/pics/seguidores/ekans.4bpp");
static const u16 sFollowerPal_Ekans[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ekans.gbapal");
static const u16 sFollowerPalShiny_Ekans[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ekans_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ekans[] = {
    overworld_frame(sFollowerPic_Ekans, 4, 4, 0),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 1),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 2),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 3),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 4),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 5),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 6),
    overworld_frame(sFollowerPic_Ekans, 4, 4, 7),
};

static const u16 sFollowerPic_Arbok[] = INCBIN_U16("graphics/object_events/pics/seguidores/arbok.4bpp");
static const u16 sFollowerPal_Arbok[] = INCBIN_U16("graphics/object_events/palettes/seguidores/arbok.gbapal");
static const u16 sFollowerPalShiny_Arbok[] = INCBIN_U16("graphics/object_events/palettes/seguidores/arbok_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Arbok[] = {
    overworld_frame(sFollowerPic_Arbok, 4, 4, 0),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 1),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 2),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 3),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 4),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 5),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 6),
    overworld_frame(sFollowerPic_Arbok, 4, 4, 7),
};

static const u16 sFollowerPic_Pikachu[] = INCBIN_U16("graphics/object_events/pics/seguidores/pikachu.4bpp");
static const u16 sFollowerPal_Pikachu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pikachu.gbapal");
static const u16 sFollowerPalShiny_Pikachu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pikachu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pikachu[] = {
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 0),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 1),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 2),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 3),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 4),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 5),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 6),
    overworld_frame(sFollowerPic_Pikachu, 4, 4, 7),
};

static const u16 sFollowerPic_Pikachu_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/pikachu_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_Pikachu_F[] = {
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 0),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 1),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 2),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 3),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 4),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 5),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 6),
    overworld_frame(sFollowerPic_Pikachu_F, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerFemale_Pikachu = {
    .species = SPECIES_PIKACHU,
    .large = FALSE,
    .formCount = 0,
    .images = sFollowerPicTable_Pikachu_F,
    .palette = sFollowerPal_Pikachu,
    .shinyPalette = sFollowerPalShiny_Pikachu,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Raichu[] = INCBIN_U16("graphics/object_events/pics/seguidores/raichu.4bpp");
static const u16 sFollowerPal_Raichu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raichu.gbapal");
static const u16 sFollowerPalShiny_Raichu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raichu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Raichu[] = {
    overworld_frame(sFollowerPic_Raichu, 4, 4, 0),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 1),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 2),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 3),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 4),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 5),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 6),
    overworld_frame(sFollowerPic_Raichu, 4, 4, 7),
};

static const u16 sFollowerPic_Sandshrew[] = INCBIN_U16("graphics/object_events/pics/seguidores/sandshrew.4bpp");
static const u16 sFollowerPal_Sandshrew[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sandshrew.gbapal");
static const u16 sFollowerPalShiny_Sandshrew[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sandshrew_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sandshrew[] = {
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 0),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 1),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 2),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 3),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 4),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 5),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 6),
    overworld_frame(sFollowerPic_Sandshrew, 4, 4, 7),
};

static const u16 sFollowerPic_Sandslash[] = INCBIN_U16("graphics/object_events/pics/seguidores/sandslash.4bpp");
static const u16 sFollowerPal_Sandslash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sandslash.gbapal");
static const u16 sFollowerPalShiny_Sandslash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sandslash_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sandslash[] = {
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 0),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 1),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 2),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 3),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 4),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 5),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 6),
    overworld_frame(sFollowerPic_Sandslash, 4, 4, 7),
};

static const u16 sFollowerPic_NidoranF[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidoran_f.4bpp");
static const u16 sFollowerPal_NidoranF[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoran_f.gbapal");
static const u16 sFollowerPalShiny_NidoranF[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoran_f_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_NidoranF[] = {
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 0),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 1),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 2),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 3),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 4),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 5),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 6),
    overworld_frame(sFollowerPic_NidoranF, 4, 4, 7),
};

static const u16 sFollowerPic_Nidorina[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidorina.4bpp");
static const u16 sFollowerPal_Nidorina[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidorina.gbapal");
static const u16 sFollowerPalShiny_Nidorina[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidorina_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nidorina[] = {
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 0),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 1),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 2),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 3),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 4),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 5),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 6),
    overworld_frame(sFollowerPic_Nidorina, 4, 4, 7),
};

static const u16 sFollowerPic_Nidoqueen[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidoqueen.4bpp");
static const u16 sFollowerPal_Nidoqueen[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoqueen.gbapal");
static const u16 sFollowerPalShiny_Nidoqueen[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoqueen_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nidoqueen[] = {
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 0),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 1),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 2),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 3),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 4),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 5),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 6),
    overworld_frame(sFollowerPic_Nidoqueen, 4, 4, 7),
};

static const u16 sFollowerPic_NidoranM[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidoran_m.4bpp");
static const u16 sFollowerPal_NidoranM[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoran_m.gbapal");
static const u16 sFollowerPalShiny_NidoranM[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoran_m_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_NidoranM[] = {
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 0),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 1),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 2),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 3),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 4),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 5),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 6),
    overworld_frame(sFollowerPic_NidoranM, 4, 4, 7),
};

static const u16 sFollowerPic_Nidorino[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidorino.4bpp");
static const u16 sFollowerPal_Nidorino[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidorino.gbapal");
static const u16 sFollowerPalShiny_Nidorino[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidorino_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nidorino[] = {
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 0),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 1),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 2),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 3),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 4),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 5),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 6),
    overworld_frame(sFollowerPic_Nidorino, 4, 4, 7),
};

static const u16 sFollowerPic_Nidoking[] = INCBIN_U16("graphics/object_events/pics/seguidores/nidoking.4bpp");
static const u16 sFollowerPal_Nidoking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoking.gbapal");
static const u16 sFollowerPalShiny_Nidoking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nidoking_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nidoking[] = {
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 0),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 1),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 2),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 3),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 4),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 5),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 6),
    overworld_frame(sFollowerPic_Nidoking, 4, 4, 7),
};

static const u16 sFollowerPic_Clefairy[] = INCBIN_U16("graphics/object_events/pics/seguidores/clefairy.4bpp");
static const u16 sFollowerPal_Clefairy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clefairy.gbapal");
static const u16 sFollowerPalShiny_Clefairy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clefairy_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Clefairy[] = {
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 0),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 1),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 2),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 3),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 4),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 5),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 6),
    overworld_frame(sFollowerPic_Clefairy, 4, 4, 7),
};

static const u16 sFollowerPic_Clefable[] = INCBIN_U16("graphics/object_events/pics/seguidores/clefable.4bpp");
static const u16 sFollowerPal_Clefable[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clefable.gbapal");
static const u16 sFollowerPalShiny_Clefable[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clefable_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Clefable[] = {
    overworld_frame(sFollowerPic_Clefable, 4, 4, 0),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 1),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 2),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 3),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 4),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 5),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 6),
    overworld_frame(sFollowerPic_Clefable, 4, 4, 7),
};

static const u16 sFollowerPic_Vulpix[] = INCBIN_U16("graphics/object_events/pics/seguidores/vulpix.4bpp");
static const u16 sFollowerPal_Vulpix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vulpix.gbapal");
static const u16 sFollowerPalShiny_Vulpix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vulpix_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Vulpix[] = {
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 0),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 1),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 2),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 3),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 4),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 5),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 6),
    overworld_frame(sFollowerPic_Vulpix, 4, 4, 7),
};

static const u16 sFollowerPic_Ninetales[] = INCBIN_U16("graphics/object_events/pics/seguidores/ninetales.4bpp");
static const u16 sFollowerPal_Ninetales[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ninetales.gbapal");
static const u16 sFollowerPalShiny_Ninetales[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ninetales_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ninetales[] = {
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 0),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 1),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 2),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 3),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 4),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 5),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 6),
    overworld_frame(sFollowerPic_Ninetales, 4, 4, 7),
};

static const u16 sFollowerPic_Jigglypuff[] = INCBIN_U16("graphics/object_events/pics/seguidores/jigglypuff.4bpp");
static const u16 sFollowerPal_Jigglypuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jigglypuff.gbapal");
static const u16 sFollowerPalShiny_Jigglypuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jigglypuff_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Jigglypuff[] = {
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 0),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 1),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 2),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 3),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 4),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 5),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 6),
    overworld_frame(sFollowerPic_Jigglypuff, 4, 4, 7),
};

static const u16 sFollowerPic_Wigglytuff[] = INCBIN_U16("graphics/object_events/pics/seguidores/wigglytuff.4bpp");
static const u16 sFollowerPal_Wigglytuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wigglytuff.gbapal");
static const u16 sFollowerPalShiny_Wigglytuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wigglytuff_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wigglytuff[] = {
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 0),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 1),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 2),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 3),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 4),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 5),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 6),
    overworld_frame(sFollowerPic_Wigglytuff, 4, 4, 7),
};

static const u16 sFollowerPic_Zubat[] = INCBIN_U16("graphics/object_events/pics/seguidores/zubat.4bpp");
static const u16 sFollowerPal_Zubat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zubat.gbapal");
static const u16 sFollowerPalShiny_Zubat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zubat_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Zubat[] = {
    overworld_frame(sFollowerPic_Zubat, 4, 4, 0),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 1),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 2),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 3),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 4),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 5),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 6),
    overworld_frame(sFollowerPic_Zubat, 4, 4, 7),
};

static const u16 sFollowerPic_Golbat[] = INCBIN_U16("graphics/object_events/pics/seguidores/golbat.4bpp");
static const u16 sFollowerPal_Golbat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golbat.gbapal");
static const u16 sFollowerPalShiny_Golbat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golbat_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Golbat[] = {
    overworld_frame(sFollowerPic_Golbat, 4, 4, 0),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 1),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 2),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 3),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 4),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 5),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 6),
    overworld_frame(sFollowerPic_Golbat, 4, 4, 7),
};

static const u16 sFollowerPic_Oddish[] = INCBIN_U16("graphics/object_events/pics/seguidores/oddish.4bpp");
static const u16 sFollowerPal_Oddish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/oddish.gbapal");
static const u16 sFollowerPalShiny_Oddish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/oddish_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Oddish[] = {
    overworld_frame(sFollowerPic_Oddish, 4, 4, 0),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 1),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 2),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 3),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 4),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 5),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 6),
    overworld_frame(sFollowerPic_Oddish, 4, 4, 7),
};

static const u16 sFollowerPic_Gloom[] = INCBIN_U16("graphics/object_events/pics/seguidores/gloom.4bpp");
static const u16 sFollowerPal_Gloom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gloom.gbapal");
static const u16 sFollowerPalShiny_Gloom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gloom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gloom[] = {
    overworld_frame(sFollowerPic_Gloom, 4, 4, 0),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 1),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 2),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 3),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 4),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 5),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 6),
    overworld_frame(sFollowerPic_Gloom, 4, 4, 7),
};

static const u16 sFollowerPic_Vileplume[] = INCBIN_U16("graphics/object_events/pics/seguidores/vileplume.4bpp");
static const u16 sFollowerPal_Vileplume[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vileplume.gbapal");
static const u16 sFollowerPalShiny_Vileplume[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vileplume_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Vileplume[] = {
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 0),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 1),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 2),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 3),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 4),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 5),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 6),
    overworld_frame(sFollowerPic_Vileplume, 4, 4, 7),
};

static const u16 sFollowerPic_Paras[] = INCBIN_U16("graphics/object_events/pics/seguidores/paras.4bpp");
static const u16 sFollowerPal_Paras[] = INCBIN_U16("graphics/object_events/palettes/seguidores/paras.gbapal");
static const u16 sFollowerPalShiny_Paras[] = INCBIN_U16("graphics/object_events/palettes/seguidores/paras_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Paras[] = {
    overworld_frame(sFollowerPic_Paras, 4, 4, 0),
    overworld_frame(sFollowerPic_Paras, 4, 4, 1),
    overworld_frame(sFollowerPic_Paras, 4, 4, 2),
    overworld_frame(sFollowerPic_Paras, 4, 4, 3),
    overworld_frame(sFollowerPic_Paras, 4, 4, 4),
    overworld_frame(sFollowerPic_Paras, 4, 4, 5),
    overworld_frame(sFollowerPic_Paras, 4, 4, 6),
    overworld_frame(sFollowerPic_Paras, 4, 4, 7),
};

static const u16 sFollowerPic_Parasect[] = INCBIN_U16("graphics/object_events/pics/seguidores/parasect.4bpp");
static const u16 sFollowerPal_Parasect[] = INCBIN_U16("graphics/object_events/palettes/seguidores/parasect.gbapal");
static const u16 sFollowerPalShiny_Parasect[] = INCBIN_U16("graphics/object_events/palettes/seguidores/parasect_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Parasect[] = {
    overworld_frame(sFollowerPic_Parasect, 4, 4, 0),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 1),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 2),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 3),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 4),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 5),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 6),
    overworld_frame(sFollowerPic_Parasect, 4, 4, 7),
};

static const u16 sFollowerPic_Venonat[] = INCBIN_U16("graphics/object_events/pics/seguidores/venonat.4bpp");
static const u16 sFollowerPal_Venonat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venonat.gbapal");
static const u16 sFollowerPalShiny_Venonat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venonat_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Venonat[] = {
    overworld_frame(sFollowerPic_Venonat, 4, 4, 0),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 1),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 2),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 3),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 4),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 5),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 6),
    overworld_frame(sFollowerPic_Venonat, 4, 4, 7),
};

static const u16 sFollowerPic_Venomoth[] = INCBIN_U16("graphics/object_events/pics/seguidores/venomoth.4bpp");
static const u16 sFollowerPal_Venomoth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venomoth.gbapal");
static const u16 sFollowerPalShiny_Venomoth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/venomoth_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Venomoth[] = {
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 0),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 1),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 2),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 3),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 4),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 5),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 6),
    overworld_frame(sFollowerPic_Venomoth, 4, 4, 7),
};

static const u16 sFollowerPic_Diglett[] = INCBIN_U16("graphics/object_events/pics/seguidores/diglett.4bpp");
static const u16 sFollowerPal_Diglett[] = INCBIN_U16("graphics/object_events/palettes/seguidores/diglett.gbapal");
static const u16 sFollowerPalShiny_Diglett[] = INCBIN_U16("graphics/object_events/palettes/seguidores/diglett_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Diglett[] = {
    overworld_frame(sFollowerPic_Diglett, 4, 4, 0),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 1),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 2),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 3),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 4),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 5),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 6),
    overworld_frame(sFollowerPic_Diglett, 4, 4, 7),
};

static const u16 sFollowerPic_Dugtrio[] = INCBIN_U16("graphics/object_events/pics/seguidores/dugtrio.4bpp");
static const u16 sFollowerPal_Dugtrio[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dugtrio.gbapal");
static const u16 sFollowerPalShiny_Dugtrio[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dugtrio_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dugtrio[] = {
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 0),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 1),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 2),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 3),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 4),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 5),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 6),
    overworld_frame(sFollowerPic_Dugtrio, 4, 4, 7),
};

static const u16 sFollowerPic_Meowth[] = INCBIN_U16("graphics/object_events/pics/seguidores/meowth.4bpp");
static const u16 sFollowerPal_Meowth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meowth.gbapal");
static const u16 sFollowerPalShiny_Meowth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meowth_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Meowth[] = {
    overworld_frame(sFollowerPic_Meowth, 4, 4, 0),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 1),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 2),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 3),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 4),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 5),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 6),
    overworld_frame(sFollowerPic_Meowth, 4, 4, 7),
};

static const u16 sFollowerPic_Persian[] = INCBIN_U16("graphics/object_events/pics/seguidores/persian.4bpp");
static const u16 sFollowerPal_Persian[] = INCBIN_U16("graphics/object_events/palettes/seguidores/persian.gbapal");
static const u16 sFollowerPalShiny_Persian[] = INCBIN_U16("graphics/object_events/palettes/seguidores/persian_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Persian[] = {
    overworld_frame(sFollowerPic_Persian, 4, 4, 0),
    overworld_frame(sFollowerPic_Persian, 4, 4, 1),
    overworld_frame(sFollowerPic_Persian, 4, 4, 2),
    overworld_frame(sFollowerPic_Persian, 4, 4, 3),
    overworld_frame(sFollowerPic_Persian, 4, 4, 4),
    overworld_frame(sFollowerPic_Persian, 4, 4, 5),
    overworld_frame(sFollowerPic_Persian, 4, 4, 6),
    overworld_frame(sFollowerPic_Persian, 4, 4, 7),
};

static const u16 sFollowerPic_Psyduck[] = INCBIN_U16("graphics/object_events/pics/seguidores/psyduck.4bpp");
static const u16 sFollowerPal_Psyduck[] = INCBIN_U16("graphics/object_events/palettes/seguidores/psyduck.gbapal");
static const u16 sFollowerPalShiny_Psyduck[] = INCBIN_U16("graphics/object_events/palettes/seguidores/psyduck_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Psyduck[] = {
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 0),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 1),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 2),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 3),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 4),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 5),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 6),
    overworld_frame(sFollowerPic_Psyduck, 4, 4, 7),
};

static const u16 sFollowerPic_Golduck[] = INCBIN_U16("graphics/object_events/pics/seguidores/golduck.4bpp");
static const u16 sFollowerPal_Golduck[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golduck.gbapal");
static const u16 sFollowerPalShiny_Golduck[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golduck_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Golduck[] = {
    overworld_frame(sFollowerPic_Golduck, 4, 4, 0),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 1),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 2),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 3),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 4),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 5),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 6),
    overworld_frame(sFollowerPic_Golduck, 4, 4, 7),
};

static const u16 sFollowerPic_Mankey[] = INCBIN_U16("graphics/object_events/pics/seguidores/mankey.4bpp");
static const u16 sFollowerPal_Mankey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mankey.gbapal");
static const u16 sFollowerPalShiny_Mankey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mankey_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mankey[] = {
    overworld_frame(sFollowerPic_Mankey, 4, 4, 0),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 1),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 2),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 3),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 4),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 5),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 6),
    overworld_frame(sFollowerPic_Mankey, 4, 4, 7),
};

static const u16 sFollowerPic_Primeape[] = INCBIN_U16("graphics/object_events/pics/seguidores/primeape.4bpp");
static const u16 sFollowerPal_Primeape[] = INCBIN_U16("graphics/object_events/palettes/seguidores/primeape.gbapal");
static const u16 sFollowerPalShiny_Primeape[] = INCBIN_U16("graphics/object_events/palettes/seguidores/primeape_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Primeape[] = {
    overworld_frame(sFollowerPic_Primeape, 4, 4, 0),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 1),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 2),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 3),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 4),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 5),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 6),
    overworld_frame(sFollowerPic_Primeape, 4, 4, 7),
};

static const u16 sFollowerPic_Growlithe[] = INCBIN_U16("graphics/object_events/pics/seguidores/growlithe.4bpp");
static const u16 sFollowerPal_Growlithe[] = INCBIN_U16("graphics/object_events/palettes/seguidores/growlithe.gbapal");
static const u16 sFollowerPalShiny_Growlithe[] = INCBIN_U16("graphics/object_events/palettes/seguidores/growlithe_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Growlithe[] = {
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 0),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 1),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 2),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 3),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 4),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 5),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 6),
    overworld_frame(sFollowerPic_Growlithe, 4, 4, 7),
};

static const u16 sFollowerPic_Arcanine[] = INCBIN_U16("graphics/object_events/pics/seguidores/arcanine.4bpp");
static const u16 sFollowerPal_Arcanine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/arcanine.gbapal");
static const u16 sFollowerPalShiny_Arcanine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/arcanine_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Arcanine[] = {
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 0),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 1),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 2),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 3),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 4),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 5),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 6),
    overworld_frame(sFollowerPic_Arcanine, 4, 4, 7),
};

static const u16 sFollowerPic_Poliwag[] = INCBIN_U16("graphics/object_events/pics/seguidores/poliwag.4bpp");
static const u16 sFollowerPal_Poliwag[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwag.gbapal");
static const u16 sFollowerPalShiny_Poliwag[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwag_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Poliwag[] = {
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 0),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 1),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 2),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 3),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 4),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 5),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 6),
    overworld_frame(sFollowerPic_Poliwag, 4, 4, 7),
};

static const u16 sFollowerPic_Poliwhirl[] = INCBIN_U16("graphics/object_events/pics/seguidores/poliwhirl.4bpp");
static const u16 sFollowerPal_Poliwhirl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwhirl.gbapal");
static const u16 sFollowerPalShiny_Poliwhirl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwhirl_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Poliwhirl[] = {
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 0),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 1),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 2),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 3),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 4),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 5),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 6),
    overworld_frame(sFollowerPic_Poliwhirl, 4, 4, 7),
};

static const u16 sFollowerPic_Poliwrath[] = INCBIN_U16("graphics/object_events/pics/seguidores/poliwrath.4bpp");
static const u16 sFollowerPal_Poliwrath[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwrath.gbapal");
static const u16 sFollowerPalShiny_Poliwrath[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poliwrath_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Poliwrath[] = {
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 0),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 1),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 2),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 3),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 4),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 5),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 6),
    overworld_frame(sFollowerPic_Poliwrath, 4, 4, 7),
};

static const u16 sFollowerPic_Abra[] = INCBIN_U16("graphics/object_events/pics/seguidores/abra.4bpp");
static const u16 sFollowerPal_Abra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/abra.gbapal");
static const u16 sFollowerPalShiny_Abra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/abra_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Abra[] = {
    overworld_frame(sFollowerPic_Abra, 4, 4, 0),
    overworld_frame(sFollowerPic_Abra, 4, 4, 1),
    overworld_frame(sFollowerPic_Abra, 4, 4, 2),
    overworld_frame(sFollowerPic_Abra, 4, 4, 3),
    overworld_frame(sFollowerPic_Abra, 4, 4, 4),
    overworld_frame(sFollowerPic_Abra, 4, 4, 5),
    overworld_frame(sFollowerPic_Abra, 4, 4, 6),
    overworld_frame(sFollowerPic_Abra, 4, 4, 7),
};

static const u16 sFollowerPic_Kadabra[] = INCBIN_U16("graphics/object_events/pics/seguidores/kadabra.4bpp");
static const u16 sFollowerPal_Kadabra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kadabra.gbapal");
static const u16 sFollowerPalShiny_Kadabra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kadabra_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kadabra[] = {
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 0),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 1),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 2),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 3),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 4),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 5),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 6),
    overworld_frame(sFollowerPic_Kadabra, 4, 4, 7),
};

static const u16 sFollowerPic_Alakazam[] = INCBIN_U16("graphics/object_events/pics/seguidores/alakazam.4bpp");
static const u16 sFollowerPal_Alakazam[] = INCBIN_U16("graphics/object_events/palettes/seguidores/alakazam.gbapal");
static const u16 sFollowerPalShiny_Alakazam[] = INCBIN_U16("graphics/object_events/palettes/seguidores/alakazam_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Alakazam[] = {
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 0),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 1),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 2),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 3),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 4),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 5),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 6),
    overworld_frame(sFollowerPic_Alakazam, 4, 4, 7),
};

static const u16 sFollowerPic_Machop[] = INCBIN_U16("graphics/object_events/pics/seguidores/machop.4bpp");
static const u16 sFollowerPal_Machop[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machop.gbapal");
static const u16 sFollowerPalShiny_Machop[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machop_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Machop[] = {
    overworld_frame(sFollowerPic_Machop, 4, 4, 0),
    overworld_frame(sFollowerPic_Machop, 4, 4, 1),
    overworld_frame(sFollowerPic_Machop, 4, 4, 2),
    overworld_frame(sFollowerPic_Machop, 4, 4, 3),
    overworld_frame(sFollowerPic_Machop, 4, 4, 4),
    overworld_frame(sFollowerPic_Machop, 4, 4, 5),
    overworld_frame(sFollowerPic_Machop, 4, 4, 6),
    overworld_frame(sFollowerPic_Machop, 4, 4, 7),
};

static const u16 sFollowerPic_Machoke[] = INCBIN_U16("graphics/object_events/pics/seguidores/machoke.4bpp");
static const u16 sFollowerPal_Machoke[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machoke.gbapal");
static const u16 sFollowerPalShiny_Machoke[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machoke_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Machoke[] = {
    overworld_frame(sFollowerPic_Machoke, 4, 4, 0),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 1),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 2),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 3),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 4),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 5),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 6),
    overworld_frame(sFollowerPic_Machoke, 4, 4, 7),
};

static const u16 sFollowerPic_Machamp[] = INCBIN_U16("graphics/object_events/pics/seguidores/machamp.4bpp");
static const u16 sFollowerPal_Machamp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machamp.gbapal");
static const u16 sFollowerPalShiny_Machamp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/machamp_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Machamp[] = {
    overworld_frame(sFollowerPic_Machamp, 4, 4, 0),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 1),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 2),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 3),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 4),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 5),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 6),
    overworld_frame(sFollowerPic_Machamp, 4, 4, 7),
};

static const u16 sFollowerPic_Bellsprout[] = INCBIN_U16("graphics/object_events/pics/seguidores/bellsprout.4bpp");
static const u16 sFollowerPal_Bellsprout[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bellsprout.gbapal");
static const u16 sFollowerPalShiny_Bellsprout[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bellsprout_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Bellsprout[] = {
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 0),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 1),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 2),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 3),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 4),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 5),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 6),
    overworld_frame(sFollowerPic_Bellsprout, 4, 4, 7),
};

static const u16 sFollowerPic_Weepinbell[] = INCBIN_U16("graphics/object_events/pics/seguidores/weepinbell.4bpp");
static const u16 sFollowerPal_Weepinbell[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weepinbell.gbapal");
static const u16 sFollowerPalShiny_Weepinbell[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weepinbell_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Weepinbell[] = {
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 0),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 1),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 2),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 3),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 4),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 5),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 6),
    overworld_frame(sFollowerPic_Weepinbell, 4, 4, 7),
};

static const u16 sFollowerPic_Victreebel[] = INCBIN_U16("graphics/object_events/pics/seguidores/victreebel.4bpp");
static const u16 sFollowerPal_Victreebel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/victreebel.gbapal");
static const u16 sFollowerPalShiny_Victreebel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/victreebel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Victreebel[] = {
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 0),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 1),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 2),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 3),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 4),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 5),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 6),
    overworld_frame(sFollowerPic_Victreebel, 4, 4, 7),
};

static const u16 sFollowerPic_Tentacool[] = INCBIN_U16("graphics/object_events/pics/seguidores/tentacool.4bpp");
static const u16 sFollowerPal_Tentacool[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tentacool.gbapal");
static const u16 sFollowerPalShiny_Tentacool[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tentacool_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tentacool[] = {
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 0),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 1),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 2),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 3),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 4),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 5),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 6),
    overworld_frame(sFollowerPic_Tentacool, 4, 4, 7),
};

static const u16 sFollowerPic_Tentacruel[] = INCBIN_U16("graphics/object_events/pics/seguidores/tentacruel.4bpp");
static const u16 sFollowerPal_Tentacruel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tentacruel.gbapal");
static const u16 sFollowerPalShiny_Tentacruel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tentacruel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tentacruel[] = {
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 0),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 1),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 2),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 3),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 4),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 5),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 6),
    overworld_frame(sFollowerPic_Tentacruel, 4, 4, 7),
};

static const u16 sFollowerPic_Geodude[] = INCBIN_U16("graphics/object_events/pics/seguidores/geodude.4bpp");
static const u16 sFollowerPal_Geodude[] = INCBIN_U16("graphics/object_events/palettes/seguidores/geodude.gbapal");
static const u16 sFollowerPalShiny_Geodude[] = INCBIN_U16("graphics/object_events/palettes/seguidores/geodude_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Geodude[] = {
    overworld_frame(sFollowerPic_Geodude, 4, 4, 0),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 1),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 2),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 3),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 4),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 5),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 6),
    overworld_frame(sFollowerPic_Geodude, 4, 4, 7),
};

static const u16 sFollowerPic_Graveler[] = INCBIN_U16("graphics/object_events/pics/seguidores/graveler.4bpp");
static const u16 sFollowerPal_Graveler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/graveler.gbapal");
static const u16 sFollowerPalShiny_Graveler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/graveler_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Graveler[] = {
    overworld_frame(sFollowerPic_Graveler, 4, 4, 0),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 1),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 2),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 3),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 4),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 5),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 6),
    overworld_frame(sFollowerPic_Graveler, 4, 4, 7),
};

static const u16 sFollowerPic_Golem[] = INCBIN_U16("graphics/object_events/pics/seguidores/golem.4bpp");
static const u16 sFollowerPal_Golem[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golem.gbapal");
static const u16 sFollowerPalShiny_Golem[] = INCBIN_U16("graphics/object_events/palettes/seguidores/golem_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Golem[] = {
    overworld_frame(sFollowerPic_Golem, 4, 4, 0),
    overworld_frame(sFollowerPic_Golem, 4, 4, 1),
    overworld_frame(sFollowerPic_Golem, 4, 4, 2),
    overworld_frame(sFollowerPic_Golem, 4, 4, 3),
    overworld_frame(sFollowerPic_Golem, 4, 4, 4),
    overworld_frame(sFollowerPic_Golem, 4, 4, 5),
    overworld_frame(sFollowerPic_Golem, 4, 4, 6),
    overworld_frame(sFollowerPic_Golem, 4, 4, 7),
};

static const u16 sFollowerPic_Ponyta[] = INCBIN_U16("graphics/object_events/pics/seguidores/ponyta.4bpp");
static const u16 sFollowerPal_Ponyta[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ponyta.gbapal");
static const u16 sFollowerPalShiny_Ponyta[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ponyta_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ponyta[] = {
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 0),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 1),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 2),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 3),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 4),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 5),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 6),
    overworld_frame(sFollowerPic_Ponyta, 4, 4, 7),
};

static const u16 sFollowerPic_Rapidash[] = INCBIN_U16("graphics/object_events/pics/seguidores/rapidash.4bpp");
static const u16 sFollowerPal_Rapidash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rapidash.gbapal");
static const u16 sFollowerPalShiny_Rapidash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rapidash_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Rapidash[] = {
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 0),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 1),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 2),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 3),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 4),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 5),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 6),
    overworld_frame(sFollowerPic_Rapidash, 4, 4, 7),
};

static const u16 sFollowerPic_Slowpoke[] = INCBIN_U16("graphics/object_events/pics/seguidores/slowpoke.4bpp");
static const u16 sFollowerPal_Slowpoke[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowpoke.gbapal");
static const u16 sFollowerPalShiny_Slowpoke[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowpoke_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slowpoke[] = {
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 0),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 1),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 2),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 3),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 4),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 5),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 6),
    overworld_frame(sFollowerPic_Slowpoke, 4, 4, 7),
};

static const u16 sFollowerPic_Slowbro[] = INCBIN_U16("graphics/object_events/pics/seguidores/slowbro.4bpp");
static const u16 sFollowerPal_Slowbro[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowbro.gbapal");
static const u16 sFollowerPalShiny_Slowbro[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowbro_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slowbro[] = {
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 0),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 1),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 2),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 3),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 4),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 5),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 6),
    overworld_frame(sFollowerPic_Slowbro, 4, 4, 7),
};

static const u16 sFollowerPic_Magnemite[] = INCBIN_U16("graphics/object_events/pics/seguidores/magnemite.4bpp");
static const u16 sFollowerPal_Magnemite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magnemite.gbapal");
static const u16 sFollowerPalShiny_Magnemite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magnemite_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magnemite[] = {
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 0),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 1),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 2),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 3),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 4),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 5),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 6),
    overworld_frame(sFollowerPic_Magnemite, 4, 4, 7),
};

static const u16 sFollowerPic_Magneton[] = INCBIN_U16("graphics/object_events/pics/seguidores/magneton.4bpp");
static const u16 sFollowerPal_Magneton[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magneton.gbapal");
static const u16 sFollowerPalShiny_Magneton[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magneton_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magneton[] = {
    overworld_frame(sFollowerPic_Magneton, 4, 4, 0),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 1),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 2),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 3),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 4),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 5),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 6),
    overworld_frame(sFollowerPic_Magneton, 4, 4, 7),
};

static const u16 sFollowerPic_Farfetchd[] = INCBIN_U16("graphics/object_events/pics/seguidores/farfetchd.4bpp");
static const u16 sFollowerPal_Farfetchd[] = INCBIN_U16("graphics/object_events/palettes/seguidores/farfetchd.gbapal");
static const u16 sFollowerPalShiny_Farfetchd[] = INCBIN_U16("graphics/object_events/palettes/seguidores/farfetchd_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Farfetchd[] = {
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 0),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 1),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 2),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 3),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 4),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 5),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 6),
    overworld_frame(sFollowerPic_Farfetchd, 4, 4, 7),
};

static const u16 sFollowerPic_Doduo[] = INCBIN_U16("graphics/object_events/pics/seguidores/doduo.4bpp");
static const u16 sFollowerPal_Doduo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/doduo.gbapal");
static const u16 sFollowerPalShiny_Doduo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/doduo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Doduo[] = {
    overworld_frame(sFollowerPic_Doduo, 4, 4, 0),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 1),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 2),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 3),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 4),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 5),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 6),
    overworld_frame(sFollowerPic_Doduo, 4, 4, 7),
};

static const u16 sFollowerPic_Dodrio[] = INCBIN_U16("graphics/object_events/pics/seguidores/dodrio.4bpp");
static const u16 sFollowerPal_Dodrio[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dodrio.gbapal");
static const u16 sFollowerPalShiny_Dodrio[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dodrio_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dodrio[] = {
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 0),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 1),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 2),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 3),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 4),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 5),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 6),
    overworld_frame(sFollowerPic_Dodrio, 4, 4, 7),
};

static const u16 sFollowerPic_Seel[] = INCBIN_U16("graphics/object_events/pics/seguidores/seel.4bpp");
static const u16 sFollowerPal_Seel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seel.gbapal");
static const u16 sFollowerPalShiny_Seel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Seel[] = {
    overworld_frame(sFollowerPic_Seel, 4, 4, 0),
    overworld_frame(sFollowerPic_Seel, 4, 4, 1),
    overworld_frame(sFollowerPic_Seel, 4, 4, 2),
    overworld_frame(sFollowerPic_Seel, 4, 4, 3),
    overworld_frame(sFollowerPic_Seel, 4, 4, 4),
    overworld_frame(sFollowerPic_Seel, 4, 4, 5),
    overworld_frame(sFollowerPic_Seel, 4, 4, 6),
    overworld_frame(sFollowerPic_Seel, 4, 4, 7),
};

static const u16 sFollowerPic_Dewgong[] = INCBIN_U16("graphics/object_events/pics/seguidores/dewgong.4bpp");
static const u16 sFollowerPal_Dewgong[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dewgong.gbapal");
static const u16 sFollowerPalShiny_Dewgong[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dewgong_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dewgong[] = {
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 0),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 1),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 2),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 3),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 4),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 5),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 6),
    overworld_frame(sFollowerPic_Dewgong, 4, 4, 7),
};

static const u16 sFollowerPic_Grimer[] = INCBIN_U16("graphics/object_events/pics/seguidores/grimer.4bpp");
static const u16 sFollowerPal_Grimer[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grimer.gbapal");
static const u16 sFollowerPalShiny_Grimer[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grimer_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Grimer[] = {
    overworld_frame(sFollowerPic_Grimer, 4, 4, 0),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 1),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 2),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 3),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 4),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 5),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 6),
    overworld_frame(sFollowerPic_Grimer, 4, 4, 7),
};

static const u16 sFollowerPic_Muk[] = INCBIN_U16("graphics/object_events/pics/seguidores/muk.4bpp");
static const u16 sFollowerPal_Muk[] = INCBIN_U16("graphics/object_events/palettes/seguidores/muk.gbapal");
static const u16 sFollowerPalShiny_Muk[] = INCBIN_U16("graphics/object_events/palettes/seguidores/muk_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Muk[] = {
    overworld_frame(sFollowerPic_Muk, 4, 4, 0),
    overworld_frame(sFollowerPic_Muk, 4, 4, 1),
    overworld_frame(sFollowerPic_Muk, 4, 4, 2),
    overworld_frame(sFollowerPic_Muk, 4, 4, 3),
    overworld_frame(sFollowerPic_Muk, 4, 4, 4),
    overworld_frame(sFollowerPic_Muk, 4, 4, 5),
    overworld_frame(sFollowerPic_Muk, 4, 4, 6),
    overworld_frame(sFollowerPic_Muk, 4, 4, 7),
};

static const u16 sFollowerPic_Shellder[] = INCBIN_U16("graphics/object_events/pics/seguidores/shellder.4bpp");
static const u16 sFollowerPal_Shellder[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shellder.gbapal");
static const u16 sFollowerPalShiny_Shellder[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shellder_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shellder[] = {
    overworld_frame(sFollowerPic_Shellder, 4, 4, 0),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 1),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 2),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 3),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 4),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 5),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 6),
    overworld_frame(sFollowerPic_Shellder, 4, 4, 7),
};

static const u16 sFollowerPic_Cloyster[] = INCBIN_U16("graphics/object_events/pics/seguidores/cloyster.4bpp");
static const u16 sFollowerPal_Cloyster[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cloyster.gbapal");
static const u16 sFollowerPalShiny_Cloyster[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cloyster_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cloyster[] = {
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 0),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 1),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 2),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 3),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 4),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 5),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 6),
    overworld_frame(sFollowerPic_Cloyster, 4, 4, 7),
};

static const u16 sFollowerPic_Gastly[] = INCBIN_U16("graphics/object_events/pics/seguidores/gastly.4bpp");
static const u16 sFollowerPal_Gastly[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gastly.gbapal");
static const u16 sFollowerPalShiny_Gastly[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gastly_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gastly[] = {
    overworld_frame(sFollowerPic_Gastly, 4, 4, 0),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 1),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 2),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 3),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 4),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 5),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 6),
    overworld_frame(sFollowerPic_Gastly, 4, 4, 7),
};

static const u16 sFollowerPic_Haunter[] = INCBIN_U16("graphics/object_events/pics/seguidores/haunter.4bpp");
static const u16 sFollowerPal_Haunter[] = INCBIN_U16("graphics/object_events/palettes/seguidores/haunter.gbapal");
static const u16 sFollowerPalShiny_Haunter[] = INCBIN_U16("graphics/object_events/palettes/seguidores/haunter_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Haunter[] = {
    overworld_frame(sFollowerPic_Haunter, 4, 4, 0),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 1),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 2),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 3),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 4),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 5),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 6),
    overworld_frame(sFollowerPic_Haunter, 4, 4, 7),
};

static const u16 sFollowerPic_Gengar[] = INCBIN_U16("graphics/object_events/pics/seguidores/gengar.4bpp");
static const u16 sFollowerPal_Gengar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gengar.gbapal");
static const u16 sFollowerPalShiny_Gengar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gengar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gengar[] = {
    overworld_frame(sFollowerPic_Gengar, 4, 4, 0),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 1),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 2),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 3),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 4),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 5),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 6),
    overworld_frame(sFollowerPic_Gengar, 4, 4, 7),
};

static const u16 sFollowerPic_Onix[] = INCBIN_U16("graphics/object_events/pics/seguidores/onix.4bpp");
static const u16 sFollowerPal_Onix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/onix.gbapal");
static const u16 sFollowerPalShiny_Onix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/onix_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Onix[] = {
    overworld_frame(sFollowerPic_Onix, 4, 4, 0),
    overworld_frame(sFollowerPic_Onix, 4, 4, 1),
    overworld_frame(sFollowerPic_Onix, 4, 4, 2),
    overworld_frame(sFollowerPic_Onix, 4, 4, 3),
    overworld_frame(sFollowerPic_Onix, 4, 4, 4),
    overworld_frame(sFollowerPic_Onix, 4, 4, 5),
    overworld_frame(sFollowerPic_Onix, 4, 4, 6),
    overworld_frame(sFollowerPic_Onix, 4, 4, 7),
};

static const u16 sFollowerPic_Drowzee[] = INCBIN_U16("graphics/object_events/pics/seguidores/drowzee.4bpp");
static const u16 sFollowerPal_Drowzee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/drowzee.gbapal");
static const u16 sFollowerPalShiny_Drowzee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/drowzee_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Drowzee[] = {
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 0),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 1),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 2),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 3),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 4),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 5),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 6),
    overworld_frame(sFollowerPic_Drowzee, 4, 4, 7),
};

static const u16 sFollowerPic_Hypno[] = INCBIN_U16("graphics/object_events/pics/seguidores/hypno.4bpp");
static const u16 sFollowerPal_Hypno[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hypno.gbapal");
static const u16 sFollowerPalShiny_Hypno[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hypno_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hypno[] = {
    overworld_frame(sFollowerPic_Hypno, 4, 4, 0),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 1),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 2),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 3),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 4),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 5),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 6),
    overworld_frame(sFollowerPic_Hypno, 4, 4, 7),
};

static const u16 sFollowerPic_Krabby[] = INCBIN_U16("graphics/object_events/pics/seguidores/krabby.4bpp");
static const u16 sFollowerPal_Krabby[] = INCBIN_U16("graphics/object_events/palettes/seguidores/krabby.gbapal");
static const u16 sFollowerPalShiny_Krabby[] = INCBIN_U16("graphics/object_events/palettes/seguidores/krabby_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Krabby[] = {
    overworld_frame(sFollowerPic_Krabby, 4, 4, 0),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 1),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 2),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 3),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 4),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 5),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 6),
    overworld_frame(sFollowerPic_Krabby, 4, 4, 7),
};

static const u16 sFollowerPic_Kingler[] = INCBIN_U16("graphics/object_events/pics/seguidores/kingler.4bpp");
static const u16 sFollowerPal_Kingler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kingler.gbapal");
static const u16 sFollowerPalShiny_Kingler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kingler_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kingler[] = {
    overworld_frame(sFollowerPic_Kingler, 4, 4, 0),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 1),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 2),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 3),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 4),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 5),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 6),
    overworld_frame(sFollowerPic_Kingler, 4, 4, 7),
};

static const u16 sFollowerPic_Voltorb[] = INCBIN_U16("graphics/object_events/pics/seguidores/voltorb.4bpp");
static const u16 sFollowerPal_Voltorb[] = INCBIN_U16("graphics/object_events/palettes/seguidores/voltorb.gbapal");
static const u16 sFollowerPalShiny_Voltorb[] = INCBIN_U16("graphics/object_events/palettes/seguidores/voltorb_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Voltorb[] = {
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 0),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 1),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 2),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 3),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 4),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 5),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 6),
    overworld_frame(sFollowerPic_Voltorb, 4, 4, 7),
};

static const u16 sFollowerPic_Electrode[] = INCBIN_U16("graphics/object_events/pics/seguidores/electrode.4bpp");
static const u16 sFollowerPal_Electrode[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electrode.gbapal");
static const u16 sFollowerPalShiny_Electrode[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electrode_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Electrode[] = {
    overworld_frame(sFollowerPic_Electrode, 4, 4, 0),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 1),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 2),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 3),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 4),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 5),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 6),
    overworld_frame(sFollowerPic_Electrode, 4, 4, 7),
};

static const u16 sFollowerPic_Exeggcute[] = INCBIN_U16("graphics/object_events/pics/seguidores/exeggcute.4bpp");
static const u16 sFollowerPal_Exeggcute[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exeggcute.gbapal");
static const u16 sFollowerPalShiny_Exeggcute[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exeggcute_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Exeggcute[] = {
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 0),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 1),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 2),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 3),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 4),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 5),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 6),
    overworld_frame(sFollowerPic_Exeggcute, 4, 4, 7),
};

static const u16 sFollowerPic_Exeggutor[] = INCBIN_U16("graphics/object_events/pics/seguidores/exeggutor.4bpp");
static const u16 sFollowerPal_Exeggutor[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exeggutor.gbapal");
static const u16 sFollowerPalShiny_Exeggutor[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exeggutor_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Exeggutor[] = {
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 0),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 1),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 2),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 3),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 4),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 5),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 6),
    overworld_frame(sFollowerPic_Exeggutor, 4, 4, 7),
};

static const u16 sFollowerPic_Cubone[] = INCBIN_U16("graphics/object_events/pics/seguidores/cubone.4bpp");
static const u16 sFollowerPal_Cubone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cubone.gbapal");
static const u16 sFollowerPalShiny_Cubone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cubone_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cubone[] = {
    overworld_frame(sFollowerPic_Cubone, 4, 4, 0),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 1),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 2),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 3),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 4),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 5),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 6),
    overworld_frame(sFollowerPic_Cubone, 4, 4, 7),
};

static const u16 sFollowerPic_Marowak[] = INCBIN_U16("graphics/object_events/pics/seguidores/marowak.4bpp");
static const u16 sFollowerPal_Marowak[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marowak.gbapal");
static const u16 sFollowerPalShiny_Marowak[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marowak_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Marowak[] = {
    overworld_frame(sFollowerPic_Marowak, 4, 4, 0),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 1),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 2),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 3),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 4),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 5),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 6),
    overworld_frame(sFollowerPic_Marowak, 4, 4, 7),
};

static const u16 sFollowerPic_Hitmonlee[] = INCBIN_U16("graphics/object_events/pics/seguidores/hitmonlee.4bpp");
static const u16 sFollowerPal_Hitmonlee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmonlee.gbapal");
static const u16 sFollowerPalShiny_Hitmonlee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmonlee_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hitmonlee[] = {
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 0),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 1),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 2),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 3),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 4),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 5),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 6),
    overworld_frame(sFollowerPic_Hitmonlee, 4, 4, 7),
};

static const u16 sFollowerPic_Hitmonchan[] = INCBIN_U16("graphics/object_events/pics/seguidores/hitmonchan.4bpp");
static const u16 sFollowerPal_Hitmonchan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmonchan.gbapal");
static const u16 sFollowerPalShiny_Hitmonchan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmonchan_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hitmonchan[] = {
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 0),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 1),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 2),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 3),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 4),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 5),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 6),
    overworld_frame(sFollowerPic_Hitmonchan, 4, 4, 7),
};

static const u16 sFollowerPic_Lickitung[] = INCBIN_U16("graphics/object_events/pics/seguidores/lickitung.4bpp");
static const u16 sFollowerPal_Lickitung[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lickitung.gbapal");
static const u16 sFollowerPalShiny_Lickitung[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lickitung_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lickitung[] = {
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 0),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 1),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 2),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 3),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 4),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 5),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 6),
    overworld_frame(sFollowerPic_Lickitung, 4, 4, 7),
};

static const u16 sFollowerPic_Koffing[] = INCBIN_U16("graphics/object_events/pics/seguidores/koffing.4bpp");
static const u16 sFollowerPal_Koffing[] = INCBIN_U16("graphics/object_events/palettes/seguidores/koffing.gbapal");
static const u16 sFollowerPalShiny_Koffing[] = INCBIN_U16("graphics/object_events/palettes/seguidores/koffing_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Koffing[] = {
    overworld_frame(sFollowerPic_Koffing, 4, 4, 0),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 1),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 2),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 3),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 4),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 5),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 6),
    overworld_frame(sFollowerPic_Koffing, 4, 4, 7),
};

static const u16 sFollowerPic_Weezing[] = INCBIN_U16("graphics/object_events/pics/seguidores/weezing.4bpp");
static const u16 sFollowerPal_Weezing[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weezing.gbapal");
static const u16 sFollowerPalShiny_Weezing[] = INCBIN_U16("graphics/object_events/palettes/seguidores/weezing_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Weezing[] = {
    overworld_frame(sFollowerPic_Weezing, 4, 4, 0),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 1),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 2),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 3),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 4),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 5),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 6),
    overworld_frame(sFollowerPic_Weezing, 4, 4, 7),
};

static const u16 sFollowerPic_Rhyhorn[] = INCBIN_U16("graphics/object_events/pics/seguidores/rhyhorn.4bpp");
static const u16 sFollowerPal_Rhyhorn[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rhyhorn.gbapal");
static const u16 sFollowerPalShiny_Rhyhorn[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rhyhorn_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Rhyhorn[] = {
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 0),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 1),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 2),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 3),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 4),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 5),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 6),
    overworld_frame(sFollowerPic_Rhyhorn, 4, 4, 7),
};

static const u16 sFollowerPic_Rhydon[] = INCBIN_U16("graphics/object_events/pics/seguidores/rhydon.4bpp");
static const u16 sFollowerPal_Rhydon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rhydon.gbapal");
static const u16 sFollowerPalShiny_Rhydon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rhydon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Rhydon[] = {
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 0),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 1),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 2),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 3),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 4),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 5),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 6),
    overworld_frame(sFollowerPic_Rhydon, 4, 4, 7),
};

static const u16 sFollowerPic_Chansey[] = INCBIN_U16("graphics/object_events/pics/seguidores/chansey.4bpp");
static const u16 sFollowerPal_Chansey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chansey.gbapal");
static const u16 sFollowerPalShiny_Chansey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chansey_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Chansey[] = {
    overworld_frame(sFollowerPic_Chansey, 4, 4, 0),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 1),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 2),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 3),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 4),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 5),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 6),
    overworld_frame(sFollowerPic_Chansey, 4, 4, 7),
};

static const u16 sFollowerPic_Tangela[] = INCBIN_U16("graphics/object_events/pics/seguidores/tangela.4bpp");
static const u16 sFollowerPal_Tangela[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tangela.gbapal");
static const u16 sFollowerPalShiny_Tangela[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tangela_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tangela[] = {
    overworld_frame(sFollowerPic_Tangela, 4, 4, 0),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 1),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 2),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 3),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 4),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 5),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 6),
    overworld_frame(sFollowerPic_Tangela, 4, 4, 7),
};

static const u16 sFollowerPic_Kangaskhan[] = INCBIN_U16("graphics/object_events/pics/seguidores/kangaskhan.4bpp");
static const u16 sFollowerPal_Kangaskhan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kangaskhan.gbapal");
static const u16 sFollowerPalShiny_Kangaskhan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kangaskhan_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kangaskhan[] = {
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 0),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 1),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 2),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 3),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 4),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 5),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 6),
    overworld_frame(sFollowerPic_Kangaskhan, 4, 4, 7),
};

static const u16 sFollowerPic_Horsea[] = INCBIN_U16("graphics/object_events/pics/seguidores/horsea.4bpp");
static const u16 sFollowerPal_Horsea[] = INCBIN_U16("graphics/object_events/palettes/seguidores/horsea.gbapal");
static const u16 sFollowerPalShiny_Horsea[] = INCBIN_U16("graphics/object_events/palettes/seguidores/horsea_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Horsea[] = {
    overworld_frame(sFollowerPic_Horsea, 4, 4, 0),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 1),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 2),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 3),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 4),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 5),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 6),
    overworld_frame(sFollowerPic_Horsea, 4, 4, 7),
};

static const u16 sFollowerPic_Seadra[] = INCBIN_U16("graphics/object_events/pics/seguidores/seadra.4bpp");
static const u16 sFollowerPal_Seadra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seadra.gbapal");
static const u16 sFollowerPalShiny_Seadra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seadra_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Seadra[] = {
    overworld_frame(sFollowerPic_Seadra, 4, 4, 0),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 1),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 2),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 3),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 4),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 5),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 6),
    overworld_frame(sFollowerPic_Seadra, 4, 4, 7),
};

static const u16 sFollowerPic_Goldeen[] = INCBIN_U16("graphics/object_events/pics/seguidores/goldeen.4bpp");
static const u16 sFollowerPal_Goldeen[] = INCBIN_U16("graphics/object_events/palettes/seguidores/goldeen.gbapal");
static const u16 sFollowerPalShiny_Goldeen[] = INCBIN_U16("graphics/object_events/palettes/seguidores/goldeen_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Goldeen[] = {
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 0),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 1),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 2),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 3),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 4),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 5),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 6),
    overworld_frame(sFollowerPic_Goldeen, 4, 4, 7),
};

static const u16 sFollowerPic_Seaking[] = INCBIN_U16("graphics/object_events/pics/seguidores/seaking.4bpp");
static const u16 sFollowerPal_Seaking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seaking.gbapal");
static const u16 sFollowerPalShiny_Seaking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seaking_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Seaking[] = {
    overworld_frame(sFollowerPic_Seaking, 4, 4, 0),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 1),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 2),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 3),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 4),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 5),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 6),
    overworld_frame(sFollowerPic_Seaking, 4, 4, 7),
};

static const u16 sFollowerPic_Staryu[] = INCBIN_U16("graphics/object_events/pics/seguidores/staryu.4bpp");
static const u16 sFollowerPal_Staryu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/staryu.gbapal");
static const u16 sFollowerPalShiny_Staryu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/staryu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Staryu[] = {
    overworld_frame(sFollowerPic_Staryu, 4, 4, 0),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 1),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 2),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 3),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 4),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 5),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 6),
    overworld_frame(sFollowerPic_Staryu, 4, 4, 7),
};

static const u16 sFollowerPic_Starmie[] = INCBIN_U16("graphics/object_events/pics/seguidores/starmie.4bpp");
static const u16 sFollowerPal_Starmie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/starmie.gbapal");
static const u16 sFollowerPalShiny_Starmie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/starmie_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Starmie[] = {
    overworld_frame(sFollowerPic_Starmie, 4, 4, 0),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 1),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 2),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 3),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 4),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 5),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 6),
    overworld_frame(sFollowerPic_Starmie, 4, 4, 7),
};

static const u16 sFollowerPic_MrMime[] = INCBIN_U16("graphics/object_events/pics/seguidores/mr_mime.4bpp");
static const u16 sFollowerPal_MrMime[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mr_mime.gbapal");
static const u16 sFollowerPalShiny_MrMime[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mr_mime_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_MrMime[] = {
    overworld_frame(sFollowerPic_MrMime, 4, 4, 0),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 1),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 2),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 3),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 4),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 5),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 6),
    overworld_frame(sFollowerPic_MrMime, 4, 4, 7),
};

static const u16 sFollowerPic_Scyther[] = INCBIN_U16("graphics/object_events/pics/seguidores/scyther.4bpp");
static const u16 sFollowerPal_Scyther[] = INCBIN_U16("graphics/object_events/palettes/seguidores/scyther.gbapal");
static const u16 sFollowerPalShiny_Scyther[] = INCBIN_U16("graphics/object_events/palettes/seguidores/scyther_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Scyther[] = {
    overworld_frame(sFollowerPic_Scyther, 4, 4, 0),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 1),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 2),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 3),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 4),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 5),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 6),
    overworld_frame(sFollowerPic_Scyther, 4, 4, 7),
};

static const u16 sFollowerPic_Jynx[] = INCBIN_U16("graphics/object_events/pics/seguidores/jynx.4bpp");
static const u16 sFollowerPal_Jynx[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jynx.gbapal");
static const u16 sFollowerPalShiny_Jynx[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jynx_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Jynx[] = {
    overworld_frame(sFollowerPic_Jynx, 4, 4, 0),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 1),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 2),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 3),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 4),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 5),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 6),
    overworld_frame(sFollowerPic_Jynx, 4, 4, 7),
};

static const u16 sFollowerPic_Electabuzz[] = INCBIN_U16("graphics/object_events/pics/seguidores/electabuzz.4bpp");
static const u16 sFollowerPal_Electabuzz[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electabuzz.gbapal");
static const u16 sFollowerPalShiny_Electabuzz[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electabuzz_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Electabuzz[] = {
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 0),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 1),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 2),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 3),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 4),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 5),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 6),
    overworld_frame(sFollowerPic_Electabuzz, 4, 4, 7),
};

static const u16 sFollowerPic_Magmar[] = INCBIN_U16("graphics/object_events/pics/seguidores/magmar.4bpp");
static const u16 sFollowerPal_Magmar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magmar.gbapal");
static const u16 sFollowerPalShiny_Magmar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magmar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magmar[] = {
    overworld_frame(sFollowerPic_Magmar, 4, 4, 0),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 1),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 2),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 3),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 4),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 5),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 6),
    overworld_frame(sFollowerPic_Magmar, 4, 4, 7),
};

static const u16 sFollowerPic_Pinsir[] = INCBIN_U16("graphics/object_events/pics/seguidores/pinsir.4bpp");
static const u16 sFollowerPal_Pinsir[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pinsir.gbapal");
static const u16 sFollowerPalShiny_Pinsir[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pinsir_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pinsir[] = {
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 0),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 1),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 2),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 3),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 4),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 5),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 6),
    overworld_frame(sFollowerPic_Pinsir, 4, 4, 7),
};

static const u16 sFollowerPic_Tauros[] = INCBIN_U16("graphics/object_events/pics/seguidores/tauros.4bpp");
static const u16 sFollowerPal_Tauros[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tauros.gbapal");
static const u16 sFollowerPalShiny_Tauros[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tauros_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tauros[] = {
    overworld_frame(sFollowerPic_Tauros, 4, 4, 0),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 1),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 2),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 3),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 4),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 5),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 6),
    overworld_frame(sFollowerPic_Tauros, 4, 4, 7),
};

static const u16 sFollowerPic_Magikarp[] = INCBIN_U16("graphics/object_events/pics/seguidores/magikarp.4bpp");
static const u16 sFollowerPal_Magikarp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magikarp.gbapal");
static const u16 sFollowerPalShiny_Magikarp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magikarp_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magikarp[] = {
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 0),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 1),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 2),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 3),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 4),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 5),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 6),
    overworld_frame(sFollowerPic_Magikarp, 4, 4, 7),
};

static const u16 sFollowerPic_Gyarados[] = INCBIN_U16("graphics/object_events/pics/seguidores/gyarados.4bpp");
static const u16 sFollowerPal_Gyarados[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gyarados.gbapal");
static const u16 sFollowerPalShiny_Gyarados[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gyarados_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gyarados[] = {
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 0),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 1),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 2),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 3),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 4),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 5),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 6),
    overworld_frame(sFollowerPic_Gyarados, 4, 4, 7),
};

static const u16 sFollowerPic_Lapras[] = INCBIN_U16("graphics/object_events/pics/seguidores/lapras.4bpp");
static const u16 sFollowerPal_Lapras[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lapras.gbapal");
static const u16 sFollowerPalShiny_Lapras[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lapras_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lapras[] = {
    overworld_frame(sFollowerPic_Lapras, 4, 4, 0),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 1),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 2),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 3),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 4),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 5),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 6),
    overworld_frame(sFollowerPic_Lapras, 4, 4, 7),
};

static const u16 sFollowerPic_Ditto[] = INCBIN_U16("graphics/object_events/pics/seguidores/ditto.4bpp");
static const u16 sFollowerPal_Ditto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ditto.gbapal");
static const u16 sFollowerPalShiny_Ditto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ditto_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ditto[] = {
    overworld_frame(sFollowerPic_Ditto, 4, 4, 0),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 1),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 2),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 3),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 4),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 5),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 6),
    overworld_frame(sFollowerPic_Ditto, 4, 4, 7),
};

static const u16 sFollowerPic_Eevee[] = INCBIN_U16("graphics/object_events/pics/seguidores/eevee.4bpp");
static const u16 sFollowerPal_Eevee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/eevee.gbapal");
static const u16 sFollowerPalShiny_Eevee[] = INCBIN_U16("graphics/object_events/palettes/seguidores/eevee_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Eevee[] = {
    overworld_frame(sFollowerPic_Eevee, 4, 4, 0),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 1),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 2),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 3),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 4),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 5),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 6),
    overworld_frame(sFollowerPic_Eevee, 4, 4, 7),
};

static const u16 sFollowerPic_Vaporeon[] = INCBIN_U16("graphics/object_events/pics/seguidores/vaporeon.4bpp");
static const u16 sFollowerPal_Vaporeon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vaporeon.gbapal");
static const u16 sFollowerPalShiny_Vaporeon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vaporeon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Vaporeon[] = {
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 0),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 1),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 2),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 3),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 4),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 5),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 6),
    overworld_frame(sFollowerPic_Vaporeon, 4, 4, 7),
};

static const u16 sFollowerPic_Jolteon[] = INCBIN_U16("graphics/object_events/pics/seguidores/jolteon.4bpp");
static const u16 sFollowerPal_Jolteon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jolteon.gbapal");
static const u16 sFollowerPalShiny_Jolteon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jolteon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Jolteon[] = {
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 0),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 1),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 2),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 3),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 4),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 5),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 6),
    overworld_frame(sFollowerPic_Jolteon, 4, 4, 7),
};

static const u16 sFollowerPic_Flareon[] = INCBIN_U16("graphics/object_events/pics/seguidores/flareon.4bpp");
static const u16 sFollowerPal_Flareon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flareon.gbapal");
static const u16 sFollowerPalShiny_Flareon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flareon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Flareon[] = {
    overworld_frame(sFollowerPic_Flareon, 4, 4, 0),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 1),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 2),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 3),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 4),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 5),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 6),
    overworld_frame(sFollowerPic_Flareon, 4, 4, 7),
};

static const u16 sFollowerPic_Porygon[] = INCBIN_U16("graphics/object_events/pics/seguidores/porygon.4bpp");
static const u16 sFollowerPal_Porygon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/porygon.gbapal");
static const u16 sFollowerPalShiny_Porygon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/porygon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Porygon[] = {
    overworld_frame(sFollowerPic_Porygon, 4, 4, 0),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 1),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 2),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 3),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 4),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 5),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 6),
    overworld_frame(sFollowerPic_Porygon, 4, 4, 7),
};

static const u16 sFollowerPic_Omanyte[] = INCBIN_U16("graphics/object_events/pics/seguidores/omanyte.4bpp");
static const u16 sFollowerPal_Omanyte[] = INCBIN_U16("graphics/object_events/palettes/seguidores/omanyte.gbapal");
static const u16 sFollowerPalShiny_Omanyte[] = INCBIN_U16("graphics/object_events/palettes/seguidores/omanyte_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Omanyte[] = {
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 0),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 1),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 2),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 3),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 4),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 5),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 6),
    overworld_frame(sFollowerPic_Omanyte, 4, 4, 7),
};

static const u16 sFollowerPic_Omastar[] = INCBIN_U16("graphics/object_events/pics/seguidores/omastar.4bpp");
static const u16 sFollowerPal_Omastar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/omastar.gbapal");
static const u16 sFollowerPalShiny_Omastar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/omastar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Omastar[] = {
    overworld_frame(sFollowerPic_Omastar, 4, 4, 0),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 1),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 2),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 3),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 4),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 5),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 6),
    overworld_frame(sFollowerPic_Omastar, 4, 4, 7),
};

static const u16 sFollowerPic_Kabuto[] = INCBIN_U16("graphics/object_events/pics/seguidores/kabuto.4bpp");
static const u16 sFollowerPal_Kabuto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kabuto.gbapal");
static const u16 sFollowerPalShiny_Kabuto[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kabuto_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kabuto[] = {
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 0),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 1),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 2),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 3),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 4),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 5),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 6),
    overworld_frame(sFollowerPic_Kabuto, 4, 4, 7),
};

static const u16 sFollowerPic_Kabutops[] = INCBIN_U16("graphics/object_events/pics/seguidores/kabutops.4bpp");
static const u16 sFollowerPal_Kabutops[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kabutops.gbapal");
static const u16 sFollowerPalShiny_Kabutops[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kabutops_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kabutops[] = {
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 0),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 1),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 2),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 3),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 4),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 5),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 6),
    overworld_frame(sFollowerPic_Kabutops, 4, 4, 7),
};

static const u16 sFollowerPic_Aerodactyl[] = INCBIN_U16("graphics/object_events/pics/seguidores/aerodactyl.4bpp");
static const u16 sFollowerPal_Aerodactyl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aerodactyl.gbapal");
static const u16 sFollowerPalShiny_Aerodactyl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aerodactyl_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Aerodactyl[] = {
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 0),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 1),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 2),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 3),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 4),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 5),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 6),
    overworld_frame(sFollowerPic_Aerodactyl, 4, 4, 7),
};

static const u16 sFollowerPic_Snorlax[] = INCBIN_U16("graphics/object_events/pics/seguidores/snorlax.4bpp");
static const u16 sFollowerPal_Snorlax[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snorlax.gbapal");
static const u16 sFollowerPalShiny_Snorlax[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snorlax_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Snorlax[] = {
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 0),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 1),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 2),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 3),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 4),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 5),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 6),
    overworld_frame(sFollowerPic_Snorlax, 4, 4, 7),
};

static const u16 sFollowerPic_Articuno[] = INCBIN_U16("graphics/object_events/pics/seguidores/articuno.4bpp");
static const u16 sFollowerPal_Articuno[] = INCBIN_U16("graphics/object_events/palettes/seguidores/articuno.gbapal");
static const u16 sFollowerPalShiny_Articuno[] = INCBIN_U16("graphics/object_events/palettes/seguidores/articuno_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Articuno[] = {
    overworld_frame(sFollowerPic_Articuno, 4, 4, 0),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 1),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 2),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 3),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 4),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 5),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 6),
    overworld_frame(sFollowerPic_Articuno, 4, 4, 7),
};

static const u16 sFollowerPic_Zapdos[] = INCBIN_U16("graphics/object_events/pics/seguidores/zapdos.4bpp");
static const u16 sFollowerPal_Zapdos[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zapdos.gbapal");
static const u16 sFollowerPalShiny_Zapdos[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zapdos_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Zapdos[] = {
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 0),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 1),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 2),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 3),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 4),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 5),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 6),
    overworld_frame(sFollowerPic_Zapdos, 4, 4, 7),
};

static const u16 sFollowerPic_Moltres[] = INCBIN_U16("graphics/object_events/pics/seguidores/moltres.4bpp");
static const u16 sFollowerPal_Moltres[] = INCBIN_U16("graphics/object_events/palettes/seguidores/moltres.gbapal");
static const u16 sFollowerPalShiny_Moltres[] = INCBIN_U16("graphics/object_events/palettes/seguidores/moltres_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Moltres[] = {
    overworld_frame(sFollowerPic_Moltres, 4, 4, 0),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 1),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 2),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 3),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 4),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 5),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 6),
    overworld_frame(sFollowerPic_Moltres, 4, 4, 7),
};

static const u16 sFollowerPic_Dratini[] = INCBIN_U16("graphics/object_events/pics/seguidores/dratini.4bpp");
static const u16 sFollowerPal_Dratini[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dratini.gbapal");
static const u16 sFollowerPalShiny_Dratini[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dratini_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dratini[] = {
    overworld_frame(sFollowerPic_Dratini, 4, 4, 0),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 1),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 2),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 3),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 4),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 5),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 6),
    overworld_frame(sFollowerPic_Dratini, 4, 4, 7),
};

static const u16 sFollowerPic_Dragonair[] = INCBIN_U16("graphics/object_events/pics/seguidores/dragonair.4bpp");
static const u16 sFollowerPal_Dragonair[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dragonair.gbapal");
static const u16 sFollowerPalShiny_Dragonair[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dragonair_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dragonair[] = {
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 0),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 1),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 2),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 3),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 4),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 5),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 6),
    overworld_frame(sFollowerPic_Dragonair, 4, 4, 7),
};

static const u16 sFollowerPic_Dragonite[] = INCBIN_U16("graphics/object_events/pics/seguidores/dragonite.4bpp");
static const u16 sFollowerPal_Dragonite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dragonite.gbapal");
static const u16 sFollowerPalShiny_Dragonite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dragonite_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dragonite[] = {
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 0),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 1),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 2),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 3),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 4),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 5),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 6),
    overworld_frame(sFollowerPic_Dragonite, 4, 4, 7),
};

static const u16 sFollowerPic_Mewtwo[] = INCBIN_U16("graphics/object_events/pics/seguidores/mewtwo.4bpp");
static const u16 sFollowerPal_Mewtwo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mewtwo.gbapal");
static const u16 sFollowerPalShiny_Mewtwo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mewtwo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mewtwo[] = {
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 0),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 1),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 2),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 3),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 4),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 5),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 6),
    overworld_frame(sFollowerPic_Mewtwo, 4, 4, 7),
};

static const u16 sFollowerPic_Mew[] = INCBIN_U16("graphics/object_events/pics/seguidores/mew.4bpp");
static const u16 sFollowerPal_Mew[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mew.gbapal");
static const u16 sFollowerPalShiny_Mew[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mew_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mew[] = {
    overworld_frame(sFollowerPic_Mew, 4, 4, 0),
    overworld_frame(sFollowerPic_Mew, 4, 4, 1),
    overworld_frame(sFollowerPic_Mew, 4, 4, 2),
    overworld_frame(sFollowerPic_Mew, 4, 4, 3),
    overworld_frame(sFollowerPic_Mew, 4, 4, 4),
    overworld_frame(sFollowerPic_Mew, 4, 4, 5),
    overworld_frame(sFollowerPic_Mew, 4, 4, 6),
    overworld_frame(sFollowerPic_Mew, 4, 4, 7),
};

static const u16 sFollowerPic_Chikorita[] = INCBIN_U16("graphics/object_events/pics/seguidores/chikorita.4bpp");
static const u16 sFollowerPal_Chikorita[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chikorita.gbapal");
static const u16 sFollowerPalShiny_Chikorita[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chikorita_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Chikorita[] = {
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 0),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 1),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 2),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 3),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 4),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 5),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 6),
    overworld_frame(sFollowerPic_Chikorita, 4, 4, 7),
};

static const u16 sFollowerPic_Bayleef[] = INCBIN_U16("graphics/object_events/pics/seguidores/bayleef.4bpp");
static const u16 sFollowerPal_Bayleef[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bayleef.gbapal");
static const u16 sFollowerPalShiny_Bayleef[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bayleef_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Bayleef[] = {
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 0),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 1),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 2),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 3),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 4),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 5),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 6),
    overworld_frame(sFollowerPic_Bayleef, 4, 4, 7),
};

static const u16 sFollowerPic_Meganium[] = INCBIN_U16("graphics/object_events/pics/seguidores/meganium.4bpp");
static const u16 sFollowerPal_Meganium[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meganium.gbapal");
static const u16 sFollowerPalShiny_Meganium[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meganium_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Meganium[] = {
    overworld_frame(sFollowerPic_Meganium, 4, 4, 0),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 1),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 2),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 3),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 4),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 5),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 6),
    overworld_frame(sFollowerPic_Meganium, 4, 4, 7),
};

static const u16 sFollowerPic_Meganium_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/meganium_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_Meganium_F[] = {
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 0),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 1),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 2),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 3),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 4),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 5),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 6),
    overworld_frame(sFollowerPic_Meganium_F, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerFemale_Meganium = {
    .species = SPECIES_MEGANIUM,
    .large = FALSE,
    .formCount = 0,
    .images = sFollowerPicTable_Meganium_F,
    .palette = sFollowerPal_Meganium,
    .shinyPalette = sFollowerPalShiny_Meganium,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Cyndaquil[] = INCBIN_U16("graphics/object_events/pics/seguidores/cyndaquil.4bpp");
static const u16 sFollowerPal_Cyndaquil[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cyndaquil.gbapal");
static const u16 sFollowerPalShiny_Cyndaquil[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cyndaquil_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cyndaquil[] = {
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 0),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 1),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 2),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 3),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 4),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 5),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 6),
    overworld_frame(sFollowerPic_Cyndaquil, 4, 4, 7),
};

static const u16 sFollowerPic_Quilava[] = INCBIN_U16("graphics/object_events/pics/seguidores/quilava.4bpp");
static const u16 sFollowerPal_Quilava[] = INCBIN_U16("graphics/object_events/palettes/seguidores/quilava.gbapal");
static const u16 sFollowerPalShiny_Quilava[] = INCBIN_U16("graphics/object_events/palettes/seguidores/quilava_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Quilava[] = {
    overworld_frame(sFollowerPic_Quilava, 4, 4, 0),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 1),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 2),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 3),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 4),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 5),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 6),
    overworld_frame(sFollowerPic_Quilava, 4, 4, 7),
};

static const u16 sFollowerPic_Typhlosion[] = INCBIN_U16("graphics/object_events/pics/seguidores/typhlosion.4bpp");
static const u16 sFollowerPal_Typhlosion[] = INCBIN_U16("graphics/object_events/palettes/seguidores/typhlosion.gbapal");
static const u16 sFollowerPalShiny_Typhlosion[] = INCBIN_U16("graphics/object_events/palettes/seguidores/typhlosion_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Typhlosion[] = {
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 0),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 1),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 2),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 3),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 4),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 5),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 6),
    overworld_frame(sFollowerPic_Typhlosion, 4, 4, 7),
};

static const u16 sFollowerPic_Totodile[] = INCBIN_U16("graphics/object_events/pics/seguidores/totodile.4bpp");
static const u16 sFollowerPal_Totodile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/totodile.gbapal");
static const u16 sFollowerPalShiny_Totodile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/totodile_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Totodile[] = {
    overworld_frame(sFollowerPic_Totodile, 4, 4, 0),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 1),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 2),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 3),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 4),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 5),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 6),
    overworld_frame(sFollowerPic_Totodile, 4, 4, 7),
};

static const u16 sFollowerPic_Croconaw[] = INCBIN_U16("graphics/object_events/pics/seguidores/croconaw.4bpp");
static const u16 sFollowerPal_Croconaw[] = INCBIN_U16("graphics/object_events/palettes/seguidores/croconaw.gbapal");
static const u16 sFollowerPalShiny_Croconaw[] = INCBIN_U16("graphics/object_events/palettes/seguidores/croconaw_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Croconaw[] = {
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 0),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 1),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 2),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 3),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 4),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 5),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 6),
    overworld_frame(sFollowerPic_Croconaw, 4, 4, 7),
};

static const u16 sFollowerPic_Feraligatr[] = INCBIN_U16("graphics/object_events/pics/seguidores/feraligatr.4bpp");
static const u16 sFollowerPal_Feraligatr[] = INCBIN_U16("graphics/object_events/palettes/seguidores/feraligatr.gbapal");
static const u16 sFollowerPalShiny_Feraligatr[] = INCBIN_U16("graphics/object_events/palettes/seguidores/feraligatr_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Feraligatr[] = {
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 0),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 1),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 2),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 3),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 4),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 5),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 6),
    overworld_frame(sFollowerPic_Feraligatr, 4, 4, 7),
};

static const u16 sFollowerPic_Sentret[] = INCBIN_U16("graphics/object_events/pics/seguidores/sentret.4bpp");
static const u16 sFollowerPal_Sentret[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sentret.gbapal");
static const u16 sFollowerPalShiny_Sentret[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sentret_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sentret[] = {
    overworld_frame(sFollowerPic_Sentret, 4, 4, 0),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 1),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 2),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 3),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 4),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 5),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 6),
    overworld_frame(sFollowerPic_Sentret, 4, 4, 7),
};

static const u16 sFollowerPic_Furret[] = INCBIN_U16("graphics/object_events/pics/seguidores/furret.4bpp");
static const u16 sFollowerPal_Furret[] = INCBIN_U16("graphics/object_events/palettes/seguidores/furret.gbapal");
static const u16 sFollowerPalShiny_Furret[] = INCBIN_U16("graphics/object_events/palettes/seguidores/furret_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Furret[] = {
    overworld_frame(sFollowerPic_Furret, 4, 4, 0),
    overworld_frame(sFollowerPic_Furret, 4, 4, 1),
    overworld_frame(sFollowerPic_Furret, 4, 4, 2),
    overworld_frame(sFollowerPic_Furret, 4, 4, 3),
    overworld_frame(sFollowerPic_Furret, 4, 4, 4),
    overworld_frame(sFollowerPic_Furret, 4, 4, 5),
    overworld_frame(sFollowerPic_Furret, 4, 4, 6),
    overworld_frame(sFollowerPic_Furret, 4, 4, 7),
};

static const u16 sFollowerPic_Hoothoot[] = INCBIN_U16("graphics/object_events/pics/seguidores/hoothoot.4bpp");
static const u16 sFollowerPal_Hoothoot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hoothoot.gbapal");
static const u16 sFollowerPalShiny_Hoothoot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hoothoot_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hoothoot[] = {
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 0),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 1),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 2),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 3),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 4),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 5),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 6),
    overworld_frame(sFollowerPic_Hoothoot, 4, 4, 7),
};

static const u16 sFollowerPic_Noctowl[] = INCBIN_U16("graphics/object_events/pics/seguidores/noctowl.4bpp");
static const u16 sFollowerPal_Noctowl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/noctowl.gbapal");
static const u16 sFollowerPalShiny_Noctowl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/noctowl_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Noctowl[] = {
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 0),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 1),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 2),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 3),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 4),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 5),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 6),
    overworld_frame(sFollowerPic_Noctowl, 4, 4, 7),
};

static const u16 sFollowerPic_Ledyba[] = INCBIN_U16("graphics/object_events/pics/seguidores/ledyba.4bpp");
static const u16 sFollowerPal_Ledyba[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ledyba.gbapal");
static const u16 sFollowerPalShiny_Ledyba[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ledyba_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ledyba[] = {
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 0),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 1),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 2),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 3),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 4),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 5),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 6),
    overworld_frame(sFollowerPic_Ledyba, 4, 4, 7),
};

static const u16 sFollowerPic_Ledian[] = INCBIN_U16("graphics/object_events/pics/seguidores/ledian.4bpp");
static const u16 sFollowerPal_Ledian[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ledian.gbapal");
static const u16 sFollowerPalShiny_Ledian[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ledian_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ledian[] = {
    overworld_frame(sFollowerPic_Ledian, 4, 4, 0),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 1),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 2),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 3),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 4),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 5),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 6),
    overworld_frame(sFollowerPic_Ledian, 4, 4, 7),
};

static const u16 sFollowerPic_Spinarak[] = INCBIN_U16("graphics/object_events/pics/seguidores/spinarak.4bpp");
static const u16 sFollowerPal_Spinarak[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spinarak.gbapal");
static const u16 sFollowerPalShiny_Spinarak[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spinarak_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Spinarak[] = {
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 0),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 1),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 2),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 3),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 4),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 5),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 6),
    overworld_frame(sFollowerPic_Spinarak, 4, 4, 7),
};

static const u16 sFollowerPic_Ariados[] = INCBIN_U16("graphics/object_events/pics/seguidores/ariados.4bpp");
static const u16 sFollowerPal_Ariados[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ariados.gbapal");
static const u16 sFollowerPalShiny_Ariados[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ariados_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ariados[] = {
    overworld_frame(sFollowerPic_Ariados, 4, 4, 0),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 1),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 2),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 3),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 4),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 5),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 6),
    overworld_frame(sFollowerPic_Ariados, 4, 4, 7),
};

static const u16 sFollowerPic_Crobat[] = INCBIN_U16("graphics/object_events/pics/seguidores/crobat.4bpp");
static const u16 sFollowerPal_Crobat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/crobat.gbapal");
static const u16 sFollowerPalShiny_Crobat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/crobat_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Crobat[] = {
    overworld_frame(sFollowerPic_Crobat, 4, 4, 0),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 1),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 2),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 3),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 4),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 5),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 6),
    overworld_frame(sFollowerPic_Crobat, 4, 4, 7),
};

static const u16 sFollowerPic_Chinchou[] = INCBIN_U16("graphics/object_events/pics/seguidores/chinchou.4bpp");
static const u16 sFollowerPal_Chinchou[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chinchou.gbapal");
static const u16 sFollowerPalShiny_Chinchou[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chinchou_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Chinchou[] = {
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 0),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 1),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 2),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 3),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 4),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 5),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 6),
    overworld_frame(sFollowerPic_Chinchou, 4, 4, 7),
};

static const u16 sFollowerPic_Lanturn[] = INCBIN_U16("graphics/object_events/pics/seguidores/lanturn.4bpp");
static const u16 sFollowerPal_Lanturn[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lanturn.gbapal");
static const u16 sFollowerPalShiny_Lanturn[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lanturn_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lanturn[] = {
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 0),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 1),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 2),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 3),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 4),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 5),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 6),
    overworld_frame(sFollowerPic_Lanturn, 4, 4, 7),
};

static const u16 sFollowerPic_Pichu[] = INCBIN_U16("graphics/object_events/pics/seguidores/pichu.4bpp");
static const u16 sFollowerPal_Pichu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pichu.gbapal");
static const u16 sFollowerPalShiny_Pichu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pichu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pichu[] = {
    overworld_frame(sFollowerPic_Pichu, 4, 4, 0),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 1),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 2),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 3),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 4),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 5),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 6),
    overworld_frame(sFollowerPic_Pichu, 4, 4, 7),
};

static const u16 sFollowerPic_Cleffa[] = INCBIN_U16("graphics/object_events/pics/seguidores/cleffa.4bpp");
static const u16 sFollowerPal_Cleffa[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cleffa.gbapal");
static const u16 sFollowerPalShiny_Cleffa[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cleffa_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cleffa[] = {
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 0),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 1),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 2),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 3),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 4),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 5),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 6),
    overworld_frame(sFollowerPic_Cleffa, 4, 4, 7),
};

static const u16 sFollowerPic_Igglybuff[] = INCBIN_U16("graphics/object_events/pics/seguidores/igglybuff.4bpp");
static const u16 sFollowerPal_Igglybuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/igglybuff.gbapal");
static const u16 sFollowerPalShiny_Igglybuff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/igglybuff_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Igglybuff[] = {
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 0),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 1),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 2),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 3),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 4),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 5),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 6),
    overworld_frame(sFollowerPic_Igglybuff, 4, 4, 7),
};

static const u16 sFollowerPic_Togepi[] = INCBIN_U16("graphics/object_events/pics/seguidores/togepi.4bpp");
static const u16 sFollowerPal_Togepi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/togepi.gbapal");
static const u16 sFollowerPalShiny_Togepi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/togepi_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Togepi[] = {
    overworld_frame(sFollowerPic_Togepi, 4, 4, 0),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 1),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 2),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 3),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 4),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 5),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 6),
    overworld_frame(sFollowerPic_Togepi, 4, 4, 7),
};

static const u16 sFollowerPic_Togetic[] = INCBIN_U16("graphics/object_events/pics/seguidores/togetic.4bpp");
static const u16 sFollowerPal_Togetic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/togetic.gbapal");
static const u16 sFollowerPalShiny_Togetic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/togetic_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Togetic[] = {
    overworld_frame(sFollowerPic_Togetic, 4, 4, 0),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 1),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 2),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 3),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 4),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 5),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 6),
    overworld_frame(sFollowerPic_Togetic, 4, 4, 7),
};

static const u16 sFollowerPic_Natu[] = INCBIN_U16("graphics/object_events/pics/seguidores/natu.4bpp");
static const u16 sFollowerPal_Natu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/natu.gbapal");
static const u16 sFollowerPalShiny_Natu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/natu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Natu[] = {
    overworld_frame(sFollowerPic_Natu, 4, 4, 0),
    overworld_frame(sFollowerPic_Natu, 4, 4, 1),
    overworld_frame(sFollowerPic_Natu, 4, 4, 2),
    overworld_frame(sFollowerPic_Natu, 4, 4, 3),
    overworld_frame(sFollowerPic_Natu, 4, 4, 4),
    overworld_frame(sFollowerPic_Natu, 4, 4, 5),
    overworld_frame(sFollowerPic_Natu, 4, 4, 6),
    overworld_frame(sFollowerPic_Natu, 4, 4, 7),
};

static const u16 sFollowerPic_Xatu[] = INCBIN_U16("graphics/object_events/pics/seguidores/xatu.4bpp");
static const u16 sFollowerPal_Xatu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/xatu.gbapal");
static const u16 sFollowerPalShiny_Xatu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/xatu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Xatu[] = {
    overworld_frame(sFollowerPic_Xatu, 4, 4, 0),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 1),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 2),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 3),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 4),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 5),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 6),
    overworld_frame(sFollowerPic_Xatu, 4, 4, 7),
};

static const u16 sFollowerPic_Mareep[] = INCBIN_U16("graphics/object_events/pics/seguidores/mareep.4bpp");
static const u16 sFollowerPal_Mareep[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mareep.gbapal");
static const u16 sFollowerPalShiny_Mareep[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mareep_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mareep[] = {
    overworld_frame(sFollowerPic_Mareep, 4, 4, 0),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 1),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 2),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 3),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 4),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 5),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 6),
    overworld_frame(sFollowerPic_Mareep, 4, 4, 7),
};

static const u16 sFollowerPic_Flaaffy[] = INCBIN_U16("graphics/object_events/pics/seguidores/flaaffy.4bpp");
static const u16 sFollowerPal_Flaaffy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flaaffy.gbapal");
static const u16 sFollowerPalShiny_Flaaffy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flaaffy_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Flaaffy[] = {
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 0),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 1),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 2),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 3),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 4),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 5),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 6),
    overworld_frame(sFollowerPic_Flaaffy, 4, 4, 7),
};

static const u16 sFollowerPic_Ampharos[] = INCBIN_U16("graphics/object_events/pics/seguidores/ampharos.4bpp");
static const u16 sFollowerPal_Ampharos[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ampharos.gbapal");
static const u16 sFollowerPalShiny_Ampharos[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ampharos_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ampharos[] = {
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 0),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 1),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 2),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 3),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 4),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 5),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 6),
    overworld_frame(sFollowerPic_Ampharos, 4, 4, 7),
};

static const u16 sFollowerPic_Bellossom[] = INCBIN_U16("graphics/object_events/pics/seguidores/bellossom.4bpp");
static const u16 sFollowerPal_Bellossom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bellossom.gbapal");
static const u16 sFollowerPalShiny_Bellossom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bellossom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Bellossom[] = {
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 0),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 1),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 2),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 3),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 4),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 5),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 6),
    overworld_frame(sFollowerPic_Bellossom, 4, 4, 7),
};

static const u16 sFollowerPic_Marill[] = INCBIN_U16("graphics/object_events/pics/seguidores/marill.4bpp");
static const u16 sFollowerPal_Marill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marill.gbapal");
static const u16 sFollowerPalShiny_Marill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marill_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Marill[] = {
    overworld_frame(sFollowerPic_Marill, 4, 4, 0),
    overworld_frame(sFollowerPic_Marill, 4, 4, 1),
    overworld_frame(sFollowerPic_Marill, 4, 4, 2),
    overworld_frame(sFollowerPic_Marill, 4, 4, 3),
    overworld_frame(sFollowerPic_Marill, 4, 4, 4),
    overworld_frame(sFollowerPic_Marill, 4, 4, 5),
    overworld_frame(sFollowerPic_Marill, 4, 4, 6),
    overworld_frame(sFollowerPic_Marill, 4, 4, 7),
};

static const u16 sFollowerPic_Azumarill[] = INCBIN_U16("graphics/object_events/pics/seguidores/azumarill.4bpp");
static const u16 sFollowerPal_Azumarill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/azumarill.gbapal");
static const u16 sFollowerPalShiny_Azumarill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/azumarill_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Azumarill[] = {
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 0),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 1),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 2),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 3),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 4),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 5),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 6),
    overworld_frame(sFollowerPic_Azumarill, 4, 4, 7),
};

static const u16 sFollowerPic_Sudowoodo[] = INCBIN_U16("graphics/object_events/pics/seguidores/sudowoodo.4bpp");
static const u16 sFollowerPal_Sudowoodo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sudowoodo.gbapal");
static const u16 sFollowerPalShiny_Sudowoodo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sudowoodo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sudowoodo[] = {
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 0),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 1),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 2),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 3),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 4),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 5),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 6),
    overworld_frame(sFollowerPic_Sudowoodo, 4, 4, 7),
};

static const u16 sFollowerPic_Politoed[] = INCBIN_U16("graphics/object_events/pics/seguidores/politoed.4bpp");
static const u16 sFollowerPal_Politoed[] = INCBIN_U16("graphics/object_events/palettes/seguidores/politoed.gbapal");
static const u16 sFollowerPalShiny_Politoed[] = INCBIN_U16("graphics/object_events/palettes/seguidores/politoed_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Politoed[] = {
    overworld_frame(sFollowerPic_Politoed, 4, 4, 0),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 1),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 2),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 3),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 4),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 5),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 6),
    overworld_frame(sFollowerPic_Politoed, 4, 4, 7),
};

static const u16 sFollowerPic_Hoppip[] = INCBIN_U16("graphics/object_events/pics/seguidores/hoppip.4bpp");
static const u16 sFollowerPal_Hoppip[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hoppip.gbapal");
static const u16 sFollowerPalShiny_Hoppip[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hoppip_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hoppip[] = {
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 0),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 1),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 2),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 3),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 4),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 5),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 6),
    overworld_frame(sFollowerPic_Hoppip, 4, 4, 7),
};

static const u16 sFollowerPic_Skiploom[] = INCBIN_U16("graphics/object_events/pics/seguidores/skiploom.4bpp");
static const u16 sFollowerPal_Skiploom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skiploom.gbapal");
static const u16 sFollowerPalShiny_Skiploom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skiploom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Skiploom[] = {
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 0),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 1),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 2),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 3),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 4),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 5),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 6),
    overworld_frame(sFollowerPic_Skiploom, 4, 4, 7),
};

static const u16 sFollowerPic_Jumpluff[] = INCBIN_U16("graphics/object_events/pics/seguidores/jumpluff.4bpp");
static const u16 sFollowerPal_Jumpluff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jumpluff.gbapal");
static const u16 sFollowerPalShiny_Jumpluff[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jumpluff_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Jumpluff[] = {
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 0),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 1),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 2),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 3),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 4),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 5),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 6),
    overworld_frame(sFollowerPic_Jumpluff, 4, 4, 7),
};

static const u16 sFollowerPic_Aipom[] = INCBIN_U16("graphics/object_events/pics/seguidores/aipom.4bpp");
static const u16 sFollowerPal_Aipom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aipom.gbapal");
static const u16 sFollowerPalShiny_Aipom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aipom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Aipom[] = {
    overworld_frame(sFollowerPic_Aipom, 4, 4, 0),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 1),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 2),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 3),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 4),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 5),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 6),
    overworld_frame(sFollowerPic_Aipom, 4, 4, 7),
};

static const u16 sFollowerPic_Sunkern[] = INCBIN_U16("graphics/object_events/pics/seguidores/sunkern.4bpp");
static const u16 sFollowerPal_Sunkern[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sunkern.gbapal");
static const u16 sFollowerPalShiny_Sunkern[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sunkern_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sunkern[] = {
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 0),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 1),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 2),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 3),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 4),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 5),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 6),
    overworld_frame(sFollowerPic_Sunkern, 4, 4, 7),
};

static const u16 sFollowerPic_Sunflora[] = INCBIN_U16("graphics/object_events/pics/seguidores/sunflora.4bpp");
static const u16 sFollowerPal_Sunflora[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sunflora.gbapal");
static const u16 sFollowerPalShiny_Sunflora[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sunflora_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sunflora[] = {
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 0),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 1),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 2),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 3),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 4),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 5),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 6),
    overworld_frame(sFollowerPic_Sunflora, 4, 4, 7),
};

static const u16 sFollowerPic_Yanma[] = INCBIN_U16("graphics/object_events/pics/seguidores/yanma.4bpp");
static const u16 sFollowerPal_Yanma[] = INCBIN_U16("graphics/object_events/palettes/seguidores/yanma.gbapal");
static const u16 sFollowerPalShiny_Yanma[] = INCBIN_U16("graphics/object_events/palettes/seguidores/yanma_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Yanma[] = {
    overworld_frame(sFollowerPic_Yanma, 4, 4, 0),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 1),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 2),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 3),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 4),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 5),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 6),
    overworld_frame(sFollowerPic_Yanma, 4, 4, 7),
};

static const u16 sFollowerPic_Wooper[] = INCBIN_U16("graphics/object_events/pics/seguidores/wooper.4bpp");
static const u16 sFollowerPal_Wooper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wooper.gbapal");
static const u16 sFollowerPalShiny_Wooper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wooper_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wooper[] = {
    overworld_frame(sFollowerPic_Wooper, 4, 4, 0),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 1),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 2),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 3),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 4),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 5),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 6),
    overworld_frame(sFollowerPic_Wooper, 4, 4, 7),
};

static const u16 sFollowerPic_Quagsire[] = INCBIN_U16("graphics/object_events/pics/seguidores/quagsire.4bpp");
static const u16 sFollowerPal_Quagsire[] = INCBIN_U16("graphics/object_events/palettes/seguidores/quagsire.gbapal");
static const u16 sFollowerPalShiny_Quagsire[] = INCBIN_U16("graphics/object_events/palettes/seguidores/quagsire_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Quagsire[] = {
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 0),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 1),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 2),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 3),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 4),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 5),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 6),
    overworld_frame(sFollowerPic_Quagsire, 4, 4, 7),
};

static const u16 sFollowerPic_Espeon[] = INCBIN_U16("graphics/object_events/pics/seguidores/espeon.4bpp");
static const u16 sFollowerPal_Espeon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/espeon.gbapal");
static const u16 sFollowerPalShiny_Espeon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/espeon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Espeon[] = {
    overworld_frame(sFollowerPic_Espeon, 4, 4, 0),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 1),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 2),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 3),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 4),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 5),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 6),
    overworld_frame(sFollowerPic_Espeon, 4, 4, 7),
};

static const u16 sFollowerPic_Umbreon[] = INCBIN_U16("graphics/object_events/pics/seguidores/umbreon.4bpp");
static const u16 sFollowerPal_Umbreon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/umbreon.gbapal");
static const u16 sFollowerPalShiny_Umbreon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/umbreon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Umbreon[] = {
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 0),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 1),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 2),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 3),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 4),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 5),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 6),
    overworld_frame(sFollowerPic_Umbreon, 4, 4, 7),
};

static const u16 sFollowerPic_Murkrow[] = INCBIN_U16("graphics/object_events/pics/seguidores/murkrow.4bpp");
static const u16 sFollowerPal_Murkrow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/murkrow.gbapal");
static const u16 sFollowerPalShiny_Murkrow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/murkrow_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Murkrow[] = {
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 0),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 1),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 2),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 3),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 4),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 5),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 6),
    overworld_frame(sFollowerPic_Murkrow, 4, 4, 7),
};

static const u16 sFollowerPic_Slowking[] = INCBIN_U16("graphics/object_events/pics/seguidores/slowking.4bpp");
static const u16 sFollowerPal_Slowking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowking.gbapal");
static const u16 sFollowerPalShiny_Slowking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slowking_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slowking[] = {
    overworld_frame(sFollowerPic_Slowking, 4, 4, 0),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 1),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 2),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 3),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 4),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 5),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 6),
    overworld_frame(sFollowerPic_Slowking, 4, 4, 7),
};

static const u16 sFollowerPic_Misdreavus[] = INCBIN_U16("graphics/object_events/pics/seguidores/misdreavus.4bpp");
static const u16 sFollowerPal_Misdreavus[] = INCBIN_U16("graphics/object_events/palettes/seguidores/misdreavus.gbapal");
static const u16 sFollowerPalShiny_Misdreavus[] = INCBIN_U16("graphics/object_events/palettes/seguidores/misdreavus_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Misdreavus[] = {
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 0),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 1),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 2),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 3),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 4),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 5),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 6),
    overworld_frame(sFollowerPic_Misdreavus, 4, 4, 7),
};

static const u16 sFollowerPic_UnownA[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_a.4bpp");
static const u16 sFollowerPal_UnownA[] = INCBIN_U16("graphics/object_events/palettes/seguidores/unown_a.gbapal");
static const u16 sFollowerPalShiny_UnownA[] = INCBIN_U16("graphics/object_events/palettes/seguidores/unown_a_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_UnownA[] = {
    overworld_frame(sFollowerPic_UnownA, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownA, 4, 4, 7),
};

static const u16 sFollowerPic_UnownB[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_b.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownB[] = {
    overworld_frame(sFollowerPic_UnownB, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownB, 4, 4, 7),
};

static const u16 sFollowerPic_UnownC[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_c.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownC[] = {
    overworld_frame(sFollowerPic_UnownC, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownC, 4, 4, 7),
};

static const u16 sFollowerPic_UnownD[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_d.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownD[] = {
    overworld_frame(sFollowerPic_UnownD, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownD, 4, 4, 7),
};

static const u16 sFollowerPic_UnownE[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_e.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownE[] = {
    overworld_frame(sFollowerPic_UnownE, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownE, 4, 4, 7),
};

static const u16 sFollowerPic_UnownF[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownF[] = {
    overworld_frame(sFollowerPic_UnownF, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownF, 4, 4, 7),
};

static const u16 sFollowerPic_UnownG[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_g.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownG[] = {
    overworld_frame(sFollowerPic_UnownG, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownG, 4, 4, 7),
};

static const u16 sFollowerPic_UnownH[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_h.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownH[] = {
    overworld_frame(sFollowerPic_UnownH, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownH, 4, 4, 7),
};

static const u16 sFollowerPic_UnownI[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_i.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownI[] = {
    overworld_frame(sFollowerPic_UnownI, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownI, 4, 4, 7),
};

static const u16 sFollowerPic_UnownJ[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_j.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownJ[] = {
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownJ, 4, 4, 7),
};

static const u16 sFollowerPic_UnownK[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_k.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownK[] = {
    overworld_frame(sFollowerPic_UnownK, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownK, 4, 4, 7),
};

static const u16 sFollowerPic_UnownL[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_l.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownL[] = {
    overworld_frame(sFollowerPic_UnownL, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownL, 4, 4, 7),
};

static const u16 sFollowerPic_UnownM[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_m.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownM[] = {
    overworld_frame(sFollowerPic_UnownM, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownM, 4, 4, 7),
};

static const u16 sFollowerPic_UnownN[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_n.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownN[] = {
    overworld_frame(sFollowerPic_UnownN, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownN, 4, 4, 7),
};

static const u16 sFollowerPic_UnownO[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_o.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownO[] = {
    overworld_frame(sFollowerPic_UnownO, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownO, 4, 4, 7),
};

static const u16 sFollowerPic_UnownP[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_p.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownP[] = {
    overworld_frame(sFollowerPic_UnownP, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownP, 4, 4, 7),
};

static const u16 sFollowerPic_UnownQ[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_q.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownQ[] = {
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownQ, 4, 4, 7),
};

static const u16 sFollowerPic_UnownR[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_r.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownR[] = {
    overworld_frame(sFollowerPic_UnownR, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownR, 4, 4, 7),
};

static const u16 sFollowerPic_UnownS[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_s.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownS[] = {
    overworld_frame(sFollowerPic_UnownS, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownS, 4, 4, 7),
};

static const u16 sFollowerPic_UnownT[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_t.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownT[] = {
    overworld_frame(sFollowerPic_UnownT, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownT, 4, 4, 7),
};

static const u16 sFollowerPic_UnownU[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_u.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownU[] = {
    overworld_frame(sFollowerPic_UnownU, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownU, 4, 4, 7),
};

static const u16 sFollowerPic_UnownV[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_v.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownV[] = {
    overworld_frame(sFollowerPic_UnownV, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownV, 4, 4, 7),
};

static const u16 sFollowerPic_UnownW[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_w.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownW[] = {
    overworld_frame(sFollowerPic_UnownW, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownW, 4, 4, 7),
};

static const u16 sFollowerPic_UnownX[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_x.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownX[] = {
    overworld_frame(sFollowerPic_UnownX, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownX, 4, 4, 7),
};

static const u16 sFollowerPic_UnownY[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_y.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownY[] = {
    overworld_frame(sFollowerPic_UnownY, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownY, 4, 4, 7),
};

static const u16 sFollowerPic_UnownZ[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_z.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownZ[] = {
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownZ, 4, 4, 7),
};

static const u16 sFollowerPic_UnownExclamation[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_exclamation.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownExclamation[] = {
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownExclamation, 4, 4, 7),
};

static const u16 sFollowerPic_UnownQuestion[] = INCBIN_U16("graphics/object_events/pics/seguidores/unown_question.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_UnownQuestion[] = {
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 0),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 1),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 2),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 3),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 4),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 5),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 6),
    overworld_frame(sFollowerPic_UnownQuestion, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerForms_Unown[28] = {
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownA,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownB,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownC,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownD,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownE,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownF,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownG,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownH,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownI,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownJ,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownK,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownL,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownM,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownN,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownO,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownP,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownQ,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownR,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownS,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownT,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownU,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownV,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownW,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownX,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownY,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownZ,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownExclamation,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
    {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_UnownQuestion,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = NULL,
    },
};

static const u16 sFollowerPic_Wobbuffet[] = INCBIN_U16("graphics/object_events/pics/seguidores/wobbuffet.4bpp");
static const u16 sFollowerPal_Wobbuffet[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wobbuffet.gbapal");
static const u16 sFollowerPalShiny_Wobbuffet[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wobbuffet_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wobbuffet[] = {
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 0),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 1),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 2),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 3),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 4),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 5),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 6),
    overworld_frame(sFollowerPic_Wobbuffet, 4, 4, 7),
};

static const u16 sFollowerPic_Wobbuffet_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/wobbuffet_f.4bpp");
static const u16 sFollowerPal_Wobbuffet_F[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wobbuffet_f.gbapal");
static const u16 sFollowerPalShiny_Wobbuffet_F[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wobbuffet_f_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wobbuffet_F[] = {
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 0),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 1),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 2),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 3),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 4),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 5),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 6),
    overworld_frame(sFollowerPic_Wobbuffet_F, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerFemale_Wobbuffet = {
    .species = SPECIES_WOBBUFFET,
    .large = FALSE,
    .formCount = 0,
    .images = sFollowerPicTable_Wobbuffet_F,
    .palette = sFollowerPal_Wobbuffet_F,
    .shinyPalette = sFollowerPalShiny_Wobbuffet_F,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Girafarig[] = INCBIN_U16("graphics/object_events/pics/seguidores/girafarig.4bpp");
static const u16 sFollowerPal_Girafarig[] = INCBIN_U16("graphics/object_events/palettes/seguidores/girafarig.gbapal");
static const u16 sFollowerPalShiny_Girafarig[] = INCBIN_U16("graphics/object_events/palettes/seguidores/girafarig_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Girafarig[] = {
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 0),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 1),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 2),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 3),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 4),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 5),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 6),
    overworld_frame(sFollowerPic_Girafarig, 4, 4, 7),
};

static const u16 sFollowerPic_Pineco[] = INCBIN_U16("graphics/object_events/pics/seguidores/pineco.4bpp");
static const u16 sFollowerPal_Pineco[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pineco.gbapal");
static const u16 sFollowerPalShiny_Pineco[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pineco_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pineco[] = {
    overworld_frame(sFollowerPic_Pineco, 4, 4, 0),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 1),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 2),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 3),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 4),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 5),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 6),
    overworld_frame(sFollowerPic_Pineco, 4, 4, 7),
};

static const u16 sFollowerPic_Forretress[] = INCBIN_U16("graphics/object_events/pics/seguidores/forretress.4bpp");
static const u16 sFollowerPal_Forretress[] = INCBIN_U16("graphics/object_events/palettes/seguidores/forretress.gbapal");
static const u16 sFollowerPalShiny_Forretress[] = INCBIN_U16("graphics/object_events/palettes/seguidores/forretress_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Forretress[] = {
    overworld_frame(sFollowerPic_Forretress, 4, 4, 0),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 1),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 2),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 3),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 4),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 5),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 6),
    overworld_frame(sFollowerPic_Forretress, 4, 4, 7),
};

static const u16 sFollowerPic_Dunsparce[] = INCBIN_U16("graphics/object_events/pics/seguidores/dunsparce.4bpp");
static const u16 sFollowerPal_Dunsparce[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dunsparce.gbapal");
static const u16 sFollowerPalShiny_Dunsparce[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dunsparce_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dunsparce[] = {
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 0),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 1),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 2),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 3),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 4),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 5),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 6),
    overworld_frame(sFollowerPic_Dunsparce, 4, 4, 7),
};

static const u16 sFollowerPic_Gligar[] = INCBIN_U16("graphics/object_events/pics/seguidores/gligar.4bpp");
static const u16 sFollowerPal_Gligar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gligar.gbapal");
static const u16 sFollowerPalShiny_Gligar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gligar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gligar[] = {
    overworld_frame(sFollowerPic_Gligar, 4, 4, 0),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 1),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 2),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 3),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 4),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 5),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 6),
    overworld_frame(sFollowerPic_Gligar, 4, 4, 7),
};

static const u16 sFollowerPic_Steelix[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/steelix.4bpp");
static const u16 sFollowerPal_Steelix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/steelix.gbapal");
static const u16 sFollowerPalShiny_Steelix[] = INCBIN_U16("graphics/object_events/palettes/seguidores/steelix_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Steelix[] = {
    overworld_frame(sFollowerPic_Steelix, 8, 8, 0),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 1),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 2),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 3),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 4),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 5),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 6),
    overworld_frame(sFollowerPic_Steelix, 8, 8, 7),
};

static const u16 sFollowerPic_Steelix_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/steelix_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_Steelix_F[] = {
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 0),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 1),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 2),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 3),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 4),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 5),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 6),
    overworld_frame(sFollowerPic_Steelix_F, 8, 8, 7),
};

static const struct FollowerSpecies sFollowerFemale_Steelix = {
    .species = SPECIES_STEELIX,
    .large = TRUE,
    .formCount = 0,
    .images = sFollowerPicTable_Steelix_F,
    .palette = sFollowerPal_Steelix,
    .shinyPalette = sFollowerPalShiny_Steelix,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Snubbull[] = INCBIN_U16("graphics/object_events/pics/seguidores/snubbull.4bpp");
static const u16 sFollowerPal_Snubbull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snubbull.gbapal");
static const u16 sFollowerPalShiny_Snubbull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snubbull_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Snubbull[] = {
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 0),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 1),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 2),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 3),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 4),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 5),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 6),
    overworld_frame(sFollowerPic_Snubbull, 4, 4, 7),
};

static const u16 sFollowerPic_Granbull[] = INCBIN_U16("graphics/object_events/pics/seguidores/granbull.4bpp");
static const u16 sFollowerPal_Granbull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/granbull.gbapal");
static const u16 sFollowerPalShiny_Granbull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/granbull_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Granbull[] = {
    overworld_frame(sFollowerPic_Granbull, 4, 4, 0),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 1),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 2),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 3),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 4),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 5),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 6),
    overworld_frame(sFollowerPic_Granbull, 4, 4, 7),
};

static const u16 sFollowerPic_Qwilfish[] = INCBIN_U16("graphics/object_events/pics/seguidores/qwilfish.4bpp");
static const u16 sFollowerPal_Qwilfish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/qwilfish.gbapal");
static const u16 sFollowerPalShiny_Qwilfish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/qwilfish_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Qwilfish[] = {
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 0),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 1),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 2),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 3),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 4),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 5),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 6),
    overworld_frame(sFollowerPic_Qwilfish, 4, 4, 7),
};

static const u16 sFollowerPic_Scizor[] = INCBIN_U16("graphics/object_events/pics/seguidores/scizor.4bpp");
static const u16 sFollowerPal_Scizor[] = INCBIN_U16("graphics/object_events/palettes/seguidores/scizor.gbapal");
static const u16 sFollowerPalShiny_Scizor[] = INCBIN_U16("graphics/object_events/palettes/seguidores/scizor_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Scizor[] = {
    overworld_frame(sFollowerPic_Scizor, 4, 4, 0),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 1),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 2),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 3),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 4),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 5),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 6),
    overworld_frame(sFollowerPic_Scizor, 4, 4, 7),
};

static const u16 sFollowerPic_Shuckle[] = INCBIN_U16("graphics/object_events/pics/seguidores/shuckle.4bpp");
static const u16 sFollowerPal_Shuckle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shuckle.gbapal");
static const u16 sFollowerPalShiny_Shuckle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shuckle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shuckle[] = {
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 0),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 1),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 2),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 3),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 4),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 5),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 6),
    overworld_frame(sFollowerPic_Shuckle, 4, 4, 7),
};

static const u16 sFollowerPic_Heracross[] = INCBIN_U16("graphics/object_events/pics/seguidores/heracross.4bpp");
static const u16 sFollowerPal_Heracross[] = INCBIN_U16("graphics/object_events/palettes/seguidores/heracross.gbapal");
static const u16 sFollowerPalShiny_Heracross[] = INCBIN_U16("graphics/object_events/palettes/seguidores/heracross_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Heracross[] = {
    overworld_frame(sFollowerPic_Heracross, 4, 4, 0),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 1),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 2),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 3),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 4),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 5),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 6),
    overworld_frame(sFollowerPic_Heracross, 4, 4, 7),
};

static const u16 sFollowerPic_Heracross_F[] = INCBIN_U16("graphics/object_events/pics/seguidores/heracross_f.4bpp");
static const struct SpriteFrameImage sFollowerPicTable_Heracross_F[] = {
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 0),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 1),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 2),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 3),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 4),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 5),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 6),
    overworld_frame(sFollowerPic_Heracross_F, 4, 4, 7),
};

static const struct FollowerSpecies sFollowerFemale_Heracross = {
    .species = SPECIES_HERACROSS,
    .large = FALSE,
    .formCount = 0,
    .images = sFollowerPicTable_Heracross_F,
    .palette = sFollowerPal_Heracross,
    .shinyPalette = sFollowerPalShiny_Heracross,
    .female = NULL,
    .forms = NULL,
};

static const u16 sFollowerPic_Sneasel[] = INCBIN_U16("graphics/object_events/pics/seguidores/sneasel.4bpp");
static const u16 sFollowerPal_Sneasel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sneasel.gbapal");
static const u16 sFollowerPalShiny_Sneasel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sneasel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sneasel[] = {
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 0),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 1),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 2),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 3),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 4),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 5),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 6),
    overworld_frame(sFollowerPic_Sneasel, 4, 4, 7),
};

static const u16 sFollowerPic_Teddiursa[] = INCBIN_U16("graphics/object_events/pics/seguidores/teddiursa.4bpp");
static const u16 sFollowerPal_Teddiursa[] = INCBIN_U16("graphics/object_events/palettes/seguidores/teddiursa.gbapal");
static const u16 sFollowerPalShiny_Teddiursa[] = INCBIN_U16("graphics/object_events/palettes/seguidores/teddiursa_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Teddiursa[] = {
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 0),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 1),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 2),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 3),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 4),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 5),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 6),
    overworld_frame(sFollowerPic_Teddiursa, 4, 4, 7),
};

static const u16 sFollowerPic_Ursaring[] = INCBIN_U16("graphics/object_events/pics/seguidores/ursaring.4bpp");
static const u16 sFollowerPal_Ursaring[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ursaring.gbapal");
static const u16 sFollowerPalShiny_Ursaring[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ursaring_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ursaring[] = {
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 0),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 1),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 2),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 3),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 4),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 5),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 6),
    overworld_frame(sFollowerPic_Ursaring, 4, 4, 7),
};

static const u16 sFollowerPic_Slugma[] = INCBIN_U16("graphics/object_events/pics/seguidores/slugma.4bpp");
static const u16 sFollowerPal_Slugma[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slugma.gbapal");
static const u16 sFollowerPalShiny_Slugma[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slugma_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slugma[] = {
    overworld_frame(sFollowerPic_Slugma, 4, 4, 0),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 1),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 2),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 3),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 4),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 5),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 6),
    overworld_frame(sFollowerPic_Slugma, 4, 4, 7),
};

static const u16 sFollowerPic_Magcargo[] = INCBIN_U16("graphics/object_events/pics/seguidores/magcargo.4bpp");
static const u16 sFollowerPal_Magcargo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magcargo.gbapal");
static const u16 sFollowerPalShiny_Magcargo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magcargo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magcargo[] = {
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 0),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 1),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 2),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 3),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 4),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 5),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 6),
    overworld_frame(sFollowerPic_Magcargo, 4, 4, 7),
};

static const u16 sFollowerPic_Swinub[] = INCBIN_U16("graphics/object_events/pics/seguidores/swinub.4bpp");
static const u16 sFollowerPal_Swinub[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swinub.gbapal");
static const u16 sFollowerPalShiny_Swinub[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swinub_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Swinub[] = {
    overworld_frame(sFollowerPic_Swinub, 4, 4, 0),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 1),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 2),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 3),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 4),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 5),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 6),
    overworld_frame(sFollowerPic_Swinub, 4, 4, 7),
};

static const u16 sFollowerPic_Piloswine[] = INCBIN_U16("graphics/object_events/pics/seguidores/piloswine.4bpp");
static const u16 sFollowerPal_Piloswine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/piloswine.gbapal");
static const u16 sFollowerPalShiny_Piloswine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/piloswine_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Piloswine[] = {
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 0),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 1),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 2),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 3),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 4),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 5),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 6),
    overworld_frame(sFollowerPic_Piloswine, 4, 4, 7),
};

static const u16 sFollowerPic_Corsola[] = INCBIN_U16("graphics/object_events/pics/seguidores/corsola.4bpp");
static const u16 sFollowerPal_Corsola[] = INCBIN_U16("graphics/object_events/palettes/seguidores/corsola.gbapal");
static const u16 sFollowerPalShiny_Corsola[] = INCBIN_U16("graphics/object_events/palettes/seguidores/corsola_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Corsola[] = {
    overworld_frame(sFollowerPic_Corsola, 4, 4, 0),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 1),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 2),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 3),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 4),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 5),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 6),
    overworld_frame(sFollowerPic_Corsola, 4, 4, 7),
};

static const u16 sFollowerPic_Remoraid[] = INCBIN_U16("graphics/object_events/pics/seguidores/remoraid.4bpp");
static const u16 sFollowerPal_Remoraid[] = INCBIN_U16("graphics/object_events/palettes/seguidores/remoraid.gbapal");
static const u16 sFollowerPalShiny_Remoraid[] = INCBIN_U16("graphics/object_events/palettes/seguidores/remoraid_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Remoraid[] = {
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 0),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 1),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 2),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 3),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 4),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 5),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 6),
    overworld_frame(sFollowerPic_Remoraid, 4, 4, 7),
};

static const u16 sFollowerPic_Octillery[] = INCBIN_U16("graphics/object_events/pics/seguidores/octillery.4bpp");
static const u16 sFollowerPal_Octillery[] = INCBIN_U16("graphics/object_events/palettes/seguidores/octillery.gbapal");
static const u16 sFollowerPalShiny_Octillery[] = INCBIN_U16("graphics/object_events/palettes/seguidores/octillery_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Octillery[] = {
    overworld_frame(sFollowerPic_Octillery, 4, 4, 0),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 1),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 2),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 3),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 4),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 5),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 6),
    overworld_frame(sFollowerPic_Octillery, 4, 4, 7),
};

static const u16 sFollowerPic_Delibird[] = INCBIN_U16("graphics/object_events/pics/seguidores/delibird.4bpp");
static const u16 sFollowerPal_Delibird[] = INCBIN_U16("graphics/object_events/palettes/seguidores/delibird.gbapal");
static const u16 sFollowerPalShiny_Delibird[] = INCBIN_U16("graphics/object_events/palettes/seguidores/delibird_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Delibird[] = {
    overworld_frame(sFollowerPic_Delibird, 4, 4, 0),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 1),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 2),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 3),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 4),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 5),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 6),
    overworld_frame(sFollowerPic_Delibird, 4, 4, 7),
};

static const u16 sFollowerPic_Mantine[] = INCBIN_U16("graphics/object_events/pics/seguidores/mantine.4bpp");
static const u16 sFollowerPal_Mantine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mantine.gbapal");
static const u16 sFollowerPalShiny_Mantine[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mantine_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mantine[] = {
    overworld_frame(sFollowerPic_Mantine, 4, 4, 0),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 1),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 2),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 3),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 4),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 5),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 6),
    overworld_frame(sFollowerPic_Mantine, 4, 4, 7),
};

static const u16 sFollowerPic_Skarmory[] = INCBIN_U16("graphics/object_events/pics/seguidores/skarmory.4bpp");
static const u16 sFollowerPal_Skarmory[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skarmory.gbapal");
static const u16 sFollowerPalShiny_Skarmory[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skarmory_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Skarmory[] = {
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 0),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 1),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 2),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 3),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 4),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 5),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 6),
    overworld_frame(sFollowerPic_Skarmory, 4, 4, 7),
};

static const u16 sFollowerPic_Houndour[] = INCBIN_U16("graphics/object_events/pics/seguidores/houndour.4bpp");
static const u16 sFollowerPal_Houndour[] = INCBIN_U16("graphics/object_events/palettes/seguidores/houndour.gbapal");
static const u16 sFollowerPalShiny_Houndour[] = INCBIN_U16("graphics/object_events/palettes/seguidores/houndour_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Houndour[] = {
    overworld_frame(sFollowerPic_Houndour, 4, 4, 0),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 1),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 2),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 3),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 4),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 5),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 6),
    overworld_frame(sFollowerPic_Houndour, 4, 4, 7),
};

static const u16 sFollowerPic_Houndoom[] = INCBIN_U16("graphics/object_events/pics/seguidores/houndoom.4bpp");
static const u16 sFollowerPal_Houndoom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/houndoom.gbapal");
static const u16 sFollowerPalShiny_Houndoom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/houndoom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Houndoom[] = {
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 0),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 1),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 2),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 3),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 4),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 5),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 6),
    overworld_frame(sFollowerPic_Houndoom, 4, 4, 7),
};

static const u16 sFollowerPic_Kingdra[] = INCBIN_U16("graphics/object_events/pics/seguidores/kingdra.4bpp");
static const u16 sFollowerPal_Kingdra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kingdra.gbapal");
static const u16 sFollowerPalShiny_Kingdra[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kingdra_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kingdra[] = {
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 0),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 1),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 2),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 3),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 4),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 5),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 6),
    overworld_frame(sFollowerPic_Kingdra, 4, 4, 7),
};

static const u16 sFollowerPic_Phanpy[] = INCBIN_U16("graphics/object_events/pics/seguidores/phanpy.4bpp");
static const u16 sFollowerPal_Phanpy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/phanpy.gbapal");
static const u16 sFollowerPalShiny_Phanpy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/phanpy_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Phanpy[] = {
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 0),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 1),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 2),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 3),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 4),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 5),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 6),
    overworld_frame(sFollowerPic_Phanpy, 4, 4, 7),
};

static const u16 sFollowerPic_Donphan[] = INCBIN_U16("graphics/object_events/pics/seguidores/donphan.4bpp");
static const u16 sFollowerPal_Donphan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/donphan.gbapal");
static const u16 sFollowerPalShiny_Donphan[] = INCBIN_U16("graphics/object_events/palettes/seguidores/donphan_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Donphan[] = {
    overworld_frame(sFollowerPic_Donphan, 4, 4, 0),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 1),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 2),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 3),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 4),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 5),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 6),
    overworld_frame(sFollowerPic_Donphan, 4, 4, 7),
};

static const u16 sFollowerPic_Porygon2[] = INCBIN_U16("graphics/object_events/pics/seguidores/porygon2.4bpp");
static const u16 sFollowerPal_Porygon2[] = INCBIN_U16("graphics/object_events/palettes/seguidores/porygon2.gbapal");
static const u16 sFollowerPalShiny_Porygon2[] = INCBIN_U16("graphics/object_events/palettes/seguidores/porygon2_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Porygon2[] = {
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 0),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 1),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 2),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 3),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 4),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 5),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 6),
    overworld_frame(sFollowerPic_Porygon2, 4, 4, 7),
};

static const u16 sFollowerPic_Stantler[] = INCBIN_U16("graphics/object_events/pics/seguidores/stantler.4bpp");
static const u16 sFollowerPal_Stantler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/stantler.gbapal");
static const u16 sFollowerPalShiny_Stantler[] = INCBIN_U16("graphics/object_events/palettes/seguidores/stantler_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Stantler[] = {
    overworld_frame(sFollowerPic_Stantler, 4, 4, 0),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 1),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 2),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 3),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 4),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 5),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 6),
    overworld_frame(sFollowerPic_Stantler, 4, 4, 7),
};

static const u16 sFollowerPic_Smeargle[] = INCBIN_U16("graphics/object_events/pics/seguidores/smeargle.4bpp");
static const u16 sFollowerPal_Smeargle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/smeargle.gbapal");
static const u16 sFollowerPalShiny_Smeargle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/smeargle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Smeargle[] = {
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 0),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 1),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 2),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 3),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 4),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 5),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 6),
    overworld_frame(sFollowerPic_Smeargle, 4, 4, 7),
};

static const u16 sFollowerPic_Tyrogue[] = INCBIN_U16("graphics/object_events/pics/seguidores/tyrogue.4bpp");
static const u16 sFollowerPal_Tyrogue[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tyrogue.gbapal");
static const u16 sFollowerPalShiny_Tyrogue[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tyrogue_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tyrogue[] = {
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 0),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 1),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 2),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 3),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 4),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 5),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 6),
    overworld_frame(sFollowerPic_Tyrogue, 4, 4, 7),
};

static const u16 sFollowerPic_Hitmontop[] = INCBIN_U16("graphics/object_events/pics/seguidores/hitmontop.4bpp");
static const u16 sFollowerPal_Hitmontop[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmontop.gbapal");
static const u16 sFollowerPalShiny_Hitmontop[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hitmontop_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hitmontop[] = {
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 0),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 1),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 2),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 3),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 4),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 5),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 6),
    overworld_frame(sFollowerPic_Hitmontop, 4, 4, 7),
};

static const u16 sFollowerPic_Smoochum[] = INCBIN_U16("graphics/object_events/pics/seguidores/smoochum.4bpp");
static const u16 sFollowerPal_Smoochum[] = INCBIN_U16("graphics/object_events/palettes/seguidores/smoochum.gbapal");
static const u16 sFollowerPalShiny_Smoochum[] = INCBIN_U16("graphics/object_events/palettes/seguidores/smoochum_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Smoochum[] = {
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 0),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 1),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 2),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 3),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 4),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 5),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 6),
    overworld_frame(sFollowerPic_Smoochum, 4, 4, 7),
};

static const u16 sFollowerPic_Elekid[] = INCBIN_U16("graphics/object_events/pics/seguidores/elekid.4bpp");
static const u16 sFollowerPal_Elekid[] = INCBIN_U16("graphics/object_events/palettes/seguidores/elekid.gbapal");
static const u16 sFollowerPalShiny_Elekid[] = INCBIN_U16("graphics/object_events/palettes/seguidores/elekid_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Elekid[] = {
    overworld_frame(sFollowerPic_Elekid, 4, 4, 0),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 1),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 2),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 3),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 4),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 5),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 6),
    overworld_frame(sFollowerPic_Elekid, 4, 4, 7),
};

static const u16 sFollowerPic_Magby[] = INCBIN_U16("graphics/object_events/pics/seguidores/magby.4bpp");
static const u16 sFollowerPal_Magby[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magby.gbapal");
static const u16 sFollowerPalShiny_Magby[] = INCBIN_U16("graphics/object_events/palettes/seguidores/magby_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Magby[] = {
    overworld_frame(sFollowerPic_Magby, 4, 4, 0),
    overworld_frame(sFollowerPic_Magby, 4, 4, 1),
    overworld_frame(sFollowerPic_Magby, 4, 4, 2),
    overworld_frame(sFollowerPic_Magby, 4, 4, 3),
    overworld_frame(sFollowerPic_Magby, 4, 4, 4),
    overworld_frame(sFollowerPic_Magby, 4, 4, 5),
    overworld_frame(sFollowerPic_Magby, 4, 4, 6),
    overworld_frame(sFollowerPic_Magby, 4, 4, 7),
};

static const u16 sFollowerPic_Miltank[] = INCBIN_U16("graphics/object_events/pics/seguidores/miltank.4bpp");
static const u16 sFollowerPal_Miltank[] = INCBIN_U16("graphics/object_events/palettes/seguidores/miltank.gbapal");
static const u16 sFollowerPalShiny_Miltank[] = INCBIN_U16("graphics/object_events/palettes/seguidores/miltank_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Miltank[] = {
    overworld_frame(sFollowerPic_Miltank, 4, 4, 0),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 1),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 2),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 3),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 4),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 5),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 6),
    overworld_frame(sFollowerPic_Miltank, 4, 4, 7),
};

static const u16 sFollowerPic_Blissey[] = INCBIN_U16("graphics/object_events/pics/seguidores/blissey.4bpp");
static const u16 sFollowerPal_Blissey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blissey.gbapal");
static const u16 sFollowerPalShiny_Blissey[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blissey_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Blissey[] = {
    overworld_frame(sFollowerPic_Blissey, 4, 4, 0),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 1),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 2),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 3),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 4),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 5),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 6),
    overworld_frame(sFollowerPic_Blissey, 4, 4, 7),
};

static const u16 sFollowerPic_Raikou[] = INCBIN_U16("graphics/object_events/pics/seguidores/raikou.4bpp");
static const u16 sFollowerPal_Raikou[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raikou.gbapal");
static const u16 sFollowerPalShiny_Raikou[] = INCBIN_U16("graphics/object_events/palettes/seguidores/raikou_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Raikou[] = {
    overworld_frame(sFollowerPic_Raikou, 4, 4, 0),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 1),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 2),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 3),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 4),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 5),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 6),
    overworld_frame(sFollowerPic_Raikou, 4, 4, 7),
};

static const u16 sFollowerPic_Entei[] = INCBIN_U16("graphics/object_events/pics/seguidores/entei.4bpp");
static const u16 sFollowerPal_Entei[] = INCBIN_U16("graphics/object_events/palettes/seguidores/entei.gbapal");
static const u16 sFollowerPalShiny_Entei[] = INCBIN_U16("graphics/object_events/palettes/seguidores/entei_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Entei[] = {
    overworld_frame(sFollowerPic_Entei, 4, 4, 0),
    overworld_frame(sFollowerPic_Entei, 4, 4, 1),
    overworld_frame(sFollowerPic_Entei, 4, 4, 2),
    overworld_frame(sFollowerPic_Entei, 4, 4, 3),
    overworld_frame(sFollowerPic_Entei, 4, 4, 4),
    overworld_frame(sFollowerPic_Entei, 4, 4, 5),
    overworld_frame(sFollowerPic_Entei, 4, 4, 6),
    overworld_frame(sFollowerPic_Entei, 4, 4, 7),
};

static const u16 sFollowerPic_Suicune[] = INCBIN_U16("graphics/object_events/pics/seguidores/suicune.4bpp");
static const u16 sFollowerPal_Suicune[] = INCBIN_U16("graphics/object_events/palettes/seguidores/suicune.gbapal");
static const u16 sFollowerPalShiny_Suicune[] = INCBIN_U16("graphics/object_events/palettes/seguidores/suicune_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Suicune[] = {
    overworld_frame(sFollowerPic_Suicune, 4, 4, 0),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 1),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 2),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 3),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 4),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 5),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 6),
    overworld_frame(sFollowerPic_Suicune, 4, 4, 7),
};

static const u16 sFollowerPic_Larvitar[] = INCBIN_U16("graphics/object_events/pics/seguidores/larvitar.4bpp");
static const u16 sFollowerPal_Larvitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/larvitar.gbapal");
static const u16 sFollowerPalShiny_Larvitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/larvitar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Larvitar[] = {
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 0),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 1),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 2),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 3),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 4),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 5),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 6),
    overworld_frame(sFollowerPic_Larvitar, 4, 4, 7),
};

static const u16 sFollowerPic_Pupitar[] = INCBIN_U16("graphics/object_events/pics/seguidores/pupitar.4bpp");
static const u16 sFollowerPal_Pupitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pupitar.gbapal");
static const u16 sFollowerPalShiny_Pupitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pupitar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pupitar[] = {
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 0),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 1),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 2),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 3),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 4),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 5),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 6),
    overworld_frame(sFollowerPic_Pupitar, 4, 4, 7),
};

static const u16 sFollowerPic_Tyranitar[] = INCBIN_U16("graphics/object_events/pics/seguidores/tyranitar.4bpp");
static const u16 sFollowerPal_Tyranitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tyranitar.gbapal");
static const u16 sFollowerPalShiny_Tyranitar[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tyranitar_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tyranitar[] = {
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 0),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 1),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 2),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 3),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 4),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 5),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 6),
    overworld_frame(sFollowerPic_Tyranitar, 4, 4, 7),
};

static const u16 sFollowerPic_Lugia[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/lugia.4bpp");
static const u16 sFollowerPal_Lugia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lugia.gbapal");
static const u16 sFollowerPalShiny_Lugia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lugia_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lugia[] = {
    overworld_frame(sFollowerPic_Lugia, 8, 8, 0),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 1),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 2),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 3),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 4),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 5),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 6),
    overworld_frame(sFollowerPic_Lugia, 8, 8, 7),
};

static const u16 sFollowerPic_HoOh[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/ho_oh.4bpp");
static const u16 sFollowerPal_HoOh[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ho_oh.gbapal");
static const u16 sFollowerPalShiny_HoOh[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ho_oh_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_HoOh[] = {
    overworld_frame(sFollowerPic_HoOh, 8, 8, 0),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 1),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 2),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 3),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 4),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 5),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 6),
    overworld_frame(sFollowerPic_HoOh, 8, 8, 7),
};

static const u16 sFollowerPic_Celebi[] = INCBIN_U16("graphics/object_events/pics/seguidores/celebi.4bpp");
static const u16 sFollowerPal_Celebi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/celebi.gbapal");
static const u16 sFollowerPalShiny_Celebi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/celebi_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Celebi[] = {
    overworld_frame(sFollowerPic_Celebi, 4, 4, 0),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 1),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 2),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 3),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 4),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 5),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 6),
    overworld_frame(sFollowerPic_Celebi, 4, 4, 7),
};

static const u16 sFollowerPic_Treecko[] = INCBIN_U16("graphics/object_events/pics/seguidores/treecko.4bpp");
static const u16 sFollowerPal_Treecko[] = INCBIN_U16("graphics/object_events/palettes/seguidores/treecko.gbapal");
static const u16 sFollowerPalShiny_Treecko[] = INCBIN_U16("graphics/object_events/palettes/seguidores/treecko_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Treecko[] = {
    overworld_frame(sFollowerPic_Treecko, 4, 4, 0),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 1),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 2),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 3),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 4),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 5),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 6),
    overworld_frame(sFollowerPic_Treecko, 4, 4, 7),
};

static const u16 sFollowerPic_Grovyle[] = INCBIN_U16("graphics/object_events/pics/seguidores/grovyle.4bpp");
static const u16 sFollowerPal_Grovyle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grovyle.gbapal");
static const u16 sFollowerPalShiny_Grovyle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grovyle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Grovyle[] = {
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 0),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 1),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 2),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 3),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 4),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 5),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 6),
    overworld_frame(sFollowerPic_Grovyle, 4, 4, 7),
};

static const u16 sFollowerPic_Sceptile[] = INCBIN_U16("graphics/object_events/pics/seguidores/sceptile.4bpp");
static const u16 sFollowerPal_Sceptile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sceptile.gbapal");
static const u16 sFollowerPalShiny_Sceptile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sceptile_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sceptile[] = {
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 0),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 1),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 2),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 3),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 4),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 5),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 6),
    overworld_frame(sFollowerPic_Sceptile, 4, 4, 7),
};

static const u16 sFollowerPic_Torchic[] = INCBIN_U16("graphics/object_events/pics/seguidores/torchic.4bpp");
static const u16 sFollowerPal_Torchic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/torchic.gbapal");
static const u16 sFollowerPalShiny_Torchic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/torchic_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Torchic[] = {
    overworld_frame(sFollowerPic_Torchic, 4, 4, 0),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 1),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 2),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 3),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 4),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 5),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 6),
    overworld_frame(sFollowerPic_Torchic, 4, 4, 7),
};

static const u16 sFollowerPic_Combusken[] = INCBIN_U16("graphics/object_events/pics/seguidores/combusken.4bpp");
static const u16 sFollowerPal_Combusken[] = INCBIN_U16("graphics/object_events/palettes/seguidores/combusken.gbapal");
static const u16 sFollowerPalShiny_Combusken[] = INCBIN_U16("graphics/object_events/palettes/seguidores/combusken_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Combusken[] = {
    overworld_frame(sFollowerPic_Combusken, 4, 4, 0),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 1),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 2),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 3),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 4),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 5),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 6),
    overworld_frame(sFollowerPic_Combusken, 4, 4, 7),
};

static const u16 sFollowerPic_Blaziken[] = INCBIN_U16("graphics/object_events/pics/seguidores/blaziken.4bpp");
static const u16 sFollowerPal_Blaziken[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blaziken.gbapal");
static const u16 sFollowerPalShiny_Blaziken[] = INCBIN_U16("graphics/object_events/palettes/seguidores/blaziken_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Blaziken[] = {
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 0),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 1),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 2),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 3),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 4),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 5),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 6),
    overworld_frame(sFollowerPic_Blaziken, 4, 4, 7),
};

static const u16 sFollowerPic_Mudkip[] = INCBIN_U16("graphics/object_events/pics/seguidores/mudkip.4bpp");
static const u16 sFollowerPal_Mudkip[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mudkip.gbapal");
static const u16 sFollowerPalShiny_Mudkip[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mudkip_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mudkip[] = {
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 0),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 1),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 2),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 3),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 4),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 5),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 6),
    overworld_frame(sFollowerPic_Mudkip, 4, 4, 7),
};

static const u16 sFollowerPic_Marshtomp[] = INCBIN_U16("graphics/object_events/pics/seguidores/marshtomp.4bpp");
static const u16 sFollowerPal_Marshtomp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marshtomp.gbapal");
static const u16 sFollowerPalShiny_Marshtomp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/marshtomp_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Marshtomp[] = {
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 0),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 1),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 2),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 3),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 4),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 5),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 6),
    overworld_frame(sFollowerPic_Marshtomp, 4, 4, 7),
};

static const u16 sFollowerPic_Swampert[] = INCBIN_U16("graphics/object_events/pics/seguidores/swampert.4bpp");
static const u16 sFollowerPal_Swampert[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swampert.gbapal");
static const u16 sFollowerPalShiny_Swampert[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swampert_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Swampert[] = {
    overworld_frame(sFollowerPic_Swampert, 4, 4, 0),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 1),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 2),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 3),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 4),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 5),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 6),
    overworld_frame(sFollowerPic_Swampert, 4, 4, 7),
};

static const u16 sFollowerPic_Poochyena[] = INCBIN_U16("graphics/object_events/pics/seguidores/poochyena.4bpp");
static const u16 sFollowerPal_Poochyena[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poochyena.gbapal");
static const u16 sFollowerPalShiny_Poochyena[] = INCBIN_U16("graphics/object_events/palettes/seguidores/poochyena_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Poochyena[] = {
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 0),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 1),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 2),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 3),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 4),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 5),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 6),
    overworld_frame(sFollowerPic_Poochyena, 4, 4, 7),
};

static const u16 sFollowerPic_Mightyena[] = INCBIN_U16("graphics/object_events/pics/seguidores/mightyena.4bpp");
static const u16 sFollowerPal_Mightyena[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mightyena.gbapal");
static const u16 sFollowerPalShiny_Mightyena[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mightyena_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mightyena[] = {
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 0),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 1),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 2),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 3),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 4),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 5),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 6),
    overworld_frame(sFollowerPic_Mightyena, 4, 4, 7),
};

static const u16 sFollowerPic_Zigzagoon[] = INCBIN_U16("graphics/object_events/pics/seguidores/zigzagoon.4bpp");
static const u16 sFollowerPal_Zigzagoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zigzagoon.gbapal");
static const u16 sFollowerPalShiny_Zigzagoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zigzagoon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Zigzagoon[] = {
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 0),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 1),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 2),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 3),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 4),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 5),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 6),
    overworld_frame(sFollowerPic_Zigzagoon, 4, 4, 7),
};

static const u16 sFollowerPic_Linoone[] = INCBIN_U16("graphics/object_events/pics/seguidores/linoone.4bpp");
static const u16 sFollowerPal_Linoone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/linoone.gbapal");
static const u16 sFollowerPalShiny_Linoone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/linoone_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Linoone[] = {
    overworld_frame(sFollowerPic_Linoone, 4, 4, 0),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 1),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 2),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 3),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 4),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 5),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 6),
    overworld_frame(sFollowerPic_Linoone, 4, 4, 7),
};

static const u16 sFollowerPic_Wurmple[] = INCBIN_U16("graphics/object_events/pics/seguidores/wurmple.4bpp");
static const u16 sFollowerPal_Wurmple[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wurmple.gbapal");
static const u16 sFollowerPalShiny_Wurmple[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wurmple_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wurmple[] = {
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 0),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 1),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 2),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 3),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 4),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 5),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 6),
    overworld_frame(sFollowerPic_Wurmple, 4, 4, 7),
};

static const u16 sFollowerPic_Silcoon[] = INCBIN_U16("graphics/object_events/pics/seguidores/silcoon.4bpp");
static const u16 sFollowerPal_Silcoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/silcoon.gbapal");
static const u16 sFollowerPalShiny_Silcoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/silcoon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Silcoon[] = {
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 0),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 1),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 2),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 3),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 4),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 5),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 6),
    overworld_frame(sFollowerPic_Silcoon, 4, 4, 7),
};

static const u16 sFollowerPic_Beautifly[] = INCBIN_U16("graphics/object_events/pics/seguidores/beautifly.4bpp");
static const u16 sFollowerPal_Beautifly[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beautifly.gbapal");
static const u16 sFollowerPalShiny_Beautifly[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beautifly_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Beautifly[] = {
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 0),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 1),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 2),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 3),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 4),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 5),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 6),
    overworld_frame(sFollowerPic_Beautifly, 4, 4, 7),
};

static const u16 sFollowerPic_Cascoon[] = INCBIN_U16("graphics/object_events/pics/seguidores/cascoon.4bpp");
static const u16 sFollowerPal_Cascoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cascoon.gbapal");
static const u16 sFollowerPalShiny_Cascoon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cascoon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cascoon[] = {
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 0),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 1),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 2),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 3),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 4),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 5),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 6),
    overworld_frame(sFollowerPic_Cascoon, 4, 4, 7),
};

static const u16 sFollowerPic_Dustox[] = INCBIN_U16("graphics/object_events/pics/seguidores/dustox.4bpp");
static const u16 sFollowerPal_Dustox[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dustox.gbapal");
static const u16 sFollowerPalShiny_Dustox[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dustox_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dustox[] = {
    overworld_frame(sFollowerPic_Dustox, 4, 4, 0),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 1),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 2),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 3),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 4),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 5),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 6),
    overworld_frame(sFollowerPic_Dustox, 4, 4, 7),
};

static const u16 sFollowerPic_Lotad[] = INCBIN_U16("graphics/object_events/pics/seguidores/lotad.4bpp");
static const u16 sFollowerPal_Lotad[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lotad.gbapal");
static const u16 sFollowerPalShiny_Lotad[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lotad_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lotad[] = {
    overworld_frame(sFollowerPic_Lotad, 4, 4, 0),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 1),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 2),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 3),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 4),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 5),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 6),
    overworld_frame(sFollowerPic_Lotad, 4, 4, 7),
};

static const u16 sFollowerPic_Lombre[] = INCBIN_U16("graphics/object_events/pics/seguidores/lombre.4bpp");
static const u16 sFollowerPal_Lombre[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lombre.gbapal");
static const u16 sFollowerPalShiny_Lombre[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lombre_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lombre[] = {
    overworld_frame(sFollowerPic_Lombre, 4, 4, 0),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 1),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 2),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 3),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 4),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 5),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 6),
    overworld_frame(sFollowerPic_Lombre, 4, 4, 7),
};

static const u16 sFollowerPic_Ludicolo[] = INCBIN_U16("graphics/object_events/pics/seguidores/ludicolo.4bpp");
static const u16 sFollowerPal_Ludicolo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ludicolo.gbapal");
static const u16 sFollowerPalShiny_Ludicolo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ludicolo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ludicolo[] = {
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 0),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 1),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 2),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 3),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 4),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 5),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 6),
    overworld_frame(sFollowerPic_Ludicolo, 4, 4, 7),
};

static const u16 sFollowerPic_Seedot[] = INCBIN_U16("graphics/object_events/pics/seguidores/seedot.4bpp");
static const u16 sFollowerPal_Seedot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seedot.gbapal");
static const u16 sFollowerPalShiny_Seedot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seedot_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Seedot[] = {
    overworld_frame(sFollowerPic_Seedot, 4, 4, 0),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 1),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 2),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 3),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 4),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 5),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 6),
    overworld_frame(sFollowerPic_Seedot, 4, 4, 7),
};

static const u16 sFollowerPic_Nuzleaf[] = INCBIN_U16("graphics/object_events/pics/seguidores/nuzleaf.4bpp");
static const u16 sFollowerPal_Nuzleaf[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nuzleaf.gbapal");
static const u16 sFollowerPalShiny_Nuzleaf[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nuzleaf_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nuzleaf[] = {
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 0),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 1),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 2),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 3),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 4),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 5),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 6),
    overworld_frame(sFollowerPic_Nuzleaf, 4, 4, 7),
};

static const u16 sFollowerPic_Shiftry[] = INCBIN_U16("graphics/object_events/pics/seguidores/shiftry.4bpp");
static const u16 sFollowerPal_Shiftry[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shiftry.gbapal");
static const u16 sFollowerPalShiny_Shiftry[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shiftry_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shiftry[] = {
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 0),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 1),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 2),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 3),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 4),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 5),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 6),
    overworld_frame(sFollowerPic_Shiftry, 4, 4, 7),
};

static const u16 sFollowerPic_Taillow[] = INCBIN_U16("graphics/object_events/pics/seguidores/taillow.4bpp");
static const u16 sFollowerPal_Taillow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/taillow.gbapal");
static const u16 sFollowerPalShiny_Taillow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/taillow_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Taillow[] = {
    overworld_frame(sFollowerPic_Taillow, 4, 4, 0),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 1),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 2),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 3),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 4),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 5),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 6),
    overworld_frame(sFollowerPic_Taillow, 4, 4, 7),
};

static const u16 sFollowerPic_Swellow[] = INCBIN_U16("graphics/object_events/pics/seguidores/swellow.4bpp");
static const u16 sFollowerPal_Swellow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swellow.gbapal");
static const u16 sFollowerPalShiny_Swellow[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swellow_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Swellow[] = {
    overworld_frame(sFollowerPic_Swellow, 4, 4, 0),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 1),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 2),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 3),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 4),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 5),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 6),
    overworld_frame(sFollowerPic_Swellow, 4, 4, 7),
};

static const u16 sFollowerPic_Wingull[] = INCBIN_U16("graphics/object_events/pics/seguidores/wingull.4bpp");
static const u16 sFollowerPal_Wingull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wingull.gbapal");
static const u16 sFollowerPalShiny_Wingull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wingull_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wingull[] = {
    overworld_frame(sFollowerPic_Wingull, 4, 4, 0),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 1),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 2),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 3),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 4),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 5),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 6),
    overworld_frame(sFollowerPic_Wingull, 4, 4, 7),
};

static const u16 sFollowerPic_Pelipper[] = INCBIN_U16("graphics/object_events/pics/seguidores/pelipper.4bpp");
static const u16 sFollowerPal_Pelipper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pelipper.gbapal");
static const u16 sFollowerPalShiny_Pelipper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/pelipper_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Pelipper[] = {
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 0),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 1),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 2),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 3),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 4),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 5),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 6),
    overworld_frame(sFollowerPic_Pelipper, 4, 4, 7),
};

static const u16 sFollowerPic_Ralts[] = INCBIN_U16("graphics/object_events/pics/seguidores/ralts.4bpp");
static const u16 sFollowerPal_Ralts[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ralts.gbapal");
static const u16 sFollowerPalShiny_Ralts[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ralts_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ralts[] = {
    overworld_frame(sFollowerPic_Ralts, 4, 4, 0),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 1),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 2),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 3),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 4),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 5),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 6),
    overworld_frame(sFollowerPic_Ralts, 4, 4, 7),
};

static const u16 sFollowerPic_Kirlia[] = INCBIN_U16("graphics/object_events/pics/seguidores/kirlia.4bpp");
static const u16 sFollowerPal_Kirlia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kirlia.gbapal");
static const u16 sFollowerPalShiny_Kirlia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kirlia_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kirlia[] = {
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 0),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 1),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 2),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 3),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 4),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 5),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 6),
    overworld_frame(sFollowerPic_Kirlia, 4, 4, 7),
};

static const u16 sFollowerPic_Gardevoir[] = INCBIN_U16("graphics/object_events/pics/seguidores/gardevoir.4bpp");
static const u16 sFollowerPal_Gardevoir[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gardevoir.gbapal");
static const u16 sFollowerPalShiny_Gardevoir[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gardevoir_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gardevoir[] = {
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 0),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 1),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 2),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 3),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 4),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 5),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 6),
    overworld_frame(sFollowerPic_Gardevoir, 4, 4, 7),
};

static const u16 sFollowerPic_Surskit[] = INCBIN_U16("graphics/object_events/pics/seguidores/surskit.4bpp");
static const u16 sFollowerPal_Surskit[] = INCBIN_U16("graphics/object_events/palettes/seguidores/surskit.gbapal");
static const u16 sFollowerPalShiny_Surskit[] = INCBIN_U16("graphics/object_events/palettes/seguidores/surskit_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Surskit[] = {
    overworld_frame(sFollowerPic_Surskit, 4, 4, 0),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 1),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 2),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 3),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 4),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 5),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 6),
    overworld_frame(sFollowerPic_Surskit, 4, 4, 7),
};

static const u16 sFollowerPic_Masquerain[] = INCBIN_U16("graphics/object_events/pics/seguidores/masquerain.4bpp");
static const u16 sFollowerPal_Masquerain[] = INCBIN_U16("graphics/object_events/palettes/seguidores/masquerain.gbapal");
static const u16 sFollowerPalShiny_Masquerain[] = INCBIN_U16("graphics/object_events/palettes/seguidores/masquerain_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Masquerain[] = {
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 0),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 1),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 2),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 3),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 4),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 5),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 6),
    overworld_frame(sFollowerPic_Masquerain, 4, 4, 7),
};

static const u16 sFollowerPic_Shroomish[] = INCBIN_U16("graphics/object_events/pics/seguidores/shroomish.4bpp");
static const u16 sFollowerPal_Shroomish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shroomish.gbapal");
static const u16 sFollowerPalShiny_Shroomish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shroomish_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shroomish[] = {
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 0),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 1),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 2),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 3),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 4),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 5),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 6),
    overworld_frame(sFollowerPic_Shroomish, 4, 4, 7),
};

static const u16 sFollowerPic_Breloom[] = INCBIN_U16("graphics/object_events/pics/seguidores/breloom.4bpp");
static const u16 sFollowerPal_Breloom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/breloom.gbapal");
static const u16 sFollowerPalShiny_Breloom[] = INCBIN_U16("graphics/object_events/palettes/seguidores/breloom_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Breloom[] = {
    overworld_frame(sFollowerPic_Breloom, 4, 4, 0),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 1),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 2),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 3),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 4),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 5),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 6),
    overworld_frame(sFollowerPic_Breloom, 4, 4, 7),
};

static const u16 sFollowerPic_Slakoth[] = INCBIN_U16("graphics/object_events/pics/seguidores/slakoth.4bpp");
static const u16 sFollowerPal_Slakoth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slakoth.gbapal");
static const u16 sFollowerPalShiny_Slakoth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slakoth_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slakoth[] = {
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 0),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 1),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 2),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 3),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 4),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 5),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 6),
    overworld_frame(sFollowerPic_Slakoth, 4, 4, 7),
};

static const u16 sFollowerPic_Vigoroth[] = INCBIN_U16("graphics/object_events/pics/seguidores/vigoroth.4bpp");
static const u16 sFollowerPal_Vigoroth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vigoroth.gbapal");
static const u16 sFollowerPalShiny_Vigoroth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vigoroth_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Vigoroth[] = {
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 0),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 1),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 2),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 3),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 4),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 5),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 6),
    overworld_frame(sFollowerPic_Vigoroth, 4, 4, 7),
};

static const u16 sFollowerPic_Slaking[] = INCBIN_U16("graphics/object_events/pics/seguidores/slaking.4bpp");
static const u16 sFollowerPal_Slaking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slaking.gbapal");
static const u16 sFollowerPalShiny_Slaking[] = INCBIN_U16("graphics/object_events/palettes/seguidores/slaking_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Slaking[] = {
    overworld_frame(sFollowerPic_Slaking, 4, 4, 0),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 1),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 2),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 3),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 4),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 5),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 6),
    overworld_frame(sFollowerPic_Slaking, 4, 4, 7),
};

static const u16 sFollowerPic_Nincada[] = INCBIN_U16("graphics/object_events/pics/seguidores/nincada.4bpp");
static const u16 sFollowerPal_Nincada[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nincada.gbapal");
static const u16 sFollowerPalShiny_Nincada[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nincada_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nincada[] = {
    overworld_frame(sFollowerPic_Nincada, 4, 4, 0),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 1),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 2),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 3),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 4),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 5),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 6),
    overworld_frame(sFollowerPic_Nincada, 4, 4, 7),
};

static const u16 sFollowerPic_Ninjask[] = INCBIN_U16("graphics/object_events/pics/seguidores/ninjask.4bpp");
static const u16 sFollowerPal_Ninjask[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ninjask.gbapal");
static const u16 sFollowerPalShiny_Ninjask[] = INCBIN_U16("graphics/object_events/palettes/seguidores/ninjask_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Ninjask[] = {
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 0),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 1),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 2),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 3),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 4),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 5),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 6),
    overworld_frame(sFollowerPic_Ninjask, 4, 4, 7),
};

static const u16 sFollowerPic_Shedinja[] = INCBIN_U16("graphics/object_events/pics/seguidores/shedinja.4bpp");
static const u16 sFollowerPal_Shedinja[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shedinja.gbapal");
static const u16 sFollowerPalShiny_Shedinja[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shedinja_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shedinja[] = {
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 0),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 1),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 2),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 3),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 4),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 5),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 6),
    overworld_frame(sFollowerPic_Shedinja, 4, 4, 7),
};

static const u16 sFollowerPic_Whismur[] = INCBIN_U16("graphics/object_events/pics/seguidores/whismur.4bpp");
static const u16 sFollowerPal_Whismur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/whismur.gbapal");
static const u16 sFollowerPalShiny_Whismur[] = INCBIN_U16("graphics/object_events/palettes/seguidores/whismur_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Whismur[] = {
    overworld_frame(sFollowerPic_Whismur, 4, 4, 0),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 1),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 2),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 3),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 4),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 5),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 6),
    overworld_frame(sFollowerPic_Whismur, 4, 4, 7),
};

static const u16 sFollowerPic_Loudred[] = INCBIN_U16("graphics/object_events/pics/seguidores/loudred.4bpp");
static const u16 sFollowerPal_Loudred[] = INCBIN_U16("graphics/object_events/palettes/seguidores/loudred.gbapal");
static const u16 sFollowerPalShiny_Loudred[] = INCBIN_U16("graphics/object_events/palettes/seguidores/loudred_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Loudred[] = {
    overworld_frame(sFollowerPic_Loudred, 4, 4, 0),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 1),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 2),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 3),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 4),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 5),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 6),
    overworld_frame(sFollowerPic_Loudred, 4, 4, 7),
};

static const u16 sFollowerPic_Exploud[] = INCBIN_U16("graphics/object_events/pics/seguidores/exploud.4bpp");
static const u16 sFollowerPal_Exploud[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exploud.gbapal");
static const u16 sFollowerPalShiny_Exploud[] = INCBIN_U16("graphics/object_events/palettes/seguidores/exploud_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Exploud[] = {
    overworld_frame(sFollowerPic_Exploud, 4, 4, 0),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 1),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 2),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 3),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 4),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 5),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 6),
    overworld_frame(sFollowerPic_Exploud, 4, 4, 7),
};

static const u16 sFollowerPic_Makuhita[] = INCBIN_U16("graphics/object_events/pics/seguidores/makuhita.4bpp");
static const u16 sFollowerPal_Makuhita[] = INCBIN_U16("graphics/object_events/palettes/seguidores/makuhita.gbapal");
static const u16 sFollowerPalShiny_Makuhita[] = INCBIN_U16("graphics/object_events/palettes/seguidores/makuhita_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Makuhita[] = {
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 0),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 1),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 2),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 3),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 4),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 5),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 6),
    overworld_frame(sFollowerPic_Makuhita, 4, 4, 7),
};

static const u16 sFollowerPic_Hariyama[] = INCBIN_U16("graphics/object_events/pics/seguidores/hariyama.4bpp");
static const u16 sFollowerPal_Hariyama[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hariyama.gbapal");
static const u16 sFollowerPalShiny_Hariyama[] = INCBIN_U16("graphics/object_events/palettes/seguidores/hariyama_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Hariyama[] = {
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 0),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 1),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 2),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 3),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 4),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 5),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 6),
    overworld_frame(sFollowerPic_Hariyama, 4, 4, 7),
};

static const u16 sFollowerPic_Azurill[] = INCBIN_U16("graphics/object_events/pics/seguidores/azurill.4bpp");
static const u16 sFollowerPal_Azurill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/azurill.gbapal");
static const u16 sFollowerPalShiny_Azurill[] = INCBIN_U16("graphics/object_events/palettes/seguidores/azurill_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Azurill[] = {
    overworld_frame(sFollowerPic_Azurill, 4, 4, 0),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 1),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 2),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 3),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 4),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 5),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 6),
    overworld_frame(sFollowerPic_Azurill, 4, 4, 7),
};

static const u16 sFollowerPic_Nosepass[] = INCBIN_U16("graphics/object_events/pics/seguidores/nosepass.4bpp");
static const u16 sFollowerPal_Nosepass[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nosepass.gbapal");
static const u16 sFollowerPalShiny_Nosepass[] = INCBIN_U16("graphics/object_events/palettes/seguidores/nosepass_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Nosepass[] = {
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 0),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 1),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 2),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 3),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 4),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 5),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 6),
    overworld_frame(sFollowerPic_Nosepass, 4, 4, 7),
};

static const u16 sFollowerPic_Skitty[] = INCBIN_U16("graphics/object_events/pics/seguidores/skitty.4bpp");
static const u16 sFollowerPal_Skitty[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skitty.gbapal");
static const u16 sFollowerPalShiny_Skitty[] = INCBIN_U16("graphics/object_events/palettes/seguidores/skitty_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Skitty[] = {
    overworld_frame(sFollowerPic_Skitty, 4, 4, 0),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 1),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 2),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 3),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 4),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 5),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 6),
    overworld_frame(sFollowerPic_Skitty, 4, 4, 7),
};

static const u16 sFollowerPic_Delcatty[] = INCBIN_U16("graphics/object_events/pics/seguidores/delcatty.4bpp");
static const u16 sFollowerPal_Delcatty[] = INCBIN_U16("graphics/object_events/palettes/seguidores/delcatty.gbapal");
static const u16 sFollowerPalShiny_Delcatty[] = INCBIN_U16("graphics/object_events/palettes/seguidores/delcatty_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Delcatty[] = {
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 0),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 1),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 2),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 3),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 4),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 5),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 6),
    overworld_frame(sFollowerPic_Delcatty, 4, 4, 7),
};

static const u16 sFollowerPic_Sableye[] = INCBIN_U16("graphics/object_events/pics/seguidores/sableye.4bpp");
static const u16 sFollowerPal_Sableye[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sableye.gbapal");
static const u16 sFollowerPalShiny_Sableye[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sableye_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sableye[] = {
    overworld_frame(sFollowerPic_Sableye, 4, 4, 0),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 1),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 2),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 3),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 4),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 5),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 6),
    overworld_frame(sFollowerPic_Sableye, 4, 4, 7),
};

static const u16 sFollowerPic_Mawile[] = INCBIN_U16("graphics/object_events/pics/seguidores/mawile.4bpp");
static const u16 sFollowerPal_Mawile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mawile.gbapal");
static const u16 sFollowerPalShiny_Mawile[] = INCBIN_U16("graphics/object_events/palettes/seguidores/mawile_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Mawile[] = {
    overworld_frame(sFollowerPic_Mawile, 4, 4, 0),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 1),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 2),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 3),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 4),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 5),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 6),
    overworld_frame(sFollowerPic_Mawile, 4, 4, 7),
};

static const u16 sFollowerPic_Aron[] = INCBIN_U16("graphics/object_events/pics/seguidores/aron.4bpp");
static const u16 sFollowerPal_Aron[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aron.gbapal");
static const u16 sFollowerPalShiny_Aron[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aron_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Aron[] = {
    overworld_frame(sFollowerPic_Aron, 4, 4, 0),
    overworld_frame(sFollowerPic_Aron, 4, 4, 1),
    overworld_frame(sFollowerPic_Aron, 4, 4, 2),
    overworld_frame(sFollowerPic_Aron, 4, 4, 3),
    overworld_frame(sFollowerPic_Aron, 4, 4, 4),
    overworld_frame(sFollowerPic_Aron, 4, 4, 5),
    overworld_frame(sFollowerPic_Aron, 4, 4, 6),
    overworld_frame(sFollowerPic_Aron, 4, 4, 7),
};

static const u16 sFollowerPic_Lairon[] = INCBIN_U16("graphics/object_events/pics/seguidores/lairon.4bpp");
static const u16 sFollowerPal_Lairon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lairon.gbapal");
static const u16 sFollowerPalShiny_Lairon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lairon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lairon[] = {
    overworld_frame(sFollowerPic_Lairon, 4, 4, 0),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 1),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 2),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 3),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 4),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 5),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 6),
    overworld_frame(sFollowerPic_Lairon, 4, 4, 7),
};

static const u16 sFollowerPic_Aggron[] = INCBIN_U16("graphics/object_events/pics/seguidores/aggron.4bpp");
static const u16 sFollowerPal_Aggron[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aggron.gbapal");
static const u16 sFollowerPalShiny_Aggron[] = INCBIN_U16("graphics/object_events/palettes/seguidores/aggron_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Aggron[] = {
    overworld_frame(sFollowerPic_Aggron, 4, 4, 0),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 1),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 2),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 3),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 4),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 5),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 6),
    overworld_frame(sFollowerPic_Aggron, 4, 4, 7),
};

static const u16 sFollowerPic_Meditite[] = INCBIN_U16("graphics/object_events/pics/seguidores/meditite.4bpp");
static const u16 sFollowerPal_Meditite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meditite.gbapal");
static const u16 sFollowerPalShiny_Meditite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/meditite_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Meditite[] = {
    overworld_frame(sFollowerPic_Meditite, 4, 4, 0),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 1),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 2),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 3),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 4),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 5),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 6),
    overworld_frame(sFollowerPic_Meditite, 4, 4, 7),
};

static const u16 sFollowerPic_Medicham[] = INCBIN_U16("graphics/object_events/pics/seguidores/medicham.4bpp");
static const u16 sFollowerPal_Medicham[] = INCBIN_U16("graphics/object_events/palettes/seguidores/medicham.gbapal");
static const u16 sFollowerPalShiny_Medicham[] = INCBIN_U16("graphics/object_events/palettes/seguidores/medicham_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Medicham[] = {
    overworld_frame(sFollowerPic_Medicham, 4, 4, 0),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 1),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 2),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 3),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 4),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 5),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 6),
    overworld_frame(sFollowerPic_Medicham, 4, 4, 7),
};

static const u16 sFollowerPic_Electrike[] = INCBIN_U16("graphics/object_events/pics/seguidores/electrike.4bpp");
static const u16 sFollowerPal_Electrike[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electrike.gbapal");
static const u16 sFollowerPalShiny_Electrike[] = INCBIN_U16("graphics/object_events/palettes/seguidores/electrike_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Electrike[] = {
    overworld_frame(sFollowerPic_Electrike, 4, 4, 0),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 1),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 2),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 3),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 4),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 5),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 6),
    overworld_frame(sFollowerPic_Electrike, 4, 4, 7),
};

static const u16 sFollowerPic_Manectric[] = INCBIN_U16("graphics/object_events/pics/seguidores/manectric.4bpp");
static const u16 sFollowerPal_Manectric[] = INCBIN_U16("graphics/object_events/palettes/seguidores/manectric.gbapal");
static const u16 sFollowerPalShiny_Manectric[] = INCBIN_U16("graphics/object_events/palettes/seguidores/manectric_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Manectric[] = {
    overworld_frame(sFollowerPic_Manectric, 4, 4, 0),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 1),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 2),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 3),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 4),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 5),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 6),
    overworld_frame(sFollowerPic_Manectric, 4, 4, 7),
};

static const u16 sFollowerPic_Plusle[] = INCBIN_U16("graphics/object_events/pics/seguidores/plusle.4bpp");
static const u16 sFollowerPal_Plusle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/plusle.gbapal");
static const u16 sFollowerPalShiny_Plusle[] = INCBIN_U16("graphics/object_events/palettes/seguidores/plusle_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Plusle[] = {
    overworld_frame(sFollowerPic_Plusle, 4, 4, 0),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 1),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 2),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 3),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 4),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 5),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 6),
    overworld_frame(sFollowerPic_Plusle, 4, 4, 7),
};

static const u16 sFollowerPic_Minun[] = INCBIN_U16("graphics/object_events/pics/seguidores/minun.4bpp");
static const u16 sFollowerPal_Minun[] = INCBIN_U16("graphics/object_events/palettes/seguidores/minun.gbapal");
static const u16 sFollowerPalShiny_Minun[] = INCBIN_U16("graphics/object_events/palettes/seguidores/minun_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Minun[] = {
    overworld_frame(sFollowerPic_Minun, 4, 4, 0),
    overworld_frame(sFollowerPic_Minun, 4, 4, 1),
    overworld_frame(sFollowerPic_Minun, 4, 4, 2),
    overworld_frame(sFollowerPic_Minun, 4, 4, 3),
    overworld_frame(sFollowerPic_Minun, 4, 4, 4),
    overworld_frame(sFollowerPic_Minun, 4, 4, 5),
    overworld_frame(sFollowerPic_Minun, 4, 4, 6),
    overworld_frame(sFollowerPic_Minun, 4, 4, 7),
};

static const u16 sFollowerPic_Volbeat[] = INCBIN_U16("graphics/object_events/pics/seguidores/volbeat.4bpp");
static const u16 sFollowerPal_Volbeat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/volbeat.gbapal");
static const u16 sFollowerPalShiny_Volbeat[] = INCBIN_U16("graphics/object_events/palettes/seguidores/volbeat_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Volbeat[] = {
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 0),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 1),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 2),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 3),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 4),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 5),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 6),
    overworld_frame(sFollowerPic_Volbeat, 4, 4, 7),
};

static const u16 sFollowerPic_Illumise[] = INCBIN_U16("graphics/object_events/pics/seguidores/illumise.4bpp");
static const u16 sFollowerPal_Illumise[] = INCBIN_U16("graphics/object_events/palettes/seguidores/illumise.gbapal");
static const u16 sFollowerPalShiny_Illumise[] = INCBIN_U16("graphics/object_events/palettes/seguidores/illumise_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Illumise[] = {
    overworld_frame(sFollowerPic_Illumise, 4, 4, 0),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 1),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 2),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 3),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 4),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 5),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 6),
    overworld_frame(sFollowerPic_Illumise, 4, 4, 7),
};

static const u16 sFollowerPic_Roselia[] = INCBIN_U16("graphics/object_events/pics/seguidores/roselia.4bpp");
static const u16 sFollowerPal_Roselia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/roselia.gbapal");
static const u16 sFollowerPalShiny_Roselia[] = INCBIN_U16("graphics/object_events/palettes/seguidores/roselia_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Roselia[] = {
    overworld_frame(sFollowerPic_Roselia, 4, 4, 0),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 1),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 2),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 3),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 4),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 5),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 6),
    overworld_frame(sFollowerPic_Roselia, 4, 4, 7),
};

static const u16 sFollowerPic_Gulpin[] = INCBIN_U16("graphics/object_events/pics/seguidores/gulpin.4bpp");
static const u16 sFollowerPal_Gulpin[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gulpin.gbapal");
static const u16 sFollowerPalShiny_Gulpin[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gulpin_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gulpin[] = {
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 0),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 1),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 2),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 3),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 4),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 5),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 6),
    overworld_frame(sFollowerPic_Gulpin, 4, 4, 7),
};

static const u16 sFollowerPic_Swalot[] = INCBIN_U16("graphics/object_events/pics/seguidores/swalot.4bpp");
static const u16 sFollowerPal_Swalot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swalot.gbapal");
static const u16 sFollowerPalShiny_Swalot[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swalot_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Swalot[] = {
    overworld_frame(sFollowerPic_Swalot, 4, 4, 0),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 1),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 2),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 3),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 4),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 5),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 6),
    overworld_frame(sFollowerPic_Swalot, 4, 4, 7),
};

static const u16 sFollowerPic_Carvanha[] = INCBIN_U16("graphics/object_events/pics/seguidores/carvanha.4bpp");
static const u16 sFollowerPal_Carvanha[] = INCBIN_U16("graphics/object_events/palettes/seguidores/carvanha.gbapal");
static const u16 sFollowerPalShiny_Carvanha[] = INCBIN_U16("graphics/object_events/palettes/seguidores/carvanha_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Carvanha[] = {
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 0),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 1),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 2),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 3),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 4),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 5),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 6),
    overworld_frame(sFollowerPic_Carvanha, 4, 4, 7),
};

static const u16 sFollowerPic_Sharpedo[] = INCBIN_U16("graphics/object_events/pics/seguidores/sharpedo.4bpp");
static const u16 sFollowerPal_Sharpedo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sharpedo.gbapal");
static const u16 sFollowerPalShiny_Sharpedo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sharpedo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sharpedo[] = {
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 0),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 1),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 2),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 3),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 4),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 5),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 6),
    overworld_frame(sFollowerPic_Sharpedo, 4, 4, 7),
};

static const u16 sFollowerPic_Wailmer[] = INCBIN_U16("graphics/object_events/pics/seguidores/wailmer.4bpp");
static const u16 sFollowerPal_Wailmer[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wailmer.gbapal");
static const u16 sFollowerPalShiny_Wailmer[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wailmer_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wailmer[] = {
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 0),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 1),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 2),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 3),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 4),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 5),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 6),
    overworld_frame(sFollowerPic_Wailmer, 4, 4, 7),
};

static const u16 sFollowerPic_Wailord[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/wailord.4bpp");
static const u16 sFollowerPal_Wailord[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wailord.gbapal");
static const u16 sFollowerPalShiny_Wailord[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wailord_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wailord[] = {
    overworld_frame(sFollowerPic_Wailord, 8, 8, 0),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 1),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 2),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 3),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 4),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 5),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 6),
    overworld_frame(sFollowerPic_Wailord, 8, 8, 7),
};

static const u16 sFollowerPic_Numel[] = INCBIN_U16("graphics/object_events/pics/seguidores/numel.4bpp");
static const u16 sFollowerPal_Numel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/numel.gbapal");
static const u16 sFollowerPalShiny_Numel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/numel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Numel[] = {
    overworld_frame(sFollowerPic_Numel, 4, 4, 0),
    overworld_frame(sFollowerPic_Numel, 4, 4, 1),
    overworld_frame(sFollowerPic_Numel, 4, 4, 2),
    overworld_frame(sFollowerPic_Numel, 4, 4, 3),
    overworld_frame(sFollowerPic_Numel, 4, 4, 4),
    overworld_frame(sFollowerPic_Numel, 4, 4, 5),
    overworld_frame(sFollowerPic_Numel, 4, 4, 6),
    overworld_frame(sFollowerPic_Numel, 4, 4, 7),
};

static const u16 sFollowerPic_Camerupt[] = INCBIN_U16("graphics/object_events/pics/seguidores/camerupt.4bpp");
static const u16 sFollowerPal_Camerupt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/camerupt.gbapal");
static const u16 sFollowerPalShiny_Camerupt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/camerupt_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Camerupt[] = {
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 0),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 1),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 2),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 3),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 4),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 5),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 6),
    overworld_frame(sFollowerPic_Camerupt, 4, 4, 7),
};

static const u16 sFollowerPic_Torkoal[] = INCBIN_U16("graphics/object_events/pics/seguidores/torkoal.4bpp");
static const u16 sFollowerPal_Torkoal[] = INCBIN_U16("graphics/object_events/palettes/seguidores/torkoal.gbapal");
static const u16 sFollowerPalShiny_Torkoal[] = INCBIN_U16("graphics/object_events/palettes/seguidores/torkoal_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Torkoal[] = {
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 0),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 1),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 2),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 3),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 4),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 5),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 6),
    overworld_frame(sFollowerPic_Torkoal, 4, 4, 7),
};

static const u16 sFollowerPic_Spoink[] = INCBIN_U16("graphics/object_events/pics/seguidores/spoink.4bpp");
static const u16 sFollowerPal_Spoink[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spoink.gbapal");
static const u16 sFollowerPalShiny_Spoink[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spoink_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Spoink[] = {
    overworld_frame(sFollowerPic_Spoink, 4, 4, 0),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 1),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 2),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 3),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 4),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 5),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 6),
    overworld_frame(sFollowerPic_Spoink, 4, 4, 7),
};

static const u16 sFollowerPic_Grumpig[] = INCBIN_U16("graphics/object_events/pics/seguidores/grumpig.4bpp");
static const u16 sFollowerPal_Grumpig[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grumpig.gbapal");
static const u16 sFollowerPalShiny_Grumpig[] = INCBIN_U16("graphics/object_events/palettes/seguidores/grumpig_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Grumpig[] = {
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 0),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 1),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 2),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 3),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 4),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 5),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 6),
    overworld_frame(sFollowerPic_Grumpig, 4, 4, 7),
};

static const u16 sFollowerPic_Spinda[] = INCBIN_U16("graphics/object_events/pics/seguidores/spinda.4bpp");
static const u16 sFollowerPal_Spinda[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spinda.gbapal");
static const u16 sFollowerPalShiny_Spinda[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spinda_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Spinda[] = {
    overworld_frame(sFollowerPic_Spinda, 4, 4, 0),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 1),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 2),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 3),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 4),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 5),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 6),
    overworld_frame(sFollowerPic_Spinda, 4, 4, 7),
};

static const u16 sFollowerPic_Trapinch[] = INCBIN_U16("graphics/object_events/pics/seguidores/trapinch.4bpp");
static const u16 sFollowerPal_Trapinch[] = INCBIN_U16("graphics/object_events/palettes/seguidores/trapinch.gbapal");
static const u16 sFollowerPalShiny_Trapinch[] = INCBIN_U16("graphics/object_events/palettes/seguidores/trapinch_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Trapinch[] = {
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 0),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 1),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 2),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 3),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 4),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 5),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 6),
    overworld_frame(sFollowerPic_Trapinch, 4, 4, 7),
};

static const u16 sFollowerPic_Vibrava[] = INCBIN_U16("graphics/object_events/pics/seguidores/vibrava.4bpp");
static const u16 sFollowerPal_Vibrava[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vibrava.gbapal");
static const u16 sFollowerPalShiny_Vibrava[] = INCBIN_U16("graphics/object_events/palettes/seguidores/vibrava_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Vibrava[] = {
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 0),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 1),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 2),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 3),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 4),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 5),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 6),
    overworld_frame(sFollowerPic_Vibrava, 4, 4, 7),
};

static const u16 sFollowerPic_Flygon[] = INCBIN_U16("graphics/object_events/pics/seguidores/flygon.4bpp");
static const u16 sFollowerPal_Flygon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flygon.gbapal");
static const u16 sFollowerPalShiny_Flygon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/flygon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Flygon[] = {
    overworld_frame(sFollowerPic_Flygon, 4, 4, 0),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 1),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 2),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 3),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 4),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 5),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 6),
    overworld_frame(sFollowerPic_Flygon, 4, 4, 7),
};

static const u16 sFollowerPic_Cacnea[] = INCBIN_U16("graphics/object_events/pics/seguidores/cacnea.4bpp");
static const u16 sFollowerPal_Cacnea[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cacnea.gbapal");
static const u16 sFollowerPalShiny_Cacnea[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cacnea_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cacnea[] = {
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 0),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 1),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 2),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 3),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 4),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 5),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 6),
    overworld_frame(sFollowerPic_Cacnea, 4, 4, 7),
};

static const u16 sFollowerPic_Cacturne[] = INCBIN_U16("graphics/object_events/pics/seguidores/cacturne.4bpp");
static const u16 sFollowerPal_Cacturne[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cacturne.gbapal");
static const u16 sFollowerPalShiny_Cacturne[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cacturne_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cacturne[] = {
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 0),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 1),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 2),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 3),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 4),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 5),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 6),
    overworld_frame(sFollowerPic_Cacturne, 4, 4, 7),
};

static const u16 sFollowerPic_Swablu[] = INCBIN_U16("graphics/object_events/pics/seguidores/swablu.4bpp");
static const u16 sFollowerPal_Swablu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swablu.gbapal");
static const u16 sFollowerPalShiny_Swablu[] = INCBIN_U16("graphics/object_events/palettes/seguidores/swablu_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Swablu[] = {
    overworld_frame(sFollowerPic_Swablu, 4, 4, 0),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 1),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 2),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 3),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 4),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 5),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 6),
    overworld_frame(sFollowerPic_Swablu, 4, 4, 7),
};

static const u16 sFollowerPic_Altaria[] = INCBIN_U16("graphics/object_events/pics/seguidores/altaria.4bpp");
static const u16 sFollowerPal_Altaria[] = INCBIN_U16("graphics/object_events/palettes/seguidores/altaria.gbapal");
static const u16 sFollowerPalShiny_Altaria[] = INCBIN_U16("graphics/object_events/palettes/seguidores/altaria_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Altaria[] = {
    overworld_frame(sFollowerPic_Altaria, 4, 4, 0),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 1),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 2),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 3),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 4),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 5),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 6),
    overworld_frame(sFollowerPic_Altaria, 4, 4, 7),
};

static const u16 sFollowerPic_Zangoose[] = INCBIN_U16("graphics/object_events/pics/seguidores/zangoose.4bpp");
static const u16 sFollowerPal_Zangoose[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zangoose.gbapal");
static const u16 sFollowerPalShiny_Zangoose[] = INCBIN_U16("graphics/object_events/palettes/seguidores/zangoose_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Zangoose[] = {
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 0),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 1),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 2),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 3),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 4),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 5),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 6),
    overworld_frame(sFollowerPic_Zangoose, 4, 4, 7),
};

static const u16 sFollowerPic_Seviper[] = INCBIN_U16("graphics/object_events/pics/seguidores/seviper.4bpp");
static const u16 sFollowerPal_Seviper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seviper.gbapal");
static const u16 sFollowerPalShiny_Seviper[] = INCBIN_U16("graphics/object_events/palettes/seguidores/seviper_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Seviper[] = {
    overworld_frame(sFollowerPic_Seviper, 4, 4, 0),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 1),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 2),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 3),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 4),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 5),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 6),
    overworld_frame(sFollowerPic_Seviper, 4, 4, 7),
};

static const u16 sFollowerPic_Lunatone[] = INCBIN_U16("graphics/object_events/pics/seguidores/lunatone.4bpp");
static const u16 sFollowerPal_Lunatone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lunatone.gbapal");
static const u16 sFollowerPalShiny_Lunatone[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lunatone_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lunatone[] = {
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 0),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 1),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 2),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 3),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 4),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 5),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 6),
    overworld_frame(sFollowerPic_Lunatone, 4, 4, 7),
};

static const u16 sFollowerPic_Solrock[] = INCBIN_U16("graphics/object_events/pics/seguidores/solrock.4bpp");
static const u16 sFollowerPal_Solrock[] = INCBIN_U16("graphics/object_events/palettes/seguidores/solrock.gbapal");
static const u16 sFollowerPalShiny_Solrock[] = INCBIN_U16("graphics/object_events/palettes/seguidores/solrock_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Solrock[] = {
    overworld_frame(sFollowerPic_Solrock, 4, 4, 0),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 1),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 2),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 3),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 4),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 5),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 6),
    overworld_frame(sFollowerPic_Solrock, 4, 4, 7),
};

static const u16 sFollowerPic_Barboach[] = INCBIN_U16("graphics/object_events/pics/seguidores/barboach.4bpp");
static const u16 sFollowerPal_Barboach[] = INCBIN_U16("graphics/object_events/palettes/seguidores/barboach.gbapal");
static const u16 sFollowerPalShiny_Barboach[] = INCBIN_U16("graphics/object_events/palettes/seguidores/barboach_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Barboach[] = {
    overworld_frame(sFollowerPic_Barboach, 4, 4, 0),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 1),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 2),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 3),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 4),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 5),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 6),
    overworld_frame(sFollowerPic_Barboach, 4, 4, 7),
};

static const u16 sFollowerPic_Whiscash[] = INCBIN_U16("graphics/object_events/pics/seguidores/whiscash.4bpp");
static const u16 sFollowerPal_Whiscash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/whiscash.gbapal");
static const u16 sFollowerPalShiny_Whiscash[] = INCBIN_U16("graphics/object_events/palettes/seguidores/whiscash_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Whiscash[] = {
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 0),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 1),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 2),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 3),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 4),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 5),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 6),
    overworld_frame(sFollowerPic_Whiscash, 4, 4, 7),
};

static const u16 sFollowerPic_Corphish[] = INCBIN_U16("graphics/object_events/pics/seguidores/corphish.4bpp");
static const u16 sFollowerPal_Corphish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/corphish.gbapal");
static const u16 sFollowerPalShiny_Corphish[] = INCBIN_U16("graphics/object_events/palettes/seguidores/corphish_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Corphish[] = {
    overworld_frame(sFollowerPic_Corphish, 4, 4, 0),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 1),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 2),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 3),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 4),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 5),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 6),
    overworld_frame(sFollowerPic_Corphish, 4, 4, 7),
};

static const u16 sFollowerPic_Crawdaunt[] = INCBIN_U16("graphics/object_events/pics/seguidores/crawdaunt.4bpp");
static const u16 sFollowerPal_Crawdaunt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/crawdaunt.gbapal");
static const u16 sFollowerPalShiny_Crawdaunt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/crawdaunt_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Crawdaunt[] = {
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 0),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 1),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 2),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 3),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 4),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 5),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 6),
    overworld_frame(sFollowerPic_Crawdaunt, 4, 4, 7),
};

static const u16 sFollowerPic_Baltoy[] = INCBIN_U16("graphics/object_events/pics/seguidores/baltoy.4bpp");
static const u16 sFollowerPal_Baltoy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/baltoy.gbapal");
static const u16 sFollowerPalShiny_Baltoy[] = INCBIN_U16("graphics/object_events/palettes/seguidores/baltoy_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Baltoy[] = {
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 0),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 1),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 2),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 3),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 4),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 5),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 6),
    overworld_frame(sFollowerPic_Baltoy, 4, 4, 7),
};

static const u16 sFollowerPic_Claydol[] = INCBIN_U16("graphics/object_events/pics/seguidores/claydol.4bpp");
static const u16 sFollowerPal_Claydol[] = INCBIN_U16("graphics/object_events/palettes/seguidores/claydol.gbapal");
static const u16 sFollowerPalShiny_Claydol[] = INCBIN_U16("graphics/object_events/palettes/seguidores/claydol_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Claydol[] = {
    overworld_frame(sFollowerPic_Claydol, 4, 4, 0),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 1),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 2),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 3),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 4),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 5),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 6),
    overworld_frame(sFollowerPic_Claydol, 4, 4, 7),
};

static const u16 sFollowerPic_Lileep[] = INCBIN_U16("graphics/object_events/pics/seguidores/lileep.4bpp");
static const u16 sFollowerPal_Lileep[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lileep.gbapal");
static const u16 sFollowerPalShiny_Lileep[] = INCBIN_U16("graphics/object_events/palettes/seguidores/lileep_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Lileep[] = {
    overworld_frame(sFollowerPic_Lileep, 4, 4, 0),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 1),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 2),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 3),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 4),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 5),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 6),
    overworld_frame(sFollowerPic_Lileep, 4, 4, 7),
};

static const u16 sFollowerPic_Cradily[] = INCBIN_U16("graphics/object_events/pics/seguidores/cradily.4bpp");
static const u16 sFollowerPal_Cradily[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cradily.gbapal");
static const u16 sFollowerPalShiny_Cradily[] = INCBIN_U16("graphics/object_events/palettes/seguidores/cradily_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Cradily[] = {
    overworld_frame(sFollowerPic_Cradily, 4, 4, 0),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 1),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 2),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 3),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 4),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 5),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 6),
    overworld_frame(sFollowerPic_Cradily, 4, 4, 7),
};

static const u16 sFollowerPic_Anorith[] = INCBIN_U16("graphics/object_events/pics/seguidores/anorith.4bpp");
static const u16 sFollowerPal_Anorith[] = INCBIN_U16("graphics/object_events/palettes/seguidores/anorith.gbapal");
static const u16 sFollowerPalShiny_Anorith[] = INCBIN_U16("graphics/object_events/palettes/seguidores/anorith_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Anorith[] = {
    overworld_frame(sFollowerPic_Anorith, 4, 4, 0),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 1),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 2),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 3),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 4),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 5),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 6),
    overworld_frame(sFollowerPic_Anorith, 4, 4, 7),
};

static const u16 sFollowerPic_Armaldo[] = INCBIN_U16("graphics/object_events/pics/seguidores/armaldo.4bpp");
static const u16 sFollowerPal_Armaldo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/armaldo.gbapal");
static const u16 sFollowerPalShiny_Armaldo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/armaldo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Armaldo[] = {
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 0),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 1),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 2),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 3),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 4),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 5),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 6),
    overworld_frame(sFollowerPic_Armaldo, 4, 4, 7),
};

static const u16 sFollowerPic_Feebas[] = INCBIN_U16("graphics/object_events/pics/seguidores/feebas.4bpp");
static const u16 sFollowerPal_Feebas[] = INCBIN_U16("graphics/object_events/palettes/seguidores/feebas.gbapal");
static const u16 sFollowerPalShiny_Feebas[] = INCBIN_U16("graphics/object_events/palettes/seguidores/feebas_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Feebas[] = {
    overworld_frame(sFollowerPic_Feebas, 4, 4, 0),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 1),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 2),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 3),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 4),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 5),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 6),
    overworld_frame(sFollowerPic_Feebas, 4, 4, 7),
};

static const u16 sFollowerPic_Milotic[] = INCBIN_U16("graphics/object_events/pics/seguidores/milotic.4bpp");
static const u16 sFollowerPal_Milotic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/milotic.gbapal");
static const u16 sFollowerPalShiny_Milotic[] = INCBIN_U16("graphics/object_events/palettes/seguidores/milotic_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Milotic[] = {
    overworld_frame(sFollowerPic_Milotic, 4, 4, 0),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 1),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 2),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 3),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 4),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 5),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 6),
    overworld_frame(sFollowerPic_Milotic, 4, 4, 7),
};

static const u16 sFollowerPic_Castform[] = INCBIN_U16("graphics/object_events/pics/seguidores/castform.4bpp");
static const u16 sFollowerPal_Castform[] = INCBIN_U16("graphics/object_events/palettes/seguidores/castform.gbapal");
static const u16 sFollowerPalShiny_Castform[] = INCBIN_U16("graphics/object_events/palettes/seguidores/castform_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Castform[] = {
    overworld_frame(sFollowerPic_Castform, 4, 4, 0),
    overworld_frame(sFollowerPic_Castform, 4, 4, 1),
    overworld_frame(sFollowerPic_Castform, 4, 4, 2),
    overworld_frame(sFollowerPic_Castform, 4, 4, 3),
    overworld_frame(sFollowerPic_Castform, 4, 4, 4),
    overworld_frame(sFollowerPic_Castform, 4, 4, 5),
    overworld_frame(sFollowerPic_Castform, 4, 4, 6),
    overworld_frame(sFollowerPic_Castform, 4, 4, 7),
};

static const u16 sFollowerPic_Kecleon[] = INCBIN_U16("graphics/object_events/pics/seguidores/kecleon.4bpp");
static const u16 sFollowerPal_Kecleon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kecleon.gbapal");
static const u16 sFollowerPalShiny_Kecleon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kecleon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kecleon[] = {
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 0),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 1),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 2),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 3),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 4),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 5),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 6),
    overworld_frame(sFollowerPic_Kecleon, 4, 4, 7),
};

static const u16 sFollowerPic_Shuppet[] = INCBIN_U16("graphics/object_events/pics/seguidores/shuppet.4bpp");
static const u16 sFollowerPal_Shuppet[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shuppet.gbapal");
static const u16 sFollowerPalShiny_Shuppet[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shuppet_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shuppet[] = {
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 0),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 1),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 2),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 3),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 4),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 5),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 6),
    overworld_frame(sFollowerPic_Shuppet, 4, 4, 7),
};

static const u16 sFollowerPic_Banette[] = INCBIN_U16("graphics/object_events/pics/seguidores/banette.4bpp");
static const u16 sFollowerPal_Banette[] = INCBIN_U16("graphics/object_events/palettes/seguidores/banette.gbapal");
static const u16 sFollowerPalShiny_Banette[] = INCBIN_U16("graphics/object_events/palettes/seguidores/banette_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Banette[] = {
    overworld_frame(sFollowerPic_Banette, 4, 4, 0),
    overworld_frame(sFollowerPic_Banette, 4, 4, 1),
    overworld_frame(sFollowerPic_Banette, 4, 4, 2),
    overworld_frame(sFollowerPic_Banette, 4, 4, 3),
    overworld_frame(sFollowerPic_Banette, 4, 4, 4),
    overworld_frame(sFollowerPic_Banette, 4, 4, 5),
    overworld_frame(sFollowerPic_Banette, 4, 4, 6),
    overworld_frame(sFollowerPic_Banette, 4, 4, 7),
};

static const u16 sFollowerPic_Duskull[] = INCBIN_U16("graphics/object_events/pics/seguidores/duskull.4bpp");
static const u16 sFollowerPal_Duskull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/duskull.gbapal");
static const u16 sFollowerPalShiny_Duskull[] = INCBIN_U16("graphics/object_events/palettes/seguidores/duskull_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Duskull[] = {
    overworld_frame(sFollowerPic_Duskull, 4, 4, 0),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 1),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 2),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 3),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 4),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 5),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 6),
    overworld_frame(sFollowerPic_Duskull, 4, 4, 7),
};

static const u16 sFollowerPic_Dusclops[] = INCBIN_U16("graphics/object_events/pics/seguidores/dusclops.4bpp");
static const u16 sFollowerPal_Dusclops[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dusclops.gbapal");
static const u16 sFollowerPalShiny_Dusclops[] = INCBIN_U16("graphics/object_events/palettes/seguidores/dusclops_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Dusclops[] = {
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 0),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 1),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 2),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 3),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 4),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 5),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 6),
    overworld_frame(sFollowerPic_Dusclops, 4, 4, 7),
};

static const u16 sFollowerPic_Tropius[] = INCBIN_U16("graphics/object_events/pics/seguidores/tropius.4bpp");
static const u16 sFollowerPal_Tropius[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tropius.gbapal");
static const u16 sFollowerPalShiny_Tropius[] = INCBIN_U16("graphics/object_events/palettes/seguidores/tropius_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Tropius[] = {
    overworld_frame(sFollowerPic_Tropius, 4, 4, 0),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 1),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 2),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 3),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 4),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 5),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 6),
    overworld_frame(sFollowerPic_Tropius, 4, 4, 7),
};

static const u16 sFollowerPic_Chimecho[] = INCBIN_U16("graphics/object_events/pics/seguidores/chimecho.4bpp");
static const u16 sFollowerPal_Chimecho[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chimecho.gbapal");
static const u16 sFollowerPalShiny_Chimecho[] = INCBIN_U16("graphics/object_events/palettes/seguidores/chimecho_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Chimecho[] = {
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 0),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 1),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 2),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 3),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 4),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 5),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 6),
    overworld_frame(sFollowerPic_Chimecho, 4, 4, 7),
};

static const u16 sFollowerPic_Absol[] = INCBIN_U16("graphics/object_events/pics/seguidores/absol.4bpp");
static const u16 sFollowerPal_Absol[] = INCBIN_U16("graphics/object_events/palettes/seguidores/absol.gbapal");
static const u16 sFollowerPalShiny_Absol[] = INCBIN_U16("graphics/object_events/palettes/seguidores/absol_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Absol[] = {
    overworld_frame(sFollowerPic_Absol, 4, 4, 0),
    overworld_frame(sFollowerPic_Absol, 4, 4, 1),
    overworld_frame(sFollowerPic_Absol, 4, 4, 2),
    overworld_frame(sFollowerPic_Absol, 4, 4, 3),
    overworld_frame(sFollowerPic_Absol, 4, 4, 4),
    overworld_frame(sFollowerPic_Absol, 4, 4, 5),
    overworld_frame(sFollowerPic_Absol, 4, 4, 6),
    overworld_frame(sFollowerPic_Absol, 4, 4, 7),
};

static const u16 sFollowerPic_Wynaut[] = INCBIN_U16("graphics/object_events/pics/seguidores/wynaut.4bpp");
static const u16 sFollowerPal_Wynaut[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wynaut.gbapal");
static const u16 sFollowerPalShiny_Wynaut[] = INCBIN_U16("graphics/object_events/palettes/seguidores/wynaut_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Wynaut[] = {
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 0),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 1),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 2),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 3),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 4),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 5),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 6),
    overworld_frame(sFollowerPic_Wynaut, 4, 4, 7),
};

static const u16 sFollowerPic_Snorunt[] = INCBIN_U16("graphics/object_events/pics/seguidores/snorunt.4bpp");
static const u16 sFollowerPal_Snorunt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snorunt.gbapal");
static const u16 sFollowerPalShiny_Snorunt[] = INCBIN_U16("graphics/object_events/palettes/seguidores/snorunt_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Snorunt[] = {
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 0),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 1),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 2),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 3),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 4),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 5),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 6),
    overworld_frame(sFollowerPic_Snorunt, 4, 4, 7),
};

static const u16 sFollowerPic_Glalie[] = INCBIN_U16("graphics/object_events/pics/seguidores/glalie.4bpp");
static const u16 sFollowerPal_Glalie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/glalie.gbapal");
static const u16 sFollowerPalShiny_Glalie[] = INCBIN_U16("graphics/object_events/palettes/seguidores/glalie_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Glalie[] = {
    overworld_frame(sFollowerPic_Glalie, 4, 4, 0),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 1),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 2),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 3),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 4),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 5),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 6),
    overworld_frame(sFollowerPic_Glalie, 4, 4, 7),
};

static const u16 sFollowerPic_Spheal[] = INCBIN_U16("graphics/object_events/pics/seguidores/spheal.4bpp");
static const u16 sFollowerPal_Spheal[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spheal.gbapal");
static const u16 sFollowerPalShiny_Spheal[] = INCBIN_U16("graphics/object_events/palettes/seguidores/spheal_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Spheal[] = {
    overworld_frame(sFollowerPic_Spheal, 4, 4, 0),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 1),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 2),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 3),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 4),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 5),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 6),
    overworld_frame(sFollowerPic_Spheal, 4, 4, 7),
};

static const u16 sFollowerPic_Sealeo[] = INCBIN_U16("graphics/object_events/pics/seguidores/sealeo.4bpp");
static const u16 sFollowerPal_Sealeo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sealeo.gbapal");
static const u16 sFollowerPalShiny_Sealeo[] = INCBIN_U16("graphics/object_events/palettes/seguidores/sealeo_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Sealeo[] = {
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 0),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 1),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 2),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 3),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 4),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 5),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 6),
    overworld_frame(sFollowerPic_Sealeo, 4, 4, 7),
};

static const u16 sFollowerPic_Walrein[] = INCBIN_U16("graphics/object_events/pics/seguidores/walrein.4bpp");
static const u16 sFollowerPal_Walrein[] = INCBIN_U16("graphics/object_events/palettes/seguidores/walrein.gbapal");
static const u16 sFollowerPalShiny_Walrein[] = INCBIN_U16("graphics/object_events/palettes/seguidores/walrein_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Walrein[] = {
    overworld_frame(sFollowerPic_Walrein, 4, 4, 0),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 1),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 2),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 3),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 4),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 5),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 6),
    overworld_frame(sFollowerPic_Walrein, 4, 4, 7),
};

static const u16 sFollowerPic_Clamperl[] = INCBIN_U16("graphics/object_events/pics/seguidores/clamperl.4bpp");
static const u16 sFollowerPal_Clamperl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clamperl.gbapal");
static const u16 sFollowerPalShiny_Clamperl[] = INCBIN_U16("graphics/object_events/palettes/seguidores/clamperl_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Clamperl[] = {
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 0),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 1),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 2),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 3),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 4),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 5),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 6),
    overworld_frame(sFollowerPic_Clamperl, 4, 4, 7),
};

static const u16 sFollowerPic_Huntail[] = INCBIN_U16("graphics/object_events/pics/seguidores/huntail.4bpp");
static const u16 sFollowerPal_Huntail[] = INCBIN_U16("graphics/object_events/palettes/seguidores/huntail.gbapal");
static const u16 sFollowerPalShiny_Huntail[] = INCBIN_U16("graphics/object_events/palettes/seguidores/huntail_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Huntail[] = {
    overworld_frame(sFollowerPic_Huntail, 4, 4, 0),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 1),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 2),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 3),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 4),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 5),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 6),
    overworld_frame(sFollowerPic_Huntail, 4, 4, 7),
};

static const u16 sFollowerPic_Gorebyss[] = INCBIN_U16("graphics/object_events/pics/seguidores/gorebyss.4bpp");
static const u16 sFollowerPal_Gorebyss[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gorebyss.gbapal");
static const u16 sFollowerPalShiny_Gorebyss[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gorebyss_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gorebyss[] = {
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 0),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 1),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 2),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 3),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 4),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 5),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 6),
    overworld_frame(sFollowerPic_Gorebyss, 4, 4, 7),
};

static const u16 sFollowerPic_Relicanth[] = INCBIN_U16("graphics/object_events/pics/seguidores/relicanth.4bpp");
static const u16 sFollowerPal_Relicanth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/relicanth.gbapal");
static const u16 sFollowerPalShiny_Relicanth[] = INCBIN_U16("graphics/object_events/palettes/seguidores/relicanth_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Relicanth[] = {
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 0),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 1),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 2),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 3),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 4),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 5),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 6),
    overworld_frame(sFollowerPic_Relicanth, 4, 4, 7),
};

static const u16 sFollowerPic_Luvdisc[] = INCBIN_U16("graphics/object_events/pics/seguidores/luvdisc.4bpp");
static const u16 sFollowerPal_Luvdisc[] = INCBIN_U16("graphics/object_events/palettes/seguidores/luvdisc.gbapal");
static const u16 sFollowerPalShiny_Luvdisc[] = INCBIN_U16("graphics/object_events/palettes/seguidores/luvdisc_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Luvdisc[] = {
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 0),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 1),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 2),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 3),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 4),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 5),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 6),
    overworld_frame(sFollowerPic_Luvdisc, 4, 4, 7),
};

static const u16 sFollowerPic_Bagon[] = INCBIN_U16("graphics/object_events/pics/seguidores/bagon.4bpp");
static const u16 sFollowerPal_Bagon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bagon.gbapal");
static const u16 sFollowerPalShiny_Bagon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/bagon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Bagon[] = {
    overworld_frame(sFollowerPic_Bagon, 4, 4, 0),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 1),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 2),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 3),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 4),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 5),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 6),
    overworld_frame(sFollowerPic_Bagon, 4, 4, 7),
};

static const u16 sFollowerPic_Shelgon[] = INCBIN_U16("graphics/object_events/pics/seguidores/shelgon.4bpp");
static const u16 sFollowerPal_Shelgon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shelgon.gbapal");
static const u16 sFollowerPalShiny_Shelgon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/shelgon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Shelgon[] = {
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 0),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 1),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 2),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 3),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 4),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 5),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 6),
    overworld_frame(sFollowerPic_Shelgon, 4, 4, 7),
};

static const u16 sFollowerPic_Salamence[] = INCBIN_U16("graphics/object_events/pics/seguidores/salamence.4bpp");
static const u16 sFollowerPal_Salamence[] = INCBIN_U16("graphics/object_events/palettes/seguidores/salamence.gbapal");
static const u16 sFollowerPalShiny_Salamence[] = INCBIN_U16("graphics/object_events/palettes/seguidores/salamence_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Salamence[] = {
    overworld_frame(sFollowerPic_Salamence, 4, 4, 0),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 1),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 2),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 3),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 4),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 5),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 6),
    overworld_frame(sFollowerPic_Salamence, 4, 4, 7),
};

static const u16 sFollowerPic_Beldum[] = INCBIN_U16("graphics/object_events/pics/seguidores/beldum.4bpp");
static const u16 sFollowerPal_Beldum[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beldum.gbapal");
static const u16 sFollowerPalShiny_Beldum[] = INCBIN_U16("graphics/object_events/palettes/seguidores/beldum_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Beldum[] = {
    overworld_frame(sFollowerPic_Beldum, 4, 4, 0),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 1),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 2),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 3),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 4),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 5),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 6),
    overworld_frame(sFollowerPic_Beldum, 4, 4, 7),
};

static const u16 sFollowerPic_Metang[] = INCBIN_U16("graphics/object_events/pics/seguidores/metang.4bpp");
static const u16 sFollowerPal_Metang[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metang.gbapal");
static const u16 sFollowerPalShiny_Metang[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metang_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Metang[] = {
    overworld_frame(sFollowerPic_Metang, 4, 4, 0),
    overworld_frame(sFollowerPic_Metang, 4, 4, 1),
    overworld_frame(sFollowerPic_Metang, 4, 4, 2),
    overworld_frame(sFollowerPic_Metang, 4, 4, 3),
    overworld_frame(sFollowerPic_Metang, 4, 4, 4),
    overworld_frame(sFollowerPic_Metang, 4, 4, 5),
    overworld_frame(sFollowerPic_Metang, 4, 4, 6),
    overworld_frame(sFollowerPic_Metang, 4, 4, 7),
};

static const u16 sFollowerPic_Metagross[] = INCBIN_U16("graphics/object_events/pics/seguidores/metagross.4bpp");
static const u16 sFollowerPal_Metagross[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metagross.gbapal");
static const u16 sFollowerPalShiny_Metagross[] = INCBIN_U16("graphics/object_events/palettes/seguidores/metagross_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Metagross[] = {
    overworld_frame(sFollowerPic_Metagross, 4, 4, 0),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 1),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 2),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 3),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 4),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 5),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 6),
    overworld_frame(sFollowerPic_Metagross, 4, 4, 7),
};

static const u16 sFollowerPic_Regirock[] = INCBIN_U16("graphics/object_events/pics/seguidores/regirock.4bpp");
static const u16 sFollowerPal_Regirock[] = INCBIN_U16("graphics/object_events/palettes/seguidores/regirock.gbapal");
static const u16 sFollowerPalShiny_Regirock[] = INCBIN_U16("graphics/object_events/palettes/seguidores/regirock_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Regirock[] = {
    overworld_frame(sFollowerPic_Regirock, 4, 4, 0),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 1),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 2),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 3),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 4),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 5),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 6),
    overworld_frame(sFollowerPic_Regirock, 4, 4, 7),
};

static const u16 sFollowerPic_Regice[] = INCBIN_U16("graphics/object_events/pics/seguidores/regice.4bpp");
static const u16 sFollowerPal_Regice[] = INCBIN_U16("graphics/object_events/palettes/seguidores/regice.gbapal");
static const u16 sFollowerPalShiny_Regice[] = INCBIN_U16("graphics/object_events/palettes/seguidores/regice_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Regice[] = {
    overworld_frame(sFollowerPic_Regice, 4, 4, 0),
    overworld_frame(sFollowerPic_Regice, 4, 4, 1),
    overworld_frame(sFollowerPic_Regice, 4, 4, 2),
    overworld_frame(sFollowerPic_Regice, 4, 4, 3),
    overworld_frame(sFollowerPic_Regice, 4, 4, 4),
    overworld_frame(sFollowerPic_Regice, 4, 4, 5),
    overworld_frame(sFollowerPic_Regice, 4, 4, 6),
    overworld_frame(sFollowerPic_Regice, 4, 4, 7),
};

static const u16 sFollowerPic_Registeel[] = INCBIN_U16("graphics/object_events/pics/seguidores/registeel.4bpp");
static const u16 sFollowerPal_Registeel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/registeel.gbapal");
static const u16 sFollowerPalShiny_Registeel[] = INCBIN_U16("graphics/object_events/palettes/seguidores/registeel_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Registeel[] = {
    overworld_frame(sFollowerPic_Registeel, 4, 4, 0),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 1),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 2),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 3),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 4),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 5),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 6),
    overworld_frame(sFollowerPic_Registeel, 4, 4, 7),
};

static const u16 sFollowerPic_Latias[] = INCBIN_U16("graphics/object_events/pics/seguidores/latias.4bpp");
static const u16 sFollowerPal_Latias[] = INCBIN_U16("graphics/object_events/palettes/seguidores/latias.gbapal");
static const u16 sFollowerPalShiny_Latias[] = INCBIN_U16("graphics/object_events/palettes/seguidores/latias_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Latias[] = {
    overworld_frame(sFollowerPic_Latias, 4, 4, 0),
    overworld_frame(sFollowerPic_Latias, 4, 4, 1),
    overworld_frame(sFollowerPic_Latias, 4, 4, 2),
    overworld_frame(sFollowerPic_Latias, 4, 4, 3),
    overworld_frame(sFollowerPic_Latias, 4, 4, 4),
    overworld_frame(sFollowerPic_Latias, 4, 4, 5),
    overworld_frame(sFollowerPic_Latias, 4, 4, 6),
    overworld_frame(sFollowerPic_Latias, 4, 4, 7),
};

static const u16 sFollowerPic_Latios[] = INCBIN_U16("graphics/object_events/pics/seguidores/latios.4bpp");
static const u16 sFollowerPal_Latios[] = INCBIN_U16("graphics/object_events/palettes/seguidores/latios.gbapal");
static const u16 sFollowerPalShiny_Latios[] = INCBIN_U16("graphics/object_events/palettes/seguidores/latios_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Latios[] = {
    overworld_frame(sFollowerPic_Latios, 4, 4, 0),
    overworld_frame(sFollowerPic_Latios, 4, 4, 1),
    overworld_frame(sFollowerPic_Latios, 4, 4, 2),
    overworld_frame(sFollowerPic_Latios, 4, 4, 3),
    overworld_frame(sFollowerPic_Latios, 4, 4, 4),
    overworld_frame(sFollowerPic_Latios, 4, 4, 5),
    overworld_frame(sFollowerPic_Latios, 4, 4, 6),
    overworld_frame(sFollowerPic_Latios, 4, 4, 7),
};

static const u16 sFollowerPic_Kyogre[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/kyogre.4bpp");
static const u16 sFollowerPal_Kyogre[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kyogre.gbapal");
static const u16 sFollowerPalShiny_Kyogre[] = INCBIN_U16("graphics/object_events/palettes/seguidores/kyogre_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Kyogre[] = {
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 0),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 1),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 2),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 3),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 4),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 5),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 6),
    overworld_frame(sFollowerPic_Kyogre, 8, 8, 7),
};

static const u16 sFollowerPic_Groudon[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/groudon.4bpp");
static const u16 sFollowerPal_Groudon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/groudon.gbapal");
static const u16 sFollowerPalShiny_Groudon[] = INCBIN_U16("graphics/object_events/palettes/seguidores/groudon_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Groudon[] = {
    overworld_frame(sFollowerPic_Groudon, 8, 8, 0),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 1),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 2),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 3),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 4),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 5),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 6),
    overworld_frame(sFollowerPic_Groudon, 8, 8, 7),
};

static const u16 sFollowerPic_Rayquaza[] = INCBIN_U16("graphics/object_events/pics/seguidores/grandes/rayquaza.4bpp");
static const u16 sFollowerPal_Rayquaza[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rayquaza.gbapal");
static const u16 sFollowerPalShiny_Rayquaza[] = INCBIN_U16("graphics/object_events/palettes/seguidores/rayquaza_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Rayquaza[] = {
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 0),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 1),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 2),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 3),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 4),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 5),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 6),
    overworld_frame(sFollowerPic_Rayquaza, 8, 8, 7),
};

static const u16 sFollowerPic_Jirachi[] = INCBIN_U16("graphics/object_events/pics/seguidores/jirachi.4bpp");
static const u16 sFollowerPal_Jirachi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jirachi.gbapal");
static const u16 sFollowerPalShiny_Jirachi[] = INCBIN_U16("graphics/object_events/palettes/seguidores/jirachi_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Jirachi[] = {
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 0),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 1),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 2),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 3),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 4),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 5),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 6),
    overworld_frame(sFollowerPic_Jirachi, 4, 4, 7),
};

static const u16 sFollowerPic_Deoxys[] = INCBIN_U16("graphics/object_events/pics/seguidores/deoxys.4bpp");
static const u16 sFollowerPal_Deoxys[] = INCBIN_U16("graphics/object_events/palettes/seguidores/deoxys.gbapal");
static const u16 sFollowerPalShiny_Deoxys[] = INCBIN_U16("graphics/object_events/palettes/seguidores/deoxys_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Deoxys[] = {
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 0),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 1),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 2),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 3),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 4),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 5),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 6),
    overworld_frame(sFollowerPic_Deoxys, 4, 4, 7),
};

static const u16 sFollowerPic_Gible[] = INCBIN_U16("graphics/object_events/pics/seguidores/gible.4bpp");
static const u16 sFollowerPal_Gible[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gible.gbapal");
static const u16 sFollowerPalShiny_Gible[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gible_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gible[] = {
    overworld_frame(sFollowerPic_Gible, 4, 4, 0),
    overworld_frame(sFollowerPic_Gible, 4, 4, 1),
    overworld_frame(sFollowerPic_Gible, 4, 4, 2),
    overworld_frame(sFollowerPic_Gible, 4, 4, 3),
    overworld_frame(sFollowerPic_Gible, 4, 4, 4),
    overworld_frame(sFollowerPic_Gible, 4, 4, 5),
    overworld_frame(sFollowerPic_Gible, 4, 4, 6),
    overworld_frame(sFollowerPic_Gible, 4, 4, 7),
};

static const u16 sFollowerPic_Gabite[] = INCBIN_U16("graphics/object_events/pics/seguidores/gabite.4bpp");
static const u16 sFollowerPal_Gabite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gabite.gbapal");
static const u16 sFollowerPalShiny_Gabite[] = INCBIN_U16("graphics/object_events/palettes/seguidores/gabite_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Gabite[] = {
    overworld_frame(sFollowerPic_Gabite, 4, 4, 0),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 1),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 2),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 3),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 4),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 5),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 6),
    overworld_frame(sFollowerPic_Gabite, 4, 4, 7),
};

static const u16 sFollowerPic_Garchomp[] = INCBIN_U16("graphics/object_events/pics/seguidores/garchomp.4bpp");
static const u16 sFollowerPal_Garchomp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/garchomp.gbapal");
static const u16 sFollowerPalShiny_Garchomp[] = INCBIN_U16("graphics/object_events/palettes/seguidores/garchomp_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Garchomp[] = {
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 0),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 1),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 2),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 3),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 4),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 5),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 6),
    overworld_frame(sFollowerPic_Garchomp, 4, 4, 7),
};

static const u16 sFollowerPic_Darkrai[] = INCBIN_U16("graphics/object_events/pics/seguidores/darkrai.4bpp");
static const u16 sFollowerPal_Darkrai[] = INCBIN_U16("graphics/object_events/palettes/seguidores/darkrai.gbapal");
static const u16 sFollowerPalShiny_Darkrai[] = INCBIN_U16("graphics/object_events/palettes/seguidores/darkrai_shiny.gbapal");
static const struct SpriteFrameImage sFollowerPicTable_Darkrai[] = {
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 0),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 1),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 2),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 3),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 4),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 5),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 6),
    overworld_frame(sFollowerPic_Darkrai, 4, 4, 7),
};

const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT] = {
    [NATIONAL_DEX_BULBASAUR - 1] = {
        .species = SPECIES_BULBASAUR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Bulbasaur,
        .palette = sFollowerPal_Bulbasaur,
        .shinyPalette = sFollowerPalShiny_Bulbasaur,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_IVYSAUR - 1] = {
        .species = SPECIES_IVYSAUR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ivysaur,
        .palette = sFollowerPal_Ivysaur,
        .shinyPalette = sFollowerPalShiny_Ivysaur,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VENUSAUR - 1] = {
        .species = SPECIES_VENUSAUR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Venusaur,
        .palette = sFollowerPal_Venusaur,
        .shinyPalette = sFollowerPalShiny_Venusaur,
        .female = &sFollowerFemale_Venusaur,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHARMANDER - 1] = {
        .species = SPECIES_CHARMANDER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Charmander,
        .palette = sFollowerPal_Charmander,
        .shinyPalette = sFollowerPalShiny_Charmander,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHARMELEON - 1] = {
        .species = SPECIES_CHARMELEON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Charmeleon,
        .palette = sFollowerPal_Charmeleon,
        .shinyPalette = sFollowerPalShiny_Charmeleon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHARIZARD - 1] = {
        .species = SPECIES_CHARIZARD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Charizard,
        .palette = sFollowerPal_Charizard,
        .shinyPalette = sFollowerPalShiny_Charizard,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SQUIRTLE - 1] = {
        .species = SPECIES_SQUIRTLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Squirtle,
        .palette = sFollowerPal_Squirtle,
        .shinyPalette = sFollowerPalShiny_Squirtle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WARTORTLE - 1] = {
        .species = SPECIES_WARTORTLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wartortle,
        .palette = sFollowerPal_Wartortle,
        .shinyPalette = sFollowerPalShiny_Wartortle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BLASTOISE - 1] = {
        .species = SPECIES_BLASTOISE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Blastoise,
        .palette = sFollowerPal_Blastoise,
        .shinyPalette = sFollowerPalShiny_Blastoise,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CATERPIE - 1] = {
        .species = SPECIES_CATERPIE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Caterpie,
        .palette = sFollowerPal_Caterpie,
        .shinyPalette = sFollowerPalShiny_Caterpie,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_METAPOD - 1] = {
        .species = SPECIES_METAPOD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Metapod,
        .palette = sFollowerPal_Metapod,
        .shinyPalette = sFollowerPalShiny_Metapod,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BUTTERFREE - 1] = {
        .species = SPECIES_BUTTERFREE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Butterfree,
        .palette = sFollowerPal_Butterfree,
        .shinyPalette = sFollowerPalShiny_Butterfree,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WEEDLE - 1] = {
        .species = SPECIES_WEEDLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Weedle,
        .palette = sFollowerPal_Weedle,
        .shinyPalette = sFollowerPalShiny_Weedle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KAKUNA - 1] = {
        .species = SPECIES_KAKUNA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kakuna,
        .palette = sFollowerPal_Kakuna,
        .shinyPalette = sFollowerPalShiny_Kakuna,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BEEDRILL - 1] = {
        .species = SPECIES_BEEDRILL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Beedrill,
        .palette = sFollowerPal_Beedrill,
        .shinyPalette = sFollowerPalShiny_Beedrill,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PIDGEY - 1] = {
        .species = SPECIES_PIDGEY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pidgey,
        .palette = sFollowerPal_Pidgey,
        .shinyPalette = sFollowerPalShiny_Pidgey,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PIDGEOTTO - 1] = {
        .species = SPECIES_PIDGEOTTO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pidgeotto,
        .palette = sFollowerPal_Pidgeotto,
        .shinyPalette = sFollowerPalShiny_Pidgeotto,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PIDGEOT - 1] = {
        .species = SPECIES_PIDGEOT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pidgeot,
        .palette = sFollowerPal_Pidgeot,
        .shinyPalette = sFollowerPalShiny_Pidgeot,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RATTATA - 1] = {
        .species = SPECIES_RATTATA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Rattata,
        .palette = sFollowerPal_Rattata,
        .shinyPalette = sFollowerPalShiny_Rattata,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RATICATE - 1] = {
        .species = SPECIES_RATICATE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Raticate,
        .palette = sFollowerPal_Raticate,
        .shinyPalette = sFollowerPalShiny_Raticate,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SPEAROW - 1] = {
        .species = SPECIES_SPEAROW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Spearow,
        .palette = sFollowerPal_Spearow,
        .shinyPalette = sFollowerPalShiny_Spearow,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FEAROW - 1] = {
        .species = SPECIES_FEAROW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Fearow,
        .palette = sFollowerPal_Fearow,
        .shinyPalette = sFollowerPalShiny_Fearow,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_EKANS - 1] = {
        .species = SPECIES_EKANS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ekans,
        .palette = sFollowerPal_Ekans,
        .shinyPalette = sFollowerPalShiny_Ekans,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARBOK - 1] = {
        .species = SPECIES_ARBOK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Arbok,
        .palette = sFollowerPal_Arbok,
        .shinyPalette = sFollowerPalShiny_Arbok,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PIKACHU - 1] = {
        .species = SPECIES_PIKACHU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pikachu,
        .palette = sFollowerPal_Pikachu,
        .shinyPalette = sFollowerPalShiny_Pikachu,
        .female = &sFollowerFemale_Pikachu,
        .forms = NULL,
    },
    [NATIONAL_DEX_RAICHU - 1] = {
        .species = SPECIES_RAICHU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Raichu,
        .palette = sFollowerPal_Raichu,
        .shinyPalette = sFollowerPalShiny_Raichu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SANDSHREW - 1] = {
        .species = SPECIES_SANDSHREW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sandshrew,
        .palette = sFollowerPal_Sandshrew,
        .shinyPalette = sFollowerPalShiny_Sandshrew,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SANDSLASH - 1] = {
        .species = SPECIES_SANDSLASH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sandslash,
        .palette = sFollowerPal_Sandslash,
        .shinyPalette = sFollowerPalShiny_Sandslash,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDORAN_F - 1] = {
        .species = SPECIES_NIDORAN_F,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_NidoranF,
        .palette = sFollowerPal_NidoranF,
        .shinyPalette = sFollowerPalShiny_NidoranF,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDORINA - 1] = {
        .species = SPECIES_NIDORINA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nidorina,
        .palette = sFollowerPal_Nidorina,
        .shinyPalette = sFollowerPalShiny_Nidorina,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDOQUEEN - 1] = {
        .species = SPECIES_NIDOQUEEN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nidoqueen,
        .palette = sFollowerPal_Nidoqueen,
        .shinyPalette = sFollowerPalShiny_Nidoqueen,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDORAN_M - 1] = {
        .species = SPECIES_NIDORAN_M,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_NidoranM,
        .palette = sFollowerPal_NidoranM,
        .shinyPalette = sFollowerPalShiny_NidoranM,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDORINO - 1] = {
        .species = SPECIES_NIDORINO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nidorino,
        .palette = sFollowerPal_Nidorino,
        .shinyPalette = sFollowerPalShiny_Nidorino,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NIDOKING - 1] = {
        .species = SPECIES_NIDOKING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nidoking,
        .palette = sFollowerPal_Nidoking,
        .shinyPalette = sFollowerPalShiny_Nidoking,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLEFAIRY - 1] = {
        .species = SPECIES_CLEFAIRY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Clefairy,
        .palette = sFollowerPal_Clefairy,
        .shinyPalette = sFollowerPalShiny_Clefairy,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLEFABLE - 1] = {
        .species = SPECIES_CLEFABLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Clefable,
        .palette = sFollowerPal_Clefable,
        .shinyPalette = sFollowerPalShiny_Clefable,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VULPIX - 1] = {
        .species = SPECIES_VULPIX,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Vulpix,
        .palette = sFollowerPal_Vulpix,
        .shinyPalette = sFollowerPalShiny_Vulpix,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NINETALES - 1] = {
        .species = SPECIES_NINETALES,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ninetales,
        .palette = sFollowerPal_Ninetales,
        .shinyPalette = sFollowerPalShiny_Ninetales,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_JIGGLYPUFF - 1] = {
        .species = SPECIES_JIGGLYPUFF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Jigglypuff,
        .palette = sFollowerPal_Jigglypuff,
        .shinyPalette = sFollowerPalShiny_Jigglypuff,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WIGGLYTUFF - 1] = {
        .species = SPECIES_WIGGLYTUFF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wigglytuff,
        .palette = sFollowerPal_Wigglytuff,
        .shinyPalette = sFollowerPalShiny_Wigglytuff,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ZUBAT - 1] = {
        .species = SPECIES_ZUBAT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Zubat,
        .palette = sFollowerPal_Zubat,
        .shinyPalette = sFollowerPalShiny_Zubat,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GOLBAT - 1] = {
        .species = SPECIES_GOLBAT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Golbat,
        .palette = sFollowerPal_Golbat,
        .shinyPalette = sFollowerPalShiny_Golbat,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ODDISH - 1] = {
        .species = SPECIES_ODDISH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Oddish,
        .palette = sFollowerPal_Oddish,
        .shinyPalette = sFollowerPalShiny_Oddish,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GLOOM - 1] = {
        .species = SPECIES_GLOOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gloom,
        .palette = sFollowerPal_Gloom,
        .shinyPalette = sFollowerPalShiny_Gloom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VILEPLUME - 1] = {
        .species = SPECIES_VILEPLUME,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Vileplume,
        .palette = sFollowerPal_Vileplume,
        .shinyPalette = sFollowerPalShiny_Vileplume,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PARAS - 1] = {
        .species = SPECIES_PARAS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Paras,
        .palette = sFollowerPal_Paras,
        .shinyPalette = sFollowerPalShiny_Paras,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PARASECT - 1] = {
        .species = SPECIES_PARASECT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Parasect,
        .palette = sFollowerPal_Parasect,
        .shinyPalette = sFollowerPalShiny_Parasect,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VENONAT - 1] = {
        .species = SPECIES_VENONAT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Venonat,
        .palette = sFollowerPal_Venonat,
        .shinyPalette = sFollowerPalShiny_Venonat,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VENOMOTH - 1] = {
        .species = SPECIES_VENOMOTH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Venomoth,
        .palette = sFollowerPal_Venomoth,
        .shinyPalette = sFollowerPalShiny_Venomoth,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DIGLETT - 1] = {
        .species = SPECIES_DIGLETT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Diglett,
        .palette = sFollowerPal_Diglett,
        .shinyPalette = sFollowerPalShiny_Diglett,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DUGTRIO - 1] = {
        .species = SPECIES_DUGTRIO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dugtrio,
        .palette = sFollowerPal_Dugtrio,
        .shinyPalette = sFollowerPalShiny_Dugtrio,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEOWTH - 1] = {
        .species = SPECIES_MEOWTH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Meowth,
        .palette = sFollowerPal_Meowth,
        .shinyPalette = sFollowerPalShiny_Meowth,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PERSIAN - 1] = {
        .species = SPECIES_PERSIAN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Persian,
        .palette = sFollowerPal_Persian,
        .shinyPalette = sFollowerPalShiny_Persian,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PSYDUCK - 1] = {
        .species = SPECIES_PSYDUCK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Psyduck,
        .palette = sFollowerPal_Psyduck,
        .shinyPalette = sFollowerPalShiny_Psyduck,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GOLDUCK - 1] = {
        .species = SPECIES_GOLDUCK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Golduck,
        .palette = sFollowerPal_Golduck,
        .shinyPalette = sFollowerPalShiny_Golduck,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MANKEY - 1] = {
        .species = SPECIES_MANKEY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mankey,
        .palette = sFollowerPal_Mankey,
        .shinyPalette = sFollowerPalShiny_Mankey,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PRIMEAPE - 1] = {
        .species = SPECIES_PRIMEAPE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Primeape,
        .palette = sFollowerPal_Primeape,
        .shinyPalette = sFollowerPalShiny_Primeape,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GROWLITHE - 1] = {
        .species = SPECIES_GROWLITHE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Growlithe,
        .palette = sFollowerPal_Growlithe,
        .shinyPalette = sFollowerPalShiny_Growlithe,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARCANINE - 1] = {
        .species = SPECIES_ARCANINE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Arcanine,
        .palette = sFollowerPal_Arcanine,
        .shinyPalette = sFollowerPalShiny_Arcanine,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_POLIWAG - 1] = {
        .species = SPECIES_POLIWAG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Poliwag,
        .palette = sFollowerPal_Poliwag,
        .shinyPalette = sFollowerPalShiny_Poliwag,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_POLIWHIRL - 1] = {
        .species = SPECIES_POLIWHIRL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Poliwhirl,
        .palette = sFollowerPal_Poliwhirl,
        .shinyPalette = sFollowerPalShiny_Poliwhirl,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_POLIWRATH - 1] = {
        .species = SPECIES_POLIWRATH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Poliwrath,
        .palette = sFollowerPal_Poliwrath,
        .shinyPalette = sFollowerPalShiny_Poliwrath,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ABRA - 1] = {
        .species = SPECIES_ABRA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Abra,
        .palette = sFollowerPal_Abra,
        .shinyPalette = sFollowerPalShiny_Abra,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KADABRA - 1] = {
        .species = SPECIES_KADABRA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kadabra,
        .palette = sFollowerPal_Kadabra,
        .shinyPalette = sFollowerPalShiny_Kadabra,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ALAKAZAM - 1] = {
        .species = SPECIES_ALAKAZAM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Alakazam,
        .palette = sFollowerPal_Alakazam,
        .shinyPalette = sFollowerPalShiny_Alakazam,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MACHOP - 1] = {
        .species = SPECIES_MACHOP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Machop,
        .palette = sFollowerPal_Machop,
        .shinyPalette = sFollowerPalShiny_Machop,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MACHOKE - 1] = {
        .species = SPECIES_MACHOKE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Machoke,
        .palette = sFollowerPal_Machoke,
        .shinyPalette = sFollowerPalShiny_Machoke,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MACHAMP - 1] = {
        .species = SPECIES_MACHAMP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Machamp,
        .palette = sFollowerPal_Machamp,
        .shinyPalette = sFollowerPalShiny_Machamp,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BELLSPROUT - 1] = {
        .species = SPECIES_BELLSPROUT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Bellsprout,
        .palette = sFollowerPal_Bellsprout,
        .shinyPalette = sFollowerPalShiny_Bellsprout,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WEEPINBELL - 1] = {
        .species = SPECIES_WEEPINBELL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Weepinbell,
        .palette = sFollowerPal_Weepinbell,
        .shinyPalette = sFollowerPalShiny_Weepinbell,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VICTREEBEL - 1] = {
        .species = SPECIES_VICTREEBEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Victreebel,
        .palette = sFollowerPal_Victreebel,
        .shinyPalette = sFollowerPalShiny_Victreebel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TENTACOOL - 1] = {
        .species = SPECIES_TENTACOOL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tentacool,
        .palette = sFollowerPal_Tentacool,
        .shinyPalette = sFollowerPalShiny_Tentacool,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TENTACRUEL - 1] = {
        .species = SPECIES_TENTACRUEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tentacruel,
        .palette = sFollowerPal_Tentacruel,
        .shinyPalette = sFollowerPalShiny_Tentacruel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GEODUDE - 1] = {
        .species = SPECIES_GEODUDE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Geodude,
        .palette = sFollowerPal_Geodude,
        .shinyPalette = sFollowerPalShiny_Geodude,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GRAVELER - 1] = {
        .species = SPECIES_GRAVELER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Graveler,
        .palette = sFollowerPal_Graveler,
        .shinyPalette = sFollowerPalShiny_Graveler,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GOLEM - 1] = {
        .species = SPECIES_GOLEM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Golem,
        .palette = sFollowerPal_Golem,
        .shinyPalette = sFollowerPalShiny_Golem,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PONYTA - 1] = {
        .species = SPECIES_PONYTA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ponyta,
        .palette = sFollowerPal_Ponyta,
        .shinyPalette = sFollowerPalShiny_Ponyta,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RAPIDASH - 1] = {
        .species = SPECIES_RAPIDASH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Rapidash,
        .palette = sFollowerPal_Rapidash,
        .shinyPalette = sFollowerPalShiny_Rapidash,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLOWPOKE - 1] = {
        .species = SPECIES_SLOWPOKE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slowpoke,
        .palette = sFollowerPal_Slowpoke,
        .shinyPalette = sFollowerPalShiny_Slowpoke,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLOWBRO - 1] = {
        .species = SPECIES_SLOWBRO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slowbro,
        .palette = sFollowerPal_Slowbro,
        .shinyPalette = sFollowerPalShiny_Slowbro,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGNEMITE - 1] = {
        .species = SPECIES_MAGNEMITE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magnemite,
        .palette = sFollowerPal_Magnemite,
        .shinyPalette = sFollowerPalShiny_Magnemite,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGNETON - 1] = {
        .species = SPECIES_MAGNETON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magneton,
        .palette = sFollowerPal_Magneton,
        .shinyPalette = sFollowerPalShiny_Magneton,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FARFETCHD - 1] = {
        .species = SPECIES_FARFETCHD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Farfetchd,
        .palette = sFollowerPal_Farfetchd,
        .shinyPalette = sFollowerPalShiny_Farfetchd,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DODUO - 1] = {
        .species = SPECIES_DODUO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Doduo,
        .palette = sFollowerPal_Doduo,
        .shinyPalette = sFollowerPalShiny_Doduo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DODRIO - 1] = {
        .species = SPECIES_DODRIO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dodrio,
        .palette = sFollowerPal_Dodrio,
        .shinyPalette = sFollowerPalShiny_Dodrio,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEEL - 1] = {
        .species = SPECIES_SEEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Seel,
        .palette = sFollowerPal_Seel,
        .shinyPalette = sFollowerPalShiny_Seel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DEWGONG - 1] = {
        .species = SPECIES_DEWGONG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dewgong,
        .palette = sFollowerPal_Dewgong,
        .shinyPalette = sFollowerPalShiny_Dewgong,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GRIMER - 1] = {
        .species = SPECIES_GRIMER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Grimer,
        .palette = sFollowerPal_Grimer,
        .shinyPalette = sFollowerPalShiny_Grimer,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MUK - 1] = {
        .species = SPECIES_MUK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Muk,
        .palette = sFollowerPal_Muk,
        .shinyPalette = sFollowerPalShiny_Muk,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHELLDER - 1] = {
        .species = SPECIES_SHELLDER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shellder,
        .palette = sFollowerPal_Shellder,
        .shinyPalette = sFollowerPalShiny_Shellder,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLOYSTER - 1] = {
        .species = SPECIES_CLOYSTER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cloyster,
        .palette = sFollowerPal_Cloyster,
        .shinyPalette = sFollowerPalShiny_Cloyster,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GASTLY - 1] = {
        .species = SPECIES_GASTLY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gastly,
        .palette = sFollowerPal_Gastly,
        .shinyPalette = sFollowerPalShiny_Gastly,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HAUNTER - 1] = {
        .species = SPECIES_HAUNTER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Haunter,
        .palette = sFollowerPal_Haunter,
        .shinyPalette = sFollowerPalShiny_Haunter,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GENGAR - 1] = {
        .species = SPECIES_GENGAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gengar,
        .palette = sFollowerPal_Gengar,
        .shinyPalette = sFollowerPalShiny_Gengar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ONIX - 1] = {
        .species = SPECIES_ONIX,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Onix,
        .palette = sFollowerPal_Onix,
        .shinyPalette = sFollowerPalShiny_Onix,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DROWZEE - 1] = {
        .species = SPECIES_DROWZEE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Drowzee,
        .palette = sFollowerPal_Drowzee,
        .shinyPalette = sFollowerPalShiny_Drowzee,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HYPNO - 1] = {
        .species = SPECIES_HYPNO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hypno,
        .palette = sFollowerPal_Hypno,
        .shinyPalette = sFollowerPalShiny_Hypno,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KRABBY - 1] = {
        .species = SPECIES_KRABBY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Krabby,
        .palette = sFollowerPal_Krabby,
        .shinyPalette = sFollowerPalShiny_Krabby,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KINGLER - 1] = {
        .species = SPECIES_KINGLER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kingler,
        .palette = sFollowerPal_Kingler,
        .shinyPalette = sFollowerPalShiny_Kingler,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VOLTORB - 1] = {
        .species = SPECIES_VOLTORB,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Voltorb,
        .palette = sFollowerPal_Voltorb,
        .shinyPalette = sFollowerPalShiny_Voltorb,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ELECTRODE - 1] = {
        .species = SPECIES_ELECTRODE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Electrode,
        .palette = sFollowerPal_Electrode,
        .shinyPalette = sFollowerPalShiny_Electrode,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_EXEGGCUTE - 1] = {
        .species = SPECIES_EXEGGCUTE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Exeggcute,
        .palette = sFollowerPal_Exeggcute,
        .shinyPalette = sFollowerPalShiny_Exeggcute,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_EXEGGUTOR - 1] = {
        .species = SPECIES_EXEGGUTOR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Exeggutor,
        .palette = sFollowerPal_Exeggutor,
        .shinyPalette = sFollowerPalShiny_Exeggutor,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CUBONE - 1] = {
        .species = SPECIES_CUBONE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cubone,
        .palette = sFollowerPal_Cubone,
        .shinyPalette = sFollowerPalShiny_Cubone,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAROWAK - 1] = {
        .species = SPECIES_MAROWAK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Marowak,
        .palette = sFollowerPal_Marowak,
        .shinyPalette = sFollowerPalShiny_Marowak,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HITMONLEE - 1] = {
        .species = SPECIES_HITMONLEE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hitmonlee,
        .palette = sFollowerPal_Hitmonlee,
        .shinyPalette = sFollowerPalShiny_Hitmonlee,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HITMONCHAN - 1] = {
        .species = SPECIES_HITMONCHAN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hitmonchan,
        .palette = sFollowerPal_Hitmonchan,
        .shinyPalette = sFollowerPalShiny_Hitmonchan,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LICKITUNG - 1] = {
        .species = SPECIES_LICKITUNG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lickitung,
        .palette = sFollowerPal_Lickitung,
        .shinyPalette = sFollowerPalShiny_Lickitung,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KOFFING - 1] = {
        .species = SPECIES_KOFFING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Koffing,
        .palette = sFollowerPal_Koffing,
        .shinyPalette = sFollowerPalShiny_Koffing,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WEEZING - 1] = {
        .species = SPECIES_WEEZING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Weezing,
        .palette = sFollowerPal_Weezing,
        .shinyPalette = sFollowerPalShiny_Weezing,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RHYHORN - 1] = {
        .species = SPECIES_RHYHORN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Rhyhorn,
        .palette = sFollowerPal_Rhyhorn,
        .shinyPalette = sFollowerPalShiny_Rhyhorn,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RHYDON - 1] = {
        .species = SPECIES_RHYDON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Rhydon,
        .palette = sFollowerPal_Rhydon,
        .shinyPalette = sFollowerPalShiny_Rhydon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHANSEY - 1] = {
        .species = SPECIES_CHANSEY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Chansey,
        .palette = sFollowerPal_Chansey,
        .shinyPalette = sFollowerPalShiny_Chansey,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TANGELA - 1] = {
        .species = SPECIES_TANGELA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tangela,
        .palette = sFollowerPal_Tangela,
        .shinyPalette = sFollowerPalShiny_Tangela,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KANGASKHAN - 1] = {
        .species = SPECIES_KANGASKHAN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kangaskhan,
        .palette = sFollowerPal_Kangaskhan,
        .shinyPalette = sFollowerPalShiny_Kangaskhan,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HORSEA - 1] = {
        .species = SPECIES_HORSEA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Horsea,
        .palette = sFollowerPal_Horsea,
        .shinyPalette = sFollowerPalShiny_Horsea,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEADRA - 1] = {
        .species = SPECIES_SEADRA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Seadra,
        .palette = sFollowerPal_Seadra,
        .shinyPalette = sFollowerPalShiny_Seadra,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GOLDEEN - 1] = {
        .species = SPECIES_GOLDEEN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Goldeen,
        .palette = sFollowerPal_Goldeen,
        .shinyPalette = sFollowerPalShiny_Goldeen,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEAKING - 1] = {
        .species = SPECIES_SEAKING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Seaking,
        .palette = sFollowerPal_Seaking,
        .shinyPalette = sFollowerPalShiny_Seaking,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_STARYU - 1] = {
        .species = SPECIES_STARYU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Staryu,
        .palette = sFollowerPal_Staryu,
        .shinyPalette = sFollowerPalShiny_Staryu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_STARMIE - 1] = {
        .species = SPECIES_STARMIE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Starmie,
        .palette = sFollowerPal_Starmie,
        .shinyPalette = sFollowerPalShiny_Starmie,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MR_MIME - 1] = {
        .species = SPECIES_MR_MIME,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_MrMime,
        .palette = sFollowerPal_MrMime,
        .shinyPalette = sFollowerPalShiny_MrMime,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SCYTHER - 1] = {
        .species = SPECIES_SCYTHER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Scyther,
        .palette = sFollowerPal_Scyther,
        .shinyPalette = sFollowerPalShiny_Scyther,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_JYNX - 1] = {
        .species = SPECIES_JYNX,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Jynx,
        .palette = sFollowerPal_Jynx,
        .shinyPalette = sFollowerPalShiny_Jynx,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ELECTABUZZ - 1] = {
        .species = SPECIES_ELECTABUZZ,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Electabuzz,
        .palette = sFollowerPal_Electabuzz,
        .shinyPalette = sFollowerPalShiny_Electabuzz,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGMAR - 1] = {
        .species = SPECIES_MAGMAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magmar,
        .palette = sFollowerPal_Magmar,
        .shinyPalette = sFollowerPalShiny_Magmar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PINSIR - 1] = {
        .species = SPECIES_PINSIR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pinsir,
        .palette = sFollowerPal_Pinsir,
        .shinyPalette = sFollowerPalShiny_Pinsir,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TAUROS - 1] = {
        .species = SPECIES_TAUROS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tauros,
        .palette = sFollowerPal_Tauros,
        .shinyPalette = sFollowerPalShiny_Tauros,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGIKARP - 1] = {
        .species = SPECIES_MAGIKARP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magikarp,
        .palette = sFollowerPal_Magikarp,
        .shinyPalette = sFollowerPalShiny_Magikarp,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GYARADOS - 1] = {
        .species = SPECIES_GYARADOS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gyarados,
        .palette = sFollowerPal_Gyarados,
        .shinyPalette = sFollowerPalShiny_Gyarados,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LAPRAS - 1] = {
        .species = SPECIES_LAPRAS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lapras,
        .palette = sFollowerPal_Lapras,
        .shinyPalette = sFollowerPalShiny_Lapras,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DITTO - 1] = {
        .species = SPECIES_DITTO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ditto,
        .palette = sFollowerPal_Ditto,
        .shinyPalette = sFollowerPalShiny_Ditto,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_EEVEE - 1] = {
        .species = SPECIES_EEVEE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Eevee,
        .palette = sFollowerPal_Eevee,
        .shinyPalette = sFollowerPalShiny_Eevee,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VAPOREON - 1] = {
        .species = SPECIES_VAPOREON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Vaporeon,
        .palette = sFollowerPal_Vaporeon,
        .shinyPalette = sFollowerPalShiny_Vaporeon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_JOLTEON - 1] = {
        .species = SPECIES_JOLTEON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Jolteon,
        .palette = sFollowerPal_Jolteon,
        .shinyPalette = sFollowerPalShiny_Jolteon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FLAREON - 1] = {
        .species = SPECIES_FLAREON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Flareon,
        .palette = sFollowerPal_Flareon,
        .shinyPalette = sFollowerPalShiny_Flareon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PORYGON - 1] = {
        .species = SPECIES_PORYGON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Porygon,
        .palette = sFollowerPal_Porygon,
        .shinyPalette = sFollowerPalShiny_Porygon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_OMANYTE - 1] = {
        .species = SPECIES_OMANYTE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Omanyte,
        .palette = sFollowerPal_Omanyte,
        .shinyPalette = sFollowerPalShiny_Omanyte,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_OMASTAR - 1] = {
        .species = SPECIES_OMASTAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Omastar,
        .palette = sFollowerPal_Omastar,
        .shinyPalette = sFollowerPalShiny_Omastar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KABUTO - 1] = {
        .species = SPECIES_KABUTO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kabuto,
        .palette = sFollowerPal_Kabuto,
        .shinyPalette = sFollowerPalShiny_Kabuto,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KABUTOPS - 1] = {
        .species = SPECIES_KABUTOPS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kabutops,
        .palette = sFollowerPal_Kabutops,
        .shinyPalette = sFollowerPalShiny_Kabutops,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AERODACTYL - 1] = {
        .species = SPECIES_AERODACTYL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Aerodactyl,
        .palette = sFollowerPal_Aerodactyl,
        .shinyPalette = sFollowerPalShiny_Aerodactyl,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SNORLAX - 1] = {
        .species = SPECIES_SNORLAX,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Snorlax,
        .palette = sFollowerPal_Snorlax,
        .shinyPalette = sFollowerPalShiny_Snorlax,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARTICUNO - 1] = {
        .species = SPECIES_ARTICUNO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Articuno,
        .palette = sFollowerPal_Articuno,
        .shinyPalette = sFollowerPalShiny_Articuno,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ZAPDOS - 1] = {
        .species = SPECIES_ZAPDOS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Zapdos,
        .palette = sFollowerPal_Zapdos,
        .shinyPalette = sFollowerPalShiny_Zapdos,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MOLTRES - 1] = {
        .species = SPECIES_MOLTRES,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Moltres,
        .palette = sFollowerPal_Moltres,
        .shinyPalette = sFollowerPalShiny_Moltres,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DRATINI - 1] = {
        .species = SPECIES_DRATINI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dratini,
        .palette = sFollowerPal_Dratini,
        .shinyPalette = sFollowerPalShiny_Dratini,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DRAGONAIR - 1] = {
        .species = SPECIES_DRAGONAIR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dragonair,
        .palette = sFollowerPal_Dragonair,
        .shinyPalette = sFollowerPalShiny_Dragonair,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DRAGONITE - 1] = {
        .species = SPECIES_DRAGONITE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dragonite,
        .palette = sFollowerPal_Dragonite,
        .shinyPalette = sFollowerPalShiny_Dragonite,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEWTWO - 1] = {
        .species = SPECIES_MEWTWO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mewtwo,
        .palette = sFollowerPal_Mewtwo,
        .shinyPalette = sFollowerPalShiny_Mewtwo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEW - 1] = {
        .species = SPECIES_MEW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mew,
        .palette = sFollowerPal_Mew,
        .shinyPalette = sFollowerPalShiny_Mew,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHIKORITA - 1] = {
        .species = SPECIES_CHIKORITA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Chikorita,
        .palette = sFollowerPal_Chikorita,
        .shinyPalette = sFollowerPalShiny_Chikorita,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BAYLEEF - 1] = {
        .species = SPECIES_BAYLEEF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Bayleef,
        .palette = sFollowerPal_Bayleef,
        .shinyPalette = sFollowerPalShiny_Bayleef,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEGANIUM - 1] = {
        .species = SPECIES_MEGANIUM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Meganium,
        .palette = sFollowerPal_Meganium,
        .shinyPalette = sFollowerPalShiny_Meganium,
        .female = &sFollowerFemale_Meganium,
        .forms = NULL,
    },
    [NATIONAL_DEX_CYNDAQUIL - 1] = {
        .species = SPECIES_CYNDAQUIL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cyndaquil,
        .palette = sFollowerPal_Cyndaquil,
        .shinyPalette = sFollowerPalShiny_Cyndaquil,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_QUILAVA - 1] = {
        .species = SPECIES_QUILAVA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Quilava,
        .palette = sFollowerPal_Quilava,
        .shinyPalette = sFollowerPalShiny_Quilava,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TYPHLOSION - 1] = {
        .species = SPECIES_TYPHLOSION,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Typhlosion,
        .palette = sFollowerPal_Typhlosion,
        .shinyPalette = sFollowerPalShiny_Typhlosion,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TOTODILE - 1] = {
        .species = SPECIES_TOTODILE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Totodile,
        .palette = sFollowerPal_Totodile,
        .shinyPalette = sFollowerPalShiny_Totodile,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CROCONAW - 1] = {
        .species = SPECIES_CROCONAW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Croconaw,
        .palette = sFollowerPal_Croconaw,
        .shinyPalette = sFollowerPalShiny_Croconaw,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FERALIGATR - 1] = {
        .species = SPECIES_FERALIGATR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Feraligatr,
        .palette = sFollowerPal_Feraligatr,
        .shinyPalette = sFollowerPalShiny_Feraligatr,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SENTRET - 1] = {
        .species = SPECIES_SENTRET,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sentret,
        .palette = sFollowerPal_Sentret,
        .shinyPalette = sFollowerPalShiny_Sentret,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FURRET - 1] = {
        .species = SPECIES_FURRET,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Furret,
        .palette = sFollowerPal_Furret,
        .shinyPalette = sFollowerPalShiny_Furret,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HOOTHOOT - 1] = {
        .species = SPECIES_HOOTHOOT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hoothoot,
        .palette = sFollowerPal_Hoothoot,
        .shinyPalette = sFollowerPalShiny_Hoothoot,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NOCTOWL - 1] = {
        .species = SPECIES_NOCTOWL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Noctowl,
        .palette = sFollowerPal_Noctowl,
        .shinyPalette = sFollowerPalShiny_Noctowl,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LEDYBA - 1] = {
        .species = SPECIES_LEDYBA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ledyba,
        .palette = sFollowerPal_Ledyba,
        .shinyPalette = sFollowerPalShiny_Ledyba,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LEDIAN - 1] = {
        .species = SPECIES_LEDIAN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ledian,
        .palette = sFollowerPal_Ledian,
        .shinyPalette = sFollowerPalShiny_Ledian,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SPINARAK - 1] = {
        .species = SPECIES_SPINARAK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Spinarak,
        .palette = sFollowerPal_Spinarak,
        .shinyPalette = sFollowerPalShiny_Spinarak,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARIADOS - 1] = {
        .species = SPECIES_ARIADOS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ariados,
        .palette = sFollowerPal_Ariados,
        .shinyPalette = sFollowerPalShiny_Ariados,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CROBAT - 1] = {
        .species = SPECIES_CROBAT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Crobat,
        .palette = sFollowerPal_Crobat,
        .shinyPalette = sFollowerPalShiny_Crobat,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHINCHOU - 1] = {
        .species = SPECIES_CHINCHOU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Chinchou,
        .palette = sFollowerPal_Chinchou,
        .shinyPalette = sFollowerPalShiny_Chinchou,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LANTURN - 1] = {
        .species = SPECIES_LANTURN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lanturn,
        .palette = sFollowerPal_Lanturn,
        .shinyPalette = sFollowerPalShiny_Lanturn,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PICHU - 1] = {
        .species = SPECIES_PICHU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pichu,
        .palette = sFollowerPal_Pichu,
        .shinyPalette = sFollowerPalShiny_Pichu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLEFFA - 1] = {
        .species = SPECIES_CLEFFA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cleffa,
        .palette = sFollowerPal_Cleffa,
        .shinyPalette = sFollowerPalShiny_Cleffa,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_IGGLYBUFF - 1] = {
        .species = SPECIES_IGGLYBUFF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Igglybuff,
        .palette = sFollowerPal_Igglybuff,
        .shinyPalette = sFollowerPalShiny_Igglybuff,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TOGEPI - 1] = {
        .species = SPECIES_TOGEPI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Togepi,
        .palette = sFollowerPal_Togepi,
        .shinyPalette = sFollowerPalShiny_Togepi,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TOGETIC - 1] = {
        .species = SPECIES_TOGETIC,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Togetic,
        .palette = sFollowerPal_Togetic,
        .shinyPalette = sFollowerPalShiny_Togetic,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NATU - 1] = {
        .species = SPECIES_NATU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Natu,
        .palette = sFollowerPal_Natu,
        .shinyPalette = sFollowerPalShiny_Natu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_XATU - 1] = {
        .species = SPECIES_XATU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Xatu,
        .palette = sFollowerPal_Xatu,
        .shinyPalette = sFollowerPalShiny_Xatu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAREEP - 1] = {
        .species = SPECIES_MAREEP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mareep,
        .palette = sFollowerPal_Mareep,
        .shinyPalette = sFollowerPalShiny_Mareep,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FLAAFFY - 1] = {
        .species = SPECIES_FLAAFFY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Flaaffy,
        .palette = sFollowerPal_Flaaffy,
        .shinyPalette = sFollowerPalShiny_Flaaffy,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AMPHAROS - 1] = {
        .species = SPECIES_AMPHAROS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ampharos,
        .palette = sFollowerPal_Ampharos,
        .shinyPalette = sFollowerPalShiny_Ampharos,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BELLOSSOM - 1] = {
        .species = SPECIES_BELLOSSOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Bellossom,
        .palette = sFollowerPal_Bellossom,
        .shinyPalette = sFollowerPalShiny_Bellossom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MARILL - 1] = {
        .species = SPECIES_MARILL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Marill,
        .palette = sFollowerPal_Marill,
        .shinyPalette = sFollowerPalShiny_Marill,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AZUMARILL - 1] = {
        .species = SPECIES_AZUMARILL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Azumarill,
        .palette = sFollowerPal_Azumarill,
        .shinyPalette = sFollowerPalShiny_Azumarill,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SUDOWOODO - 1] = {
        .species = SPECIES_SUDOWOODO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sudowoodo,
        .palette = sFollowerPal_Sudowoodo,
        .shinyPalette = sFollowerPalShiny_Sudowoodo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_POLITOED - 1] = {
        .species = SPECIES_POLITOED,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Politoed,
        .palette = sFollowerPal_Politoed,
        .shinyPalette = sFollowerPalShiny_Politoed,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HOPPIP - 1] = {
        .species = SPECIES_HOPPIP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hoppip,
        .palette = sFollowerPal_Hoppip,
        .shinyPalette = sFollowerPalShiny_Hoppip,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SKIPLOOM - 1] = {
        .species = SPECIES_SKIPLOOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Skiploom,
        .palette = sFollowerPal_Skiploom,
        .shinyPalette = sFollowerPalShiny_Skiploom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_JUMPLUFF - 1] = {
        .species = SPECIES_JUMPLUFF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Jumpluff,
        .palette = sFollowerPal_Jumpluff,
        .shinyPalette = sFollowerPalShiny_Jumpluff,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AIPOM - 1] = {
        .species = SPECIES_AIPOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Aipom,
        .palette = sFollowerPal_Aipom,
        .shinyPalette = sFollowerPalShiny_Aipom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SUNKERN - 1] = {
        .species = SPECIES_SUNKERN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sunkern,
        .palette = sFollowerPal_Sunkern,
        .shinyPalette = sFollowerPalShiny_Sunkern,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SUNFLORA - 1] = {
        .species = SPECIES_SUNFLORA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sunflora,
        .palette = sFollowerPal_Sunflora,
        .shinyPalette = sFollowerPalShiny_Sunflora,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_YANMA - 1] = {
        .species = SPECIES_YANMA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Yanma,
        .palette = sFollowerPal_Yanma,
        .shinyPalette = sFollowerPalShiny_Yanma,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WOOPER - 1] = {
        .species = SPECIES_WOOPER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wooper,
        .palette = sFollowerPal_Wooper,
        .shinyPalette = sFollowerPalShiny_Wooper,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_QUAGSIRE - 1] = {
        .species = SPECIES_QUAGSIRE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Quagsire,
        .palette = sFollowerPal_Quagsire,
        .shinyPalette = sFollowerPalShiny_Quagsire,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ESPEON - 1] = {
        .species = SPECIES_ESPEON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Espeon,
        .palette = sFollowerPal_Espeon,
        .shinyPalette = sFollowerPalShiny_Espeon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_UMBREON - 1] = {
        .species = SPECIES_UMBREON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Umbreon,
        .palette = sFollowerPal_Umbreon,
        .shinyPalette = sFollowerPalShiny_Umbreon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MURKROW - 1] = {
        .species = SPECIES_MURKROW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Murkrow,
        .palette = sFollowerPal_Murkrow,
        .shinyPalette = sFollowerPalShiny_Murkrow,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLOWKING - 1] = {
        .species = SPECIES_SLOWKING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slowking,
        .palette = sFollowerPal_Slowking,
        .shinyPalette = sFollowerPalShiny_Slowking,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MISDREAVUS - 1] = {
        .species = SPECIES_MISDREAVUS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Misdreavus,
        .palette = sFollowerPal_Misdreavus,
        .shinyPalette = sFollowerPalShiny_Misdreavus,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_UNOWN - 1] = {
        .species = SPECIES_UNOWN,
        .large = FALSE,
        .formCount = 28,
        .images = sFollowerPicTable_UnownA,
        .palette = sFollowerPal_UnownA,
        .shinyPalette = sFollowerPalShiny_UnownA,
        .female = NULL,
        .forms = sFollowerForms_Unown,
    },
    [NATIONAL_DEX_WOBBUFFET - 1] = {
        .species = SPECIES_WOBBUFFET,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wobbuffet,
        .palette = sFollowerPal_Wobbuffet,
        .shinyPalette = sFollowerPalShiny_Wobbuffet,
        .female = &sFollowerFemale_Wobbuffet,
        .forms = NULL,
    },
    [NATIONAL_DEX_GIRAFARIG - 1] = {
        .species = SPECIES_GIRAFARIG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Girafarig,
        .palette = sFollowerPal_Girafarig,
        .shinyPalette = sFollowerPalShiny_Girafarig,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PINECO - 1] = {
        .species = SPECIES_PINECO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pineco,
        .palette = sFollowerPal_Pineco,
        .shinyPalette = sFollowerPalShiny_Pineco,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FORRETRESS - 1] = {
        .species = SPECIES_FORRETRESS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Forretress,
        .palette = sFollowerPal_Forretress,
        .shinyPalette = sFollowerPalShiny_Forretress,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DUNSPARCE - 1] = {
        .species = SPECIES_DUNSPARCE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dunsparce,
        .palette = sFollowerPal_Dunsparce,
        .shinyPalette = sFollowerPalShiny_Dunsparce,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GLIGAR - 1] = {
        .species = SPECIES_GLIGAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gligar,
        .palette = sFollowerPal_Gligar,
        .shinyPalette = sFollowerPalShiny_Gligar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_STEELIX - 1] = {
        .species = SPECIES_STEELIX,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Steelix,
        .palette = sFollowerPal_Steelix,
        .shinyPalette = sFollowerPalShiny_Steelix,
        .female = &sFollowerFemale_Steelix,
        .forms = NULL,
    },
    [NATIONAL_DEX_SNUBBULL - 1] = {
        .species = SPECIES_SNUBBULL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Snubbull,
        .palette = sFollowerPal_Snubbull,
        .shinyPalette = sFollowerPalShiny_Snubbull,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GRANBULL - 1] = {
        .species = SPECIES_GRANBULL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Granbull,
        .palette = sFollowerPal_Granbull,
        .shinyPalette = sFollowerPalShiny_Granbull,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_QWILFISH - 1] = {
        .species = SPECIES_QWILFISH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Qwilfish,
        .palette = sFollowerPal_Qwilfish,
        .shinyPalette = sFollowerPalShiny_Qwilfish,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SCIZOR - 1] = {
        .species = SPECIES_SCIZOR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Scizor,
        .palette = sFollowerPal_Scizor,
        .shinyPalette = sFollowerPalShiny_Scizor,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHUCKLE - 1] = {
        .species = SPECIES_SHUCKLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shuckle,
        .palette = sFollowerPal_Shuckle,
        .shinyPalette = sFollowerPalShiny_Shuckle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HERACROSS - 1] = {
        .species = SPECIES_HERACROSS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Heracross,
        .palette = sFollowerPal_Heracross,
        .shinyPalette = sFollowerPalShiny_Heracross,
        .female = &sFollowerFemale_Heracross,
        .forms = NULL,
    },
    [NATIONAL_DEX_SNEASEL - 1] = {
        .species = SPECIES_SNEASEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sneasel,
        .palette = sFollowerPal_Sneasel,
        .shinyPalette = sFollowerPalShiny_Sneasel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TEDDIURSA - 1] = {
        .species = SPECIES_TEDDIURSA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Teddiursa,
        .palette = sFollowerPal_Teddiursa,
        .shinyPalette = sFollowerPalShiny_Teddiursa,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_URSARING - 1] = {
        .species = SPECIES_URSARING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ursaring,
        .palette = sFollowerPal_Ursaring,
        .shinyPalette = sFollowerPalShiny_Ursaring,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLUGMA - 1] = {
        .species = SPECIES_SLUGMA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slugma,
        .palette = sFollowerPal_Slugma,
        .shinyPalette = sFollowerPalShiny_Slugma,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGCARGO - 1] = {
        .species = SPECIES_MAGCARGO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magcargo,
        .palette = sFollowerPal_Magcargo,
        .shinyPalette = sFollowerPalShiny_Magcargo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SWINUB - 1] = {
        .species = SPECIES_SWINUB,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Swinub,
        .palette = sFollowerPal_Swinub,
        .shinyPalette = sFollowerPalShiny_Swinub,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PILOSWINE - 1] = {
        .species = SPECIES_PILOSWINE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Piloswine,
        .palette = sFollowerPal_Piloswine,
        .shinyPalette = sFollowerPalShiny_Piloswine,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CORSOLA - 1] = {
        .species = SPECIES_CORSOLA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Corsola,
        .palette = sFollowerPal_Corsola,
        .shinyPalette = sFollowerPalShiny_Corsola,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_REMORAID - 1] = {
        .species = SPECIES_REMORAID,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Remoraid,
        .palette = sFollowerPal_Remoraid,
        .shinyPalette = sFollowerPalShiny_Remoraid,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_OCTILLERY - 1] = {
        .species = SPECIES_OCTILLERY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Octillery,
        .palette = sFollowerPal_Octillery,
        .shinyPalette = sFollowerPalShiny_Octillery,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DELIBIRD - 1] = {
        .species = SPECIES_DELIBIRD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Delibird,
        .palette = sFollowerPal_Delibird,
        .shinyPalette = sFollowerPalShiny_Delibird,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MANTINE - 1] = {
        .species = SPECIES_MANTINE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mantine,
        .palette = sFollowerPal_Mantine,
        .shinyPalette = sFollowerPalShiny_Mantine,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SKARMORY - 1] = {
        .species = SPECIES_SKARMORY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Skarmory,
        .palette = sFollowerPal_Skarmory,
        .shinyPalette = sFollowerPalShiny_Skarmory,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HOUNDOUR - 1] = {
        .species = SPECIES_HOUNDOUR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Houndour,
        .palette = sFollowerPal_Houndour,
        .shinyPalette = sFollowerPalShiny_Houndour,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HOUNDOOM - 1] = {
        .species = SPECIES_HOUNDOOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Houndoom,
        .palette = sFollowerPal_Houndoom,
        .shinyPalette = sFollowerPalShiny_Houndoom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KINGDRA - 1] = {
        .species = SPECIES_KINGDRA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kingdra,
        .palette = sFollowerPal_Kingdra,
        .shinyPalette = sFollowerPalShiny_Kingdra,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PHANPY - 1] = {
        .species = SPECIES_PHANPY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Phanpy,
        .palette = sFollowerPal_Phanpy,
        .shinyPalette = sFollowerPalShiny_Phanpy,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DONPHAN - 1] = {
        .species = SPECIES_DONPHAN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Donphan,
        .palette = sFollowerPal_Donphan,
        .shinyPalette = sFollowerPalShiny_Donphan,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PORYGON2 - 1] = {
        .species = SPECIES_PORYGON2,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Porygon2,
        .palette = sFollowerPal_Porygon2,
        .shinyPalette = sFollowerPalShiny_Porygon2,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_STANTLER - 1] = {
        .species = SPECIES_STANTLER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Stantler,
        .palette = sFollowerPal_Stantler,
        .shinyPalette = sFollowerPalShiny_Stantler,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SMEARGLE - 1] = {
        .species = SPECIES_SMEARGLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Smeargle,
        .palette = sFollowerPal_Smeargle,
        .shinyPalette = sFollowerPalShiny_Smeargle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TYROGUE - 1] = {
        .species = SPECIES_TYROGUE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tyrogue,
        .palette = sFollowerPal_Tyrogue,
        .shinyPalette = sFollowerPalShiny_Tyrogue,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HITMONTOP - 1] = {
        .species = SPECIES_HITMONTOP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hitmontop,
        .palette = sFollowerPal_Hitmontop,
        .shinyPalette = sFollowerPalShiny_Hitmontop,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SMOOCHUM - 1] = {
        .species = SPECIES_SMOOCHUM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Smoochum,
        .palette = sFollowerPal_Smoochum,
        .shinyPalette = sFollowerPalShiny_Smoochum,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ELEKID - 1] = {
        .species = SPECIES_ELEKID,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Elekid,
        .palette = sFollowerPal_Elekid,
        .shinyPalette = sFollowerPalShiny_Elekid,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAGBY - 1] = {
        .species = SPECIES_MAGBY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Magby,
        .palette = sFollowerPal_Magby,
        .shinyPalette = sFollowerPalShiny_Magby,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MILTANK - 1] = {
        .species = SPECIES_MILTANK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Miltank,
        .palette = sFollowerPal_Miltank,
        .shinyPalette = sFollowerPalShiny_Miltank,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BLISSEY - 1] = {
        .species = SPECIES_BLISSEY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Blissey,
        .palette = sFollowerPal_Blissey,
        .shinyPalette = sFollowerPalShiny_Blissey,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RAIKOU - 1] = {
        .species = SPECIES_RAIKOU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Raikou,
        .palette = sFollowerPal_Raikou,
        .shinyPalette = sFollowerPalShiny_Raikou,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ENTEI - 1] = {
        .species = SPECIES_ENTEI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Entei,
        .palette = sFollowerPal_Entei,
        .shinyPalette = sFollowerPalShiny_Entei,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SUICUNE - 1] = {
        .species = SPECIES_SUICUNE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Suicune,
        .palette = sFollowerPal_Suicune,
        .shinyPalette = sFollowerPalShiny_Suicune,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LARVITAR - 1] = {
        .species = SPECIES_LARVITAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Larvitar,
        .palette = sFollowerPal_Larvitar,
        .shinyPalette = sFollowerPalShiny_Larvitar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PUPITAR - 1] = {
        .species = SPECIES_PUPITAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pupitar,
        .palette = sFollowerPal_Pupitar,
        .shinyPalette = sFollowerPalShiny_Pupitar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TYRANITAR - 1] = {
        .species = SPECIES_TYRANITAR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tyranitar,
        .palette = sFollowerPal_Tyranitar,
        .shinyPalette = sFollowerPalShiny_Tyranitar,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LUGIA - 1] = {
        .species = SPECIES_LUGIA,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Lugia,
        .palette = sFollowerPal_Lugia,
        .shinyPalette = sFollowerPalShiny_Lugia,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HO_OH - 1] = {
        .species = SPECIES_HO_OH,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_HoOh,
        .palette = sFollowerPal_HoOh,
        .shinyPalette = sFollowerPalShiny_HoOh,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CELEBI - 1] = {
        .species = SPECIES_CELEBI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Celebi,
        .palette = sFollowerPal_Celebi,
        .shinyPalette = sFollowerPalShiny_Celebi,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TREECKO - 1] = {
        .species = SPECIES_TREECKO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Treecko,
        .palette = sFollowerPal_Treecko,
        .shinyPalette = sFollowerPalShiny_Treecko,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GROVYLE - 1] = {
        .species = SPECIES_GROVYLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Grovyle,
        .palette = sFollowerPal_Grovyle,
        .shinyPalette = sFollowerPalShiny_Grovyle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SCEPTILE - 1] = {
        .species = SPECIES_SCEPTILE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sceptile,
        .palette = sFollowerPal_Sceptile,
        .shinyPalette = sFollowerPalShiny_Sceptile,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TORCHIC - 1] = {
        .species = SPECIES_TORCHIC,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Torchic,
        .palette = sFollowerPal_Torchic,
        .shinyPalette = sFollowerPalShiny_Torchic,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_COMBUSKEN - 1] = {
        .species = SPECIES_COMBUSKEN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Combusken,
        .palette = sFollowerPal_Combusken,
        .shinyPalette = sFollowerPalShiny_Combusken,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BLAZIKEN - 1] = {
        .species = SPECIES_BLAZIKEN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Blaziken,
        .palette = sFollowerPal_Blaziken,
        .shinyPalette = sFollowerPalShiny_Blaziken,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MUDKIP - 1] = {
        .species = SPECIES_MUDKIP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mudkip,
        .palette = sFollowerPal_Mudkip,
        .shinyPalette = sFollowerPalShiny_Mudkip,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MARSHTOMP - 1] = {
        .species = SPECIES_MARSHTOMP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Marshtomp,
        .palette = sFollowerPal_Marshtomp,
        .shinyPalette = sFollowerPalShiny_Marshtomp,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SWAMPERT - 1] = {
        .species = SPECIES_SWAMPERT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Swampert,
        .palette = sFollowerPal_Swampert,
        .shinyPalette = sFollowerPalShiny_Swampert,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_POOCHYENA - 1] = {
        .species = SPECIES_POOCHYENA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Poochyena,
        .palette = sFollowerPal_Poochyena,
        .shinyPalette = sFollowerPalShiny_Poochyena,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MIGHTYENA - 1] = {
        .species = SPECIES_MIGHTYENA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mightyena,
        .palette = sFollowerPal_Mightyena,
        .shinyPalette = sFollowerPalShiny_Mightyena,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ZIGZAGOON - 1] = {
        .species = SPECIES_ZIGZAGOON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Zigzagoon,
        .palette = sFollowerPal_Zigzagoon,
        .shinyPalette = sFollowerPalShiny_Zigzagoon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LINOONE - 1] = {
        .species = SPECIES_LINOONE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Linoone,
        .palette = sFollowerPal_Linoone,
        .shinyPalette = sFollowerPalShiny_Linoone,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WURMPLE - 1] = {
        .species = SPECIES_WURMPLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wurmple,
        .palette = sFollowerPal_Wurmple,
        .shinyPalette = sFollowerPalShiny_Wurmple,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SILCOON - 1] = {
        .species = SPECIES_SILCOON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Silcoon,
        .palette = sFollowerPal_Silcoon,
        .shinyPalette = sFollowerPalShiny_Silcoon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BEAUTIFLY - 1] = {
        .species = SPECIES_BEAUTIFLY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Beautifly,
        .palette = sFollowerPal_Beautifly,
        .shinyPalette = sFollowerPalShiny_Beautifly,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CASCOON - 1] = {
        .species = SPECIES_CASCOON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cascoon,
        .palette = sFollowerPal_Cascoon,
        .shinyPalette = sFollowerPalShiny_Cascoon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DUSTOX - 1] = {
        .species = SPECIES_DUSTOX,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dustox,
        .palette = sFollowerPal_Dustox,
        .shinyPalette = sFollowerPalShiny_Dustox,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LOTAD - 1] = {
        .species = SPECIES_LOTAD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lotad,
        .palette = sFollowerPal_Lotad,
        .shinyPalette = sFollowerPalShiny_Lotad,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LOMBRE - 1] = {
        .species = SPECIES_LOMBRE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lombre,
        .palette = sFollowerPal_Lombre,
        .shinyPalette = sFollowerPalShiny_Lombre,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LUDICOLO - 1] = {
        .species = SPECIES_LUDICOLO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ludicolo,
        .palette = sFollowerPal_Ludicolo,
        .shinyPalette = sFollowerPalShiny_Ludicolo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEEDOT - 1] = {
        .species = SPECIES_SEEDOT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Seedot,
        .palette = sFollowerPal_Seedot,
        .shinyPalette = sFollowerPalShiny_Seedot,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NUZLEAF - 1] = {
        .species = SPECIES_NUZLEAF,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nuzleaf,
        .palette = sFollowerPal_Nuzleaf,
        .shinyPalette = sFollowerPalShiny_Nuzleaf,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHIFTRY - 1] = {
        .species = SPECIES_SHIFTRY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shiftry,
        .palette = sFollowerPal_Shiftry,
        .shinyPalette = sFollowerPalShiny_Shiftry,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TAILLOW - 1] = {
        .species = SPECIES_TAILLOW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Taillow,
        .palette = sFollowerPal_Taillow,
        .shinyPalette = sFollowerPalShiny_Taillow,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SWELLOW - 1] = {
        .species = SPECIES_SWELLOW,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Swellow,
        .palette = sFollowerPal_Swellow,
        .shinyPalette = sFollowerPalShiny_Swellow,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WINGULL - 1] = {
        .species = SPECIES_WINGULL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wingull,
        .palette = sFollowerPal_Wingull,
        .shinyPalette = sFollowerPalShiny_Wingull,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PELIPPER - 1] = {
        .species = SPECIES_PELIPPER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Pelipper,
        .palette = sFollowerPal_Pelipper,
        .shinyPalette = sFollowerPalShiny_Pelipper,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RALTS - 1] = {
        .species = SPECIES_RALTS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ralts,
        .palette = sFollowerPal_Ralts,
        .shinyPalette = sFollowerPalShiny_Ralts,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KIRLIA - 1] = {
        .species = SPECIES_KIRLIA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kirlia,
        .palette = sFollowerPal_Kirlia,
        .shinyPalette = sFollowerPalShiny_Kirlia,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GARDEVOIR - 1] = {
        .species = SPECIES_GARDEVOIR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gardevoir,
        .palette = sFollowerPal_Gardevoir,
        .shinyPalette = sFollowerPalShiny_Gardevoir,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SURSKIT - 1] = {
        .species = SPECIES_SURSKIT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Surskit,
        .palette = sFollowerPal_Surskit,
        .shinyPalette = sFollowerPalShiny_Surskit,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MASQUERAIN - 1] = {
        .species = SPECIES_MASQUERAIN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Masquerain,
        .palette = sFollowerPal_Masquerain,
        .shinyPalette = sFollowerPalShiny_Masquerain,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHROOMISH - 1] = {
        .species = SPECIES_SHROOMISH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shroomish,
        .palette = sFollowerPal_Shroomish,
        .shinyPalette = sFollowerPalShiny_Shroomish,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BRELOOM - 1] = {
        .species = SPECIES_BRELOOM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Breloom,
        .palette = sFollowerPal_Breloom,
        .shinyPalette = sFollowerPalShiny_Breloom,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLAKOTH - 1] = {
        .species = SPECIES_SLAKOTH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slakoth,
        .palette = sFollowerPal_Slakoth,
        .shinyPalette = sFollowerPalShiny_Slakoth,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VIGOROTH - 1] = {
        .species = SPECIES_VIGOROTH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Vigoroth,
        .palette = sFollowerPal_Vigoroth,
        .shinyPalette = sFollowerPalShiny_Vigoroth,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SLAKING - 1] = {
        .species = SPECIES_SLAKING,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Slaking,
        .palette = sFollowerPal_Slaking,
        .shinyPalette = sFollowerPalShiny_Slaking,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NINCADA - 1] = {
        .species = SPECIES_NINCADA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nincada,
        .palette = sFollowerPal_Nincada,
        .shinyPalette = sFollowerPalShiny_Nincada,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NINJASK - 1] = {
        .species = SPECIES_NINJASK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Ninjask,
        .palette = sFollowerPal_Ninjask,
        .shinyPalette = sFollowerPalShiny_Ninjask,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHEDINJA - 1] = {
        .species = SPECIES_SHEDINJA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shedinja,
        .palette = sFollowerPal_Shedinja,
        .shinyPalette = sFollowerPalShiny_Shedinja,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WHISMUR - 1] = {
        .species = SPECIES_WHISMUR,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Whismur,
        .palette = sFollowerPal_Whismur,
        .shinyPalette = sFollowerPalShiny_Whismur,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LOUDRED - 1] = {
        .species = SPECIES_LOUDRED,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Loudred,
        .palette = sFollowerPal_Loudred,
        .shinyPalette = sFollowerPalShiny_Loudred,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_EXPLOUD - 1] = {
        .species = SPECIES_EXPLOUD,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Exploud,
        .palette = sFollowerPal_Exploud,
        .shinyPalette = sFollowerPalShiny_Exploud,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAKUHITA - 1] = {
        .species = SPECIES_MAKUHITA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Makuhita,
        .palette = sFollowerPal_Makuhita,
        .shinyPalette = sFollowerPalShiny_Makuhita,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HARIYAMA - 1] = {
        .species = SPECIES_HARIYAMA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Hariyama,
        .palette = sFollowerPal_Hariyama,
        .shinyPalette = sFollowerPalShiny_Hariyama,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AZURILL - 1] = {
        .species = SPECIES_AZURILL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Azurill,
        .palette = sFollowerPal_Azurill,
        .shinyPalette = sFollowerPalShiny_Azurill,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NOSEPASS - 1] = {
        .species = SPECIES_NOSEPASS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Nosepass,
        .palette = sFollowerPal_Nosepass,
        .shinyPalette = sFollowerPalShiny_Nosepass,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SKITTY - 1] = {
        .species = SPECIES_SKITTY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Skitty,
        .palette = sFollowerPal_Skitty,
        .shinyPalette = sFollowerPalShiny_Skitty,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DELCATTY - 1] = {
        .species = SPECIES_DELCATTY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Delcatty,
        .palette = sFollowerPal_Delcatty,
        .shinyPalette = sFollowerPalShiny_Delcatty,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SABLEYE - 1] = {
        .species = SPECIES_SABLEYE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sableye,
        .palette = sFollowerPal_Sableye,
        .shinyPalette = sFollowerPalShiny_Sableye,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MAWILE - 1] = {
        .species = SPECIES_MAWILE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Mawile,
        .palette = sFollowerPal_Mawile,
        .shinyPalette = sFollowerPalShiny_Mawile,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARON - 1] = {
        .species = SPECIES_ARON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Aron,
        .palette = sFollowerPal_Aron,
        .shinyPalette = sFollowerPalShiny_Aron,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LAIRON - 1] = {
        .species = SPECIES_LAIRON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lairon,
        .palette = sFollowerPal_Lairon,
        .shinyPalette = sFollowerPalShiny_Lairon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_AGGRON - 1] = {
        .species = SPECIES_AGGRON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Aggron,
        .palette = sFollowerPal_Aggron,
        .shinyPalette = sFollowerPalShiny_Aggron,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEDITITE - 1] = {
        .species = SPECIES_MEDITITE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Meditite,
        .palette = sFollowerPal_Meditite,
        .shinyPalette = sFollowerPalShiny_Meditite,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MEDICHAM - 1] = {
        .species = SPECIES_MEDICHAM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Medicham,
        .palette = sFollowerPal_Medicham,
        .shinyPalette = sFollowerPalShiny_Medicham,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ELECTRIKE - 1] = {
        .species = SPECIES_ELECTRIKE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Electrike,
        .palette = sFollowerPal_Electrike,
        .shinyPalette = sFollowerPalShiny_Electrike,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MANECTRIC - 1] = {
        .species = SPECIES_MANECTRIC,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Manectric,
        .palette = sFollowerPal_Manectric,
        .shinyPalette = sFollowerPalShiny_Manectric,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_PLUSLE - 1] = {
        .species = SPECIES_PLUSLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Plusle,
        .palette = sFollowerPal_Plusle,
        .shinyPalette = sFollowerPalShiny_Plusle,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MINUN - 1] = {
        .species = SPECIES_MINUN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Minun,
        .palette = sFollowerPal_Minun,
        .shinyPalette = sFollowerPalShiny_Minun,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VOLBEAT - 1] = {
        .species = SPECIES_VOLBEAT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Volbeat,
        .palette = sFollowerPal_Volbeat,
        .shinyPalette = sFollowerPalShiny_Volbeat,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ILLUMISE - 1] = {
        .species = SPECIES_ILLUMISE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Illumise,
        .palette = sFollowerPal_Illumise,
        .shinyPalette = sFollowerPalShiny_Illumise,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ROSELIA - 1] = {
        .species = SPECIES_ROSELIA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Roselia,
        .palette = sFollowerPal_Roselia,
        .shinyPalette = sFollowerPalShiny_Roselia,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GULPIN - 1] = {
        .species = SPECIES_GULPIN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gulpin,
        .palette = sFollowerPal_Gulpin,
        .shinyPalette = sFollowerPalShiny_Gulpin,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SWALOT - 1] = {
        .species = SPECIES_SWALOT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Swalot,
        .palette = sFollowerPal_Swalot,
        .shinyPalette = sFollowerPalShiny_Swalot,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CARVANHA - 1] = {
        .species = SPECIES_CARVANHA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Carvanha,
        .palette = sFollowerPal_Carvanha,
        .shinyPalette = sFollowerPalShiny_Carvanha,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHARPEDO - 1] = {
        .species = SPECIES_SHARPEDO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sharpedo,
        .palette = sFollowerPal_Sharpedo,
        .shinyPalette = sFollowerPalShiny_Sharpedo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WAILMER - 1] = {
        .species = SPECIES_WAILMER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wailmer,
        .palette = sFollowerPal_Wailmer,
        .shinyPalette = sFollowerPalShiny_Wailmer,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WAILORD - 1] = {
        .species = SPECIES_WAILORD,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Wailord,
        .palette = sFollowerPal_Wailord,
        .shinyPalette = sFollowerPalShiny_Wailord,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_NUMEL - 1] = {
        .species = SPECIES_NUMEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Numel,
        .palette = sFollowerPal_Numel,
        .shinyPalette = sFollowerPalShiny_Numel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CAMERUPT - 1] = {
        .species = SPECIES_CAMERUPT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Camerupt,
        .palette = sFollowerPal_Camerupt,
        .shinyPalette = sFollowerPalShiny_Camerupt,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TORKOAL - 1] = {
        .species = SPECIES_TORKOAL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Torkoal,
        .palette = sFollowerPal_Torkoal,
        .shinyPalette = sFollowerPalShiny_Torkoal,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SPOINK - 1] = {
        .species = SPECIES_SPOINK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Spoink,
        .palette = sFollowerPal_Spoink,
        .shinyPalette = sFollowerPalShiny_Spoink,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GRUMPIG - 1] = {
        .species = SPECIES_GRUMPIG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Grumpig,
        .palette = sFollowerPal_Grumpig,
        .shinyPalette = sFollowerPalShiny_Grumpig,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SPINDA - 1] = {
        .species = SPECIES_SPINDA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Spinda,
        .palette = sFollowerPal_Spinda,
        .shinyPalette = sFollowerPalShiny_Spinda,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TRAPINCH - 1] = {
        .species = SPECIES_TRAPINCH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Trapinch,
        .palette = sFollowerPal_Trapinch,
        .shinyPalette = sFollowerPalShiny_Trapinch,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_VIBRAVA - 1] = {
        .species = SPECIES_VIBRAVA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Vibrava,
        .palette = sFollowerPal_Vibrava,
        .shinyPalette = sFollowerPalShiny_Vibrava,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FLYGON - 1] = {
        .species = SPECIES_FLYGON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Flygon,
        .palette = sFollowerPal_Flygon,
        .shinyPalette = sFollowerPalShiny_Flygon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CACNEA - 1] = {
        .species = SPECIES_CACNEA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cacnea,
        .palette = sFollowerPal_Cacnea,
        .shinyPalette = sFollowerPalShiny_Cacnea,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CACTURNE - 1] = {
        .species = SPECIES_CACTURNE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cacturne,
        .palette = sFollowerPal_Cacturne,
        .shinyPalette = sFollowerPalShiny_Cacturne,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SWABLU - 1] = {
        .species = SPECIES_SWABLU,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Swablu,
        .palette = sFollowerPal_Swablu,
        .shinyPalette = sFollowerPalShiny_Swablu,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ALTARIA - 1] = {
        .species = SPECIES_ALTARIA,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Altaria,
        .palette = sFollowerPal_Altaria,
        .shinyPalette = sFollowerPalShiny_Altaria,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ZANGOOSE - 1] = {
        .species = SPECIES_ZANGOOSE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Zangoose,
        .palette = sFollowerPal_Zangoose,
        .shinyPalette = sFollowerPalShiny_Zangoose,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEVIPER - 1] = {
        .species = SPECIES_SEVIPER,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Seviper,
        .palette = sFollowerPal_Seviper,
        .shinyPalette = sFollowerPalShiny_Seviper,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LUNATONE - 1] = {
        .species = SPECIES_LUNATONE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lunatone,
        .palette = sFollowerPal_Lunatone,
        .shinyPalette = sFollowerPalShiny_Lunatone,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SOLROCK - 1] = {
        .species = SPECIES_SOLROCK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Solrock,
        .palette = sFollowerPal_Solrock,
        .shinyPalette = sFollowerPalShiny_Solrock,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BARBOACH - 1] = {
        .species = SPECIES_BARBOACH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Barboach,
        .palette = sFollowerPal_Barboach,
        .shinyPalette = sFollowerPalShiny_Barboach,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WHISCASH - 1] = {
        .species = SPECIES_WHISCASH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Whiscash,
        .palette = sFollowerPal_Whiscash,
        .shinyPalette = sFollowerPalShiny_Whiscash,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CORPHISH - 1] = {
        .species = SPECIES_CORPHISH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Corphish,
        .palette = sFollowerPal_Corphish,
        .shinyPalette = sFollowerPalShiny_Corphish,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CRAWDAUNT - 1] = {
        .species = SPECIES_CRAWDAUNT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Crawdaunt,
        .palette = sFollowerPal_Crawdaunt,
        .shinyPalette = sFollowerPalShiny_Crawdaunt,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BALTOY - 1] = {
        .species = SPECIES_BALTOY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Baltoy,
        .palette = sFollowerPal_Baltoy,
        .shinyPalette = sFollowerPalShiny_Baltoy,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLAYDOL - 1] = {
        .species = SPECIES_CLAYDOL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Claydol,
        .palette = sFollowerPal_Claydol,
        .shinyPalette = sFollowerPalShiny_Claydol,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LILEEP - 1] = {
        .species = SPECIES_LILEEP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Lileep,
        .palette = sFollowerPal_Lileep,
        .shinyPalette = sFollowerPalShiny_Lileep,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CRADILY - 1] = {
        .species = SPECIES_CRADILY,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Cradily,
        .palette = sFollowerPal_Cradily,
        .shinyPalette = sFollowerPalShiny_Cradily,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ANORITH - 1] = {
        .species = SPECIES_ANORITH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Anorith,
        .palette = sFollowerPal_Anorith,
        .shinyPalette = sFollowerPalShiny_Anorith,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ARMALDO - 1] = {
        .species = SPECIES_ARMALDO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Armaldo,
        .palette = sFollowerPal_Armaldo,
        .shinyPalette = sFollowerPalShiny_Armaldo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_FEEBAS - 1] = {
        .species = SPECIES_FEEBAS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Feebas,
        .palette = sFollowerPal_Feebas,
        .shinyPalette = sFollowerPalShiny_Feebas,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_MILOTIC - 1] = {
        .species = SPECIES_MILOTIC,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Milotic,
        .palette = sFollowerPal_Milotic,
        .shinyPalette = sFollowerPalShiny_Milotic,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CASTFORM - 1] = {
        .species = SPECIES_CASTFORM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Castform,
        .palette = sFollowerPal_Castform,
        .shinyPalette = sFollowerPalShiny_Castform,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KECLEON - 1] = {
        .species = SPECIES_KECLEON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Kecleon,
        .palette = sFollowerPal_Kecleon,
        .shinyPalette = sFollowerPalShiny_Kecleon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHUPPET - 1] = {
        .species = SPECIES_SHUPPET,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shuppet,
        .palette = sFollowerPal_Shuppet,
        .shinyPalette = sFollowerPalShiny_Shuppet,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BANETTE - 1] = {
        .species = SPECIES_BANETTE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Banette,
        .palette = sFollowerPal_Banette,
        .shinyPalette = sFollowerPalShiny_Banette,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DUSKULL - 1] = {
        .species = SPECIES_DUSKULL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Duskull,
        .palette = sFollowerPal_Duskull,
        .shinyPalette = sFollowerPalShiny_Duskull,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DUSCLOPS - 1] = {
        .species = SPECIES_DUSCLOPS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Dusclops,
        .palette = sFollowerPal_Dusclops,
        .shinyPalette = sFollowerPalShiny_Dusclops,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_TROPIUS - 1] = {
        .species = SPECIES_TROPIUS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Tropius,
        .palette = sFollowerPal_Tropius,
        .shinyPalette = sFollowerPalShiny_Tropius,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CHIMECHO - 1] = {
        .species = SPECIES_CHIMECHO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Chimecho,
        .palette = sFollowerPal_Chimecho,
        .shinyPalette = sFollowerPalShiny_Chimecho,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_ABSOL - 1] = {
        .species = SPECIES_ABSOL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Absol,
        .palette = sFollowerPal_Absol,
        .shinyPalette = sFollowerPalShiny_Absol,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WYNAUT - 1] = {
        .species = SPECIES_WYNAUT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Wynaut,
        .palette = sFollowerPal_Wynaut,
        .shinyPalette = sFollowerPalShiny_Wynaut,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SNORUNT - 1] = {
        .species = SPECIES_SNORUNT,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Snorunt,
        .palette = sFollowerPal_Snorunt,
        .shinyPalette = sFollowerPalShiny_Snorunt,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GLALIE - 1] = {
        .species = SPECIES_GLALIE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Glalie,
        .palette = sFollowerPal_Glalie,
        .shinyPalette = sFollowerPalShiny_Glalie,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SPHEAL - 1] = {
        .species = SPECIES_SPHEAL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Spheal,
        .palette = sFollowerPal_Spheal,
        .shinyPalette = sFollowerPalShiny_Spheal,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SEALEO - 1] = {
        .species = SPECIES_SEALEO,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Sealeo,
        .palette = sFollowerPal_Sealeo,
        .shinyPalette = sFollowerPalShiny_Sealeo,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_WALREIN - 1] = {
        .species = SPECIES_WALREIN,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Walrein,
        .palette = sFollowerPal_Walrein,
        .shinyPalette = sFollowerPalShiny_Walrein,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_CLAMPERL - 1] = {
        .species = SPECIES_CLAMPERL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Clamperl,
        .palette = sFollowerPal_Clamperl,
        .shinyPalette = sFollowerPalShiny_Clamperl,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_HUNTAIL - 1] = {
        .species = SPECIES_HUNTAIL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Huntail,
        .palette = sFollowerPal_Huntail,
        .shinyPalette = sFollowerPalShiny_Huntail,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GOREBYSS - 1] = {
        .species = SPECIES_GOREBYSS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gorebyss,
        .palette = sFollowerPal_Gorebyss,
        .shinyPalette = sFollowerPalShiny_Gorebyss,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RELICANTH - 1] = {
        .species = SPECIES_RELICANTH,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Relicanth,
        .palette = sFollowerPal_Relicanth,
        .shinyPalette = sFollowerPalShiny_Relicanth,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LUVDISC - 1] = {
        .species = SPECIES_LUVDISC,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Luvdisc,
        .palette = sFollowerPal_Luvdisc,
        .shinyPalette = sFollowerPalShiny_Luvdisc,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BAGON - 1] = {
        .species = SPECIES_BAGON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Bagon,
        .palette = sFollowerPal_Bagon,
        .shinyPalette = sFollowerPalShiny_Bagon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SHELGON - 1] = {
        .species = SPECIES_SHELGON,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Shelgon,
        .palette = sFollowerPal_Shelgon,
        .shinyPalette = sFollowerPalShiny_Shelgon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_SALAMENCE - 1] = {
        .species = SPECIES_SALAMENCE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Salamence,
        .palette = sFollowerPal_Salamence,
        .shinyPalette = sFollowerPalShiny_Salamence,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_BELDUM - 1] = {
        .species = SPECIES_BELDUM,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Beldum,
        .palette = sFollowerPal_Beldum,
        .shinyPalette = sFollowerPalShiny_Beldum,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_METANG - 1] = {
        .species = SPECIES_METANG,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Metang,
        .palette = sFollowerPal_Metang,
        .shinyPalette = sFollowerPalShiny_Metang,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_METAGROSS - 1] = {
        .species = SPECIES_METAGROSS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Metagross,
        .palette = sFollowerPal_Metagross,
        .shinyPalette = sFollowerPalShiny_Metagross,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_REGIROCK - 1] = {
        .species = SPECIES_REGIROCK,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Regirock,
        .palette = sFollowerPal_Regirock,
        .shinyPalette = sFollowerPalShiny_Regirock,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_REGICE - 1] = {
        .species = SPECIES_REGICE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Regice,
        .palette = sFollowerPal_Regice,
        .shinyPalette = sFollowerPalShiny_Regice,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_REGISTEEL - 1] = {
        .species = SPECIES_REGISTEEL,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Registeel,
        .palette = sFollowerPal_Registeel,
        .shinyPalette = sFollowerPalShiny_Registeel,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LATIAS - 1] = {
        .species = SPECIES_LATIAS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Latias,
        .palette = sFollowerPal_Latias,
        .shinyPalette = sFollowerPalShiny_Latias,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_LATIOS - 1] = {
        .species = SPECIES_LATIOS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Latios,
        .palette = sFollowerPal_Latios,
        .shinyPalette = sFollowerPalShiny_Latios,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_KYOGRE - 1] = {
        .species = SPECIES_KYOGRE,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Kyogre,
        .palette = sFollowerPal_Kyogre,
        .shinyPalette = sFollowerPalShiny_Kyogre,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GROUDON - 1] = {
        .species = SPECIES_GROUDON,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Groudon,
        .palette = sFollowerPal_Groudon,
        .shinyPalette = sFollowerPalShiny_Groudon,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_RAYQUAZA - 1] = {
        .species = SPECIES_RAYQUAZA,
        .large = TRUE,
        .formCount = 0,
        .images = sFollowerPicTable_Rayquaza,
        .palette = sFollowerPal_Rayquaza,
        .shinyPalette = sFollowerPalShiny_Rayquaza,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_JIRACHI - 1] = {
        .species = SPECIES_JIRACHI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Jirachi,
        .palette = sFollowerPal_Jirachi,
        .shinyPalette = sFollowerPalShiny_Jirachi,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DEOXYS - 1] = {
        .species = SPECIES_DEOXYS,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Deoxys,
        .palette = sFollowerPal_Deoxys,
        .shinyPalette = sFollowerPalShiny_Deoxys,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GIBLE - 1] = {
        .species = SPECIES_GIBLE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gible,
        .palette = sFollowerPal_Gible,
        .shinyPalette = sFollowerPalShiny_Gible,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GABITE - 1] = {
        .species = SPECIES_GABITE,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Gabite,
        .palette = sFollowerPal_Gabite,
        .shinyPalette = sFollowerPalShiny_Gabite,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_GARCHOMP - 1] = {
        .species = SPECIES_GARCHOMP,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Garchomp,
        .palette = sFollowerPal_Garchomp,
        .shinyPalette = sFollowerPalShiny_Garchomp,
        .female = NULL,
        .forms = NULL,
    },
    [NATIONAL_DEX_DARKRAI - 1] = {
        .species = SPECIES_DARKRAI,
        .large = FALSE,
        .formCount = 0,
        .images = sFollowerPicTable_Darkrai,
        .palette = sFollowerPal_Darkrai,
        .shinyPalette = sFollowerPalShiny_Darkrai,
        .female = NULL,
        .forms = NULL,
    },
};

// Imagens dos gráficos dinâmicos (32x32 e 64x64) antes de a espécie ser resolvida em tempo de execução.
#define FOLLOWER_DEFAULT_IMAGES sFollowerPicTable_Bulbasaur
#define FOLLOWER_DEFAULT_LARGE_IMAGES sFollowerPicTable_Steelix
