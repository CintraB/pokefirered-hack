const struct Decoration gDecorations[] = {
    {
        DECOR_NONE,
        _("Mesa Pequena"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_DESK,
        0,
        DecorDesc_SMALL_DESK,
        DecorGfx_SMALL_DESK
    }, {
        DECOR_SMALL_DESK,
        _("Mesa Pequena"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_DESK,
        3000,
        DecorDesc_SMALL_DESK,
        DecorGfx_SMALL_DESK
    }, {
        DECOR_POKEMON_DESK,
        _("Mesa Pokémon"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_DESK,
        3000,
        DecorDesc_POKEMON_DESK,
        DecorGfx_POKEMON_DESK
    }, {
        DECOR_HEAVY_DESK,
        _("Mesa Pesada"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x2,
        DECORCAT_DESK,
        6000,
        DecorDesc_HEAVY_DESK,
        DecorGfx_HEAVY_DESK
    }, {
        DECOR_RAGGED_DESK,
        _("Mesa Rústica"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x2,
        DECORCAT_DESK,
        6000,
        DecorDesc_RAGGED_DESK,
        DecorGfx_RAGGED_DESK
    }, {
        DECOR_COMFORT_DESK,
        _("Mesa Conforto"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x2,
        DECORCAT_DESK,
        6000,
        DecorDesc_COMFORT_DESK,
        DecorGfx_COMFORT_DESK
    }, {
        DECOR_PRETTY_DESK,
        _("Mesa Bonita"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_DESK,
        9000,
        DecorDesc_PRETTY_DESK,
        DecorGfx_PRETTY_DESK
    }, {
        DECOR_BRICK_DESK,
        _("Mesa de Tijolos"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_DESK,
        9000,
        DecorDesc_BRICK_DESK,
        DecorGfx_BRICK_DESK
    }, {
        DECOR_CAMP_DESK,
        _("Mesa de Camping"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_DESK,
        9000,
        DecorDesc_CAMP_DESK,
        DecorGfx_CAMP_DESK
    }, {
        DECOR_HARD_DESK,
        _("Mesa Dura"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_DESK,
        9000,
        DecorDesc_HARD_DESK,
        DecorGfx_HARD_DESK
    }, {
        DECOR_SMALL_CHAIR,
        _("Cadeira Pequena"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_SMALL_CHAIR,
        DecorGfx_SMALL_CHAIR
    }, {
        DECOR_POKEMON_CHAIR,
        _("Cadeira Pokémon"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_POKEMON_CHAIR,
        DecorGfx_POKEMON_CHAIR
    }, {
        DECOR_HEAVY_CHAIR,
        _("Cadeira Pesada"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_HEAVY_CHAIR,
        DecorGfx_HEAVY_CHAIR
    }, {
        DECOR_PRETTY_CHAIR,
        _("Cadeira Bonita"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_PRETTY_CHAIR,
        DecorGfx_PRETTY_CHAIR
    }, {
        DECOR_COMFORT_CHAIR,
        _("Cad. Conforto"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_COMFORT_CHAIR,
        DecorGfx_COMFORT_CHAIR
    }, {
        DECOR_RAGGED_CHAIR,
        _("Cadeira Rústica"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_RAGGED_CHAIR,
        DecorGfx_RAGGED_CHAIR
    }, {
        DECOR_BRICK_CHAIR,
        _("Cad. de Tijolos"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_BRICK_CHAIR,
        DecorGfx_BRICK_CHAIR
    }, {
        DECOR_CAMP_CHAIR,
        _("Cad. de Camping"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_CAMP_CHAIR,
        DecorGfx_CAMP_CHAIR
    }, {
        DECOR_HARD_CHAIR,
        _("Cadeira Dura"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_CHAIR,
        2000,
        DecorDesc_HARD_CHAIR,
        DecorGfx_HARD_CHAIR
    }, {
        DECOR_RED_PLANT,
        _("Planta Vermelha"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_PLANT,
        3000,
        DecorDesc_RED_PLANT,
        DecorGfx_RED_PLANT
    }, {
        DECOR_TROPICAL_PLANT,
        _("Planta Tropical"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_PLANT,
        3000,
        DecorDesc_TROPICAL_PLANT,
        DecorGfx_TROPICAL_PLANT
    }, {
        DECOR_PRETTY_FLOWERS,
        _("Flores Bonitas"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_PLANT,
        3000,
        DecorDesc_PRETTY_FLOWERS,
        DecorGfx_PRETTY_FLOWERS
    }, {
        DECOR_COLORFUL_PLANT,
        _("Planta Colorida"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_2x2,
        DECORCAT_PLANT,
        5000,
        DecorDesc_COLORFUL_PLANT,
        DecorGfx_COLORFUL_PLANT
    }, {
        DECOR_BIG_PLANT,
        _("Planta Grande"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_2x2,
        DECORCAT_PLANT,
        5000,
        DecorDesc_BIG_PLANT,
        DecorGfx_BIG_PLANT
    }, {
        DECOR_GORGEOUS_PLANT,
        _("Planta Luxuosa"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_2x2,
        DECORCAT_PLANT,
        5000,
        DecorDesc_GORGEOUS_PLANT,
        DecorGfx_GORGEOUS_PLANT
    }, {
        DECOR_RED_BRICK,
        _("Tijolo Vermelho"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_RED_BRICK,
        DecorGfx_RED_BRICK
    }, {
        DECOR_YELLOW_BRICK,
        _("Tijolo Amarelo"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_YELLOW_BRICK,
        DecorGfx_YELLOW_BRICK
    }, {
        DECOR_BLUE_BRICK,
        _("Tijolo Azul"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_BLUE_BRICK,
        DecorGfx_BLUE_BRICK
    }, {
        DECOR_RED_BALLOON,
        _("Balão Vermelho"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_RED_BALLOON,
        DecorGfx_RED_BALLOON
    }, {
        DECOR_BLUE_BALLOON,
        _("Balão Azul"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_BLUE_BALLOON,
        DecorGfx_BLUE_BALLOON
    }, {
        DECOR_YELLOW_BALLOON,
        _("Balão Amarelo"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_YELLOW_BALLOON,
        DecorGfx_YELLOW_BALLOON
    }, {
        DECOR_RED_TENT,
        _("Tenda Vermelha"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_ORNAMENT,
        10000,
        DecorDesc_RED_TENT,
        DecorGfx_RED_TENT
    }, {
        DECOR_BLUE_TENT,
        _("Tenda Azul"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_ORNAMENT,
        10000,
        DecorDesc_BLUE_TENT,
        DecorGfx_BLUE_TENT
    }, {
        DECOR_SOLID_BOARD,
        _("Tábua Sólida"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        3000,
        DecorDesc_SOLID_BOARD,
        DecorGfx_SOLID_BOARD
    }, {
        DECOR_SLIDE,
        _("Escorregador"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_2x4,
        DECORCAT_ORNAMENT,
        8000,
        DecorDesc_SLIDE,
        DecorGfx_SLIDE
    }, {
        DECOR_FENCE_LENGTH,
        _("Cerca Comprida"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_FENCE_LENGTH,
        DecorGfx_FENCE_LENGTH
    }, {
        DECOR_FENCE_WIDTH,
        _("Cerca Larga"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        500,
        DecorDesc_FENCE_WIDTH,
        DecorGfx_FENCE_WIDTH
    }, {
        DECOR_TIRE,
        _("Pneu"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_2x2,
        DECORCAT_ORNAMENT,
        800,
        DecorDesc_TIRE,
        DecorGfx_TIRE
    }, {
        DECOR_STAND,
        _("Pedestal"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_4x2,
        DECORCAT_ORNAMENT,
        7000,
        DecorDesc_STAND,
        DecorGfx_STAND
    }, {
        DECOR_MUD_BALL,
        _("Bola de Lama"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        200,
        DecorDesc_MUD_BALL,
        DecorGfx_MUD_BALL
    }, {
        DECOR_BREAKABLE_DOOR,
        _("Porta Quebrável"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        3000,
        DecorDesc_BREAKABLE_DOOR,
        DecorGfx_BREAKABLE_DOOR
    }, {
        DECOR_SAND_ORNAMENT,
        _("Adorno de Areia"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        3000,
        DecorDesc_SAND_ORNAMENT,
        DecorGfx_SAND_ORNAMENT
    }, {
        DECOR_SILVER_SHIELD,
        _("Escudo de Prata"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        0,
        DecorDesc_SILVER_SHIELD,
        DecorGfx_SILVER_SHIELD
    }, {
        DECOR_GOLD_SHIELD,
        _("Escudo de Ouro"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        0,
        DecorDesc_GOLD_SHIELD,
        DecorGfx_GOLD_SHIELD
    }, {
        DECOR_GLASS_ORNAMENT,
        _("Adorno de Vidro"),
        DECORPERM_BEHIND_FLOOR,
        DECORSHAPE_1x2,
        DECORCAT_ORNAMENT,
        0,
        DecorDesc_GLASS_ORNAMENT,
        DecorGfx_GLASS_ORNAMENT
    }, {
        DECOR_TV,
        _("TV"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        3000,
        DecorDesc_TV,
        DecorGfx_TV
    }, {
        DECOR_ROUND_TV,
        _("TV Redonda"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        4000,
        DecorDesc_ROUND_TV,
        DecorGfx_ROUND_TV
    }, {
        DECOR_CUTE_TV,
        _("TV Fofa"),
        DECORPERM_SOLID_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_ORNAMENT,
        4000,
        DecorDesc_CUTE_TV,
        DecorGfx_CUTE_TV
    }, {
        DECOR_GLITTER_MAT,
        _("Tapete Brilho"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        2000,
        DecorDesc_GLITTER_MAT,
        DecorGfx_GLITTER_MAT
    }, {
        DECOR_JUMP_MAT,
        _("Tapete Saltador"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        2000,
        DecorDesc_JUMP_MAT,
        DecorGfx_JUMP_MAT
    }, {
        DECOR_SPIN_MAT,
        _("Tapete Giro"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        2000,
        DecorDesc_SPIN_MAT,
        DecorGfx_SPIN_MAT
    }, {
        DECOR_C_LOW_NOTE_MAT,
        _("Tapete Dó Baixo"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_C_LOW_NOTE_MAT,
        DecorGfx_C_LOW_NOTE_MAT
    }, {
        DECOR_D_NOTE_MAT,
        _("Tapete Ré"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_D_NOTE_MAT,
        DecorGfx_D_NOTE_MAT
    }, {
        DECOR_E_NOTE_MAT,
        _("Tapete Mi"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_E_NOTE_MAT,
        DecorGfx_E_NOTE_MAT
    }, {
        DECOR_F_NOTE_MAT,
        _("Tapete Fá"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_F_NOTE_MAT,
        DecorGfx_F_NOTE_MAT
    }, {
        DECOR_G_NOTE_MAT,
        _("Tapete Sol"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_G_NOTE_MAT,
        DecorGfx_G_NOTE_MAT
    }, {
        DECOR_A_NOTE_MAT,
        _("Tapete Lá"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_A_NOTE_MAT,
        DecorGfx_A_NOTE_MAT
    }, {
        DECOR_B_NOTE_MAT,
        _("Tapete Si"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_B_NOTE_MAT,
        DecorGfx_B_NOTE_MAT
    }, {
        DECOR_C_HIGH_NOTE_MAT,
        _("Tapete Dó Alto"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_1x1,
        DECORCAT_MAT,
        500,
        DecorDesc_C_HIGH_NOTE_MAT,
        DecorGfx_C_HIGH_NOTE_MAT
    }, {
        DECOR_SURF_MAT,
        _("Tapete Surfar"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_SURF_MAT,
        DecorGfx_SURF_MAT
    }, {
        DECOR_THUNDER_MAT,
        _("Tapete Trovão"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_THUNDER_MAT,
        DecorGfx_THUNDER_MAT
    }, {
        DECOR_FIRE_BLAST_MAT,
        _("Tapete Rajada"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_FIRE_BLAST_MAT,
        DecorGfx_FIRE_BLAST_MAT
    }, {
        DECOR_POWDER_SNOW_MAT,
        _("Tapete Neve"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_POWDER_SNOW_MAT,
        DecorGfx_POWDER_SNOW_MAT
    }, {
        DECOR_ATTRACT_MAT,
        _("Tapete Atração"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_ATTRACT_MAT,
        DecorGfx_ATTRACT_MAT
    }, {
        DECOR_FISSURE_MAT,
        _("Tapete Fissura"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_FISSURE_MAT,
        DecorGfx_FISSURE_MAT
    }, {
        DECOR_SPIKES_MAT,
        _("Tapete Espinhos"),
        DECORPERM_PASS_FLOOR,
        DECORSHAPE_3x3,
        DECORCAT_MAT,
        4000,
        DecorDesc_SPIKES_MAT,
        DecorGfx_SPIKES_MAT
    }, {
        DECOR_BALL_POSTER,
        _("Pôster de Bolas"),
        DECORPERM_NA_WALL,
        DECORSHAPE_1x1,
        DECORCAT_POSTER,
        1000,
        DecorDesc_BALL_POSTER,
        DecorGfx_BALL_POSTER
    }, {
        DECOR_GREEN_POSTER,
        _("Pôster Verde"),
        DECORPERM_NA_WALL,
        DECORSHAPE_1x1,
        DECORCAT_POSTER,
        1000,
        DecorDesc_GREEN_POSTER,
        DecorGfx_GREEN_POSTER
    }, {
        DECOR_RED_POSTER,
        _("Pôster Vermelho"),
        DECORPERM_NA_WALL,
        DECORSHAPE_1x1,
        DECORCAT_POSTER,
        1000,
        DecorDesc_RED_POSTER,
        DecorGfx_RED_POSTER
    }, {
        DECOR_BLUE_POSTER,
        _("Pôster Azul"),
        DECORPERM_NA_WALL,
        DECORSHAPE_1x1,
        DECORCAT_POSTER,
        1000,
        DecorDesc_BLUE_POSTER,
        DecorGfx_BLUE_POSTER
    }, {
        DECOR_CUTE_POSTER,
        _("Pôster Fofo"),
        DECORPERM_NA_WALL,
        DECORSHAPE_1x1,
        DECORCAT_POSTER,
        1000,
        DecorDesc_CUTE_POSTER,
        DecorGfx_CUTE_POSTER
    }, {
        DECOR_PIKA_POSTER,
        _("Pôster Pika"),
        DECORPERM_NA_WALL,
        DECORSHAPE_2x1,
        DECORCAT_POSTER,
        1500,
        DecorDesc_PIKA_POSTER,
        DecorGfx_PIKA_POSTER
    }, {
        DECOR_LONG_POSTER,
        _("Pôster Longo"),
        DECORPERM_NA_WALL,
        DECORSHAPE_2x1,
        DECORCAT_POSTER,
        1500,
        DecorDesc_LONG_POSTER,
        DecorGfx_LONG_POSTER
    }, {
        DECOR_SEA_POSTER,
        _("Pôster do Mar"),
        DECORPERM_NA_WALL,
        DECORSHAPE_2x1,
        DECORCAT_POSTER,
        1500,
        DecorDesc_SEA_POSTER,
        DecorGfx_SEA_POSTER
    }, {
        DECOR_SKY_POSTER,
        _("Pôster do Céu"),
        DECORPERM_NA_WALL,
        DECORSHAPE_2x1,
        DECORCAT_POSTER,
        1500,
        DecorDesc_SKY_POSTER,
        DecorGfx_SKY_POSTER
    }, {
        DECOR_KISS_POSTER,
        _("Pôster do Beijo"),
        DECORPERM_NA_WALL,
        DECORSHAPE_2x1,
        DECORCAT_POSTER,
        1500,
        DecorDesc_KISS_POSTER,
        DecorGfx_KISS_POSTER
    }, {
        DECOR_PICHU_DOLL,
        _("Boneco Pichu"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_PICHU_DOLL,
        DecorGfx_PICHU_DOLL
    }, {
        DECOR_PIKACHU_DOLL,
        _("Boneco Pikachu"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_PIKACHU_DOLL,
        DecorGfx_PIKACHU_DOLL
    }, {
        DECOR_MARILL_DOLL,
        _("Boneco Marill"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_MARILL_DOLL,
        DecorGfx_MARILL_DOLL
    }, {
        DECOR_TOGEPI_DOLL,
        _("Boneco Togepi"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_TOGEPI_DOLL,
        DecorGfx_TOGEPI_DOLL
    }, {
        DECOR_CYNDAQUIL_DOLL,
        _("Bon. Cyndaquil"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_CYNDAQUIL_DOLL,
        DecorGfx_CYNDAQUIL_DOLL
    }, {
        DECOR_CHIKORITA_DOLL,
        _("Bon. Chikorita"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_CHIKORITA_DOLL,
        DecorGfx_CHIKORITA_DOLL
    }, {
        DECOR_TOTODILE_DOLL,
        _("Boneco Totodile"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_TOTODILE_DOLL,
        DecorGfx_TOTODILE_DOLL
    }, {
        DECOR_JIGGLYPUFF_DOLL,
        _("Bon. Jigglypuff"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_JIGGLYPUFF_DOLL,
        DecorGfx_JIGGLYPUFF_DOLL
    }, {
        DECOR_MEOWTH_DOLL,
        _("Boneco Meowth"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_MEOWTH_DOLL,
        DecorGfx_MEOWTH_DOLL
    }, {
        DECOR_CLEFAIRY_DOLL,
        _("Boneco Clefairy"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_CLEFAIRY_DOLL,
        DecorGfx_CLEFAIRY_DOLL
    }, {
        DECOR_DITTO_DOLL,
        _("Boneco Ditto"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_DITTO_DOLL,
        DecorGfx_DITTO_DOLL
    }, {
        DECOR_SMOOCHUM_DOLL,
        _("Boneco Smoochum"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_SMOOCHUM_DOLL,
        DecorGfx_SMOOCHUM_DOLL
    }, {
        DECOR_TREECKO_DOLL,
        _("Boneco Treecko"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_TREECKO_DOLL,
        DecorGfx_TREECKO_DOLL
    }, {
        DECOR_TORCHIC_DOLL,
        _("Boneco Torchic"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_TORCHIC_DOLL,
        DecorGfx_TORCHIC_DOLL
    }, {
        DECOR_MUDKIP_DOLL,
        _("Boneco Mudkip"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_MUDKIP_DOLL,
        DecorGfx_MUDKIP_DOLL
    }, {
        DECOR_DUSKULL_DOLL,
        _("Boneco Duskull"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_DUSKULL_DOLL,
        DecorGfx_DUSKULL_DOLL
    }, {
        DECOR_WYNAUT_DOLL,
        _("Boneco Wynaut"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_WYNAUT_DOLL,
        DecorGfx_WYNAUT_DOLL
    }, {
        DECOR_BALTOY_DOLL,
        _("Boneco Baltoy"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_BALTOY_DOLL,
        DecorGfx_BALTOY_DOLL
    }, {
        DECOR_KECLEON_DOLL,
        _("Boneco Kecleon"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_KECLEON_DOLL,
        DecorGfx_KECLEON_DOLL
    }, {
        DECOR_AZURILL_DOLL,
        _("Boneco Azurill"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_AZURILL_DOLL,
        DecorGfx_AZURILL_DOLL
    }, {
        DECOR_SKITTY_DOLL,
        _("Boneco Skitty"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_SKITTY_DOLL,
        DecorGfx_SKITTY_DOLL
    }, {
        DECOR_SWABLU_DOLL,
        _("Boneco Swablu"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_SWABLU_DOLL,
        DecorGfx_SWABLU_DOLL
    }, {
        DECOR_GULPIN_DOLL,
        _("Boneco Gulpin"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_GULPIN_DOLL,
        DecorGfx_GULPIN_DOLL
    }, {
        DECOR_LOTAD_DOLL,
        _("Boneco Lotad"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_LOTAD_DOLL,
        DecorGfx_LOTAD_DOLL
    }, {
        DECOR_SEEDOT_DOLL,
        _("Boneco Seedot"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_DOLL,
        3000,
        DecorDesc_SEEDOT_DOLL,
        DecorGfx_SEEDOT_DOLL
    }, {
        DECOR_PIKA_CUSHION,
        _("Almof. Pika"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_PIKA_CUSHION,
        DecorGfx_PIKA_CUSHION
    }, {
        DECOR_ROUND_CUSHION,
        _("Almof. Redonda"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_ROUND_CUSHION,
        DecorGfx_ROUND_CUSHION
    }, {
        DECOR_KISS_CUSHION,
        _("Almof. Beijo"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_KISS_CUSHION,
        DecorGfx_KISS_CUSHION
    }, {
        DECOR_ZIGZAG_CUSHION,
        _("Almof. Zigzag"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_ZIGZAG_CUSHION,
        DecorGfx_ZIGZAG_CUSHION
    }, {
        DECOR_SPIN_CUSHION,
        _("Almof. Spinda"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_SPIN_CUSHION,
        DecorGfx_SPIN_CUSHION
    }, {
        DECOR_DIAMOND_CUSHION,
        _("Almof. Diamante"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_DIAMOND_CUSHION,
        DecorGfx_DIAMOND_CUSHION
    }, {
        DECOR_BALL_CUSHION,
        _("Almof. de Bola"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_BALL_CUSHION,
        DecorGfx_BALL_CUSHION
    }, {
        DECOR_GRASS_CUSHION,
        _("Almof. de Grama"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_GRASS_CUSHION,
        DecorGfx_GRASS_CUSHION
    }, {
        DECOR_FIRE_CUSHION,
        _("Almof. de Fogo"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_FIRE_CUSHION,
        DecorGfx_FIRE_CUSHION
    }, {
        DECOR_WATER_CUSHION,
        _("Almof. de Água"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x1,
        DECORCAT_CUSHION,
        2000,
        DecorDesc_WATER_CUSHION,
        DecorGfx_WATER_CUSHION
    }, {
        DECOR_SNORLAX_DOLL,
        _("Boneco Snorlax"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_SNORLAX_DOLL,
        DecorGfx_SNORLAX_DOLL
    }, {
        DECOR_RHYDON_DOLL,
        _("Boneco Rhydon"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_RHYDON_DOLL,
        DecorGfx_RHYDON_DOLL
    }, {
        DECOR_LAPRAS_DOLL,
        _("Boneco Lapras"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_LAPRAS_DOLL,
        DecorGfx_LAPRAS_DOLL
    }, {
        DECOR_VENUSAUR_DOLL,
        _("Boneco Venusaur"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_VENUSAUR_DOLL,
        DecorGfx_VENUSAUR_DOLL
    }, {
        DECOR_CHARIZARD_DOLL,
        _("Bon. Charizard"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_CHARIZARD_DOLL,
        DecorGfx_CHARIZARD_DOLL
    }, {
        DECOR_BLASTOISE_DOLL,
        _("Bon. Blastoise"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_BLASTOISE_DOLL,
        DecorGfx_BLASTOISE_DOLL
    }, {
        DECOR_WAILMER_DOLL,
        _("Boneco Wailmer"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_WAILMER_DOLL,
        DecorGfx_WAILMER_DOLL
    }, {
        DECOR_REGIROCK_DOLL,
        _("Boneco Regirock"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_REGIROCK_DOLL,
        DecorGfx_REGIROCK_DOLL
    }, {
        DECOR_REGICE_DOLL,
        _("Boneco Regice"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_REGICE_DOLL,
        DecorGfx_REGICE_DOLL
    }, {
        DECOR_REGISTEEL_DOLL,
        _("Bon. Registeel"),
        DECORPERM_SPRITE,
        DECORSHAPE_1x2,
        DECORCAT_DOLL,
        10000,
        DecorDesc_REGISTEEL_DOLL,
        DecorGfx_REGISTEEL_DOLL}
};
