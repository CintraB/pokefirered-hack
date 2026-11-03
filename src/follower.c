#include "global.h"
#include "follower.h"
#include "event_object_movement.h"
#include "field_effect.h"
#include "field_player_avatar.h"
#include "field_weather.h"
#include "fieldmap.h"
#include "link.h"
#include "main.h"
#include "metatile_behavior.h"
#include "overworld.h"
#include "palette.h"
#include "pokemon.h"
#include "quest_log.h"
#include "constants/event_objects.h"
#include "constants/species.h"
#include "constants/trainer_types.h"

// Pokémon seguidor (POK-48): o 1º da equipe, se estiver em gFollowerSpecies, é um objeto de evento a mais no campo,
// fora dos templates do mapa (localId OBJ_EVENT_ID_FOLLOWER, graphicsId dinâmico OBJ_EVENT_GFX_FOLLOWER: imagens e
// paleta da espécie trocadas na criação do sprite, Follower_OnSpriteCreated).
//
// - Nunca vai para o save (load_save.c) nem para a cena do Quest Log (quest_log_objects.c): ao CONTINUAR, na volta
//   de batalha/menu e ao montar um mapa ele é recriado da equipe (overworld.c: Follower_Spawn depois dos NPCs do mapa
//   e Follower_Refresh na volta ao campo). No replay do Quest Log não aparece.
// - Paleta no slot fixo PALSLOT_FOLLOWER (= PALSLOT_NPC_SPECIAL_REFLECTION, 11): o S.S. Anne e os outros objetos do
//   slot 10 só escrevem no 11 o reflexo do Seagallop e do Meteorito (gSpecialObjectReflectionPaletteSets); num mapa
//   com um deles o seguidor não aparece (IsFollowerPaletteSlotInUse). Carregada com o tom do dia/noite
//   (ApplyGlobalFieldPaletteTint) e o gamma do clima, e recarregada do ROM no retint (ReloadObjectEventPalettes).
// - Parado (sem movimento em curso), toca a animação parada da direção: os 2 quadros alternando a cada
//   FOLLOWER_IDLE_FRAMES.
// - Anda junto (Follower_OnPlayerMovement, chamado só de ObjectEventSetHeldMovement quando o objeto é o jogador): a
//   cada ação do jogador que muda de tile, o seguidor vai para o tile por onde o jogador acabou de passar (o de trás
//   do destino dele), começando no mesmo quadro. Mapa ação do jogador → ação do seguidor (sFollowerMoves):
//     andar (walk_slower/slow/normal/fast/faster/slowest, slide, glide, correnteza) → a mesma ação, na direção do
//       seguidor até o tile alvo, no mesmo ritmo (IsPlayerMovingByInput vale para o seguidor: 11 quadros/tile por
//       input, 16 por script);
//     correr (player_run; player_run_slow na escada de pedra) → a mesma ação: ritmo de correr (5 por input, 8 por
//       script) com os quadros de andar (GetRunAnimNum: o seguidor não tem quadros de corrida);
//     girar (spin) → walk_fast (a mesma velocidade, MOVE_SPEED_FAST_1; o seguidor não tem quadros de giro);
//     pulo de 1 tile (jump) → jump;
//     pulo de ledge (jump_2) → jump_2 junto: alinhado atrás, cai no tile da ledge, logo atrás do jogador; vindo de
//       lado, pula a ledge da coluna dele (se houver) e cai ao lado do jogador; no tile do jogador, jump de 1 tile;
//     virar no lugar, walk_in_place, face_*, emotes, delays e o resto → o seguidor fica.
//   Vale para input, applymovement e tile de movimento forçado: todos passam por ObjectEventSetHeldMovement. Se o
//   seguidor está no tile do jogador (nasceu escondido), o 1º passo só o revela. Longe demais para uma ação (jogador
//   teleportado por script), ele aparece direto no tile alvo. Não colide com ninguém (DoesObjectCollideWithObjectAt)
//   e não é objeto "no tile" para o A (GetObjectEventIdByPosition, GetInteractedObjectEventScript).

struct FollowerState
{
    u16 species;    // espécie do objeto atual (a do 1º da equipe quando ele foi criado)
    u8 shiny:1;
    u8 unused:7;
    u8 unused2;
};

STATIC_ASSERT(sizeof(struct FollowerState) <= 16, FollowerStateCabeEm16BytesDeEwram);
// optionsFollowerOff ocupa um dos 4 bits livres do bitfield de 0x14-0x15: nada muda de lugar
STATIC_ASSERT(offsetof(struct SaveBlock2, pokedex) == 0x18, OpcaoDoSeguidorNoBitfieldDe0x15);
STATIC_ASSERT(sizeof(struct SaveBlock2) == 0xF24, SaveBlock2NaoMudouComOSeguidor);

EWRAM_DATA static struct FollowerState sFollowerState = {0};

enum {
    FOLLOW_STEP,    // 1 tile, andando/correndo
    FOLLOW_JUMP,    // 1 tile, pulando
    FOLLOW_JUMP_2,  // 2 tiles, pulando (ledge)
};

// Ações do jogador que mudam de tile: a 1ª das 4 (sul, norte, oeste, leste), o tipo e a 1ª das 4 do seguidor
struct FollowerMove
{
    u8 playerAction;
    u8 kind;
    u8 followerAction;
};

static const struct FollowerMove sFollowerMoves[] = {
    { MOVEMENT_ACTION_WALK_SLOWER_DOWN,         FOLLOW_STEP,   MOVEMENT_ACTION_WALK_SLOWER_DOWN },
    { MOVEMENT_ACTION_WALK_SLOW_DOWN,           FOLLOW_STEP,   MOVEMENT_ACTION_WALK_SLOW_DOWN },
    { MOVEMENT_ACTION_WALK_NORMAL_DOWN,         FOLLOW_STEP,   MOVEMENT_ACTION_WALK_NORMAL_DOWN },
    { MOVEMENT_ACTION_JUMP_2_DOWN,              FOLLOW_JUMP_2, MOVEMENT_ACTION_JUMP_2_DOWN },
    { MOVEMENT_ACTION_WALK_FAST_DOWN,           FOLLOW_STEP,   MOVEMENT_ACTION_WALK_FAST_DOWN },
    { MOVEMENT_ACTION_RIDE_WATER_CURRENT_DOWN,  FOLLOW_STEP,   MOVEMENT_ACTION_RIDE_WATER_CURRENT_DOWN },
    { MOVEMENT_ACTION_WALK_FASTER_DOWN,         FOLLOW_STEP,   MOVEMENT_ACTION_WALK_FASTER_DOWN },
    { MOVEMENT_ACTION_SLIDE_DOWN,               FOLLOW_STEP,   MOVEMENT_ACTION_SLIDE_DOWN },
    { MOVEMENT_ACTION_PLAYER_RUN_DOWN,          FOLLOW_STEP,   MOVEMENT_ACTION_PLAYER_RUN_DOWN },
    { MOVEMENT_ACTION_PLAYER_RUN_DOWN_SLOW,     FOLLOW_STEP,   MOVEMENT_ACTION_PLAYER_RUN_DOWN_SLOW },
    { MOVEMENT_ACTION_JUMP_DOWN,                FOLLOW_JUMP,   MOVEMENT_ACTION_JUMP_DOWN },
    { MOVEMENT_ACTION_SPIN_DOWN,                FOLLOW_STEP,   MOVEMENT_ACTION_WALK_FAST_DOWN },
    { MOVEMENT_ACTION_WALK_SLOWEST_DOWN,        FOLLOW_STEP,   MOVEMENT_ACTION_WALK_SLOWEST_DOWN },
    { MOVEMENT_ACTION_GLIDE_DOWN,               FOLLOW_STEP,   MOVEMENT_ACTION_GLIDE_DOWN },
};

static const u8 sIdleAnims[] = {
    [DIR_NONE]  = FOLLOWER_ANIM_IDLE_SOUTH,
    [DIR_SOUTH] = FOLLOWER_ANIM_IDLE_SOUTH,
    [DIR_NORTH] = FOLLOWER_ANIM_IDLE_NORTH,
    [DIR_WEST]  = FOLLOWER_ANIM_IDLE_WEST,
    [DIR_EAST]  = FOLLOWER_ANIM_IDLE_EAST,
};

const struct FollowerSpecies *Follower_GetSpeciesInfo(u16 species)
{
    u32 i;

    if (species == SPECIES_NONE)
        return NULL;
    for (i = 0; i < FOLLOWER_SPECIES_COUNT; i++)
    {
        if (gFollowerSpecies[i].species == species)
            return &gFollowerSpecies[i];
    }
    return NULL;
}

bool8 Follower_IsEnabled(void)
{
    return !gSaveBlock2Ptr->optionsFollowerOff;
}

bool8 Follower_IsFollowerObject(const struct ObjectEvent *objectEvent)
{
    return objectEvent->localId == OBJ_EVENT_ID_FOLLOWER && objectEvent->graphicsId == OBJ_EVENT_GFX_FOLLOWER;
}

u8 Follower_GetObjectEventId(void)
{
    u8 i;

    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        if (gObjectEvents[i].active && Follower_IsFollowerObject(&gObjectEvents[i]))
            return i;
    }
    return OBJECT_EVENTS_COUNT;
}

// O 1º da equipe, se segue o jogador: não é ovo, tem PS e está na tabela
static const struct FollowerSpecies *GetLeadSpeciesInfo(bool8 *shiny)
{
    struct Pokemon *mon = &gPlayerParty[0];
    u16 species;

    if (gPlayerPartyCount == 0)
        return NULL;
    species = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);
    if (species == SPECIES_NONE || species == SPECIES_EGG || GetMonData(mon, MON_DATA_HP) == 0)
        return NULL;
    *shiny = IsMonShiny(mon);
    return Follower_GetSpeciesInfo(species);
}

static bool8 HasFreeObjectEvent(void)
{
    u8 i;

    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        if (!gObjectEvents[i].active)
            return TRUE;
    }
    return FALSE;
}

bool8 Follower_ShouldExist(void)
{
    bool8 shiny;

    if (!Follower_IsEnabled())
        return FALSE;
    // replay do Quest Log: fora. A cena final (QL_STATE_PLAYBACK_LAST) já é o jogo carregado do save, que continua
    // dali sem recarregar os objetos: o seguidor nasce nela (a paleta entra no backup do tom cinza e volta no fim)
    if (gQuestLogState == QL_STATE_PLAYBACK)
        return FALSE;
    // link e Sala União: InitObjectEventPalettes(1) deixa os slots 8+ para os sprites dinâmicos
    if (InUnionRoom() || gReservedSpritePaletteCount < OBJ_PALSLOT_COUNT)
        return FALSE;
    if (TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_MACH_BIKE | PLAYER_AVATAR_FLAG_ACRO_BIKE
                            | PLAYER_AVATAR_FLAG_SURFING | PLAYER_AVATAR_FLAG_UNDERWATER))
        return FALSE;
    if (GetLeadSpeciesInfo(&shiny) == NULL)
        return FALSE;
    if (IsFollowerPaletteSlotInUse())
        return FALSE;
    if (Follower_GetObjectEventId() == OBJECT_EVENTS_COUNT && !HasFreeObjectEvent())
        return FALSE;
    return TRUE;
}

static void LoadFollowerPalette(void)
{
    const struct FollowerSpecies *info = Follower_GetSpeciesInfo(sFollowerState.species);

    if (info == NULL)
        info = &gFollowerSpecies[0];
    LoadPalette(sFollowerState.shiny ? info->shinyPalette : info->palette, OBJ_PLTT_ID(PALSLOT_FOLLOWER), PLTT_SIZE_4BPP);
    ApplyGlobalFieldPaletteTint(PALSLOT_FOLLOWER);
}

void Follower_ReloadPalette(void)
{
    if (Follower_GetObjectEventId() != OBJECT_EVENTS_COUNT)
        LoadFollowerPalette();
}

static bool8 FollowerMovementTypeCallback(struct ObjectEvent *objectEvent, struct Sprite *sprite)
{
    return FALSE;
}

// Parado: a animação parada da direção para onde ele olha (os 2 quadros alternando). Com movimento em curso, quem
// manda no sprite é a ação de movimento.
static void UpdateIdleAnim(struct ObjectEvent *objectEvent, struct Sprite *sprite)
{
    u8 anim;

    if (objectEvent->singleMovementActive || (objectEvent->heldMovementActive && !objectEvent->heldMovementFinished))
        return;
    anim = sIdleAnims[objectEvent->facingDirection <= DIR_EAST ? objectEvent->facingDirection : DIR_SOUTH];
    if (sprite->animNum != anim)
        StartSpriteAnim(sprite, anim);
    if (!objectEvent->frozen && !objectEvent->disableAnim)
        sprite->animPaused = FALSE;
}

static void SpriteCB_Follower(struct Sprite *sprite)
{
    struct ObjectEvent *objectEvent = &gObjectEvents[sprite->data[0]];

    UpdateObjectEventCurrentMovement(objectEvent, sprite, FollowerMovementTypeCallback);
    // ninguém espera o fim do passo do seguidor (waitmovement): solta a ação terminada para a próxima entrar
    // (ObjectEventSetHeldMovement recusa enquanto heldMovementActive)
    if (objectEvent->heldMovementActive && objectEvent->heldMovementFinished)
        ObjectEventClearHeldMovement(objectEvent);
    UpdateIdleAnim(objectEvent, sprite);
}

static u8 GetDirectionToNeighbor(s16 dx, s16 dy)
{
    if (dx > 0)
        return DIR_EAST;
    if (dx < 0)
        return DIR_WEST;
    if (dy > 0)
        return DIR_SOUTH;
    return DIR_NORTH;
}

// Pulo de ledge vindo de lado: o tile do seguidor na direção do pulo também é ledge para essa direção e o tile
// depois dela é chão
static bool8 CanFollowerJumpOwnLedge(struct ObjectEvent *follower, u8 direction)
{
    s16 x = follower->currentCoords.x, y = follower->currentCoords.y;

    MoveCoords(direction, &x, &y);
    if (GetLedgeJumpDirection(x, y, direction) != direction)
        return FALSE;
    MoveCoords(direction, &x, &y);
    return !MapGridGetCollisionAt(x, y) && !MetatileBehavior_IsSurfable(MapGridGetMetatileBehaviorAt(x, y));
}

void Follower_OnPlayerMovement(struct ObjectEvent *player, u8 movementActionId)
{
    const struct FollowerMove *move = NULL;
    struct ObjectEvent *follower;
    u8 objectEventId, direction, action;
    s16 targetX, targetY, dx, dy, sideX, sideY;
    u32 i;

    for (i = 0; i < ARRAY_COUNT(sFollowerMoves); i++)
    {
        if (movementActionId >= sFollowerMoves[i].playerAction && movementActionId < sFollowerMoves[i].playerAction + 4)
        {
            move = &sFollowerMoves[i];
            break;
        }
    }
    if (move == NULL)
        return;   // virar, andar no lugar, emote...: o seguidor fica
    objectEventId = Follower_GetObjectEventId();
    if (objectEventId == OBJECT_EVENTS_COUNT)
        return;
    follower = &gObjectEvents[objectEventId];
    direction = movementActionId - move->playerAction + DIR_SOUTH;

    // passo anterior ainda em curso (não deveria: as ações dos dois têm a mesma duração): termina no tile dele
    if (follower->heldMovementActive && !follower->heldMovementFinished)
        MoveObjectEventToMapCoords(follower, follower->currentCoords.x, follower->currentCoords.y);
    ObjectEventClearHeldMovementIfActive(follower);
    follower->invisible = FALSE;   // nasceu escondido no tile do jogador: o 1º passo o revela

    // alvo: o tile por onde o jogador acabou de passar (o de trás do destino; no pulo de ledge, o da ledge)
    targetX = player->currentCoords.x;
    targetY = player->currentCoords.y;
    if (move->kind == FOLLOW_JUMP_2)
        MoveCoords(direction, &targetX, &targetY);
    dx = targetX - follower->currentCoords.x;
    dy = targetY - follower->currentCoords.y;
    sideX = follower->currentCoords.x - player->currentCoords.x;
    sideY = follower->currentCoords.y - player->currentCoords.y;
    if (dx == 0 && dy == 0)
        return;

    if (abs(dx) + abs(dy) == 1)
    {
        u8 toward = GetDirectionToNeighbor(dx, dy);

        if (move->kind == FOLLOW_STEP)
            action = move->followerAction + toward - DIR_SOUTH;
        else
            action = MOVEMENT_ACTION_JUMP_DOWN + toward - DIR_SOUTH;
    }
    else if (move->kind == FOLLOW_JUMP_2
          && dx == 2 * gDirectionToVectors[direction].x && dy == 2 * gDirectionToVectors[direction].y)
    {
        action = move->followerAction + direction - DIR_SOUTH;   // alinhado atrás: pula junto
    }
    else if (move->kind == FOLLOW_JUMP_2 && abs(sideX) + abs(sideY) == 1
          && sideX * gDirectionToVectors[direction].x + sideY * gDirectionToVectors[direction].y == 0
          && CanFollowerJumpOwnLedge(follower, direction))
    {
        action = move->followerAction + direction - DIR_SOUTH;   // ao lado: pula a ledge dele e cai ao lado
    }
    else
    {
        // longe demais para uma ação (teleporte por script, ledge sem par ao lado): aparece no alvo
        MoveObjectEventToMapCoords(follower, targetX, targetY);
        follower->currentElevation = player->currentElevation;
        follower->previousElevation = player->currentElevation;
        ObjectEventTurn(follower, direction);
        return;
    }
    ObjectEventSetHeldMovement(follower, action);
}

void Follower_OnSpriteCreated(struct ObjectEvent *objectEvent, struct Sprite *sprite)
{
    const struct FollowerSpecies *info = Follower_GetSpeciesInfo(sFollowerState.species);

    // estado perdido (não deveria acontecer: o objeto nunca vem do save): a 1ª espécie até o Follower_Refresh
    if (info == NULL)
        info = &gFollowerSpecies[0];
    sprite->images = info->images;
    sprite->callback = SpriteCB_Follower;
    LoadFollowerPalette();
    UpdateSpritePaletteWithWeather(PALSLOT_FOLLOWER);
}

static u8 CreateFollowerAt(s16 x, s16 y, u8 direction, bool8 hidden, u8 elevation)
{
    struct ObjectEventTemplate template;
    const struct FollowerSpecies *info;
    struct ObjectEvent *objectEvent;
    bool8 shiny = FALSE;
    u8 objectEventId;

    info = GetLeadSpeciesInfo(&shiny);
    if (info == NULL)
        return OBJECT_EVENTS_COUNT;
    sFollowerState.species = info->species;
    sFollowerState.shiny = shiny;

    memset(&template, 0, sizeof(template));
    template.localId = OBJ_EVENT_ID_FOLLOWER;
    template.graphicsId = OBJ_EVENT_GFX_FOLLOWER;
    template.kind = OBJ_KIND_NORMAL;
    template.x = x - MAP_OFFSET;
    template.y = y - MAP_OFFSET;
    template.objUnion.normal.elevation = elevation;
    template.objUnion.normal.movementType = MOVEMENT_TYPE_NONE;
    template.objUnion.normal.trainerType = TRAINER_TYPE_NONE;
    objectEventId = SpawnSpecialObjectEvent(&template);   // imagens/paleta: Follower_OnSpriteCreated
    if (objectEventId == OBJECT_EVENTS_COUNT)
        return OBJECT_EVENTS_COUNT;

    objectEvent = &gObjectEvents[objectEventId];
    objectEvent->invisible = hidden;
    ObjectEventTurn(objectEvent, direction);
    gSprites[objectEvent->spriteId].invisible = hidden;
    return objectEventId;
}

void Follower_Remove(void)
{
    u8 objectEventId = Follower_GetObjectEventId();

    if (objectEventId != OBJECT_EVENTS_COUNT)
        RemoveObjectEventById(objectEventId);
}

void Follower_Spawn(void)
{
    struct ObjectEvent *player;
    s16 x, y;
    u8 back;
    bool8 hidden = FALSE;

    Follower_Remove();
    if (!Follower_ShouldExist())
        return;
    player = &gObjectEvents[gPlayerAvatar.objectEventId];
    back = GetOppositeDirection(player->facingDirection);
    x = player->currentCoords.x;
    y = player->currentCoords.y;
    MoveCoords(back, &x, &y);
    if (!CanFollowerSpawnAt(player, x, y, back))
    {
        // atrás ocupado ou bloqueado: no tile do jogador, escondido até o 1º passo (Task 3)
        x = player->currentCoords.x;
        y = player->currentCoords.y;
        hidden = TRUE;
    }
    CreateFollowerAt(x, y, player->facingDirection, hidden, player->currentElevation);
}

void Follower_Refresh(void)
{
    struct ObjectEvent *objectEvent;
    const struct FollowerSpecies *info;
    bool8 shiny = FALSE;
    u8 objectEventId;

    if (!Follower_ShouldExist())
    {
        Follower_Remove();
        return;
    }
    objectEventId = Follower_GetObjectEventId();
    if (objectEventId == OBJECT_EVENTS_COUNT)
    {
        Follower_Spawn();
        return;
    }
    info = GetLeadSpeciesInfo(&shiny);
    if (info->species != sFollowerState.species || shiny != sFollowerState.shiny)
    {
        // outra espécie (troca do 1º, evolução) ou shiny: recria no mesmo tile, virado para o mesmo lado
        s16 x, y;
        u8 direction, elevation;
        bool8 hidden;

        objectEvent = &gObjectEvents[objectEventId];
        x = objectEvent->currentCoords.x;
        y = objectEvent->currentCoords.y;
        direction = objectEvent->facingDirection;
        elevation = objectEvent->currentElevation;
        hidden = objectEvent->invisible;
        Follower_Remove();
        CreateFollowerAt(x, y, direction, hidden, elevation);
    }
}

u32 Follower_TestGetState(u8 what)
{
    u8 objectEventId = Follower_GetObjectEventId();
    struct ObjectEvent *objectEvent = &gObjectEvents[objectEventId];
    struct Sprite *sprite;
    u32 count = 0, idleFrame = 0;
    u8 i;

    if (gMain.callback1 != CB1_Overworld)
        return 0xFFFFFFFF;
    switch (what)
    {
    case 0:
        if (objectEventId == OBJECT_EVENTS_COUNT)
            return 0;
        return 1 | sFollowerState.species << 8 | (u32)sFollowerState.shiny << 24 | (u32)objectEvent->invisible << 25;
    case 1:
        if (objectEventId == OBJECT_EVENTS_COUNT)
            return 0xFFFFFFFE;
        return (u16)(objectEvent->currentCoords.x - MAP_OFFSET) | (u32)(u16)(objectEvent->currentCoords.y - MAP_OFFSET) << 16;
    case 2:
        for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
        {
            if (gObjectEvents[i].active && gObjectEvents[i].localId == OBJ_EVENT_ID_FOLLOWER)
                count++;
        }
        if (objectEventId == OBJECT_EVENTS_COUNT)
            return count << 16;
        sprite = &gSprites[objectEvent->spriteId];
        if (sprite->animNum >= FOLLOWER_ANIM_IDLE_SOUTH && sprite->animNum <= FOLLOWER_ANIM_IDLE_EAST)
            idleFrame = sprite->animCmdIndex & 1;
        return objectEvent->facingDirection | idleFrame << 8 | count << 16;
    }
    return 0xFFFFFFFF;
}
