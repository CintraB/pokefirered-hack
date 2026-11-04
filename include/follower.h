#ifndef GUARD_FOLLOWER_H
#define GUARD_FOLLOWER_H

#include "global.h"
#include "sprite.h"
#include "constants/event_object_movement.h"
#include "constants/event_objects.h"

// Pokémon seguidor (POK-48): o 1º da equipe anda atrás do jogador no campo (src/follower.c).
//
// Um único graphicsId (OBJ_EVENT_GFX_FOLLOWER) serve a todas as espécies: as imagens e a paleta são
// escolhidas em tempo de execução por gFollowerSpecies (src/data/object_events/follower_species.h, gerado por
// tools/seguidores/converter.py a partir do pacote HGSS do Veekun).
//
// Folha de cada espécie: 8 quadros 32x32, ou 64x64 nos 7 grandes (sul, norte, oeste, leste; 2 por direção; o leste
// tem desenho próprio). A paleta shiny usa os mesmos índices da normal.
struct FollowerSpecies
{
    u16 species;
    bool8 large;                               // 64x64 (POK-53: ainda não seguem; a Task 3 liga o gráfico 64x64)
    u8 formCount;                              // Unown: 28 (forms[letra de GetUnownLetterByPersonality]); demais: 0
    const struct SpriteFrameImage *images;
    const u16 *palette;
    const u16 *shinyPalette;
    const struct FollowerSpecies *female;      // NULL = usa a padrão
    const struct FollowerSpecies *forms;       // formCount entradas (species = SPECIES_UNOWN, large igual)
};

// gFollowerSpecies[dex nacional - 1]
#define FOLLOWER_SPECIES_COUNT 386

// localId do objeto do seguidor: fora dos templates dos mapas (localId = índice + 1, no máximo
// OBJECT_EVENT_TEMPLATES_COUNT = 64) e abaixo de LOCALID_PLAYER (0xFF)
#define OBJ_EVENT_ID_FOLLOWER 0xFE

// Animação parada: os 2 quadros da direção alternam a cada FOLLOWER_IDLE_FRAMES quadros (o "respirar" do HGSS)
#define FOLLOWER_IDLE_FRAMES 20

// Animações paradas em sAnimTable_Follower, depois das 20 padrão (sul, norte, oeste, leste)
#define FOLLOWER_ANIM_IDLE_SOUTH (ANIM_STD_COUNT + 0)
#define FOLLOWER_ANIM_IDLE_NORTH (ANIM_STD_COUNT + 1)
#define FOLLOWER_ANIM_IDLE_WEST  (ANIM_STD_COUNT + 2)
#define FOLLOWER_ANIM_IDLE_EAST  (ANIM_STD_COUNT + 3)

// Corrida (o seguidor não tem quadros de corrida): os 2 quadros de andar, FOLLOWER_RUN_TICKS cada. O último quadro do
// passo não avança a animação (UpdateMovementNormal pausa antes do AnimateSprites), então num passo de 5 quadros
// (corrida por input) a troca só acontece se cada quadro durar no máximo 3: assim cada passo mostra os 2 e o seguinte
// começa no outro (a perna alterna de um tile para o outro).
#define FOLLOWER_ANIM_RUN_SOUTH  (ANIM_STD_COUNT + 4)
#define FOLLOWER_ANIM_RUN_NORTH  (ANIM_STD_COUNT + 5)
#define FOLLOWER_ANIM_RUN_WEST   (ANIM_STD_COUNT + 6)
#define FOLLOWER_ANIM_RUN_EAST   (ANIM_STD_COUNT + 7)
#define FOLLOWER_RUN_TICKS 3

extern const struct FollowerSpecies gFollowerSpecies[FOLLOWER_SPECIES_COUNT];

struct ObjectEvent;

// Entrada base da espécie (busca O(1) pela Pokédex nacional). NULL se a espécie não segue o jogador: SPECIES_NONE,
// ovo, fora de 1..386, sem entrada na tabela ou (por enquanto) grande.
const struct FollowerSpecies *Follower_GetSpeciesInfo(u16 species);

// Opção "Seguidor: Sim/Não" do menu de Opções (SaveBlock2.optionsFollowerOff, 0 = Sim)
bool8 Follower_IsEnabled(void);

// Opção Sim, 1º da equipe não-ovo com PS > 0 e espécie na tabela, a pé (sem bicicleta/surf), fora do replay do
// Quest Log e de link, mapa sem objeto que use o slot de paleta do seguidor e com objeto livre para ele.
bool8 Follower_ShouldExist(void);

// Cria (ou recria) o seguidor atrás do jogador se Follower_ShouldExist(); tile de trás ocupado ou bloqueado = no
// tile do jogador, escondido até o 1º passo.
void Follower_Spawn(void);
void Follower_Remove(void);
// Compara espécie/shiny/estado com o objeto atual: cria, apaga ou recria (no mesmo tile) se mudou.
void Follower_Refresh(void);

// Índice em gObjectEvents (OBJECT_EVENTS_COUNT se não existe)
u8 Follower_GetObjectEventId(void);
bool8 Follower_IsFollowerObject(const struct ObjectEvent *objectEvent);

// Ganchos do motor de objetos (event_object_movement.c): o sprite do seguidor acabou de ser criado (spawn ou volta ao
// campo) e precisa das imagens, da paleta e do callback da espécie; e a paleta recarregada do ROM (tom dia/noite).
void Follower_OnSpriteCreated(struct ObjectEvent *objectEvent, struct Sprite *sprite);
void Follower_ReloadPalette(void);

// Gancho de ObjectEventSetHeldMovement (só ele chama): o jogador começou a ação `movementActionId` (ainda no tile de
// partida); o seguidor vai junto para o tile por onde o jogador passa (mapa ação → ação no topo de src/follower.c).
void Follower_OnPlayerMovement(struct ObjectEvent *player, u8 movementActionId);

// Atalho TEST_CMD_FOLLOWER_STATE (include/test_hooks.h): 0 = existe | espécie << 8 | shiny << 24 | escondido << 25;
// 1 = x | y << 16 (s16, sem o MAP_OFFSET; 0xFFFFFFFE = não existe); 2 = direção | quadro parado << 8 | objetos com
// o localId do seguidor << 16; 0xFFFFFFFF fora do campo
u32 Follower_TestGetState(u8 what);

#endif // GUARD_FOLLOWER_H
