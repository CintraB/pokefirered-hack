#include "global.h"
#include "gflib.h"
#include "battle.h"
#include "battle_anim.h"
#include "strings.h"
#include "battle_message.h"
#include "link.h"
#include "event_scripts.h"
#include "event_data.h"
#include "item.h"
#include "battle_tower.h"
#include "trainer_tower.h"
#include "battle_setup.h"
#include "field_specials.h"
#include "new_menu_helpers.h"
#include "battle_controllers.h"
#include "graphics.h"
#include "battle_ai_switch_items.h"
#include "constants/moves.h"
#include "constants/items.h"
#include "constants/trainers.h"
#include "constants/weather.h"

struct BattleWindowText
{
    u8 fillValue;
    u8 fontId;
    u8 x;
    u8 y;
    u8 letterSpacing;
    u8 lineSpacing;
    u8 speed;
    u8 fgColor;
    u8 bgColor;
    u8 shadowColor;
};

static EWRAM_DATA u8 sBattlerAbilities[MAX_BATTLERS_COUNT] = {};
static EWRAM_DATA struct BattleMsgData *sBattleMsgDataPtr = NULL;

static void ChooseMoveUsedParticle(u8 *textPtr);
static void ChooseTypeOfMoveUsedString(u8 *textPtr);
static void ExpandBattleTextBuffPlaceholders(const u8 *src, u8 *dst);

static const u8 sText_Empty1[] = _("");
static const u8 sText_Trainer1LoseText[] = _("{B_TRAINER1_LOSE_TEXT}");
static const u8 sText_Trainer2LoseText[] = _("{B_TRAINER2_LOSE_TEXT}");
static const u8 sText_Trainer1RecallPkmn1[] = _("{B_TRAINER1_NAME}: {B_OPPONENT_MON1_NAME}, volte!");
static const u8 sText_Trainer1WinText[] = _("{B_TRAINER1_WIN_TEXT}");
static const u8 sText_Trainer1RecallPkmn2[] = _("{B_TRAINER1_NAME}: {B_OPPONENT_MON2_NAME}, volte!");
static const u8 sText_Trainer1RecallBoth[] = _("{B_TRAINER1_NAME}: {B_OPPONENT_MON1_NAME} e\n{B_OPPONENT_MON2_NAME}, voltem!");
static const u8 sText_Trainer2WinText[] = _("{B_TRAINER2_WIN_TEXT}");
static const u8 sText_PkmnGainedEXP[] = _("O {B_BUFF1} ganhou\n{B_BUFF3} PE{B_BUFF2}!\p");
static const u8 sText_TeamGainedExp[] = _("O resto da equipe também\nganhou PE!\p");
static const u8 sText_EmptyString4[] = _("");
static const u8 sText_ABoosted[] = _(" com bônus");
static const u8 sText_PkmnGrewToLv[] = _("O {B_BUFF1} subiu para o\nNv. {B_BUFF2}!{WAIT_SE}\p");
static const u8 sText_PkmnLearnedMove[] = _("O {B_BUFF1} aprendeu\n{B_BUFF2}!{WAIT_SE}\p");
static const u8 sText_TryToLearnMove1[] = _("O {B_BUFF1} está tentando\naprender {B_BUFF2}.\p");
static const u8 sText_TryToLearnMove2[] = _("Mas o {B_BUFF1} não pode\naprender mais de quatro golpes.\p");
static const u8 sText_TryToLearnMove3[] = _("Esquecer um golpe para dar\nlugar a {B_BUFF2}?");
static const u8 sText_PkmnForgotMove[] = _("O {B_BUFF1} esqueceu\n{B_BUFF2}.\p");
static const u8 sText_StopLearningMove[] = _("{PAUSE 32}Desistir de aprender\n{B_BUFF2}?");
static const u8 sText_DidNotLearnMove[] = _("O {B_BUFF1} não aprendeu\n{B_BUFF2}.\p");
static const u8 sText_UseNextPkmn[] = _("Usar o próximo Pokémon?");
static const u8 sText_AttackMissed[] = _("O golpe do\n{B_ATK_NAME_WITH_PREFIX} errou!");
static const u8 sText_PkmnProtectedItself[] = _("O {B_DEF_NAME_WITH_PREFIX}\nse protegeu!");
static const u8 sText_AvoidedDamage[] = _("O {B_DEF_NAME_WITH_PREFIX} evitou\no dano com {B_DEF_ABILITY}!");
static const u8 sText_PkmnMakesGroundMiss[] = _("O {B_DEF_NAME_WITH_PREFIX} escapa dos\ngolpes Terrestres com {B_DEF_ABILITY}!");
static const u8 sText_PkmnAvoidedAttack[] = _("O {B_DEF_NAME_WITH_PREFIX}\nevitou o golpe!");
static const u8 sText_ItDoesntAffect[] = _("Não afeta o\n{B_DEF_NAME_WITH_PREFIX}…");
static const u8 sText_AttackerFainted[] = _("O {B_ATK_NAME_WITH_PREFIX}\ndesmaiou!\p");
static const u8 sText_TargetFainted[] = _("O {B_DEF_NAME_WITH_PREFIX}\ndesmaiou!\p");
static const u8 sText_PlayerGotMoney[] = _("{B_PLAYER_NAME} ganhou ¥{B_BUFF1}\npela vitória!\p");
static const u8 sText_PlayerWhiteout[] = _("{B_PLAYER_NAME} não tem mais\nPokémon em condições de lutar!\p");
static const u8 sText_PlayerPanicked[] = _("{B_PLAYER_NAME} entrou em pânico\ne perdeu ¥{B_BUFF1}…\p… … … …\p{B_PLAYER_NAME} apagou!{PAUSE_UNTIL_PRESS}");
static const u8 sText_PlayerWhiteoutAgainstTrainer[] = _("{B_PLAYER_NAME} não tem mais\nPokémon em condições de lutar!\pVocê perdeu para\n{B_TRAINER1_CLASS} {B_TRAINER1_NAME}!{PAUSE_UNTIL_PRESS}");
static const u8 sText_PlayerPaidAsPrizeMoney[] = _("{B_PLAYER_NAME} pagou ¥{B_BUFF1} de\nprêmio…\p… … … …\p{B_PLAYER_NAME} apagou!{PAUSE_UNTIL_PRESS}");
static const u8 sText_PlayerWhiteout2[] = _("{B_PLAYER_NAME} apagou!{PAUSE_UNTIL_PRESS}");
static const u8 sText_PreventsEscape[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX} impede\na fuga com {B_SCR_ACTIVE_ABILITY}!\p");
static const u8 sText_CantEscape2[] = _("Não dá para fugir!\p");
static const u8 sText_AttackerCantEscape[] = _("O {B_ATK_NAME_WITH_PREFIX}\nnão consegue fugir!");
static const u8 sText_HitXTimes[] = _("Acertou {B_BUFF1} vez(es)!");
static const u8 sText_PkmnFellAsleep[] = _("O {B_EFF_NAME_WITH_PREFIX}\nadormeceu!");
static const u8 sText_PkmnMadeSleep[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nfez o {B_EFF_NAME_WITH_PREFIX} dormir!");
static const u8 sText_PkmnAlreadyAsleep[] = _("O {B_DEF_NAME_WITH_PREFIX} já\nestá dormindo!");
static const u8 sText_PkmnAlreadyAsleep2[] = _("O {B_ATK_NAME_WITH_PREFIX} já\nestá dormindo!");
static const u8 sText_PkmnWasntAffected[] = _("O {B_DEF_NAME_WITH_PREFIX}\nnão foi afetado!");
static const u8 sText_PkmnWasPoisoned[] = _("O {B_EFF_NAME_WITH_PREFIX}\nfoi envenenado!");
static const u8 sText_PkmnPoisonedBy[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nenvenenou o {B_EFF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnHurtByPoison[] = _("O {B_ATK_NAME_WITH_PREFIX} foi ferido\npelo veneno!");
static const u8 sText_PkmnAlreadyPoisoned[] = _("O {B_DEF_NAME_WITH_PREFIX} já\nestá envenenado.");
static const u8 sText_PkmnBadlyPoisoned[] = _("O {B_EFF_NAME_WITH_PREFIX} foi\ngravemente envenenado!");
static const u8 sText_PkmnEnergyDrained[] = _("O {B_DEF_NAME_WITH_PREFIX} teve\na energia drenada!");
static const u8 sText_PkmnWasBurned[] = _("O {B_EFF_NAME_WITH_PREFIX}\nfoi queimado!");
static const u8 sText_PkmnBurnedBy[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nqueimou o {B_EFF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnHurtByBurn[] = _("O {B_ATK_NAME_WITH_PREFIX} foi ferido\npela queimadura!");
static const u8 sText_PkmnAlreadyHasBurn[] = _("O {B_DEF_NAME_WITH_PREFIX} já\nestá queimado.");
static const u8 sText_PkmnWasFrozen[] = _("O {B_EFF_NAME_WITH_PREFIX}\nficou congelado!");
static const u8 sText_PkmnFrozenBy[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncongelou o {B_EFF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnIsFrozen[] = _("O {B_ATK_NAME_WITH_PREFIX} está\ncongelado!");
static const u8 sText_PkmnWasDefrosted[] = _("O {B_DEF_NAME_WITH_PREFIX} foi\ndescongelado!");
static const u8 sText_PkmnWasDefrosted2[] = _("O {B_ATK_NAME_WITH_PREFIX} foi\ndescongelado!");
static const u8 sText_PkmnWasDefrostedBy[] = _("O {B_ATK_NAME_WITH_PREFIX} foi\ndescongelado por {B_CURRENT_MOVE}!");
static const u8 sText_PkmnWasParalyzed[] = _("O {B_EFF_NAME_WITH_PREFIX} está paralisado!\nTalvez não consiga se mover!");
static const u8 sText_PkmnWasParalyzedBy[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nparalisou o {B_EFF_NAME_WITH_PREFIX}!\lTalvez não consiga se mover!");
static const u8 sText_PkmnIsParalyzed[] = _("O {B_ATK_NAME_WITH_PREFIX} está paralisado!\nNão consegue se mover!");
static const u8 sText_PkmnIsAlreadyParalyzed[] = _("O {B_DEF_NAME_WITH_PREFIX} já\nestá paralisado!");
static const u8 sText_PkmnHealedParalysis[] = _("O {B_DEF_NAME_WITH_PREFIX} foi\ncurado da paralisia!");
static const u8 sText_PkmnDreamEaten[] = _("O sonho do\n{B_DEF_NAME_WITH_PREFIX} foi devorado!");
static const u8 sText_StatsWontIncrease[] = _("Não dá para aumentar mais\n{B_BUFF1} do {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_StatsWontDecrease[] = _("Não dá para diminuir mais\n{B_BUFF1} do {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_TeamStoppedWorking[] = _("O efeito de {B_BUFF1} da\nsua equipe acabou!");
static const u8 sText_FoeStoppedWorking[] = _("O efeito de {B_BUFF1} da\nequipe inimiga acabou!");
static const u8 sText_PkmnIsConfused[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nconfuso!");
static const u8 sText_PkmnHealedConfusion[] = _("O {B_ATK_NAME_WITH_PREFIX} saiu\nda confusão!");
static const u8 sText_PkmnWasConfused[] = _("O {B_EFF_NAME_WITH_PREFIX} ficou\nconfuso!");
static const u8 sText_PkmnAlreadyConfused[] = _("O {B_DEF_NAME_WITH_PREFIX} já\nestá confuso!");
static const u8 sText_PkmnFellInLove[] = _("O {B_DEF_NAME_WITH_PREFIX}\nse apaixonou!");
static const u8 sText_PkmnInLove[] = _("O {B_ATK_NAME_WITH_PREFIX} está apaixonado\npelo {B_SCR_ACTIVE_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnImmobilizedByLove[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nimobilizado pelo amor!");
static const u8 sText_PkmnBlownAway[] = _("O {B_DEF_NAME_WITH_PREFIX} foi\nlançado para longe!");
static const u8 sText_PkmnChangedType[] = _("O {B_ATK_NAME_WITH_PREFIX} se transformou\nno tipo {B_BUFF1}!");
static const u8 sText_PkmnFlinched[] = _("O {B_ATK_NAME_WITH_PREFIX} hesitou!");
static const u8 sText_PkmnRegainedHealth[] = _("O {B_DEF_NAME_WITH_PREFIX}\nrecuperou PS!");
static const u8 sText_PkmnHPFull[] = _("Os PS do {B_DEF_NAME_WITH_PREFIX}\nestão cheios!");
static const u8 sText_PkmnRaisedSpDef[] = _("{B_CURRENT_MOVE} da equipe {B_ATK_PREFIX2}\naumentou a Defesa Especial!");
static const u8 sText_PkmnRaisedSpDefALittle[] = _("{B_CURRENT_MOVE} da equipe {B_ATK_PREFIX2}\naumentou um pouco a Defesa Especial!");
static const u8 sText_PkmnRaisedDef[] = _("{B_CURRENT_MOVE} da equipe {B_ATK_PREFIX2}\naumentou a Defesa!");
static const u8 sText_PkmnRaisedDefALittle[] = _("{B_CURRENT_MOVE} da equipe {B_ATK_PREFIX2}\naumentou um pouco a Defesa!");
static const u8 sText_PkmnCoveredByVeil[] = _("A equipe {B_ATK_PREFIX2} está\nprotegida por um véu!");
static const u8 sText_PkmnUsedSafeguard[] = _("A equipe do {B_DEF_NAME_WITH_PREFIX} está\nprotegida por Salvaguarda!");
static const u8 sText_PkmnSafeguardExpired[] = _("A equipe {B_ATK_PREFIX3} não está mais\nprotegida por Salvaguarda!");
static const u8 sText_PkmnWentToSleep[] = _("O {B_ATK_NAME_WITH_PREFIX} foi\ndormir!");
static const u8 sText_PkmnSleptHealthy[] = _("O {B_ATK_NAME_WITH_PREFIX} dormiu e\nficou saudável!");
static const u8 sText_PkmnWhippedWhirlwind[] = _("O {B_ATK_NAME_WITH_PREFIX} criou\num turbilhão de vento!");
static const u8 sText_PkmnTookSunlight[] = _("O {B_ATK_NAME_WITH_PREFIX} absorveu\na luz do sol!");
static const u8 sText_PkmnLoweredHead[] = _("O {B_ATK_NAME_WITH_PREFIX} abaixou\na cabeça!");
static const u8 sText_PkmnIsGlowing[] = _("O {B_ATK_NAME_WITH_PREFIX}\nestá brilhando!");
static const u8 sText_PkmnFlewHigh[] = _("O {B_ATK_NAME_WITH_PREFIX} voou\nbem alto!");
static const u8 sText_PkmnDugHole[] = _("O {B_ATK_NAME_WITH_PREFIX} cavou\num buraco!");
static const u8 sText_PkmnHidUnderwater[] = _("O {B_ATK_NAME_WITH_PREFIX} se escondeu\ndebaixo d'água!");
static const u8 sText_PkmnSprangUp[] = _("O {B_ATK_NAME_WITH_PREFIX}\nsaltou bem alto!");
static const u8 sText_PkmnSqueezedByBind[] = _("O {B_DEF_NAME_WITH_PREFIX} foi apertado\npela Ligação do {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnTrappedInVortex[] = _("O {B_DEF_NAME_WITH_PREFIX} ficou preso\nno redemoinho!");
static const u8 sText_PkmnTrappedBySandTomb[] = _("O {B_DEF_NAME_WITH_PREFIX} ficou preso\nno Fosso de Areia!");
static const u8 sText_PkmnWrappedBy[] = _("O {B_DEF_NAME_WITH_PREFIX} foi enrolado\npelo {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnClamped[] = _("O {B_ATK_NAME_WITH_PREFIX} prendeu\no {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnHurtBy[] = _("O {B_ATK_NAME_WITH_PREFIX} foi ferido\npor {B_BUFF1}!");
static const u8 sText_PkmnFreedFrom[] = _("O {B_ATK_NAME_WITH_PREFIX} se livrou\nde {B_BUFF1}!");
static const u8 sText_PkmnCrashed[] = _("O {B_ATK_NAME_WITH_PREFIX} passou\ndireto e caiu!");
const u8 gBattleText_MistShroud[] = _("A equipe {B_ATK_PREFIX2} ficou\nenvolta em Névoa!");
static const u8 sText_PkmnProtectedByMist[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX} está\nprotegido pela Névoa!");
const u8 gBattleText_GetPumped[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nse concentrando!");
static const u8 sText_PkmnHitWithRecoil[] = _("O {B_ATK_NAME_WITH_PREFIX} sofreu\ndano de recuo!");
static const u8 sText_PkmnProtectedItself2[] = _("O {B_ATK_NAME_WITH_PREFIX}\nse protegeu!");
static const u8 sText_PkmnBuffetedBySandstorm[] = _("O {B_ATK_NAME_WITH_PREFIX} foi atingido\npela tempestade de areia!");
static const u8 sText_PkmnPeltedByHail[] = _("O {B_ATK_NAME_WITH_PREFIX} foi atingido\npelo granizo!");
static const u8 sText_PkmnsXWoreOff[] = _("{B_BUFF1} da equipe\n{B_ATK_PREFIX1} acabou!");
static const u8 sText_PkmnSeeded[] = _("O {B_DEF_NAME_WITH_PREFIX}\nfoi semeado!");
static const u8 sText_PkmnEvadedAttack[] = _("O {B_DEF_NAME_WITH_PREFIX} se esquivou\ndo golpe!");
static const u8 sText_PkmnSappedByLeechSeed[] = _("Semente Sanguessuga drenou\nos PS do {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnFastAsleep[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nem sono profundo.");
static const u8 sText_PkmnWokeUp[] = _("O {B_ATK_NAME_WITH_PREFIX} acordou!");
static const u8 sText_PkmnUproarKeptAwake[] = _("Mas o Tumulto do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\no manteve acordado!");
static const u8 sText_PkmnWokeUpInUproar[] = _("O {B_ATK_NAME_WITH_PREFIX} acordou\ncom o Tumulto!");
static const u8 sText_PkmnCausedUproar[] = _("O {B_ATK_NAME_WITH_PREFIX} causou\num Tumulto!");
static const u8 sText_PkmnMakingUproar[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nfazendo Tumulto!");
static const u8 sText_PkmnCalmedDown[] = _("O {B_ATK_NAME_WITH_PREFIX} se acalmou.");
static const u8 sText_PkmnCantSleepInUproar[] = _("Mas o {B_DEF_NAME_WITH_PREFIX} não pode\ndormir com o Tumulto!");
static const u8 sText_PkmnStockpiled[] = _("O {B_ATK_NAME_WITH_PREFIX} acumulou\nenergia {B_BUFF1} vez(es)!");
static const u8 sText_PkmnCantStockpile[] = _("O {B_ATK_NAME_WITH_PREFIX} não consegue\nacumular mais!");
static const u8 sText_PkmnCantSleepInUproar2[] = _("Mas o {B_DEF_NAME_WITH_PREFIX} não pode\ndormir com o Tumulto!");
static const u8 sText_UproarKeptPkmnAwake[] = _("Mas o Tumulto manteve\no {B_DEF_NAME_WITH_PREFIX} acordado!");
static const u8 sText_PkmnStayedAwakeUsing[] = _("O {B_DEF_NAME_WITH_PREFIX} ficou acordado\ncom {B_DEF_ABILITY}!");
static const u8 sText_PkmnStoringEnergy[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nacumulando energia!");
static const u8 sText_PkmnUnleashedEnergy[] = _("O {B_ATK_NAME_WITH_PREFIX} liberou\na energia!");
static const u8 sText_PkmnFatigueConfusion[] = _("O {B_ATK_NAME_WITH_PREFIX} ficou\nconfuso de cansaço!");
static const u8 sText_PkmnPickedUpItem[] = _("{B_PLAYER_NAME} recolheu\n¥{B_BUFF1}!\p");
static const u8 sText_PkmnUnaffected[] = _("O {B_DEF_NAME_WITH_PREFIX} está\nimune!");
static const u8 sText_PkmnTransformedInto[] = _("O {B_ATK_NAME_WITH_PREFIX} se transformou\nem {B_BUFF1}!");
static const u8 sText_PkmnMadeSubstitute[] = _("O {B_ATK_NAME_WITH_PREFIX} criou\num Substituto!");
static const u8 sText_PkmnHasSubstitute[] = _("O {B_ATK_NAME_WITH_PREFIX} já\ntem um Substituto!");
static const u8 sText_SubstituteDamaged[] = _("O Substituto recebeu o dano\nno lugar do {B_DEF_NAME_WITH_PREFIX}!\p");
static const u8 sText_PkmnSubstituteFaded[] = _("O Substituto do\n{B_DEF_NAME_WITH_PREFIX} sumiu!\p");
static const u8 sText_PkmnMustRecharge[] = _("O {B_ATK_NAME_WITH_PREFIX} precisa\nrecarregar!");
static const u8 sText_PkmnRageBuilding[] = _("A Ira do {B_DEF_NAME_WITH_PREFIX}\nestá aumentando!");
static const u8 sText_PkmnMoveWasDisabled[] = _("O golpe {B_BUFF1} do\n{B_DEF_NAME_WITH_PREFIX} foi inabilitado!");
static const u8 sText_PkmnMoveDisabledNoMore[] = _("O {B_ATK_NAME_WITH_PREFIX} não está\nmais inabilitado!");
static const u8 sText_PkmnGotEncore[] = _("O {B_DEF_NAME_WITH_PREFIX} recebeu\num pedido de Bis!");
static const u8 sText_PkmnEncoreEnded[] = _("O Bis do {B_ATK_NAME_WITH_PREFIX}\nacabou!");
static const u8 sText_PkmnTookAim[] = _("O {B_ATK_NAME_WITH_PREFIX} mirou\no {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnSketchedMove[] = _("O {B_ATK_NAME_WITH_PREFIX} copiou\n{B_BUFF1} com Esboço!");
static const u8 sText_PkmnTryingToTakeFoe[] = _("O {B_ATK_NAME_WITH_PREFIX} quer levar\no oponente junto!");
static const u8 sText_PkmnTookFoe[] = _("O {B_DEF_NAME_WITH_PREFIX} levou\no {B_ATK_NAME_WITH_PREFIX} junto!");
static const u8 sText_PkmnReducedPP[] = _("O {B_DEF_NAME_WITH_PREFIX} perdeu\n{B_BUFF2} PP de {B_BUFF1}!");
static const u8 sText_PkmnStoleItem[] = _("O {B_ATK_NAME_WITH_PREFIX} roubou\n{B_LAST_ITEM} do {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_TargetCantEscapeNow[] = _("O {B_DEF_NAME_WITH_PREFIX} não pode\nmais fugir!");
static const u8 sText_PkmnFellIntoNightmare[] = _("O {B_DEF_NAME_WITH_PREFIX} caiu\nnum Pesadelo!");
static const u8 sText_PkmnLockedInNightmare[] = _("O {B_ATK_NAME_WITH_PREFIX} está preso\nnum Pesadelo!");
static const u8 sText_PkmnLaidCurse[] = _("O {B_ATK_NAME_WITH_PREFIX} sacrificou PS\ne amaldiçoou o {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnAfflictedByCurse[] = _("O {B_ATK_NAME_WITH_PREFIX} sofre\ncom a Maldição!");
static const u8 sText_SpikesScattered[] = _("Espinhos se espalharam pelo\ncampo do oponente!");
static const u8 sText_PkmnHurtBySpikes[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX} foi ferido\npelos Espinhos!");
static const u8 sText_PkmnIdentified[] = _("O {B_ATK_NAME_WITH_PREFIX} identificou\no {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnPerishCountFell[] = _("O {B_ATK_NAME_WITH_PREFIX} está com\ncontagem fatal {B_BUFF1}!");
static const u8 sText_PkmnBracedItself[] = _("O {B_ATK_NAME_WITH_PREFIX} se\npreparou para aguentar!");
static const u8 sText_PkmnEnduredHit[] = _("O {B_DEF_NAME_WITH_PREFIX} aguentou\no golpe!");
static const u8 sText_MagnitudeStrength[] = _("Magnitude {B_BUFF1}!");
static const u8 sText_PkmnCutHPMaxedAttack[] = _("O {B_ATK_NAME_WITH_PREFIX} sacrificou PS\ne maximizou o Ataque!");
static const u8 sText_PkmnCopiedStatChanges[] = _("O {B_ATK_NAME_WITH_PREFIX} copiou\nas mudanças de atributo\ldo {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnGotFree[] = _("O {B_ATK_NAME_WITH_PREFIX} se livrou de\n{B_BUFF1} do {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnShedLeechSeed[] = _("O {B_ATK_NAME_WITH_PREFIX} se livrou\nda Semente Sanguessuga!");
static const u8 sText_PkmnBlewAwaySpikes[] = _("O {B_ATK_NAME_WITH_PREFIX} varreu\nos Espinhos!");
static const u8 sText_PkmnFledFromBattle[] = _("O {B_ATK_NAME_WITH_PREFIX} fugiu\nda batalha!");
static const u8 sText_PkmnForesawAttack[] = _("O {B_ATK_NAME_WITH_PREFIX} previu\num ataque!");
static const u8 sText_PkmnTookAttack[] = _("O {B_DEF_NAME_WITH_PREFIX} recebeu\no ataque de {B_BUFF1}!");
static const u8 sText_PkmnChoseXAsDestiny[] = _("O {B_ATK_NAME_WITH_PREFIX} escolheu\n{B_CURRENT_MOVE} como destino!");
static const u8 sText_PkmnAttack[] = _("Golpe do {B_BUFF1}!");
static const u8 sText_PkmnCenterAttention[] = _("O {B_ATK_NAME_WITH_PREFIX} virou o\ncentro das atenções!");
static const u8 sText_PkmnChargingPower[] = _("O {B_ATK_NAME_WITH_PREFIX} começou\na carregar energia!");
static const u8 sText_NaturePowerTurnedInto[] = _("Poder Natural virou\n{B_CURRENT_MOVE}!");
static const u8 sText_PkmnStatusNormal[] = _("O status do {B_ATK_NAME_WITH_PREFIX}\nvoltou ao normal!");
static const u8 sText_PkmnSubjectedToTorment[] = _("O {B_DEF_NAME_WITH_PREFIX} foi\natormentado!");
static const u8 sText_PkmnTighteningFocus[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nreunindo forças!");
static const u8 sText_PkmnFellForTaunt[] = _("O {B_DEF_NAME_WITH_PREFIX} caiu\nno Insulto!");
static const u8 sText_PkmnReadyToHelp[] = _("O {B_ATK_NAME_WITH_PREFIX} está pronto\npara ajudar o {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnSwitchedItems[] = _("O {B_ATK_NAME_WITH_PREFIX} trocou\nde item com o oponente!");
static const u8 sText_PkmnObtainedX[] = _("O {B_ATK_NAME_WITH_PREFIX} obteve\n{B_BUFF1}.");
static const u8 sText_PkmnObtainedX2[] = _("O {B_DEF_NAME_WITH_PREFIX} obteve\n{B_BUFF2}.");
static const u8 sText_PkmnObtainedXYObtainedZ[] = _("O {B_ATK_NAME_WITH_PREFIX} obteve\n{B_BUFF1}.\pO {B_DEF_NAME_WITH_PREFIX} obteve\n{B_BUFF2}.");
static const u8 sText_PkmnCopiedFoe[] = _("O {B_ATK_NAME_WITH_PREFIX} copiou\n{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnMadeWish[] = _("O {B_ATK_NAME_WITH_PREFIX} fez\num Desejo!");
static const u8 sText_PkmnWishCameTrue[] = _("O Desejo do {B_BUFF1}\nse realizou!");
static const u8 sText_PkmnPlantedRoots[] = _("O {B_ATK_NAME_WITH_PREFIX}\nfincou raízes!");
static const u8 sText_PkmnAbsorbedNutrients[] = _("O {B_ATK_NAME_WITH_PREFIX} absorveu\nnutrientes pelas raízes!");
static const u8 sText_PkmnAnchoredItself[] = _("O {B_DEF_NAME_WITH_PREFIX} se firmou\ncom as raízes!");
static const u8 sText_PkmnWasMadeDrowsy[] = _("O {B_ATK_NAME_WITH_PREFIX} deixou\no {B_DEF_NAME_WITH_PREFIX} sonolento!");
static const u8 sText_PkmnKnockedOff[] = _("O {B_ATK_NAME_WITH_PREFIX} derrubou\n{B_LAST_ITEM} do {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnSwappedAbilities[] = _("O {B_ATK_NAME_WITH_PREFIX} trocou de\nhabilidade com o oponente!");
static const u8 sText_PkmnSealedOpponentMove[] = _("O {B_ATK_NAME_WITH_PREFIX} selou\nos golpes do oponente!");
static const u8 sText_PkmnWantsGrudge[] = _("O {B_ATK_NAME_WITH_PREFIX} quer deixar\no oponente com Mágoa!");
static const u8 sText_PkmnLostPPGrudge[] = _("O golpe {B_BUFF1} do\n{B_ATK_NAME_WITH_PREFIX} perdeu\ltodo o PP com a Mágoa!");
static const u8 sText_PkmnShroudedItself[] = _("O {B_ATK_NAME_WITH_PREFIX} se cobriu\ncom {B_CURRENT_MOVE}!");
static const u8 sText_PkmnMoveBounced[] = _("Casaco Mágico rebateu\n{B_CURRENT_MOVE} do {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnWaitsForTarget[] = _("O {B_ATK_NAME_WITH_PREFIX} espera\no oponente agir!");
static const u8 sText_PkmnSnatchedMove[] = _("O {B_DEF_NAME_WITH_PREFIX} arrebatou\no golpe do {B_SCR_ACTIVE_NAME_WITH_PREFIX}!");
static const u8 sText_ElectricityWeakened[] = _("O poder da eletricidade\nenfraqueceu!");
static const u8 sText_FireWeakened[] = _("O poder do fogo\nenfraqueceu!");
static const u8 sText_XFoundOneY[] = _("O {B_ATK_NAME_WITH_PREFIX} encontrou\n{B_LAST_ITEM}!");
static const u8 sText_SoothingAroma[] = _("Um aroma calmante se\nespalhou pela área!");
static const u8 sText_ItemsCantBeUsedNow[] = _("Não dá para usar itens agora.{PAUSE 64}");
static const u8 sText_ForXCommaYZ[] = _("Para o {B_SCR_ACTIVE_NAME_WITH_PREFIX},\na {B_LAST_ITEM} {B_BUFF1}");
static const u8 sText_PkmnUsedXToGetPumped[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX} usou\n{B_LAST_ITEM} e se concentrou!");
static const u8 sText_PkmnLostFocus[] = _("O {B_ATK_NAME_WITH_PREFIX} perdeu a\nconcentração e não se moveu!");
static const u8 sText_PkmnWasDraggedOut[] = _("O {B_DEF_NAME_WITH_PREFIX} foi\npuxado para a batalha!\p");
static const u8 sText_TheWallShattered[] = _("A barreira se quebrou!");
static const u8 sText_ButNoEffect[] = _("Mas não teve efeito!");
static const u8 sText_PkmnHasNoMovesLeft[] = _("O {B_ACTIVE_NAME_WITH_PREFIX} não tem\nmais golpes!\p");
static const u8 sText_PkmnMoveIsDisabled[] = _("O golpe {B_CURRENT_MOVE} do\n{B_ACTIVE_NAME_WITH_PREFIX} está inabilitado!\p");
static const u8 sText_PkmnCantUseMoveTorment[] = _("O {B_ACTIVE_NAME_WITH_PREFIX} está atormentado\ne não pode repetir o golpe!\p");
static const u8 sText_PkmnCantUseMoveTaunt[] = _("Por causa do Insulto, o\n{B_ACTIVE_NAME_WITH_PREFIX} não pode usar\l{B_CURRENT_MOVE}!\p");
static const u8 sText_PkmnCantUseMoveSealed[] = _("O {B_ACTIVE_NAME_WITH_PREFIX} não pode\nusar {B_CURRENT_MOVE}, que foi selado!\p");
static const u8 sText_PkmnMadeItRain[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nfez chover!");
static const u8 sText_PkmnRaisedSpeed[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\naumentou a Velocidade!");
static const u8 sText_PkmnProtectedBy[] = _("O {B_DEF_NAME_WITH_PREFIX} foi protegido\npor {B_DEF_ABILITY}!");
static const u8 sText_PkmnPreventsUsage[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nimpede o {B_ATK_NAME_WITH_PREFIX}\lde usar {B_CURRENT_MOVE}!");
static const u8 sText_PkmnRestoredHPUsing[] = _("O {B_DEF_NAME_WITH_PREFIX} recuperou PS\ncom {B_DEF_ABILITY}!");
static const u8 sText_PkmnsXMadeYUseless[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\ntornou {B_CURRENT_MOVE} inútil!");
static const u8 sText_PkmnChangedTypeWith[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\no mudou para o tipo {B_BUFF1}!");
static const u8 sText_PkmnPreventsParalysisWith[] = _("{B_DEF_ABILITY} do {B_EFF_NAME_WITH_PREFIX}\nimpede a paralisia!");
static const u8 sText_PkmnPreventsRomanceWith[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nimpede a paixão!");
static const u8 sText_PkmnPreventsPoisoningWith[] = _("{B_DEF_ABILITY} do {B_EFF_NAME_WITH_PREFIX}\nimpede o envenenamento!");
static const u8 sText_PkmnPreventsConfusionWith[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nimpede a confusão!");
static const u8 sText_PkmnRaisedFirePowerWith[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nfortaleceu os golpes de Fogo!");
static const u8 sText_PkmnAnchorsItselfWith[] = _("O {B_DEF_NAME_WITH_PREFIX} se firma\ncom {B_DEF_ABILITY}!");
static const u8 sText_PkmnCutsAttackWith[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nreduz o Ataque\ldo {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnPreventsStatLossWith[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nimpede a perda de atributos!");
static const u8 sText_PkmnHurtsWith[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nferiu o {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnTraced[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX} copiou\n{B_BUFF2} do {B_BUFF1}!");
static const u8 sText_PkmnsXPreventsBurns[] = _("{B_EFF_ABILITY} do {B_EFF_NAME_WITH_PREFIX}\nimpede queimaduras!");
static const u8 sText_PkmnsXBlocksY[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nbloqueia {B_CURRENT_MOVE}!");
static const u8 sText_PkmnsXBlocksY2[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nbloqueia {B_CURRENT_MOVE}!");
static const u8 sText_PkmnsXRestoredHPALittle2[] = _("{B_ATK_ABILITY} do {B_ATK_NAME_WITH_PREFIX}\nrecuperou um pouco de PS!");
static const u8 sText_PkmnsXWhippedUpSandstorm[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nlevantou uma tempestade de areia!");
static const u8 sText_PkmnsXIntensifiedSun[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nintensificou os raios de sol!");
static const u8 sText_PkmnsXPreventsYLoss[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nimpede que {B_BUFF1} diminua!");
static const u8 sText_PkmnsXInfatuatedY[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\napaixonou o {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_PkmnsXMadeYIneffective[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\ntornou {B_CURRENT_MOVE} ineficaz!");
static const u8 sText_PkmnsXCuredYProblem[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou {B_BUFF1}!");
static const u8 sText_ItSuckedLiquidOoze[] = _("O golpe sugou\no Lodo Líquido!");
static const u8 sText_PkmnTransformed[] = _("O {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nse transformou!");
static const u8 sText_PkmnsXTookAttack[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nabsorveu o ataque!");
const u8 gText_PkmnsXPreventsSwitching[] = _("{B_LAST_ABILITY} do {B_BUFF1}\nimpede a troca!\p");
static const u8 sText_PreventedFromWorking[] = _("{B_DEF_ABILITY} do {B_DEF_NAME_WITH_PREFIX}\nimpediu o {B_SCR_ACTIVE_NAME_WITH_PREFIX}\lde usar {B_BUFF1}!");
static const u8 sText_PkmnsXMadeItIneffective[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ntornou o golpe ineficaz!");
static const u8 sText_PkmnsXPreventsFlinching[] = _("{B_EFF_ABILITY} do {B_EFF_NAME_WITH_PREFIX}\nimpede a hesitação!");
static const u8 sText_PkmnsXPreventsYsZ[] = _("{B_ATK_ABILITY} do {B_ATK_NAME_WITH_PREFIX}\nimpede que {B_DEF_ABILITY}\ldo {B_DEF_NAME_WITH_PREFIX} funcione!");
static const u8 sText_PkmnsXCuredItsYProblem[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou {B_BUFF1}!");
static const u8 sText_PkmnsXHadNoEffectOnY[] = _("{B_SCR_ACTIVE_ABILITY} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nnão afetou o {B_EFF_NAME_WITH_PREFIX}!");
static const u8 sText_TooScaredToMove[] = _("O {B_ATK_NAME_WITH_PREFIX} está com medo\ndemais para se mover!");
static const u8 sText_GetOutGetOut[] = _("Fantasma: Vá embora…… Vá embora……");
static const u8 sText_StatSharply[] = _("Aumentou muito");
const u8 gBattleText_Rose[] = _("Aumentou");
static const u8 sText_StatHarshly[] = _("Diminuiu muito");
static const u8 sText_StatFell[] = _("Diminuiu");
static const u8 sText_AttackersStatRose[] = _("{B_BUFF2} {B_BUFF1}\ndo {B_ATK_NAME_WITH_PREFIX}!");
const u8 gText_DefendersStatRose[] = _("{B_BUFF2} {B_BUFF1}\ndo {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_UsingItemTheStatOfPkmnRose[] = _("{B_BUFF2} {B_BUFF1}\ndo {B_SCR_ACTIVE_NAME_WITH_PREFIX}\lcom {B_LAST_ITEM}!");
static const u8 sText_AttackersStatFell[] = _("{B_BUFF2} {B_BUFF1}\ndo {B_ATK_NAME_WITH_PREFIX}!");
static const u8 sText_DefendersStatFell[] = _("{B_BUFF2} {B_BUFF1}\ndo {B_DEF_NAME_WITH_PREFIX}!");
static const u8 sText_StatsWontIncrease2[] = _("Os atributos do {B_ATK_NAME_WITH_PREFIX}\nnão vão subir mais!");
static const u8 sText_StatsWontDecrease2[] = _("Os atributos do {B_DEF_NAME_WITH_PREFIX}\nnão vão cair mais!");
static const u8 sText_CriticalHit[] = _("Um golpe crítico!");
static const u8 sText_OneHitKO[] = _("Nocaute de um golpe só!");
static const u8 sText_123Poof[] = _("{PAUSE 32}1, {PAUSE 15}2 e{PAUSE 15}… {PAUSE 15}… {PAUSE 15}… {PAUSE 15}{PLAY_SE SE_BALL_BOUNCE_1}Puf!\p");
static const u8 sText_AndEllipsis[] = _("E…\p");
static const u8 sText_HMMovesCantBeForgotten[] = _("Golpes de MO não podem ser\nesquecidos agora.\p");
static const u8 sText_NotVeryEffective[] = _("Não é muito eficaz…");
static const u8 sText_SuperEffective[] = _("É supereficaz!");
static const u8 sText_GotAwaySafely[] = _("{PLAY_SE SE_FLEE}Você fugiu em segurança!\p");
static const u8 sText_PkmnFledUsingIts[] = _("{PLAY_SE SE_FLEE}O {B_ATK_NAME_WITH_PREFIX} fugiu\nusando {B_LAST_ITEM}!\p");
static const u8 sText_PkmnFledUsing[] = _("{PLAY_SE SE_FLEE}O {B_ATK_NAME_WITH_PREFIX} fugiu\ncom {B_ATK_ABILITY}!\p");
static const u8 sText_WildPkmnFled[] = _("{PLAY_SE SE_FLEE}O {B_BUFF1} selvagem fugiu!");
static const u8 sText_PlayerDefeatedLinkTrainer[] = _("Você derrotou\n{B_LINK_OPPONENT1_NAME}!");
static const u8 sText_TwoLinkTrainersDefeated[] = _("Você venceu {B_LINK_OPPONENT1_NAME}\ne {B_LINK_OPPONENT2_NAME}!");
static const u8 sText_PlayerLostAgainstLinkTrainer[] = _("Você perdeu para\n{B_LINK_OPPONENT1_NAME}!");
static const u8 sText_PlayerLostToTwo[] = _("Você perdeu para {B_LINK_OPPONENT1_NAME}\ne {B_LINK_OPPONENT2_NAME}!");
static const u8 sText_PlayerBattledToDrawLinkTrainer[] = _("Você empatou com\n{B_LINK_OPPONENT1_NAME}!");
static const u8 sText_PlayerBattledToDrawVsTwo[] = _("Você empatou com\n{B_LINK_OPPONENT1_NAME} e {B_LINK_OPPONENT2_NAME}!");
static const u8 sText_WildFled[] = _("{PLAY_SE SE_FLEE}{B_LINK_OPPONENT1_NAME} fugiu!");
static const u8 sText_TwoWildFled[] = _("{PLAY_SE SE_FLEE}{B_LINK_OPPONENT1_NAME} e\n{B_LINK_OPPONENT2_NAME} fugiram!");
static const u8 sText_NoRunningFromTrainers[] = _("Não! Não se foge de uma\nbatalha contra um Treinador!\p");
static const u8 sText_CantEscape[] = _("Não dá para fugir!\p");
static const u8 sText_DontLeaveBirch[] = _(""); // Dummied
static const u8 sText_ButNothingHappened[] = _("Mas nada aconteceu!");
static const u8 sText_ButItFailed[] = _("Mas falhou!");
static const u8 sText_ItHurtConfusion[] = _("Ele se machucou\nna confusão!");
static const u8 sText_MirrorMoveFailed[] = _("O Ataque Espelhado falhou!");
static const u8 sText_StartedToRain[] = _("Começou a chover!");
static const u8 sText_DownpourStarted[] = _("Começou um temporal!"); // corresponds to DownpourText in pokegold and pokecrystal and is used by Rain Dance in GSC
static const u8 sText_RainContinues[] = _("Continua chovendo.");
static const u8 sText_DownpourContinues[] = _("O temporal continua."); // unused
static const u8 sText_RainStopped[] = _("A chuva parou.");
static const u8 sText_SandstormBrewed[] = _("Uma tempestade de areia se formou!");
static const u8 sText_SandstormRages[] = _("A tempestade de areia segue forte.");
static const u8 sText_SandstormSubsided[] = _("A tempestade de areia passou.");
static const u8 sText_SunlightGotBright[] = _("A luz do sol ficou forte!");
static const u8 sText_SunlightStrong[] = _("A luz do sol está forte.");
static const u8 sText_SunlightFaded[] = _("A luz do sol enfraqueceu.");
static const u8 sText_StartedHail[] = _("Começou a cair granizo!");
static const u8 sText_HailContinues[] = _("O granizo continua caindo.");
static const u8 sText_HailStopped[] = _("O granizo parou.");
static const u8 sText_FailedToSpitUp[] = _("Mas não havia nada\npara cuspir!");
static const u8 sText_FailedToSwallow[] = _("Mas não havia nada\npara engolir!");
static const u8 sText_WindBecameHeatWave[] = _("O vento virou uma\nOnda de Calor!");
static const u8 sText_StatChangesGone[] = _("Todas as mudanças de atributo\nforam eliminadas!");
static const u8 sText_CoinsScattered[] = _("Moedas se espalharam por toda parte!");
static const u8 sText_TooWeakForSubstitute[] = _("Está fraco demais para\ncriar um Substituto!");
static const u8 sText_SharedPain[] = _("Os combatentes dividiram\na dor!");
static const u8 sText_BellChimed[] = _("Um sino tocou!");
static const u8 sText_FaintInThree[] = _("Todos os Pokémon afetados vão\ndesmaiar em três turnos!");
static const u8 sText_NoPPLeft[] = _("Este golpe está\nsem PP!\p");
static const u8 sText_ButNoPPLeft[] = _("Mas o golpe estava\nsem PP!");
static const u8 sText_PkmnIgnoresAsleep[] = _("O {B_ATK_NAME_WITH_PREFIX} ignorou as\nordens enquanto dormia!");
static const u8 sText_PkmnIgnoredOrders[] = _("O {B_ATK_NAME_WITH_PREFIX} ignorou\nas ordens!");
static const u8 sText_PkmnBeganToNap[] = _("O {B_ATK_NAME_WITH_PREFIX}\ntirou um cochilo!");
static const u8 sText_PkmnLoafing[] = _("O {B_ATK_NAME_WITH_PREFIX} está\nfazendo corpo mole!");
static const u8 sText_PkmnWontObey[] = _("O {B_ATK_NAME_WITH_PREFIX} não\nobedece!");
static const u8 sText_PkmnTurnedAway[] = _("O {B_ATK_NAME_WITH_PREFIX}\ndeu as costas!");
static const u8 sText_PkmnPretendNotNotice[] = _("O {B_ATK_NAME_WITH_PREFIX} fingiu\nnão perceber!");
static const u8 sText_EnemyAboutToSwitchPkmn[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME} vai\nenviar o {B_BUFF2}.\p{B_PLAYER_NAME} vai trocar\nde Pokémon?");
static const u8 sText_PkmnLearnedMove2[] = _("O {B_ATK_NAME_WITH_PREFIX} aprendeu\n{B_BUFF1}!");
static const u8 sText_PlayerDefeatedLinkTrainerTrainer1[] = _("Você derrotou\n{B_TRAINER1_CLASS} {B_TRAINER1_NAME}!\p");
static const u8 sText_ThrewARock[] = _("{B_PLAYER_NAME} jogou uma Pedra\nno {B_OPPONENT_MON1_NAME}!");
static const u8 sText_ThrewSomeBait[] = _("{B_PLAYER_NAME} jogou uma Isca\npara o {B_OPPONENT_MON1_NAME}!");
static const u8 sText_PkmnWatchingCarefully[] = _("O {B_OPPONENT_MON1_NAME} está observando\natentamente!");
static const u8 sText_PkmnIsAngry[] = _("O {B_OPPONENT_MON1_NAME} está bravo!");
static const u8 sText_PkmnIsEating[] = _("O {B_OPPONENT_MON1_NAME} está comendo!");
static const u8 sText_OutOfSafariBalls[] = _("{PLAY_SE SE_DING_DONG}Locutor: Suas Bolas Safári\nacabaram! Fim de jogo!\p");
static const u8 sText_WildPkmnAppeared[] = _("Um {B_OPPONENT_MON1_NAME} selvagem apareceu!\p");
static const u8 sText_WildPkmnAppeared2[] = _("Um {B_OPPONENT_MON1_NAME} selvagem apareceu!\p");
static const u8 sText_WildPkmnAppearedPause[] = _("Um {B_OPPONENT_MON1_NAME} selvagem apareceu!{PAUSE 127}");
static const u8 sText_TwoWildPkmnAppeared[] = _("Um {B_OPPONENT_MON1_NAME} e um {B_OPPONENT_MON2_NAME}\nselvagens apareceram!\p");
static const u8 sText_GhostAppearedCantId[] = _("O Fantasma apareceu!\pDroga!\nNão dá para identificar o Fantasma!\p");
static const u8 sText_TheGhostAppeared[] = _("O Fantasma apareceu!\p");
static const u8 sText_SilphScopeUnveil[] = _("O Visor Silph revelou a\nidentidade do Fantasma!");
static const u8 sText_TheGhostWas[] = _("O Fantasma era um Marowak!\p\n");
static const u8 sText_Trainer1WantsToBattle[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME}\nquer batalhar!\p");
static const u8 sText_LinkTrainerWantsToBattle[] = _("{B_LINK_OPPONENT1_NAME}\nquer batalhar!");
static const u8 sText_TwoLinkTrainersWantToBattle[] = _("{B_LINK_OPPONENT1_NAME} e {B_LINK_OPPONENT2_NAME}\nquerem batalhar!");
static const u8 sText_Trainer1SentOutPkmn[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME} enviou\no {B_OPPONENT_MON1_NAME}!{PAUSE 60}");
static const u8 sText_Trainer1SentOutTwoPkmn[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME} enviou\no {B_OPPONENT_MON1_NAME} e o {B_OPPONENT_MON2_NAME}!{PAUSE 60}");
static const u8 sText_Trainer1SentOutPkmn2[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME} enviou\no {B_BUFF1}!");
static const u8 sText_LinkTrainerSentOutPkmn[] = _("{B_LINK_OPPONENT1_NAME} enviou\no {B_OPPONENT_MON1_NAME}!");
static const u8 sText_LinkTrainerSentOutTwoPkmn[] = _("{B_LINK_OPPONENT1_NAME} enviou\no {B_OPPONENT_MON1_NAME} e o {B_OPPONENT_MON2_NAME}!");
static const u8 sText_TwoLinkTrainersSentOutPkmn[] = _("{B_LINK_OPPONENT1_NAME} enviou o {B_LINK_OPPONENT_MON1_NAME}!\n{B_LINK_OPPONENT2_NAME} enviou o {B_LINK_OPPONENT_MON2_NAME}!");
static const u8 sText_LinkTrainerSentOutPkmn2[] = _("{B_LINK_OPPONENT1_NAME} enviou\no {B_BUFF1}!");
static const u8 sText_LinkTrainerMultiSentOutPkmn[] = _("{B_LINK_SCR_TRAINER_NAME} enviou\no {B_BUFF1}!");
static const u8 sText_GoPkmn[] = _("Vai, {B_PLAYER_MON1_NAME}!");
static const u8 sText_GoTwoPkmn[] = _("Vão, {B_PLAYER_MON1_NAME} e\n{B_PLAYER_MON2_NAME}!");
static const u8 sText_GoPkmn2[] = _("Vai, {B_BUFF1}!");
static const u8 sText_DoItPkmn[] = _("Vamos lá, {B_BUFF1}!");
static const u8 sText_GoForItPkmn[] = _("Força, {B_BUFF1}!");
static const u8 sText_YourFoesWeakGetEmPkmn[] = _("O oponente está fraco!\nAcabe com ele, {B_BUFF1}!");
static const u8 sText_LinkPartnerSentOutPkmnGoPkmn[] = _("{B_LINK_PARTNER_NAME} enviou o {B_LINK_PLAYER_MON2_NAME}!\nVai, {B_LINK_PLAYER_MON1_NAME}!");
static const u8 sText_PkmnThatsEnough[] = _("{B_BUFF1}, já chega!\nVolte!");
static const u8 sText_PkmnComeBack[] = _("{B_BUFF1}, volte!");
static const u8 sText_PkmnOkComeBack[] = _("{B_BUFF1}, tudo bem!\nVolte!");
const u8 sText_PkmnGoodComeBack[] = _("{B_BUFF1}, muito bem!\nVolte!");
static const u8 sText_Trainer1WithdrewPkmn[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME}\nrecolheu o {B_BUFF1}!");
static const u8 sText_LinkTrainer1WithdrewPkmn[] = _("{B_LINK_OPPONENT1_NAME} recolheu\no {B_BUFF1}!");
static const u8 sText_LinkTrainer2WithdrewPkmn[] = _("{B_LINK_SCR_TRAINER_NAME} recolheu\no {B_BUFF1}!");
static const u8 sText_WildPkmnPrefix[] = _(" selvagem"); // PT-BR: appended after the name, see HANDLE_NICKNAME_STRING_CASE
static const u8 sText_FoePkmnPrefix[] = _(" inimigo");
static const u8 sText_FoePkmnPrefix2[] = _("inimiga"); // PT-BR: "a equipe inimiga/aliada" ({B_*_PREFIX1..3})
static const u8 sText_AllyPkmnPrefix[] = _("aliada");
static const u8 sText_FoePkmnPrefix3[] = _("inimiga");
static const u8 sText_AllyPkmnPrefix2[] = _("aliada");
static const u8 sText_FoePkmnPrefix4[] = _("inimiga");
static const u8 sText_AllyPkmnPrefix3[] = _("aliada");
static const u8 sText_AttackerUsedX[] = _("O {B_ATK_NAME_WITH_PREFIX} usou\n{B_BUFF2}");
static const u8 sText_ExclamationMark[] = _("!");
static const u8 sText_ExclamationMark2[] = _("!");
static const u8 sText_ExclamationMark3[] = _("!");
static const u8 sText_ExclamationMark4[] = _("!");
static const u8 sText_ExclamationMark5[] = _("!");

static const u8 sText_HP2[] = _("os PS");
static const u8 sText_Attack2[] = _("o Ataque");
static const u8 sText_Defense2[] = _("a Defesa");
static const u8 sText_Speed[] = _("a Velocidade");
static const u8 sText_SpAtk2[] = _("o Atq. Esp.");
static const u8 sText_SpDef2[] = _("a Def. Esp.");
static const u8 sText_Accuracy[] = _("a precisão");
static const u8 sText_Evasiveness[] = _("a evasão");

const u8 *const gStatNamesTable[] = {
    sText_HP2,
    sText_Attack2,
    sText_Defense2,
    sText_Speed,
    sText_SpAtk2,
    sText_SpDef2,
    sText_Accuracy,
    sText_Evasiveness
};

static const u8 sText_PokeblockWasTooSpicy[] = _("era picante demais!"); //
static const u8 sText_PokeblockWasTooDry[] = _("era seca demais!");
static const u8 sText_PokeblockWasTooSweet[] = _("era doce demais!");
static const u8 sText_PokeblockWasTooBitter[] = _("era amarga demais!");
static const u8 sText_PokeblockWasTooSour[] = _("era azeda demais!");

const u8 *const gPokeblockWasTooXStringTable[] = {
    sText_PokeblockWasTooSpicy,
    sText_PokeblockWasTooDry,
    sText_PokeblockWasTooSweet,
    sText_PokeblockWasTooBitter,
    sText_PokeblockWasTooSour
};

static const u8 sText_PlayerUsedItem[] = _("{B_PLAYER_NAME} usou\n{B_LAST_ITEM}!");
static const u8 sText_OldManUsedItem[] = _("O velho usou\n{B_LAST_ITEM}!");
static const u8 sText_PokedudeUsedItem[] = _("O Cara Pokémon usou\n{B_LAST_ITEM}!");
static const u8 sText_Trainer1UsedItem[] = _("{B_TRAINER1_CLASS} {B_TRAINER1_NAME}\nusou {B_LAST_ITEM}!");
static const u8 sText_TrainerBlockedBall[] = _("O Treinador bloqueou a Bola!");
static const u8 sText_DontBeAThief[] = _("Roubar é feio!");
static const u8 sText_ItDodgedBall[] = _("Ele se esquivou da Bola!\nEste Pokémon não pode ser pego!");
static const u8 sText_YouMissedPkmn[] = _("Você errou o Pokémon!");
static const u8 sText_PkmnBrokeFree[] = _("Ah, não!\nO Pokémon escapou!");
static const u8 sText_ItAppearedCaught[] = _("Ahh!\nParecia que tinha pegado!");
static const u8 sText_AarghAlmostHadIt[] = _("Argh!\nFoi por pouco!");
static const u8 sText_ShootSoClose[] = _("Droga!\nFaltou tão pouco!");
static const u8 sText_ItDodgedBall2[] = _("よけられた!\nこいつは つかまりそうにないぞ!"); // Unused version of the Marowak ghost dodging text
static const u8 sText_GotchaPkmnCaught[] = _("Peguei!\nO {B_OPPONENT_MON1_NAME} foi capturado!{WAIT_SE}{PLAY_BGM MUS_CAUGHT}\p");
static const u8 sText_GotchaPkmnCaught2[] = _("Peguei!\nO {B_OPPONENT_MON1_NAME} foi capturado!{WAIT_SE}{PLAY_BGM MUS_CAUGHT}{PAUSE 127}");
static const u8 sText_GiveNicknameCaptured[] = _("Dar um apelido ao\n{B_OPPONENT_MON1_NAME} capturado?");
static const u8 sText_PkmnSentToPC[] = _("O {B_OPPONENT_MON1_NAME} foi enviado\nao PC {B_PC_CREATOR_NAME}.");
static const u8 sText_Someones[] = _("de alguém");
static const u8 sText_Bills[] = _("do Bill");
static const u8 sText_PkmnDataAddedToDex[] = _("Os dados do {B_OPPONENT_MON1_NAME} foram\nadicionados à Pokédex.\p");
static const u8 sText_ItIsRaining[] = _("Está chovendo."); // used only in RSE when a battle starts in a rainy area
static const u8 sText_SandstormIsRaging[] = _("Há uma tempestade de areia.");
static const u8 sText_BoxIsFull[] = _("A Caixa está cheia!\nNão dá para capturar mais!\p");
static const u8 sText_EnigmaBerry[] = _("Fruta Enigma");
static const u8 sText_BerryPrefix[] = _("Fruta "); // PT-BR: "Fruta" + berry name, like the item names
static const u8 sText_Enigma[] = _("ナゾ");
static const u8 sText_PkmnsItemCuredParalysis[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou a paralisia!");
static const u8 sText_PkmnsItemCuredPoison[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou o envenenamento!");
static const u8 sText_PkmnsItemHealedBurn[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou a queimadura!");
static const u8 sText_PkmnsItemDefrostedIt[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\no descongelou!");
static const u8 sText_PkmnsItemWokeIt[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\no acordou!");
static const u8 sText_PkmnsItemSnappedOut[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\no tirou da confusão!");
static const u8 sText_PkmnsItemCuredProblem[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\ncurou {B_BUFF1}!");
static const u8 sText_PkmnsItemNormalizedStatus[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nnormalizou seu status!");
static const u8 sText_PkmnsItemRestoredHealth[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nrestaurou os PS!");
static const u8 sText_PkmnsItemRestoredPP[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nrestaurou o PP de {B_BUFF1}!");
static const u8 sText_PkmnsItemRestoredStatus[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nrestaurou seu status!");
static const u8 sText_PkmnsItemRestoredHPALittle[] = _("{B_LAST_ITEM} do {B_SCR_ACTIVE_NAME_WITH_PREFIX}\nrestaurou um pouco de PS!");
static const u8 sText_ItemAllowsOnlyYMove[] = _("O efeito de {B_LAST_ITEM} só permite\nusar {B_CURRENT_MOVE}!\p");
static const u8 sText_PkmnHungOnWithX[] = _("O {B_DEF_NAME_WITH_PREFIX} aguentou\nfirme com {B_LAST_ITEM}!");
const u8 gText_EmptyString3[] = _("");
static const u8 sText_PlayedFluteCatchyTune[] = _("{B_PLAYER_NAME} tocou a {B_LAST_ITEM}.\pQue melodia contagiante!");
static const u8 sText_PlayedThe[] = _("{B_PLAYER_NAME} tocou a\n{B_LAST_ITEM}.");
static const u8 sText_PkmnHearingFluteAwoke[] = _("Os Pokémon que ouviram a Flauta\nacordaram!");
static const u8 sText_YouThrowABallNowRight[] = _("Agora você joga uma Bola, né?\nEu… Eu vou dar o meu melhor!");
const u8 gText_ForPetesSake[] = _("Carvalho: Ah, francamente…\nAfobado como sempre.\p{B_PLAYER_NAME}.\pVocê nunca teve uma batalha\nPokémon antes, não é?\pNuma batalha Pokémon, os Treinadores\ncolocam seus Pokémon para lutar\luns contra os outros.\p");
const u8 gText_TheTrainerThat[] = _("Vence o Treinador que fizer os\nPokémon do outro Treinador\ldesmaiarem, zerando os PS deles.\p");
const u8 gText_TryBattling[] = _("Mas, em vez de falar sobre isso,\nvocê vai aprender mais na prática.\pBatalhe e veja como é.\p");
const u8 gText_InflictingDamageIsKey[] = _("Carvalho: Causar dano ao oponente\né a chave de qualquer batalha.\p");
const u8 gText_LoweringStats[] = _("Carvalho: Diminuir os atributos\ndo oponente te dá vantagem.\p");
const u8 gText_KeepAnEyeOnHP[] = _("Carvalho: Fique de olho nos PS\ndo seu Pokémon.\pEle desmaia se os PS\nchegarem a “0”.\p");
const u8 gText_OakNoRunningFromATrainer[] = _("Carvalho: Não! Não se foge de uma\nbatalha contra um Treinador!\p");
const u8 gText_WinEarnsPrizeMoney[] = _("Carvalho: Hum! Excelente!\pSe você vencer, ganha dinheiro\ne seus Pokémon ficam mais fortes!\pBatalhe com outros Treinadores e\ndeixe seus Pokémon fortes!\p");
const u8 gText_HowDissapointing[] = _("Carvalho: Hum…\nQue decepção…\pQuem vence ganha dinheiro,\ne seus Pokémon crescem.\pMas quem perde, {B_PLAYER_NAME},\npaga o prêmio…\pComo ninguém te avisou,\ndesta vez eu pago.\pMas lá fora não vai ser assim.\pPor isso, fortaleça seus Pokémon\nem batalhas com Pokémon selvagens.\p");

const u8 *const gBattleStringsTable[BATTLESTRINGS_COUNT - BATTLESTRINGS_TABLE_START] = {
    [STRINGID_TRAINER1LOSETEXT - BATTLESTRINGS_TABLE_START]              = sText_Trainer1LoseText,
    [STRINGID_PKMNGAINEDEXP - BATTLESTRINGS_TABLE_START]                 = sText_PkmnGainedEXP,
    [STRINGID_PKMNGREWTOLV - BATTLESTRINGS_TABLE_START]                  = sText_PkmnGrewToLv,
    [STRINGID_PKMNLEARNEDMOVE - BATTLESTRINGS_TABLE_START]               = sText_PkmnLearnedMove,
    [STRINGID_TRYTOLEARNMOVE1 - BATTLESTRINGS_TABLE_START]               = sText_TryToLearnMove1,
    [STRINGID_TRYTOLEARNMOVE2 - BATTLESTRINGS_TABLE_START]               = sText_TryToLearnMove2,
    [STRINGID_TRYTOLEARNMOVE3 - BATTLESTRINGS_TABLE_START]               = sText_TryToLearnMove3,
    [STRINGID_PKMNFORGOTMOVE - BATTLESTRINGS_TABLE_START]                = sText_PkmnForgotMove,
    [STRINGID_STOPLEARNINGMOVE - BATTLESTRINGS_TABLE_START]              = sText_StopLearningMove,
    [STRINGID_DIDNOTLEARNMOVE - BATTLESTRINGS_TABLE_START]               = sText_DidNotLearnMove,
    [STRINGID_PKMNLEARNEDMOVE2 - BATTLESTRINGS_TABLE_START]              = sText_PkmnLearnedMove2,
    [STRINGID_ATTACKMISSED - BATTLESTRINGS_TABLE_START]                  = sText_AttackMissed,
    [STRINGID_PKMNPROTECTEDITSELF - BATTLESTRINGS_TABLE_START]           = sText_PkmnProtectedItself,
    [STRINGID_STATSWONTINCREASE2 - BATTLESTRINGS_TABLE_START]            = sText_StatsWontIncrease2,
    [STRINGID_AVOIDEDDAMAGE - BATTLESTRINGS_TABLE_START]                 = sText_AvoidedDamage,
    [STRINGID_ITDOESNTAFFECT - BATTLESTRINGS_TABLE_START]                = sText_ItDoesntAffect,
    [STRINGID_ATTACKERFAINTED - BATTLESTRINGS_TABLE_START]               = sText_AttackerFainted,
    [STRINGID_TARGETFAINTED - BATTLESTRINGS_TABLE_START]                 = sText_TargetFainted,
    [STRINGID_PLAYERGOTMONEY - BATTLESTRINGS_TABLE_START]                = sText_PlayerGotMoney,
    [STRINGID_PLAYERWHITEOUT - BATTLESTRINGS_TABLE_START]                = sText_PlayerWhiteout,
    [STRINGID_PLAYERWHITEOUT2 - BATTLESTRINGS_TABLE_START]               = sText_PlayerPanicked,
    [STRINGID_PREVENTSESCAPE - BATTLESTRINGS_TABLE_START]                = sText_PreventsEscape,
    [STRINGID_HITXTIMES - BATTLESTRINGS_TABLE_START]                     = sText_HitXTimes,
    [STRINGID_PKMNFELLASLEEP - BATTLESTRINGS_TABLE_START]                = sText_PkmnFellAsleep,
    [STRINGID_PKMNMADESLEEP - BATTLESTRINGS_TABLE_START]                 = sText_PkmnMadeSleep,
    [STRINGID_PKMNALREADYASLEEP - BATTLESTRINGS_TABLE_START]             = sText_PkmnAlreadyAsleep,
    [STRINGID_PKMNALREADYASLEEP2 - BATTLESTRINGS_TABLE_START]            = sText_PkmnAlreadyAsleep2,
    [STRINGID_PKMNWASNTAFFECTED - BATTLESTRINGS_TABLE_START]             = sText_PkmnWasntAffected,
    [STRINGID_PKMNWASPOISONED - BATTLESTRINGS_TABLE_START]               = sText_PkmnWasPoisoned,
    [STRINGID_PKMNPOISONEDBY - BATTLESTRINGS_TABLE_START]                = sText_PkmnPoisonedBy,
    [STRINGID_PKMNHURTBYPOISON - BATTLESTRINGS_TABLE_START]              = sText_PkmnHurtByPoison,
    [STRINGID_PKMNALREADYPOISONED - BATTLESTRINGS_TABLE_START]           = sText_PkmnAlreadyPoisoned,
    [STRINGID_PKMNBADLYPOISONED - BATTLESTRINGS_TABLE_START]             = sText_PkmnBadlyPoisoned,
    [STRINGID_PKMNENERGYDRAINED - BATTLESTRINGS_TABLE_START]             = sText_PkmnEnergyDrained,
    [STRINGID_PKMNWASBURNED - BATTLESTRINGS_TABLE_START]                 = sText_PkmnWasBurned,
    [STRINGID_PKMNBURNEDBY - BATTLESTRINGS_TABLE_START]                  = sText_PkmnBurnedBy,
    [STRINGID_PKMNHURTBYBURN - BATTLESTRINGS_TABLE_START]                = sText_PkmnHurtByBurn,
    [STRINGID_PKMNWASFROZEN - BATTLESTRINGS_TABLE_START]                 = sText_PkmnWasFrozen,
    [STRINGID_PKMNFROZENBY - BATTLESTRINGS_TABLE_START]                  = sText_PkmnFrozenBy,
    [STRINGID_PKMNISFROZEN - BATTLESTRINGS_TABLE_START]                  = sText_PkmnIsFrozen,
    [STRINGID_PKMNWASDEFROSTED - BATTLESTRINGS_TABLE_START]              = sText_PkmnWasDefrosted,
    [STRINGID_PKMNWASDEFROSTED2 - BATTLESTRINGS_TABLE_START]             = sText_PkmnWasDefrosted2,
    [STRINGID_PKMNWASDEFROSTEDBY - BATTLESTRINGS_TABLE_START]            = sText_PkmnWasDefrostedBy,
    [STRINGID_PKMNWASPARALYZED - BATTLESTRINGS_TABLE_START]              = sText_PkmnWasParalyzed,
    [STRINGID_PKMNWASPARALYZEDBY - BATTLESTRINGS_TABLE_START]            = sText_PkmnWasParalyzedBy,
    [STRINGID_PKMNISPARALYZED - BATTLESTRINGS_TABLE_START]               = sText_PkmnIsParalyzed,
    [STRINGID_PKMNISALREADYPARALYZED - BATTLESTRINGS_TABLE_START]        = sText_PkmnIsAlreadyParalyzed,
    [STRINGID_PKMNHEALEDPARALYSIS - BATTLESTRINGS_TABLE_START]           = sText_PkmnHealedParalysis,
    [STRINGID_PKMNDREAMEATEN - BATTLESTRINGS_TABLE_START]                = sText_PkmnDreamEaten,
    [STRINGID_STATSWONTINCREASE - BATTLESTRINGS_TABLE_START]             = sText_StatsWontIncrease,
    [STRINGID_STATSWONTDECREASE - BATTLESTRINGS_TABLE_START]             = sText_StatsWontDecrease,
    [STRINGID_TEAMSTOPPEDWORKING - BATTLESTRINGS_TABLE_START]            = sText_TeamStoppedWorking,
    [STRINGID_FOESTOPPEDWORKING - BATTLESTRINGS_TABLE_START]             = sText_FoeStoppedWorking,
    [STRINGID_PKMNISCONFUSED - BATTLESTRINGS_TABLE_START]                = sText_PkmnIsConfused,
    [STRINGID_PKMNHEALEDCONFUSION - BATTLESTRINGS_TABLE_START]           = sText_PkmnHealedConfusion,
    [STRINGID_PKMNWASCONFUSED - BATTLESTRINGS_TABLE_START]               = sText_PkmnWasConfused,
    [STRINGID_PKMNALREADYCONFUSED - BATTLESTRINGS_TABLE_START]           = sText_PkmnAlreadyConfused,
    [STRINGID_PKMNFELLINLOVE - BATTLESTRINGS_TABLE_START]                = sText_PkmnFellInLove,
    [STRINGID_PKMNINLOVE - BATTLESTRINGS_TABLE_START]                    = sText_PkmnInLove,
    [STRINGID_PKMNIMMOBILIZEDBYLOVE - BATTLESTRINGS_TABLE_START]         = sText_PkmnImmobilizedByLove,
    [STRINGID_PKMNBLOWNAWAY - BATTLESTRINGS_TABLE_START]                 = sText_PkmnBlownAway,
    [STRINGID_PKMNCHANGEDTYPE - BATTLESTRINGS_TABLE_START]               = sText_PkmnChangedType,
    [STRINGID_PKMNFLINCHED - BATTLESTRINGS_TABLE_START]                  = sText_PkmnFlinched,
    [STRINGID_PKMNREGAINEDHEALTH - BATTLESTRINGS_TABLE_START]            = sText_PkmnRegainedHealth,
    [STRINGID_PKMNHPFULL - BATTLESTRINGS_TABLE_START]                    = sText_PkmnHPFull,
    [STRINGID_PKMNRAISEDSPDEF - BATTLESTRINGS_TABLE_START]               = sText_PkmnRaisedSpDef,
    [STRINGID_PKMNRAISEDDEF - BATTLESTRINGS_TABLE_START]                 = sText_PkmnRaisedDef,
    [STRINGID_PKMNCOVEREDBYVEIL - BATTLESTRINGS_TABLE_START]             = sText_PkmnCoveredByVeil,
    [STRINGID_PKMNUSEDSAFEGUARD - BATTLESTRINGS_TABLE_START]             = sText_PkmnUsedSafeguard,
    [STRINGID_PKMNSAFEGUARDEXPIRED - BATTLESTRINGS_TABLE_START]          = sText_PkmnSafeguardExpired,
    [STRINGID_PKMNWENTTOSLEEP - BATTLESTRINGS_TABLE_START]               = sText_PkmnWentToSleep,
    [STRINGID_PKMNSLEPTHEALTHY - BATTLESTRINGS_TABLE_START]              = sText_PkmnSleptHealthy,
    [STRINGID_PKMNWHIPPEDWHIRLWIND - BATTLESTRINGS_TABLE_START]          = sText_PkmnWhippedWhirlwind,
    [STRINGID_PKMNTOOKSUNLIGHT - BATTLESTRINGS_TABLE_START]              = sText_PkmnTookSunlight,
    [STRINGID_PKMNLOWEREDHEAD - BATTLESTRINGS_TABLE_START]               = sText_PkmnLoweredHead,
    [STRINGID_PKMNISGLOWING - BATTLESTRINGS_TABLE_START]                 = sText_PkmnIsGlowing,
    [STRINGID_PKMNFLEWHIGH - BATTLESTRINGS_TABLE_START]                  = sText_PkmnFlewHigh,
    [STRINGID_PKMNDUGHOLE - BATTLESTRINGS_TABLE_START]                   = sText_PkmnDugHole,
    [STRINGID_PKMNSQUEEZEDBYBIND - BATTLESTRINGS_TABLE_START]            = sText_PkmnSqueezedByBind,
    [STRINGID_PKMNTRAPPEDINVORTEX - BATTLESTRINGS_TABLE_START]           = sText_PkmnTrappedInVortex,
    [STRINGID_PKMNWRAPPEDBY - BATTLESTRINGS_TABLE_START]                 = sText_PkmnWrappedBy,
    [STRINGID_PKMNCLAMPED - BATTLESTRINGS_TABLE_START]                   = sText_PkmnClamped,
    [STRINGID_PKMNHURTBY - BATTLESTRINGS_TABLE_START]                    = sText_PkmnHurtBy,
    [STRINGID_PKMNFREEDFROM - BATTLESTRINGS_TABLE_START]                 = sText_PkmnFreedFrom,
    [STRINGID_PKMNCRASHED - BATTLESTRINGS_TABLE_START]                   = sText_PkmnCrashed,
    [STRINGID_PKMNSHROUDEDINMIST - BATTLESTRINGS_TABLE_START]            = gBattleText_MistShroud,
    [STRINGID_PKMNPROTECTEDBYMIST - BATTLESTRINGS_TABLE_START]           = sText_PkmnProtectedByMist,
    [STRINGID_PKMNGETTINGPUMPED - BATTLESTRINGS_TABLE_START]             = gBattleText_GetPumped,
    [STRINGID_PKMNHITWITHRECOIL - BATTLESTRINGS_TABLE_START]             = sText_PkmnHitWithRecoil,
    [STRINGID_PKMNPROTECTEDITSELF2 - BATTLESTRINGS_TABLE_START]          = sText_PkmnProtectedItself2,
    [STRINGID_PKMNBUFFETEDBYSANDSTORM - BATTLESTRINGS_TABLE_START]       = sText_PkmnBuffetedBySandstorm,
    [STRINGID_PKMNPELTEDBYHAIL - BATTLESTRINGS_TABLE_START]              = sText_PkmnPeltedByHail,
    [STRINGID_PKMNSEEDED - BATTLESTRINGS_TABLE_START]                    = sText_PkmnSeeded,
    [STRINGID_PKMNEVADEDATTACK - BATTLESTRINGS_TABLE_START]              = sText_PkmnEvadedAttack,
    [STRINGID_PKMNSAPPEDBYLEECHSEED - BATTLESTRINGS_TABLE_START]         = sText_PkmnSappedByLeechSeed,
    [STRINGID_PKMNFASTASLEEP - BATTLESTRINGS_TABLE_START]                = sText_PkmnFastAsleep,
    [STRINGID_PKMNWOKEUP - BATTLESTRINGS_TABLE_START]                    = sText_PkmnWokeUp,
    [STRINGID_PKMNUPROARKEPTAWAKE - BATTLESTRINGS_TABLE_START]           = sText_PkmnUproarKeptAwake,
    [STRINGID_PKMNWOKEUPINUPROAR - BATTLESTRINGS_TABLE_START]            = sText_PkmnWokeUpInUproar,
    [STRINGID_PKMNCAUSEDUPROAR - BATTLESTRINGS_TABLE_START]              = sText_PkmnCausedUproar,
    [STRINGID_PKMNMAKINGUPROAR - BATTLESTRINGS_TABLE_START]              = sText_PkmnMakingUproar,
    [STRINGID_PKMNCALMEDDOWN - BATTLESTRINGS_TABLE_START]                = sText_PkmnCalmedDown,
    [STRINGID_PKMNCANTSLEEPINUPROAR - BATTLESTRINGS_TABLE_START]         = sText_PkmnCantSleepInUproar,
    [STRINGID_PKMNSTOCKPILED - BATTLESTRINGS_TABLE_START]                = sText_PkmnStockpiled,
    [STRINGID_PKMNCANTSTOCKPILE - BATTLESTRINGS_TABLE_START]             = sText_PkmnCantStockpile,
    [STRINGID_PKMNCANTSLEEPINUPROAR2 - BATTLESTRINGS_TABLE_START]        = sText_PkmnCantSleepInUproar2,
    [STRINGID_UPROARKEPTPKMNAWAKE - BATTLESTRINGS_TABLE_START]           = sText_UproarKeptPkmnAwake,
    [STRINGID_PKMNSTAYEDAWAKEUSING - BATTLESTRINGS_TABLE_START]          = sText_PkmnStayedAwakeUsing,
    [STRINGID_PKMNSTORINGENERGY - BATTLESTRINGS_TABLE_START]             = sText_PkmnStoringEnergy,
    [STRINGID_PKMNUNLEASHEDENERGY - BATTLESTRINGS_TABLE_START]           = sText_PkmnUnleashedEnergy,
    [STRINGID_PKMNFATIGUECONFUSION - BATTLESTRINGS_TABLE_START]          = sText_PkmnFatigueConfusion,
    [STRINGID_PLAYERPICKEDUPMONEY - BATTLESTRINGS_TABLE_START]           = sText_PkmnPickedUpItem,
    [STRINGID_PKMNUNAFFECTED - BATTLESTRINGS_TABLE_START]                = sText_PkmnUnaffected,
    [STRINGID_PKMNTRANSFORMEDINTO - BATTLESTRINGS_TABLE_START]           = sText_PkmnTransformedInto,
    [STRINGID_PKMNMADESUBSTITUTE - BATTLESTRINGS_TABLE_START]            = sText_PkmnMadeSubstitute,
    [STRINGID_PKMNHASSUBSTITUTE - BATTLESTRINGS_TABLE_START]             = sText_PkmnHasSubstitute,
    [STRINGID_SUBSTITUTEDAMAGED - BATTLESTRINGS_TABLE_START]             = sText_SubstituteDamaged,
    [STRINGID_PKMNSUBSTITUTEFADED - BATTLESTRINGS_TABLE_START]           = sText_PkmnSubstituteFaded,
    [STRINGID_PKMNMUSTRECHARGE - BATTLESTRINGS_TABLE_START]              = sText_PkmnMustRecharge,
    [STRINGID_PKMNRAGEBUILDING - BATTLESTRINGS_TABLE_START]              = sText_PkmnRageBuilding,
    [STRINGID_PKMNMOVEWASDISABLED - BATTLESTRINGS_TABLE_START]           = sText_PkmnMoveWasDisabled,
    [STRINGID_PKMNMOVEISDISABLED - BATTLESTRINGS_TABLE_START]            = sText_PkmnMoveIsDisabled,
    [STRINGID_PKMNMOVEDISABLEDNOMORE - BATTLESTRINGS_TABLE_START]        = sText_PkmnMoveDisabledNoMore,
    [STRINGID_PKMNGOTENCORE - BATTLESTRINGS_TABLE_START]                 = sText_PkmnGotEncore,
    [STRINGID_PKMNENCOREENDED - BATTLESTRINGS_TABLE_START]               = sText_PkmnEncoreEnded,
    [STRINGID_PKMNTOOKAIM - BATTLESTRINGS_TABLE_START]                   = sText_PkmnTookAim,
    [STRINGID_PKMNSKETCHEDMOVE - BATTLESTRINGS_TABLE_START]              = sText_PkmnSketchedMove,
    [STRINGID_PKMNTRYINGTOTAKEFOE - BATTLESTRINGS_TABLE_START]           = sText_PkmnTryingToTakeFoe,
    [STRINGID_PKMNTOOKFOE - BATTLESTRINGS_TABLE_START]                   = sText_PkmnTookFoe,
    [STRINGID_PKMNREDUCEDPP - BATTLESTRINGS_TABLE_START]                 = sText_PkmnReducedPP,
    [STRINGID_PKMNSTOLEITEM - BATTLESTRINGS_TABLE_START]                 = sText_PkmnStoleItem,
    [STRINGID_TARGETCANTESCAPENOW - BATTLESTRINGS_TABLE_START]           = sText_TargetCantEscapeNow,
    [STRINGID_PKMNFELLINTONIGHTMARE - BATTLESTRINGS_TABLE_START]         = sText_PkmnFellIntoNightmare,
    [STRINGID_PKMNLOCKEDINNIGHTMARE - BATTLESTRINGS_TABLE_START]         = sText_PkmnLockedInNightmare,
    [STRINGID_PKMNLAIDCURSE - BATTLESTRINGS_TABLE_START]                 = sText_PkmnLaidCurse,
    [STRINGID_PKMNAFFLICTEDBYCURSE - BATTLESTRINGS_TABLE_START]          = sText_PkmnAfflictedByCurse,
    [STRINGID_SPIKESSCATTERED - BATTLESTRINGS_TABLE_START]               = sText_SpikesScattered,
    [STRINGID_PKMNHURTBYSPIKES - BATTLESTRINGS_TABLE_START]              = sText_PkmnHurtBySpikes,
    [STRINGID_PKMNIDENTIFIED - BATTLESTRINGS_TABLE_START]                = sText_PkmnIdentified,
    [STRINGID_PKMNPERISHCOUNTFELL - BATTLESTRINGS_TABLE_START]           = sText_PkmnPerishCountFell,
    [STRINGID_PKMNBRACEDITSELF - BATTLESTRINGS_TABLE_START]              = sText_PkmnBracedItself,
    [STRINGID_PKMNENDUREDHIT - BATTLESTRINGS_TABLE_START]                = sText_PkmnEnduredHit,
    [STRINGID_MAGNITUDESTRENGTH - BATTLESTRINGS_TABLE_START]             = sText_MagnitudeStrength,
    [STRINGID_PKMNCUTHPMAXEDATTACK - BATTLESTRINGS_TABLE_START]          = sText_PkmnCutHPMaxedAttack,
    [STRINGID_PKMNCOPIEDSTATCHANGES - BATTLESTRINGS_TABLE_START]         = sText_PkmnCopiedStatChanges,
    [STRINGID_PKMNGOTFREE - BATTLESTRINGS_TABLE_START]                   = sText_PkmnGotFree,
    [STRINGID_PKMNSHEDLEECHSEED - BATTLESTRINGS_TABLE_START]             = sText_PkmnShedLeechSeed,
    [STRINGID_PKMNBLEWAWAYSPIKES - BATTLESTRINGS_TABLE_START]            = sText_PkmnBlewAwaySpikes,
    [STRINGID_PKMNFLEDFROMBATTLE - BATTLESTRINGS_TABLE_START]            = sText_PkmnFledFromBattle,
    [STRINGID_PKMNFORESAWATTACK - BATTLESTRINGS_TABLE_START]             = sText_PkmnForesawAttack,
    [STRINGID_PKMNTOOKATTACK - BATTLESTRINGS_TABLE_START]                = sText_PkmnTookAttack,
    [STRINGID_PKMNATTACK - BATTLESTRINGS_TABLE_START]                    = sText_PkmnAttack,
    [STRINGID_PKMNCENTERATTENTION - BATTLESTRINGS_TABLE_START]           = sText_PkmnCenterAttention,
    [STRINGID_PKMNCHARGINGPOWER - BATTLESTRINGS_TABLE_START]             = sText_PkmnChargingPower,
    [STRINGID_NATUREPOWERTURNEDINTO - BATTLESTRINGS_TABLE_START]         = sText_NaturePowerTurnedInto,
    [STRINGID_PKMNSTATUSNORMAL - BATTLESTRINGS_TABLE_START]              = sText_PkmnStatusNormal,
    [STRINGID_PKMNHASNOMOVESLEFT - BATTLESTRINGS_TABLE_START]            = sText_PkmnHasNoMovesLeft,
    [STRINGID_PKMNSUBJECTEDTOTORMENT - BATTLESTRINGS_TABLE_START]        = sText_PkmnSubjectedToTorment,
    [STRINGID_PKMNCANTUSEMOVETORMENT - BATTLESTRINGS_TABLE_START]        = sText_PkmnCantUseMoveTorment,
    [STRINGID_PKMNTIGHTENINGFOCUS - BATTLESTRINGS_TABLE_START]           = sText_PkmnTighteningFocus,
    [STRINGID_PKMNFELLFORTAUNT - BATTLESTRINGS_TABLE_START]              = sText_PkmnFellForTaunt,
    [STRINGID_PKMNCANTUSEMOVETAUNT - BATTLESTRINGS_TABLE_START]          = sText_PkmnCantUseMoveTaunt,
    [STRINGID_PKMNREADYTOHELP - BATTLESTRINGS_TABLE_START]               = sText_PkmnReadyToHelp,
    [STRINGID_PKMNSWITCHEDITEMS - BATTLESTRINGS_TABLE_START]             = sText_PkmnSwitchedItems,
    [STRINGID_PKMNCOPIEDFOE - BATTLESTRINGS_TABLE_START]                 = sText_PkmnCopiedFoe,
    [STRINGID_PKMNMADEWISH - BATTLESTRINGS_TABLE_START]                  = sText_PkmnMadeWish,
    [STRINGID_PKMNWISHCAMETRUE - BATTLESTRINGS_TABLE_START]              = sText_PkmnWishCameTrue,
    [STRINGID_PKMNPLANTEDROOTS - BATTLESTRINGS_TABLE_START]              = sText_PkmnPlantedRoots,
    [STRINGID_PKMNABSORBEDNUTRIENTS - BATTLESTRINGS_TABLE_START]         = sText_PkmnAbsorbedNutrients,
    [STRINGID_PKMNANCHOREDITSELF - BATTLESTRINGS_TABLE_START]            = sText_PkmnAnchoredItself,
    [STRINGID_PKMNWASMADEDROWSY - BATTLESTRINGS_TABLE_START]             = sText_PkmnWasMadeDrowsy,
    [STRINGID_PKMNKNOCKEDOFF - BATTLESTRINGS_TABLE_START]                = sText_PkmnKnockedOff,
    [STRINGID_PKMNSWAPPEDABILITIES - BATTLESTRINGS_TABLE_START]          = sText_PkmnSwappedAbilities,
    [STRINGID_PKMNSEALEDOPPONENTMOVE - BATTLESTRINGS_TABLE_START]        = sText_PkmnSealedOpponentMove,
    [STRINGID_PKMNCANTUSEMOVESEALED - BATTLESTRINGS_TABLE_START]         = sText_PkmnCantUseMoveSealed,
    [STRINGID_PKMNWANTSGRUDGE - BATTLESTRINGS_TABLE_START]               = sText_PkmnWantsGrudge,
    [STRINGID_PKMNLOSTPPGRUDGE - BATTLESTRINGS_TABLE_START]              = sText_PkmnLostPPGrudge,
    [STRINGID_PKMNSHROUDEDITSELF - BATTLESTRINGS_TABLE_START]            = sText_PkmnShroudedItself,
    [STRINGID_PKMNMOVEBOUNCED - BATTLESTRINGS_TABLE_START]               = sText_PkmnMoveBounced,
    [STRINGID_PKMNWAITSFORTARGET - BATTLESTRINGS_TABLE_START]            = sText_PkmnWaitsForTarget,
    [STRINGID_PKMNSNATCHEDMOVE - BATTLESTRINGS_TABLE_START]              = sText_PkmnSnatchedMove,
    [STRINGID_PKMNMADEITRAIN - BATTLESTRINGS_TABLE_START]                = sText_PkmnMadeItRain,
    [STRINGID_PKMNRAISEDSPEED - BATTLESTRINGS_TABLE_START]               = sText_PkmnRaisedSpeed,
    [STRINGID_PKMNPROTECTEDBY - BATTLESTRINGS_TABLE_START]               = sText_PkmnProtectedBy,
    [STRINGID_PKMNPREVENTSUSAGE - BATTLESTRINGS_TABLE_START]             = sText_PkmnPreventsUsage,
    [STRINGID_PKMNRESTOREDHPUSING - BATTLESTRINGS_TABLE_START]           = sText_PkmnRestoredHPUsing,
    [STRINGID_PKMNCHANGEDTYPEWITH - BATTLESTRINGS_TABLE_START]           = sText_PkmnChangedTypeWith,
    [STRINGID_PKMNPREVENTSPARALYSISWITH - BATTLESTRINGS_TABLE_START]     = sText_PkmnPreventsParalysisWith,
    [STRINGID_PKMNPREVENTSROMANCEWITH - BATTLESTRINGS_TABLE_START]       = sText_PkmnPreventsRomanceWith,
    [STRINGID_PKMNPREVENTSPOISONINGWITH - BATTLESTRINGS_TABLE_START]     = sText_PkmnPreventsPoisoningWith,
    [STRINGID_PKMNPREVENTSCONFUSIONWITH - BATTLESTRINGS_TABLE_START]     = sText_PkmnPreventsConfusionWith,
    [STRINGID_PKMNRAISEDFIREPOWERWITH - BATTLESTRINGS_TABLE_START]       = sText_PkmnRaisedFirePowerWith,
    [STRINGID_PKMNANCHORSITSELFWITH - BATTLESTRINGS_TABLE_START]         = sText_PkmnAnchorsItselfWith,
    [STRINGID_PKMNCUTSATTACKWITH - BATTLESTRINGS_TABLE_START]            = sText_PkmnCutsAttackWith,
    [STRINGID_PKMNPREVENTSSTATLOSSWITH - BATTLESTRINGS_TABLE_START]      = sText_PkmnPreventsStatLossWith,
    [STRINGID_PKMNHURTSWITH - BATTLESTRINGS_TABLE_START]                 = sText_PkmnHurtsWith,
    [STRINGID_PKMNTRACED - BATTLESTRINGS_TABLE_START]                    = sText_PkmnTraced,
    [STRINGID_STATSHARPLY - BATTLESTRINGS_TABLE_START]                   = sText_StatSharply,
    [STRINGID_STATROSE - BATTLESTRINGS_TABLE_START]                      = gBattleText_Rose,
    [STRINGID_STATHARSHLY - BATTLESTRINGS_TABLE_START]                   = sText_StatHarshly,
    [STRINGID_STATFELL - BATTLESTRINGS_TABLE_START]                      = sText_StatFell,
    [STRINGID_ATTACKERSSTATROSE - BATTLESTRINGS_TABLE_START]             = sText_AttackersStatRose,
    [STRINGID_DEFENDERSSTATROSE - BATTLESTRINGS_TABLE_START]             = gText_DefendersStatRose,
    [STRINGID_ATTACKERSSTATFELL - BATTLESTRINGS_TABLE_START]             = sText_AttackersStatFell,
    [STRINGID_DEFENDERSSTATFELL - BATTLESTRINGS_TABLE_START]             = sText_DefendersStatFell,
    [STRINGID_CRITICALHIT - BATTLESTRINGS_TABLE_START]                   = sText_CriticalHit,
    [STRINGID_ONEHITKO - BATTLESTRINGS_TABLE_START]                      = sText_OneHitKO,
    [STRINGID_123POOF - BATTLESTRINGS_TABLE_START]                       = sText_123Poof,
    [STRINGID_ANDELLIPSIS - BATTLESTRINGS_TABLE_START]                   = sText_AndEllipsis,
    [STRINGID_NOTVERYEFFECTIVE - BATTLESTRINGS_TABLE_START]              = sText_NotVeryEffective,
    [STRINGID_SUPEREFFECTIVE - BATTLESTRINGS_TABLE_START]                = sText_SuperEffective,
    [STRINGID_GOTAWAYSAFELY - BATTLESTRINGS_TABLE_START]                 = sText_GotAwaySafely,
    [STRINGID_WILDPKMNFLED - BATTLESTRINGS_TABLE_START]                  = sText_WildPkmnFled,
    [STRINGID_NORUNNINGFROMTRAINERS - BATTLESTRINGS_TABLE_START]         = sText_NoRunningFromTrainers,
    [STRINGID_CANTESCAPE - BATTLESTRINGS_TABLE_START]                    = sText_CantEscape,
    [STRINGID_DONTLEAVEBIRCH - BATTLESTRINGS_TABLE_START]                = sText_DontLeaveBirch,
    [STRINGID_BUTNOTHINGHAPPENED - BATTLESTRINGS_TABLE_START]            = sText_ButNothingHappened,
    [STRINGID_BUTITFAILED - BATTLESTRINGS_TABLE_START]                   = sText_ButItFailed,
    [STRINGID_ITHURTCONFUSION - BATTLESTRINGS_TABLE_START]               = sText_ItHurtConfusion,
    [STRINGID_MIRRORMOVEFAILED - BATTLESTRINGS_TABLE_START]              = sText_MirrorMoveFailed,
    [STRINGID_STARTEDTORAIN - BATTLESTRINGS_TABLE_START]                 = sText_StartedToRain,
    [STRINGID_DOWNPOURSTARTED - BATTLESTRINGS_TABLE_START]               = sText_DownpourStarted,
    [STRINGID_RAINCONTINUES - BATTLESTRINGS_TABLE_START]                 = sText_RainContinues,
    [STRINGID_DOWNPOURCONTINUES - BATTLESTRINGS_TABLE_START]             = sText_DownpourContinues,
    [STRINGID_RAINSTOPPED - BATTLESTRINGS_TABLE_START]                   = sText_RainStopped,
    [STRINGID_SANDSTORMBREWED - BATTLESTRINGS_TABLE_START]               = sText_SandstormBrewed,
    [STRINGID_SANDSTORMRAGES - BATTLESTRINGS_TABLE_START]                = sText_SandstormRages,
    [STRINGID_SANDSTORMSUBSIDED - BATTLESTRINGS_TABLE_START]             = sText_SandstormSubsided,
    [STRINGID_SUNLIGHTGOTBRIGHT - BATTLESTRINGS_TABLE_START]             = sText_SunlightGotBright,
    [STRINGID_SUNLIGHTSTRONG - BATTLESTRINGS_TABLE_START]                = sText_SunlightStrong,
    [STRINGID_SUNLIGHTFADED - BATTLESTRINGS_TABLE_START]                 = sText_SunlightFaded,
    [STRINGID_STARTEDHAIL - BATTLESTRINGS_TABLE_START]                   = sText_StartedHail,
    [STRINGID_HAILCONTINUES - BATTLESTRINGS_TABLE_START]                 = sText_HailContinues,
    [STRINGID_HAILSTOPPED - BATTLESTRINGS_TABLE_START]                   = sText_HailStopped,
    [STRINGID_FAILEDTOSPITUP - BATTLESTRINGS_TABLE_START]                = sText_FailedToSpitUp,
    [STRINGID_FAILEDTOSWALLOW - BATTLESTRINGS_TABLE_START]               = sText_FailedToSwallow,
    [STRINGID_WINDBECAMEHEATWAVE - BATTLESTRINGS_TABLE_START]            = sText_WindBecameHeatWave,
    [STRINGID_STATCHANGESGONE - BATTLESTRINGS_TABLE_START]               = sText_StatChangesGone,
    [STRINGID_COINSSCATTERED - BATTLESTRINGS_TABLE_START]                = sText_CoinsScattered,
    [STRINGID_TOOWEAKFORSUBSTITUTE - BATTLESTRINGS_TABLE_START]          = sText_TooWeakForSubstitute,
    [STRINGID_SHAREDPAIN - BATTLESTRINGS_TABLE_START]                    = sText_SharedPain,
    [STRINGID_BELLCHIMED - BATTLESTRINGS_TABLE_START]                    = sText_BellChimed,
    [STRINGID_FAINTINTHREE - BATTLESTRINGS_TABLE_START]                  = sText_FaintInThree,
    [STRINGID_NOPPLEFT - BATTLESTRINGS_TABLE_START]                      = sText_NoPPLeft,
    [STRINGID_BUTNOPPLEFT - BATTLESTRINGS_TABLE_START]                   = sText_ButNoPPLeft,
    [STRINGID_PLAYERUSEDITEM - BATTLESTRINGS_TABLE_START]                = sText_PlayerUsedItem,
    [STRINGID_OLDMANUSEDITEM - BATTLESTRINGS_TABLE_START]                = sText_OldManUsedItem,
    [STRINGID_TRAINERBLOCKEDBALL - BATTLESTRINGS_TABLE_START]            = sText_TrainerBlockedBall,
    [STRINGID_DONTBEATHIEF - BATTLESTRINGS_TABLE_START]                  = sText_DontBeAThief,
    [STRINGID_ITDODGEDBALL - BATTLESTRINGS_TABLE_START]                  = sText_ItDodgedBall,
    [STRINGID_YOUMISSEDPKMN - BATTLESTRINGS_TABLE_START]                 = sText_YouMissedPkmn,
    [STRINGID_PKMNBROKEFREE - BATTLESTRINGS_TABLE_START]                 = sText_PkmnBrokeFree,
    [STRINGID_ITAPPEAREDCAUGHT - BATTLESTRINGS_TABLE_START]              = sText_ItAppearedCaught,
    [STRINGID_AARGHALMOSTHADIT - BATTLESTRINGS_TABLE_START]              = sText_AarghAlmostHadIt,
    [STRINGID_SHOOTSOCLOSE - BATTLESTRINGS_TABLE_START]                  = sText_ShootSoClose,
    [STRINGID_GOTCHAPKMNCAUGHT - BATTLESTRINGS_TABLE_START]              = sText_GotchaPkmnCaught,
    [STRINGID_GOTCHAPKMNCAUGHT2 - BATTLESTRINGS_TABLE_START]             = sText_GotchaPkmnCaught2,
    [STRINGID_GIVENICKNAMECAPTURED - BATTLESTRINGS_TABLE_START]          = sText_GiveNicknameCaptured,
    [STRINGID_PKMNSENTTOPC - BATTLESTRINGS_TABLE_START]                  = sText_PkmnSentToPC,
    [STRINGID_PKMNDATAADDEDTODEX - BATTLESTRINGS_TABLE_START]            = sText_PkmnDataAddedToDex,
    [STRINGID_ITISRAINING - BATTLESTRINGS_TABLE_START]                   = sText_ItIsRaining,
    [STRINGID_SANDSTORMISRAGING - BATTLESTRINGS_TABLE_START]             = sText_SandstormIsRaging,
    [STRINGID_CANTESCAPE2 - BATTLESTRINGS_TABLE_START]                   = sText_CantEscape2,
    [STRINGID_PKMNIGNORESASLEEP - BATTLESTRINGS_TABLE_START]             = sText_PkmnIgnoresAsleep,
    [STRINGID_PKMNIGNOREDORDERS - BATTLESTRINGS_TABLE_START]             = sText_PkmnIgnoredOrders,
    [STRINGID_PKMNBEGANTONAP - BATTLESTRINGS_TABLE_START]                = sText_PkmnBeganToNap,
    [STRINGID_PKMNLOAFING - BATTLESTRINGS_TABLE_START]                   = sText_PkmnLoafing,
    [STRINGID_PKMNWONTOBEY - BATTLESTRINGS_TABLE_START]                  = sText_PkmnWontObey,
    [STRINGID_PKMNTURNEDAWAY - BATTLESTRINGS_TABLE_START]                = sText_PkmnTurnedAway,
    [STRINGID_PKMNPRETENDNOTNOTICE - BATTLESTRINGS_TABLE_START]          = sText_PkmnPretendNotNotice,
    [STRINGID_ENEMYABOUTTOSWITCHPKMN - BATTLESTRINGS_TABLE_START]        = sText_EnemyAboutToSwitchPkmn,
    [STRINGID_THREWROCK - BATTLESTRINGS_TABLE_START]                     = sText_ThrewARock,
    [STRINGID_THREWBAIT - BATTLESTRINGS_TABLE_START]                     = sText_ThrewSomeBait,
    [STRINGID_PKMNWATCHINGCAREFULLY - BATTLESTRINGS_TABLE_START]         = sText_PkmnWatchingCarefully,
    [STRINGID_PKMNANGRY - BATTLESTRINGS_TABLE_START]                     = sText_PkmnIsAngry,
    [STRINGID_PKMNEATING - BATTLESTRINGS_TABLE_START]                    = sText_PkmnIsEating,
    [STRINGID_DUMMY288 - BATTLESTRINGS_TABLE_START]                      = sText_Empty1,
    [STRINGID_DUMMY289 - BATTLESTRINGS_TABLE_START]                      = sText_Empty1,
    [STRINGID_OUTOFSAFARIBALLS - BATTLESTRINGS_TABLE_START]              = sText_OutOfSafariBalls,
    [STRINGID_PKMNSITEMCUREDPARALYSIS - BATTLESTRINGS_TABLE_START]       = sText_PkmnsItemCuredParalysis,
    [STRINGID_PKMNSITEMCUREDPOISON - BATTLESTRINGS_TABLE_START]          = sText_PkmnsItemCuredPoison,
    [STRINGID_PKMNSITEMHEALEDBURN - BATTLESTRINGS_TABLE_START]           = sText_PkmnsItemHealedBurn,
    [STRINGID_PKMNSITEMDEFROSTEDIT - BATTLESTRINGS_TABLE_START]          = sText_PkmnsItemDefrostedIt,
    [STRINGID_PKMNSITEMWOKEIT - BATTLESTRINGS_TABLE_START]               = sText_PkmnsItemWokeIt,
    [STRINGID_PKMNSITEMSNAPPEDOUT - BATTLESTRINGS_TABLE_START]           = sText_PkmnsItemSnappedOut,
    [STRINGID_PKMNSITEMCUREDPROBLEM - BATTLESTRINGS_TABLE_START]         = sText_PkmnsItemCuredProblem,
    [STRINGID_PKMNSITEMRESTOREDHEALTH - BATTLESTRINGS_TABLE_START]       = sText_PkmnsItemRestoredHealth,
    [STRINGID_PKMNSITEMRESTOREDPP - BATTLESTRINGS_TABLE_START]           = sText_PkmnsItemRestoredPP,
    [STRINGID_PKMNSITEMRESTOREDSTATUS - BATTLESTRINGS_TABLE_START]       = sText_PkmnsItemRestoredStatus,
    [STRINGID_PKMNSITEMRESTOREDHPALITTLE - BATTLESTRINGS_TABLE_START]    = sText_PkmnsItemRestoredHPALittle,
    [STRINGID_ITEMALLOWSONLYYMOVE - BATTLESTRINGS_TABLE_START]           = sText_ItemAllowsOnlyYMove,
    [STRINGID_PKMNHUNGONWITHX - BATTLESTRINGS_TABLE_START]               = sText_PkmnHungOnWithX,
    [STRINGID_EMPTYSTRING3 - BATTLESTRINGS_TABLE_START]                  = gText_EmptyString3,
    [STRINGID_PKMNSXPREVENTSBURNS - BATTLESTRINGS_TABLE_START]           = sText_PkmnsXPreventsBurns,
    [STRINGID_PKMNSXBLOCKSY - BATTLESTRINGS_TABLE_START]                 = sText_PkmnsXBlocksY,
    [STRINGID_PKMNSXRESTOREDHPALITTLE2 - BATTLESTRINGS_TABLE_START]      = sText_PkmnsXRestoredHPALittle2,
    [STRINGID_PKMNSXWHIPPEDUPSANDSTORM - BATTLESTRINGS_TABLE_START]      = sText_PkmnsXWhippedUpSandstorm,
    [STRINGID_PKMNSXPREVENTSYLOSS - BATTLESTRINGS_TABLE_START]           = sText_PkmnsXPreventsYLoss,
    [STRINGID_PKMNSXINFATUATEDY - BATTLESTRINGS_TABLE_START]             = sText_PkmnsXInfatuatedY,
    [STRINGID_PKMNSXMADEYINEFFECTIVE - BATTLESTRINGS_TABLE_START]        = sText_PkmnsXMadeYIneffective,
    [STRINGID_PKMNSXCUREDYPROBLEM - BATTLESTRINGS_TABLE_START]           = sText_PkmnsXCuredYProblem,
    [STRINGID_ITSUCKEDLIQUIDOOZE - BATTLESTRINGS_TABLE_START]            = sText_ItSuckedLiquidOoze,
    [STRINGID_PKMNTRANSFORMED - BATTLESTRINGS_TABLE_START]               = sText_PkmnTransformed,
    [STRINGID_ELECTRICITYWEAKENED - BATTLESTRINGS_TABLE_START]           = sText_ElectricityWeakened,
    [STRINGID_FIREWEAKENED - BATTLESTRINGS_TABLE_START]                  = sText_FireWeakened,
    [STRINGID_PKMNHIDUNDERWATER - BATTLESTRINGS_TABLE_START]             = sText_PkmnHidUnderwater,
    [STRINGID_PKMNSPRANGUP - BATTLESTRINGS_TABLE_START]                  = sText_PkmnSprangUp,
    [STRINGID_HMMOVESCANTBEFORGOTTEN - BATTLESTRINGS_TABLE_START]        = sText_HMMovesCantBeForgotten,
    [STRINGID_XFOUNDONEY - BATTLESTRINGS_TABLE_START]                    = sText_XFoundOneY,
    [STRINGID_PLAYERDEFEATEDTRAINER1 - BATTLESTRINGS_TABLE_START]        = sText_PlayerDefeatedLinkTrainerTrainer1,
    [STRINGID_SOOTHINGAROMA - BATTLESTRINGS_TABLE_START]                 = sText_SoothingAroma,
    [STRINGID_ITEMSCANTBEUSEDNOW - BATTLESTRINGS_TABLE_START]            = sText_ItemsCantBeUsedNow,
    [STRINGID_FORXCOMMAYZ - BATTLESTRINGS_TABLE_START]                   = sText_ForXCommaYZ,
    [STRINGID_USINGITEMSTATOFPKMNROSE - BATTLESTRINGS_TABLE_START]       = sText_UsingItemTheStatOfPkmnRose,
    [STRINGID_PKMNUSEDXTOGETPUMPED - BATTLESTRINGS_TABLE_START]          = sText_PkmnUsedXToGetPumped,
    [STRINGID_PKMNSXMADEYUSELESS - BATTLESTRINGS_TABLE_START]            = sText_PkmnsXMadeYUseless,
    [STRINGID_PKMNTRAPPEDBYSANDTOMB - BATTLESTRINGS_TABLE_START]         = sText_PkmnTrappedBySandTomb,
    [STRINGID_EMPTYSTRING4 - BATTLESTRINGS_TABLE_START]                  = sText_EmptyString4,
    [STRINGID_ABOOSTED - BATTLESTRINGS_TABLE_START]                      = sText_ABoosted,
    [STRINGID_PKMNSXINTENSIFIEDSUN - BATTLESTRINGS_TABLE_START]          = sText_PkmnsXIntensifiedSun,
    [STRINGID_PKMNMAKESGROUNDMISS - BATTLESTRINGS_TABLE_START]           = sText_PkmnMakesGroundMiss,
    [STRINGID_YOUTHROWABALLNOWRIGHT - BATTLESTRINGS_TABLE_START]         = sText_YouThrowABallNowRight,
    [STRINGID_PKMNSXTOOKATTACK - BATTLESTRINGS_TABLE_START]              = sText_PkmnsXTookAttack,
    [STRINGID_PKMNCHOSEXASDESTINY - BATTLESTRINGS_TABLE_START]           = sText_PkmnChoseXAsDestiny,
    [STRINGID_PKMNLOSTFOCUS - BATTLESTRINGS_TABLE_START]                 = sText_PkmnLostFocus,
    [STRINGID_USENEXTPKMN - BATTLESTRINGS_TABLE_START]                   = sText_UseNextPkmn,
    [STRINGID_PKMNFLEDUSINGITS - BATTLESTRINGS_TABLE_START]              = sText_PkmnFledUsingIts,
    [STRINGID_PKMNFLEDUSING - BATTLESTRINGS_TABLE_START]                 = sText_PkmnFledUsing,
    [STRINGID_PKMNWASDRAGGEDOUT - BATTLESTRINGS_TABLE_START]             = sText_PkmnWasDraggedOut,
    [STRINGID_PREVENTEDFROMWORKING - BATTLESTRINGS_TABLE_START]          = sText_PreventedFromWorking,
    [STRINGID_PKMNSITEMNORMALIZEDSTATUS - BATTLESTRINGS_TABLE_START]     = sText_PkmnsItemNormalizedStatus,
    [STRINGID_TRAINER1USEDITEM - BATTLESTRINGS_TABLE_START]              = sText_Trainer1UsedItem,
    [STRINGID_BOXISFULL - BATTLESTRINGS_TABLE_START]                     = sText_BoxIsFull,
    [STRINGID_PKMNAVOIDEDATTACK - BATTLESTRINGS_TABLE_START]             = sText_PkmnAvoidedAttack,
    [STRINGID_PKMNSXMADEITINEFFECTIVE - BATTLESTRINGS_TABLE_START]       = sText_PkmnsXMadeItIneffective,
    [STRINGID_PKMNSXPREVENTSFLINCHING - BATTLESTRINGS_TABLE_START]       = sText_PkmnsXPreventsFlinching,
    [STRINGID_PKMNALREADYHASBURN - BATTLESTRINGS_TABLE_START]            = sText_PkmnAlreadyHasBurn,
    [STRINGID_STATSWONTDECREASE2 - BATTLESTRINGS_TABLE_START]            = sText_StatsWontDecrease2,
    [STRINGID_PKMNSXBLOCKSY2 - BATTLESTRINGS_TABLE_START]                = sText_PkmnsXBlocksY2,
    [STRINGID_PKMNSXWOREOFF - BATTLESTRINGS_TABLE_START]                 = sText_PkmnsXWoreOff,
    [STRINGID_PKMNRAISEDDEFALITTLE - BATTLESTRINGS_TABLE_START]          = sText_PkmnRaisedDefALittle,
    [STRINGID_PKMNRAISEDSPDEFALITTLE - BATTLESTRINGS_TABLE_START]        = sText_PkmnRaisedSpDefALittle,
    [STRINGID_THEWALLSHATTERED - BATTLESTRINGS_TABLE_START]              = sText_TheWallShattered,
    [STRINGID_PKMNSXPREVENTSYSZ - BATTLESTRINGS_TABLE_START]             = sText_PkmnsXPreventsYsZ,
    [STRINGID_PKMNSXCUREDITSYPROBLEM - BATTLESTRINGS_TABLE_START]        = sText_PkmnsXCuredItsYProblem,
    [STRINGID_ATTACKERCANTESCAPE - BATTLESTRINGS_TABLE_START]            = sText_AttackerCantEscape,
    [STRINGID_PKMNOBTAINEDX - BATTLESTRINGS_TABLE_START]                 = sText_PkmnObtainedX,
    [STRINGID_PKMNOBTAINEDX2 - BATTLESTRINGS_TABLE_START]                = sText_PkmnObtainedX2,
    [STRINGID_PKMNOBTAINEDXYOBTAINEDZ - BATTLESTRINGS_TABLE_START]       = sText_PkmnObtainedXYObtainedZ,
    [STRINGID_BUTNOEFFECT - BATTLESTRINGS_TABLE_START]                   = sText_ButNoEffect,
    [STRINGID_PKMNSXHADNOEFFECTONY - BATTLESTRINGS_TABLE_START]          = sText_PkmnsXHadNoEffectOnY,
    [STRINGID_OAKPLAYERWON - BATTLESTRINGS_TABLE_START]                  = gText_WinEarnsPrizeMoney,
    [STRINGID_OAKPLAYERLOST - BATTLESTRINGS_TABLE_START]                 = gText_HowDissapointing,
    [STRINGID_PLAYERLOSTAGAINSTENEMYTRAINER - BATTLESTRINGS_TABLE_START] = sText_PlayerWhiteoutAgainstTrainer,
    [STRINGID_PLAYERPAIDPRIZEMONEY - BATTLESTRINGS_TABLE_START]          = sText_PlayerPaidAsPrizeMoney,
    [STRINGID_PKMNTRANSFERREDSOMEONESPC - BATTLESTRINGS_TABLE_START]     = Text_MonSentToBoxInSomeonesPC,
    [STRINGID_PKMNTRANSFERREDBILLSPC - BATTLESTRINGS_TABLE_START]        = Text_MonSentToBoxInBillsPC,
    [STRINGID_PKMNBOXSOMEONESPCFULL - BATTLESTRINGS_TABLE_START]         = Text_MonSentToBoxSomeonesBoxFull,
    [STRINGID_PKMNBOXBILLSPCFULL - BATTLESTRINGS_TABLE_START]            = Text_MonSentToBoxBillsBoxFull,
    [STRINGID_POKEDUDEUSED - BATTLESTRINGS_TABLE_START]                  = sText_PokedudeUsedItem,
    [STRINGID_POKEFLUTECATCHY - BATTLESTRINGS_TABLE_START]               = sText_PlayedFluteCatchyTune,
    [STRINGID_POKEFLUTE - BATTLESTRINGS_TABLE_START]                     = sText_PlayedThe,
    [STRINGID_MONHEARINGFLUTEAWOKE - BATTLESTRINGS_TABLE_START]          = sText_PkmnHearingFluteAwoke,
    [STRINGID_TRAINER2LOSETEXT - BATTLESTRINGS_TABLE_START]              = sText_Trainer2LoseText,
    [STRINGID_TRAINER2WINTEXT - BATTLESTRINGS_TABLE_START]               = sText_Trainer2WinText,
    [STRINGID_PLAYERWHITEDOUT - BATTLESTRINGS_TABLE_START]               = sText_PlayerWhiteout2,
    [STRINGID_MONTOOSCAREDTOMOVE - BATTLESTRINGS_TABLE_START]            = sText_TooScaredToMove,
    [STRINGID_GHOSTGETOUTGETOUT - BATTLESTRINGS_TABLE_START]             = sText_GetOutGetOut,
    [STRINGID_SILPHSCOPEUNVEILED - BATTLESTRINGS_TABLE_START]            = sText_SilphScopeUnveil,
    [STRINGID_GHOSTWASMAROWAK - BATTLESTRINGS_TABLE_START]               = sText_TheGhostWas,
    [STRINGID_TRAINER1MON1COMEBACK - BATTLESTRINGS_TABLE_START]          = sText_Trainer1RecallPkmn1,
    [STRINGID_TRAINER1WINTEXT - BATTLESTRINGS_TABLE_START]               = sText_Trainer1WinText,
    [STRINGID_TRAINER1MON2COMEBACK - BATTLESTRINGS_TABLE_START]          = sText_Trainer1RecallPkmn2,
    [STRINGID_TRAINER1MON1AND2COMEBACK - BATTLESTRINGS_TABLE_START]      = sText_Trainer1RecallBoth,
    [STRINGID_TEAMGAINEDEXP - BATTLESTRINGS_TABLE_START]                 = sText_TeamGainedExp,
};

const u16 gMissStringIds[] =
{
    [B_MSG_MISSED]      = STRINGID_ATTACKMISSED,
    [B_MSG_PROTECTED]   = STRINGID_PKMNPROTECTEDITSELF,
    [B_MSG_AVOIDED_ATK] = STRINGID_PKMNAVOIDEDATTACK,
    [B_MSG_AVOIDED_DMG] = STRINGID_AVOIDEDDAMAGE,
    [B_MSG_GROUND_MISS] = STRINGID_PKMNMAKESGROUNDMISS
};

const u16 gNoEscapeStringIds[] =
{
    [B_MSG_CANT_ESCAPE]          = STRINGID_CANTESCAPE,
    [B_MSG_DONT_LEAVE_BIRCH]     = STRINGID_DONTLEAVEBIRCH,
    [B_MSG_PREVENTS_ESCAPE]      = STRINGID_PREVENTSESCAPE,
    [B_MSG_CANT_ESCAPE_2]        = STRINGID_CANTESCAPE2,
    [B_MSG_ATTACKER_CANT_ESCAPE] = STRINGID_ATTACKERCANTESCAPE
};

const u16 gMoveWeatherChangeStringIds[] =
{
    [B_MSG_STARTED_RAIN]      = STRINGID_STARTEDTORAIN,
    [B_MSG_STARTED_DOWNPOUR]  = STRINGID_DOWNPOURSTARTED,
    [B_MSG_WEATHER_FAILED]    = STRINGID_BUTITFAILED,
    [B_MSG_STARTED_SANDSTORM] = STRINGID_SANDSTORMBREWED,
    [B_MSG_STARTED_SUNLIGHT]  = STRINGID_SUNLIGHTGOTBRIGHT,
    [B_MSG_STARTED_HAIL]      = STRINGID_STARTEDHAIL
};

const u16 gSandstormHailContinuesStringIds[] =
{
    [B_MSG_SANDSTORM] = STRINGID_SANDSTORMRAGES,
    [B_MSG_HAIL]      = STRINGID_HAILCONTINUES
};

const u16 gSandstormHailDmgStringIds[] =
{
    [B_MSG_SANDSTORM] = STRINGID_PKMNBUFFETEDBYSANDSTORM,
    [B_MSG_HAIL]      = STRINGID_PKMNPELTEDBYHAIL
};

const u16 gSandstormHailEndStringIds[] =
{
    [B_MSG_SANDSTORM] = STRINGID_SANDSTORMSUBSIDED,
    [B_MSG_HAIL]      = STRINGID_HAILSTOPPED
};

const u16 gRainContinuesStringIds[] =
{
    [B_MSG_RAIN_CONTINUES]     = STRINGID_RAINCONTINUES,
    [B_MSG_DOWNPOUR_CONTINUES] = STRINGID_DOWNPOURCONTINUES,
    [B_MSG_RAIN_STOPPED]       = STRINGID_RAINSTOPPED
};

const u16 gProtectLikeUsedStringIds[] =
{
    [B_MSG_PROTECTED_ITSELF] = STRINGID_PKMNPROTECTEDITSELF2,
    [B_MSG_BRACED_ITSELF]    = STRINGID_PKMNBRACEDITSELF,
    [B_MSG_PROTECT_FAILED]   = STRINGID_BUTITFAILED
};

const u16 gReflectLightScreenSafeguardStringIds[] =
{
    [B_MSG_SIDE_STATUS_FAILED]     = STRINGID_BUTITFAILED,
    [B_MSG_SET_REFLECT_SINGLE]     = STRINGID_PKMNRAISEDDEF,
    [B_MSG_SET_REFLECT_DOUBLE]     = STRINGID_PKMNRAISEDDEFALITTLE,
    [B_MSG_SET_LIGHTSCREEN_SINGLE] = STRINGID_PKMNRAISEDSPDEF,
    [B_MSG_SET_LIGHTSCREEN_DOUBLE] = STRINGID_PKMNRAISEDSPDEFALITTLE,
    [B_MSG_SET_SAFEGUARD]          = STRINGID_PKMNCOVEREDBYVEIL
};

const u16 gLeechSeedStringIds[] =
{
    [B_MSG_LEECH_SEED_SET]   = STRINGID_PKMNSEEDED,
    [B_MSG_LEECH_SEED_MISS]  = STRINGID_PKMNEVADEDATTACK,
    [B_MSG_LEECH_SEED_FAIL]  = STRINGID_ITDOESNTAFFECT,
    [B_MSG_LEECH_SEED_DRAIN] = STRINGID_PKMNSAPPEDBYLEECHSEED,
    [B_MSG_LEECH_SEED_OOZE]  = STRINGID_ITSUCKEDLIQUIDOOZE
};

const u16 gRestUsedStringIds[] =
{
    [B_MSG_REST]          = STRINGID_PKMNWENTTOSLEEP,
    [B_MSG_REST_STATUSED] = STRINGID_PKMNSLEPTHEALTHY
};

const u16 gUproarOverTurnStringIds[] =
{
    [B_MSG_UPROAR_CONTINUES] = STRINGID_PKMNMAKINGUPROAR,
    [B_MSG_UPROAR_ENDS]      = STRINGID_PKMNCALMEDDOWN
};

const u16 gStockpileUsedStringIds[] =
{
    [B_MSG_STOCKPILED]     = STRINGID_PKMNSTOCKPILED,
    [B_MSG_CANT_STOCKPILE] = STRINGID_PKMNCANTSTOCKPILE
};

const u16 gWokeUpStringIds[] =
{
    [B_MSG_WOKE_UP]        = STRINGID_PKMNWOKEUP,
    [B_MSG_WOKE_UP_UPROAR] = STRINGID_PKMNWOKEUPINUPROAR
};

const u16 gSwallowFailStringIds[] =
{
    [B_MSG_SWALLOW_FAILED]  = STRINGID_FAILEDTOSWALLOW,
    [B_MSG_SWALLOW_FULL_HP] = STRINGID_PKMNHPFULL
};

const u16 gUproarAwakeStringIds[] =
{
    [B_MSG_CANT_SLEEP_UPROAR]  = STRINGID_PKMNCANTSLEEPINUPROAR2,
    [B_MSG_UPROAR_KEPT_AWAKE]  = STRINGID_UPROARKEPTPKMNAWAKE,
    [B_MSG_STAYED_AWAKE_USING] = STRINGID_PKMNSTAYEDAWAKEUSING
};

const u16 gStatUpStringIds[] =
{
    [B_MSG_ATTACKER_STAT_ROSE] = STRINGID_ATTACKERSSTATROSE,
    [B_MSG_DEFENDER_STAT_ROSE] = STRINGID_DEFENDERSSTATROSE,
    [B_MSG_STAT_WONT_INCREASE] = STRINGID_STATSWONTINCREASE,
    [B_MSG_STAT_ROSE_EMPTY]    = STRINGID_EMPTYSTRING3,
    [B_MSG_STAT_ROSE_ITEM]     = STRINGID_USINGITEMSTATOFPKMNROSE,
    [B_MSG_USED_DIRE_HIT]      = STRINGID_PKMNUSEDXTOGETPUMPED,
};

const u16 gStatDownStringIds[] =
{
    [B_MSG_ATTACKER_STAT_FELL] = STRINGID_ATTACKERSSTATFELL,
    [B_MSG_DEFENDER_STAT_FELL] = STRINGID_DEFENDERSSTATFELL,
    [B_MSG_STAT_WONT_DECREASE] = STRINGID_STATSWONTDECREASE,
    [B_MSG_STAT_FELL_EMPTY]    = STRINGID_EMPTYSTRING3
};

// Index read from sTWOTURN_STRINGID
const u16 gFirstTurnOfTwoStringIds[] =
{
    [B_MSG_TURN1_RAZOR_WIND] = STRINGID_PKMNWHIPPEDWHIRLWIND,
    [B_MSG_TURN1_SOLAR_BEAM] = STRINGID_PKMNTOOKSUNLIGHT,
    [B_MSG_TURN1_SKULL_BASH] = STRINGID_PKMNLOWEREDHEAD,
    [B_MSG_TURN1_SKY_ATTACK] = STRINGID_PKMNISGLOWING,
    [B_MSG_TURN1_FLY]        = STRINGID_PKMNFLEWHIGH,
    [B_MSG_TURN1_DIG]        = STRINGID_PKMNDUGHOLE,
    [B_MSG_TURN1_DIVE]       = STRINGID_PKMNHIDUNDERWATER,
    [B_MSG_TURN1_BOUNCE]     = STRINGID_PKMNSPRANGUP
};

// Index copied from move's index in gTrappingMoves
const u16 gWrappedStringIds[] =
{
    STRINGID_PKMNSQUEEZEDBYBIND,   // MOVE_BIND
    STRINGID_PKMNWRAPPEDBY,        // MOVE_WRAP
    STRINGID_PKMNTRAPPEDINVORTEX,  // MOVE_FIRE_SPIN
    STRINGID_PKMNCLAMPED,          // MOVE_CLAMP
    STRINGID_PKMNTRAPPEDINVORTEX,  // MOVE_WHIRLPOOL
    STRINGID_PKMNTRAPPEDBYSANDTOMB // MOVE_SAND_TOMB
};

const u16 gMistUsedStringIds[] =
{
    [B_MSG_SET_MIST]    = STRINGID_PKMNSHROUDEDINMIST,
    [B_MSG_MIST_FAILED] = STRINGID_BUTITFAILED
};

const u16 gFocusEnergyUsedStringIds[] =
{
    [B_MSG_GETTING_PUMPED]      = STRINGID_PKMNGETTINGPUMPED,
    [B_MSG_FOCUS_ENERGY_FAILED] = STRINGID_BUTITFAILED
};

const u16 gTransformUsedStringIds[] =
{
    [B_MSG_TRANSFORMED]      = STRINGID_PKMNTRANSFORMEDINTO,
    [B_MSG_TRANSFORM_FAILED] = STRINGID_BUTITFAILED
};

const u16 gSubstituteUsedStringIds[] =
{
    [B_MSG_SET_SUBSTITUTE]    = STRINGID_PKMNMADESUBSTITUTE,
    [B_MSG_SUBSTITUTE_FAILED] = STRINGID_TOOWEAKFORSUBSTITUTE
};

const u16 gGotPoisonedStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNWASPOISONED,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNPOISONEDBY
};

const u16 gGotParalyzedStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNWASPARALYZED,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNWASPARALYZEDBY
};

const u16 gFellAsleepStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNFELLASLEEP,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNMADESLEEP
};

const u16 gGotBurnedStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNWASBURNED,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNBURNEDBY
};

const u16 gGotFrozenStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNWASFROZEN,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNFROZENBY
};

const u16 gGotDefrostedStringIds[] =
{
    [B_MSG_DEFROSTED]         = STRINGID_PKMNWASDEFROSTED2,
    [B_MSG_DEFROSTED_BY_MOVE] = STRINGID_PKMNWASDEFROSTEDBY
};

const u16 gKOFailedStringIds[] =
{
    [B_MSG_KO_MISS]       = STRINGID_ATTACKMISSED,
    [B_MSG_KO_UNAFFECTED] = STRINGID_PKMNUNAFFECTED
};

const u16 gAttractUsedStringIds[] =
{
    [B_MSG_STATUSED]            = STRINGID_PKMNFELLINLOVE,
    [B_MSG_STATUSED_BY_ABILITY] = STRINGID_PKMNSXINFATUATEDY
};

const u16 gAbsorbDrainStringIds[] =
{
    [B_MSG_ABSORB]      = STRINGID_PKMNENERGYDRAINED,
    [B_MSG_ABSORB_OOZE] = STRINGID_ITSUCKEDLIQUIDOOZE
};

const u16 gSportsUsedStringIds[] =
{
    [B_MSG_WEAKEN_ELECTRIC] = STRINGID_ELECTRICITYWEAKENED,
    [B_MSG_WEAKEN_FIRE]     = STRINGID_FIREWEAKENED
};

const u16 gPartyStatusHealStringIds[] =
{
    [B_MSG_BELL]                     = STRINGID_BELLCHIMED,
    [B_MSG_BELL_SOUNDPROOF_ATTACKER] = STRINGID_BELLCHIMED,
    [B_MSG_BELL_SOUNDPROOF_PARTNER]  = STRINGID_BELLCHIMED,
    [B_MSG_BELL_BOTH_SOUNDPROOF]     = STRINGID_BELLCHIMED,
    [B_MSG_SOOTHING_AROMA]           = STRINGID_SOOTHINGAROMA
};

const u16 gFutureMoveUsedStringIds[] =
{
    [B_MSG_FUTURE_SIGHT] = STRINGID_PKMNFORESAWATTACK,
    [B_MSG_DOOM_DESIRE]  = STRINGID_PKMNCHOSEXASDESTINY
};

const u16 gBallEscapeStringIds[] =
{
    [BALL_NO_SHAKES]     = STRINGID_PKMNBROKEFREE,
    [BALL_1_SHAKE]       = STRINGID_ITAPPEAREDCAUGHT,
    [BALL_2_SHAKES]      = STRINGID_AARGHALMOSTHADIT,
    [BALL_3_SHAKES_FAIL] = STRINGID_SHOOTSOCLOSE
};

// Overworld weathers that don't have an associated battle weather default to "It is raining."
const u16 gWeatherStartsStringIds[] =
{
    [WEATHER_NONE]               = STRINGID_ITISRAINING,
    [WEATHER_SUNNY_CLOUDS]       = STRINGID_ITISRAINING,
    [WEATHER_SUNNY]              = STRINGID_ITISRAINING,
    [WEATHER_RAIN]               = STRINGID_ITISRAINING,
    [WEATHER_SNOW]               = STRINGID_STARTEDHAIL, // Hack 7 — frente A
    [WEATHER_RAIN_THUNDERSTORM]  = STRINGID_ITISRAINING,
    [WEATHER_FOG_HORIZONTAL]     = STRINGID_ITISRAINING,
    [WEATHER_VOLCANIC_ASH]       = STRINGID_ITISRAINING,
    [WEATHER_SANDSTORM]          = STRINGID_SANDSTORMISRAGING,
    [WEATHER_FOG_DIAGONAL]       = STRINGID_ITISRAINING,
    [WEATHER_UNDERWATER]         = STRINGID_ITISRAINING,
    [WEATHER_SHADE]              = STRINGID_ITISRAINING,
    [WEATHER_DROUGHT]            = STRINGID_SUNLIGHTSTRONG,
    [WEATHER_DOWNPOUR]           = STRINGID_ITISRAINING,
    [WEATHER_UNDERWATER_BUBBLES] = STRINGID_ITISRAINING,
    [WEATHER_ABNORMAL]           = STRINGID_ITISRAINING
};

const u16 gInobedientStringIds[] =
{
    [B_MSG_LOAFING]            = STRINGID_PKMNLOAFING,
    [B_MSG_WONT_OBEY]          = STRINGID_PKMNWONTOBEY,
    [B_MSG_TURNED_AWAY]        = STRINGID_PKMNTURNEDAWAY,
    [B_MSG_PRETEND_NOT_NOTICE] = STRINGID_PKMNPRETENDNOTNOTICE
};

const u16 gSafariReactionStringIds[NUM_SAFARI_REACTIONS] =
{
    [B_MSG_MON_WATCHING] = STRINGID_PKMNWATCHINGCAREFULLY,
    [B_MSG_MON_ANGRY]    = STRINGID_PKMNANGRY,
    [B_MSG_MON_EATING]   = STRINGID_PKMNEATING
};

const u16 gTrainerItemCuredStatusStringIds[] =
{
    [AI_HEAL_CONFUSION] = STRINGID_PKMNSITEMSNAPPEDOUT,
    [AI_HEAL_PARALYSIS] = STRINGID_PKMNSITEMCUREDPARALYSIS,
    [AI_HEAL_FREEZE]    = STRINGID_PKMNSITEMDEFROSTEDIT,
    [AI_HEAL_BURN]      = STRINGID_PKMNSITEMHEALEDBURN,
    [AI_HEAL_POISON]    = STRINGID_PKMNSITEMCUREDPOISON,
    [AI_HEAL_SLEEP]     = STRINGID_PKMNSITEMWOKEIT
};

const u16 gBerryEffectStringIds[] =
{
    [B_MSG_CURED_PROBLEM]     = STRINGID_PKMNSITEMCUREDPROBLEM,
    [B_MSG_NORMALIZED_STATUS] = STRINGID_PKMNSITEMNORMALIZEDSTATUS
};

const u16 gBRNPreventionStringIds[] =
{
    [B_MSG_ABILITY_PREVENTS_MOVE_STATUS]    = STRINGID_PKMNSXPREVENTSBURNS,
    [B_MSG_ABILITY_PREVENTS_ABILITY_STATUS] = STRINGID_PKMNSXPREVENTSYSZ,
    [B_MSG_STATUS_HAD_NO_EFFECT]            = STRINGID_PKMNSXHADNOEFFECTONY
};

const u16 gPRLZPreventionStringIds[] =
{
    [B_MSG_ABILITY_PREVENTS_MOVE_STATUS]    = STRINGID_PKMNPREVENTSPARALYSISWITH,
    [B_MSG_ABILITY_PREVENTS_ABILITY_STATUS] = STRINGID_PKMNSXPREVENTSYSZ,
    [B_MSG_STATUS_HAD_NO_EFFECT]            = STRINGID_PKMNSXHADNOEFFECTONY
};

const u16 gPSNPreventionStringIds[] =
{
    [B_MSG_ABILITY_PREVENTS_MOVE_STATUS]    = STRINGID_PKMNPREVENTSPOISONINGWITH,
    [B_MSG_ABILITY_PREVENTS_ABILITY_STATUS] = STRINGID_PKMNSXPREVENTSYSZ,
    [B_MSG_STATUS_HAD_NO_EFFECT]            = STRINGID_PKMNSXHADNOEFFECTONY
};

const u16 gItemSwapStringIds[] =
{
    [B_MSG_ITEM_SWAP_TAKEN] = STRINGID_PKMNOBTAINEDX,
    [B_MSG_ITEM_SWAP_GIVEN] = STRINGID_PKMNOBTAINEDX2,
    [B_MSG_ITEM_SWAP_BOTH]  = STRINGID_PKMNOBTAINEDXYOBTAINEDZ
};

const u16 gFlashFireStringIds[] =
{
    [B_MSG_FLASH_FIRE_BOOST]    = STRINGID_PKMNRAISEDFIREPOWERWITH,
    [B_MSG_FLASH_FIRE_NO_BOOST] = STRINGID_PKMNSXMADEYINEFFECTIVE
};

const u16 gCaughtMonStringIds[] =
{
    [B_MSG_SENT_SOMEONES_PC]  = STRINGID_PKMNTRANSFERREDSOMEONESPC,
    [B_MSG_SENT_BILLS_PC]     = STRINGID_PKMNTRANSFERREDBILLSPC,
    [B_MSG_SOMEONES_BOX_FULL] = STRINGID_PKMNBOXSOMEONESPCFULL,
    [B_MSG_BILLS_BOX_FULL]    = STRINGID_PKMNBOXBILLSPCFULL
};

// Index is determined in VARIOUS_GET_BATTLERS_FOR_RECALL by ORing flags for each present battler on the losing side.
// No battlers (0) is skipped.
const u16 gDoubleBattleRecallStrings[1 << (MAX_BATTLERS_COUNT / 2)] =
{
    STRINGID_TRAINER1MON1COMEBACK,
    STRINGID_TRAINER1MON1COMEBACK,
    STRINGID_TRAINER1MON2COMEBACK,
    STRINGID_TRAINER1MON1AND2COMEBACK
};

const u16 gTrappingMoves[NUM_TRAPPING_MOVES + 1] =
{
    MOVE_BIND,
    MOVE_WRAP,
    MOVE_FIRE_SPIN,
    MOVE_CLAMP,
    MOVE_WHIRLPOOL,
    MOVE_SAND_TOMB,
    0xFFFF // Never read
};

const u8 gText_PkmnIsEvolving[] = _("O quê?\nO {STR_VAR_1} está evoluindo!");
const u8 gText_CongratsPkmnEvolved[] = _("Parabéns! Seu {STR_VAR_1}\nevoluiu para {STR_VAR_2}!{WAIT_SE}\p");
const u8 gText_PkmnStoppedEvolving[] = _("Hein? O {STR_VAR_1}\nparou de evoluir!\p");
const u8 gText_EllipsisQuestionMark[] = _("……?\p");
const u8 gText_WhatWillPkmnDo[] = _("O que o\n{B_ACTIVE_NAME_WITH_PREFIX} fará?");
const u8 gText_WhatWillPlayerThrow[] = _("O que {B_PLAYER_NAME}\nvai jogar?");
const u8 gText_WhatWillOldManDo[] = _("O que o velho\nvai fazer?");
const u8 gText_LinkStandby[] = _("{PAUSE 16}Aguardando conexão…");
const u8 gText_BattleMenu[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}Lutar{CLEAR_TO 56}Bolsa\nPokémon{CLEAR_TO 56}Fugir");
const u8 gText_SafariZoneMenu[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}Bola{CLEAR_TO 56}Isca\nPedra{CLEAR_TO 56}Fugir");
const u8 gText_MoveInterfacePP[] = _("PP ");
const u8 gText_MoveInterfaceType[] = _("Tipo/");
const u8 gText_MoveInterfaceDynamicColors[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}");
const u8 gText_WhichMoveToForget_Unused[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}どの わざを\nわすれさせたい?");
const u8 gText_BattleYesNoChoice[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}Sim\nNão");
const u8 gText_BattleSwitchWhich[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}Trocar\nqual?");
static const u8 sText_UnusedColors[] = _("{PALETTE 5}{COLOR_HIGHLIGHT_SHADOW 13 14 15}");
static const u8 sText_RightArrow2[] = _("{RIGHT_ARROW_2}");
static const u8 sText_Plus[] = _("{PLUS}");
static const u8 sText_Dash[] = _("-");

static const u8 sText_MaxHP[] = _("{FONT_SMALL}Máx.{FONT_NORMAL} PS");
static const u8 sText_Attack[] = _("Ataque ");
static const u8 sText_Defense[] = _("Defesa");
static const u8 sText_SpAtk[] = _("Atq. Esp.");
static const u8 sText_SpDef[] = _("Def. Esp.");

// Unused
static const u8 *const sStatNamesTable2[] =
{
    sText_MaxHP,
    sText_SpAtk,
    sText_Attack,
    sText_SpDef,
    sText_Defense,
    sText_Speed
};

const u8 gText_SafariBalls[] = _("{HIGHLIGHT 2}Bolas Safári"); //
const u8 gText_HighlightRed_Left[] = _("{HIGHLIGHT 2}Bolas: ");
const u8 gText_HighlightRed[] = _("{HIGHLIGHT 2}");
const u8 gText_Sleep[] = _("o sono");
const u8 gText_Poison[] = _("o envenenamento");
const u8 gText_Burn[] = _("a queimadura");
const u8 gText_Paralysis[] = _("a paralisia");
const u8 gText_Ice[] = _("o congelamento");
const u8 gText_Confusion[] = _("a confusão");
const u8 gText_Love[] = _("a paixão");
const u8 gText_BattleTowerBan_Space[] = _("  ");
const u8 gText_BattleTowerBan_Newline1[] = _("\n");
const u8 gText_BattleTowerBan_Newline2[] = _("\n");
const u8 gText_BattleTowerBan_Is1[] = _(" é");
const u8 gText_BattleTowerBan_Is2[] = _(" é");
const u8 gText_BadEgg[] = _("Ovo Ruim");
const u8 gText_BattleWallyName[] = _("ミツル");
const u8 gText_Win[] = _("{HIGHLIGHT 0}Vitória");
const u8 gText_Loss[] = _("{HIGHLIGHT 0}Derrota");
const u8 gText_Draw[] = _("{HIGHLIGHT 0}Empate");
static const u8 sText_SpaceIs[] = _(" é");
static const u8 sText_ApostropheS[] = _(" de");
const u8 gText_ANormalMove[] = _("golpe Normal");
const u8 gText_AFightingMove[] = _("golpe Lutador");
const u8 gText_AFlyingMove[] = _("golpe Voador");
const u8 gText_APoisonMove[] = _("golpe Venenoso");
const u8 gText_AGroundMove[] = _("golpe Terra");
const u8 gText_ARockMove[] = _("golpe Pedra");
const u8 gText_ABugMove[] = _("golpe Inseto");
const u8 gText_AGhostMove[] = _("golpe Fantasma");
const u8 gText_ASteelMove[] = _("golpe Aço");
const u8 gText_AMysteryMove[] = _("golpe ???");
const u8 gText_AFireMove[] = _("golpe Fogo");
const u8 gText_AWaterMove[] = _("golpe Água");
const u8 gText_AGrassMove[] = _("golpe Planta");
const u8 gText_AnElectricMove[] = _("golpe Elétrico");
const u8 gText_APsychicMove[] = _("golpe Psíquico");
const u8 gText_AnIceMove[] = _("golpe Gelo");
const u8 gText_ADragonMove[] = _("golpe Dragão");
const u8 gText_ADarkMove[] = _("golpe Sombrio");
const u8 gText_TimeBoard[] = _("Quadro de Tempos");
const u8 gText_ClearTime[] = _("Tempo Final"); // Unused
const u8 gText_XMinYZSec[] = _("{STR_VAR_1}min {STR_VAR_2},{STR_VAR_3}s");
const u8 gText_Unused_1F[] = _("1F");
const u8 gText_Unused_2F[] = _("2F");
const u8 gText_Unused_3F[] = _("3F");
const u8 gText_Unused_4F[] = _("4F");
const u8 gText_Unused_5F[] = _("5F");
const u8 gText_Unused_6F[] = _("6F");
const u8 gText_Unused_7F[] = _("7F");
const u8 gText_Unused_8F[] = _("8F");

const u8 *const gTrainerTowerChallengeTypeTexts[NUM_TOWER_CHALLENGE_TYPES] =
{
    gOtherText_Single,
    gOtherText_Double,
    gOtherText_Knockout,
    gOtherText_Mixed
};

static const u8 sText_Trainer1Fled[] = _("{PLAY_SE SE_FLEE}{B_TRAINER1_CLASS} {B_TRAINER1_NAME} fugiu!");
static const u8 sText_PlayerLostAgainstTrainer1[] = _("Você perdeu para\n{B_TRAINER1_CLASS} {B_TRAINER1_NAME}!");
static const u8 sText_PlayerBattledToDrawTrainer1[] = _("Você empatou com\n{B_TRAINER1_CLASS} {B_TRAINER1_NAME}!");

static const u8 *const sATypeMove_Table[NUMBER_OF_MON_TYPES] =
{
    [TYPE_NORMAL]   = gText_ANormalMove,
    [TYPE_FIGHTING] = gText_AFightingMove,
    [TYPE_FLYING]   = gText_AFlyingMove,
    [TYPE_POISON]   = gText_APoisonMove,
    [TYPE_GROUND]   = gText_AGroundMove,
    [TYPE_ROCK]     = gText_ARockMove,
    [TYPE_BUG]      = gText_ABugMove,
    [TYPE_GHOST]    = gText_AGhostMove,
    [TYPE_STEEL]    = gText_ASteelMove,
    [TYPE_MYSTERY]  = gText_AMysteryMove,
    [TYPE_FIRE]     = gText_AFireMove,
    [TYPE_WATER]    = gText_AWaterMove,
    [TYPE_GRASS]    = gText_AGrassMove,
    [TYPE_ELECTRIC] = gText_AnElectricMove,
    [TYPE_PSYCHIC]  = gText_APsychicMove,
    [TYPE_ICE]      = gText_AnIceMove,
    [TYPE_DRAGON]   = gText_ADragonMove,
    [TYPE_DARK]     = gText_ADarkMove
};

static const u16 sGrammarMoveUsedTable[] =
{
    MOVE_SWORDS_DANCE,
    MOVE_STRENGTH,
    MOVE_GROWTH,
    MOVE_HARDEN,
    MOVE_MINIMIZE,
    MOVE_SMOKESCREEN,
    MOVE_WITHDRAW,
    MOVE_DEFENSE_CURL,
    MOVE_EGG_BOMB,
    MOVE_SMOG,
    MOVE_BONE_CLUB,
    MOVE_FLASH,
    MOVE_SPLASH,
    MOVE_ACID_ARMOR,
    MOVE_BONEMERANG,
    MOVE_REST,
    MOVE_SHARPEN,
    MOVE_SUBSTITUTE,
    MOVE_MIND_READER,
    MOVE_SNORE,
    MOVE_PROTECT,
    MOVE_SPIKES,
    MOVE_ENDURE,
    MOVE_ROLLOUT,
    MOVE_SWAGGER,
    MOVE_SLEEP_TALK,
    MOVE_HIDDEN_POWER,
    MOVE_PSYCH_UP,
    MOVE_EXTREME_SPEED,
    MOVE_FOLLOW_ME,
    MOVE_TRICK,
    MOVE_ASSIST,
    MOVE_INGRAIN,
    MOVE_KNOCK_OFF,
    MOVE_CAMOUFLAGE,
    MOVE_ASTONISH,
    MOVE_ODOR_SLEUTH,
    MOVE_GRASS_WHISTLE,
    MOVE_SHEER_COLD,
    MOVE_MUDDY_WATER,
    MOVE_IRON_DEFENSE,
    MOVE_BOUNCE,
    MOVE_NONE,

    MOVE_TELEPORT,
    MOVE_RECOVER,
    MOVE_BIDE,
    MOVE_AMNESIA,
    MOVE_FLAIL,
    MOVE_TAUNT,
    MOVE_BULK_UP,
    MOVE_NONE,

    MOVE_MEDITATE,
    MOVE_AGILITY,
    MOVE_MIMIC,
    MOVE_DOUBLE_TEAM,
    MOVE_BARRAGE,
    MOVE_TRANSFORM,
    MOVE_STRUGGLE,
    MOVE_SCARY_FACE,
    MOVE_CHARGE,
    MOVE_WISH,
    MOVE_BRICK_BREAK,
    MOVE_YAWN,
    MOVE_FEATHER_DANCE,
    MOVE_TEETER_DANCE,
    MOVE_MUD_SPORT,
    MOVE_FAKE_TEARS,
    MOVE_WATER_SPORT,
    MOVE_CALM_MIND,
    MOVE_NONE,

    MOVE_POUND,
    MOVE_SCRATCH,
    MOVE_VICE_GRIP,
    MOVE_WING_ATTACK,
    MOVE_FLY,
    MOVE_BIND,
    MOVE_SLAM,
    MOVE_HORN_ATTACK,
    MOVE_WRAP,
    MOVE_THRASH,
    MOVE_TAIL_WHIP,
    MOVE_LEER,
    MOVE_BITE,
    MOVE_GROWL,
    MOVE_ROAR,
    MOVE_SING,
    MOVE_PECK,
    MOVE_ABSORB,
    MOVE_STRING_SHOT,
    MOVE_EARTHQUAKE,
    MOVE_FISSURE,
    MOVE_DIG,
    MOVE_TOXIC,
    MOVE_SCREECH,
    MOVE_METRONOME,
    MOVE_LICK,
    MOVE_CLAMP,
    MOVE_CONSTRICT,
    MOVE_POISON_GAS,
    MOVE_BUBBLE,
    MOVE_SLASH,
    MOVE_SPIDER_WEB,
    MOVE_NIGHTMARE,
    MOVE_CURSE,
    MOVE_FORESIGHT,
    MOVE_CHARM,
    MOVE_ATTRACT,
    MOVE_ROCK_SMASH,
    MOVE_UPROAR,
    MOVE_SPIT_UP,
    MOVE_SWALLOW,
    MOVE_TORMENT,
    MOVE_FLATTER,
    MOVE_ROLE_PLAY,
    MOVE_ENDEAVOR,
    MOVE_TICKLE,
    MOVE_COVET,
    MOVE_NONE
};

void BufferStringBattle(u16 stringId)
{
    s32 i;
    const u8 *stringPtr = NULL;

    sBattleMsgDataPtr = (struct BattleMsgData *)(&gBattleBufferA[gActiveBattler][4]);
    gLastUsedItem = sBattleMsgDataPtr->lastItem;
    gLastUsedAbility = sBattleMsgDataPtr->lastAbility;
    gBattleScripting.battler = sBattleMsgDataPtr->scrActive;
    *(&gBattleStruct->scriptPartyIdx) = sBattleMsgDataPtr->bakScriptPartyIdx;
    *(&gBattleStruct->hpScale) = sBattleMsgDataPtr->hpScale;
    gPotentialItemEffectBattler = sBattleMsgDataPtr->itemEffectBattler;
    *(&gBattleStruct->stringMoveType) = sBattleMsgDataPtr->moveType;

    for (i = 0; i < MAX_BATTLERS_COUNT; i++)
    {
        sBattlerAbilities[i] = sBattleMsgDataPtr->abilities[i];
    }
    for (i = 0; i < TEXT_BUFF_ARRAY_COUNT; i++)
    {
        gBattleTextBuff1[i] = sBattleMsgDataPtr->textBuffs[0][i];
        gBattleTextBuff2[i] = sBattleMsgDataPtr->textBuffs[1][i];
        gBattleTextBuff3[i] = sBattleMsgDataPtr->textBuffs[2][i];
    }

    switch (stringId)
    {
    case STRINGID_INTROMSG: // first battle msg
        if (gBattleTypeFlags & BATTLE_TYPE_TRAINER)
        {
            if (gBattleTypeFlags & BATTLE_TYPE_LINK)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                {
                    stringPtr = sText_TwoLinkTrainersWantToBattle;
                }
                else
                {
                    if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                        stringPtr = sText_Trainer1WantsToBattle;
                    else
                        stringPtr = sText_LinkTrainerWantsToBattle;
                }
            }
            else
            {
                stringPtr = sText_Trainer1WantsToBattle;
            }
        }
        else
        {
            if (gBattleTypeFlags & BATTLE_TYPE_GHOST)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_GHOST_UNVEILED)
                    stringPtr = sText_TheGhostAppeared;
                else
                    stringPtr = sText_GhostAppearedCantId;
            }
            else if (gBattleTypeFlags & BATTLE_TYPE_LEGENDARY)
                stringPtr = sText_WildPkmnAppeared2;
            else if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE) // interesting, looks like they had something planned for wild double battles
                stringPtr = sText_TwoWildPkmnAppeared;
            else if (gBattleTypeFlags & BATTLE_TYPE_OLD_MAN_TUTORIAL)
                stringPtr = sText_WildPkmnAppearedPause;
            else
                stringPtr = sText_WildPkmnAppeared;
        }
        break;
    case STRINGID_INTROSENDOUT: // poke first send-out
        if (GetBattlerSide(gActiveBattler) == B_SIDE_PLAYER)
        {
            if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                    stringPtr = sText_LinkPartnerSentOutPkmnGoPkmn;
                else
                    stringPtr = sText_GoTwoPkmn;
            }
            else
            {
                stringPtr = sText_GoPkmn;
            }
        }
        else
        {
            if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                    stringPtr = sText_TwoLinkTrainersSentOutPkmn;
                else if (gBattleTypeFlags & BATTLE_TYPE_LINK)
                    stringPtr = sText_LinkTrainerSentOutTwoPkmn;
                else
                    stringPtr = sText_Trainer1SentOutTwoPkmn;
            }
            else
            {
                if (!(gBattleTypeFlags & BATTLE_TYPE_LINK))
                    stringPtr = sText_Trainer1SentOutPkmn;
                else if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                    stringPtr = sText_Trainer1SentOutPkmn;
                else
                    stringPtr = sText_LinkTrainerSentOutPkmn;
            }
        }
        break;
    case STRINGID_RETURNMON: // sending poke to ball msg
        if (GetBattlerSide(gActiveBattler) == B_SIDE_PLAYER)
        {
            if (*(&gBattleStruct->hpScale) == 0)
                stringPtr = sText_PkmnThatsEnough;
            else if (*(&gBattleStruct->hpScale) == 1 || gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
                stringPtr = sText_PkmnComeBack;
            else if (*(&gBattleStruct->hpScale) == 2)
                stringPtr = sText_PkmnOkComeBack;
            else
                stringPtr = sText_PkmnGoodComeBack;
        }
        else
        {
            if (gTrainerBattleOpponent_A == TRAINER_LINK_OPPONENT)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                    stringPtr = sText_LinkTrainer2WithdrewPkmn;
                else
                    stringPtr = sText_LinkTrainer1WithdrewPkmn;
            }
            else
            {
                stringPtr = sText_Trainer1WithdrewPkmn;
            }
        }
        break;
    case STRINGID_SWITCHINMON: // switch-in msg
        if (GetBattlerSide(gBattleScripting.battler) == B_SIDE_PLAYER)
        {
            if (*(&gBattleStruct->hpScale) == 0 || gBattleTypeFlags & BATTLE_TYPE_DOUBLE)
                stringPtr = sText_GoPkmn2;
            else if (*(&gBattleStruct->hpScale) == 1)
                stringPtr = sText_DoItPkmn;
            else if (*(&gBattleStruct->hpScale) == 2)
                stringPtr = sText_GoForItPkmn;
            else
                stringPtr = sText_YourFoesWeakGetEmPkmn;
        }
        else
        {
            if (gBattleTypeFlags & BATTLE_TYPE_LINK)
            {
                if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                    stringPtr = sText_LinkTrainerMultiSentOutPkmn;
                else if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                    stringPtr = sText_Trainer1SentOutPkmn2;
                else
                    stringPtr = sText_LinkTrainerSentOutPkmn2;
            }
            else
            {
                stringPtr = sText_Trainer1SentOutPkmn2;
            }
        }
        break;
    case STRINGID_USEDMOVE: // pokemon used a move msg
        ChooseMoveUsedParticle(gBattleTextBuff1); // buff1 doesn't appear in the string, leftover from japanese move names

        if (sBattleMsgDataPtr->currentMove >= MOVES_COUNT)
            StringCopy(gBattleTextBuff2, sATypeMove_Table[*(&gBattleStruct->stringMoveType)]);
        else
            StringCopy(gBattleTextBuff2, gMoveNames[sBattleMsgDataPtr->currentMove]);

        ChooseTypeOfMoveUsedString(gBattleTextBuff2);
        stringPtr = sText_AttackerUsedX;
        break;
    case STRINGID_BATTLEEND: // battle end
        if (gBattleTextBuff1[0] & B_OUTCOME_LINK_BATTLE_RAN)
        {
            gBattleTextBuff1[0] &= ~(B_OUTCOME_LINK_BATTLE_RAN);
            if (GetBattlerSide(gActiveBattler) == B_SIDE_OPPONENT && gBattleTextBuff1[0] != B_OUTCOME_DREW)
                gBattleTextBuff1[0] ^= (B_OUTCOME_LOST | B_OUTCOME_WON);

            if (gBattleTextBuff1[0] == B_OUTCOME_LOST || gBattleTextBuff1[0] == B_OUTCOME_DREW)
                stringPtr = sText_GotAwaySafely;
            else if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
                stringPtr = sText_TwoWildFled;
            else if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                stringPtr = sText_Trainer1Fled;
            else
                stringPtr = sText_WildFled;
        }
        else
        {
            if (GetBattlerSide(gActiveBattler) == B_SIDE_OPPONENT && gBattleTextBuff1[0] != B_OUTCOME_DREW)
                gBattleTextBuff1[0] ^= (B_OUTCOME_LOST | B_OUTCOME_WON);

            if (gBattleTypeFlags & BATTLE_TYPE_MULTI)
            {
                switch (gBattleTextBuff1[0])
                {
                case B_OUTCOME_WON:
                    stringPtr = sText_TwoLinkTrainersDefeated;
                    break;
                case B_OUTCOME_LOST:
                    stringPtr = sText_PlayerLostToTwo;
                    break;
                case B_OUTCOME_DREW:
                    stringPtr = sText_PlayerBattledToDrawVsTwo;
                    break;
                }
            }
            else if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
            {
                switch (gBattleTextBuff1[0])
                {
                case B_OUTCOME_WON:
                    stringPtr = sText_PlayerDefeatedLinkTrainerTrainer1;
                    break;
                case B_OUTCOME_LOST:
                    stringPtr = sText_PlayerLostAgainstTrainer1;
                    break;
                case B_OUTCOME_DREW:
                    stringPtr = sText_PlayerBattledToDrawTrainer1;
                    break;
                }
            }
            else
            {
                switch (gBattleTextBuff1[0])
                {
                case B_OUTCOME_WON:
                    stringPtr = sText_PlayerDefeatedLinkTrainer;
                    break;
                case B_OUTCOME_LOST:
                    stringPtr = sText_PlayerLostAgainstLinkTrainer;
                    break;
                case B_OUTCOME_DREW:
                    stringPtr = sText_PlayerBattledToDrawLinkTrainer;
                    break;
                }
            }
        }
        break;
    default: // load a string from the table
        if (stringId >= BATTLESTRINGS_COUNT)
        {
            gDisplayedStringBattle[0] = EOS;
            return;
        }
        else
        {
            stringPtr = gBattleStringsTable[stringId - BATTLESTRINGS_TABLE_START];
        }
        break;
    }

    BattleStringExpandPlaceholdersToDisplayedString(stringPtr);
}

u32 BattleStringExpandPlaceholdersToDisplayedString(const u8 *src)
{
    return BattleStringExpandPlaceholders(src, gDisplayedStringBattle);
}

static const u8 *TryGetStatusString(u8 *src)
{
    u32 i;
    u8 status[] = _("$$$$$$$");
    u32 chars1, chars2, *cmp;
    u8 *statusPtr;

    statusPtr = status;
    for (i = 0; i < 8 && *src != EOS; i++)
        *statusPtr++ = *src++;

    chars1 = *(u32 *)status;
    chars2 = *((u32 *)status + 1);

    for (i = 0; i < NELEMS(gStatusConditionStringsTable); i++)
    {
        cmp = (u32 *)gStatusConditionStringsTable[i][0];
        if (chars1 == cmp[0] && chars2 == cmp[1])
            return gStatusConditionStringsTable[i][1];
    }
    return NULL;
}

#define HANDLE_NICKNAME_STRING_CASE(battlerId, monIndex)                \
    if (GetBattlerSide(battlerId) != B_SIDE_PLAYER)                     \
    {                                                                   \
        GetMonData(&gEnemyParty[monIndex], MON_DATA_NICKNAME, text);    \
        StringGet_Nickname(text);                                       \
        if (gBattleTypeFlags & BATTLE_TYPE_TRAINER)                     \
            StringAppend(text, sText_FoePkmnPrefix);                    \
        else                                                            \
            StringAppend(text, sText_WildPkmnPrefix);                   \
        /* PT-BR: the side word follows the name ("Rattata selvagem",   \
           "Pidgey inimigo"); text[30] holds the 10-letter nickname     \
           plus the suffix. Each message writes the article, always     \
           masculine ("o Pokémon"): "O {B_ATK_NAME_WITH_PREFIX} usou",  \
           "do {B_DEF_NAME_WITH_PREFIX}", for any species or nickname */ \
    }                                                                   \
    else                                                                \
    {                                                                   \
        GetMonData(&gPlayerParty[monIndex], MON_DATA_NICKNAME, text);   \
        StringGet_Nickname(text);                                       \
    }                                                                   \
    toCpy = text;

u32 BattleStringExpandPlaceholders(const u8 *src, u8 *dst)
{
    u32 dstId = 0; // if they used dstId, why not use srcId as well?
    const u8 *toCpy = NULL;
    u8 text[30];
    u8 multiplayerId;
    s32 i;

    multiplayerId = GetMultiplayerId();

    while (*src != EOS)
    {
        if (*src == PLACEHOLDER_BEGIN)
        {
            src++;
            switch (*src)
            {
            case B_TXT_BUFF1:
                if (gBattleTextBuff1[0] == B_BUFF_PLACEHOLDER_BEGIN)
                {
                    ExpandBattleTextBuffPlaceholders(gBattleTextBuff1, gStringVar1);
                    toCpy = gStringVar1;
                }
                else
                {
                    toCpy = TryGetStatusString(gBattleTextBuff1);
                    if (toCpy == NULL)
                        toCpy = gBattleTextBuff1;
                }
                break;
            case B_TXT_BUFF2:
                if (gBattleTextBuff2[0] == B_BUFF_PLACEHOLDER_BEGIN)
                {
                    ExpandBattleTextBuffPlaceholders(gBattleTextBuff2, gStringVar2);
                    toCpy = gStringVar2;
                }
                else
                    toCpy = gBattleTextBuff2;
                break;
            case B_TXT_BUFF3:
                if (gBattleTextBuff3[0] == B_BUFF_PLACEHOLDER_BEGIN)
                {
                    ExpandBattleTextBuffPlaceholders(gBattleTextBuff3, gStringVar3);
                    toCpy = gStringVar3;
                }
                else
                    toCpy = gBattleTextBuff3;
                break;
            case B_TXT_COPY_VAR_1:
                toCpy = gStringVar1;
                break;
            case B_TXT_COPY_VAR_2:
                toCpy = gStringVar2;
                break;
            case B_TXT_COPY_VAR_3:
                toCpy = gStringVar3;
                break;
            case B_TXT_PLAYER_MON1_NAME: // first player poke name
                GetMonData(&gPlayerParty[gBattlerPartyIndexes[GetBattlerAtPosition(B_POSITION_PLAYER_LEFT)]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_OPPONENT_MON1_NAME: // first enemy poke name
                GetMonData(&gEnemyParty[gBattlerPartyIndexes[GetBattlerAtPosition(B_POSITION_OPPONENT_LEFT)]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_PLAYER_MON2_NAME: // second player poke name
                GetMonData(&gPlayerParty[gBattlerPartyIndexes[GetBattlerAtPosition(B_POSITION_PLAYER_RIGHT)]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_OPPONENT_MON2_NAME: // second enemy poke name
                GetMonData(&gEnemyParty[gBattlerPartyIndexes[GetBattlerAtPosition(B_POSITION_OPPONENT_RIGHT)]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_LINK_PLAYER_MON1_NAME: // link first player poke name
                GetMonData(&gPlayerParty[gBattlerPartyIndexes[gLinkPlayers[multiplayerId].id]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_LINK_OPPONENT_MON1_NAME: // link first opponent poke name
                GetMonData(&gEnemyParty[gBattlerPartyIndexes[gLinkPlayers[multiplayerId].id ^ 1]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_LINK_PLAYER_MON2_NAME: // link second player poke name
                GetMonData(&gPlayerParty[gBattlerPartyIndexes[gLinkPlayers[multiplayerId].id ^ 2]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_LINK_OPPONENT_MON2_NAME: // link second opponent poke name
                GetMonData(&gEnemyParty[gBattlerPartyIndexes[gLinkPlayers[multiplayerId].id ^ 3]],
                           MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_ATK_NAME_WITH_PREFIX_MON1: // attacker name with prefix, only battlerId 0/1
                HANDLE_NICKNAME_STRING_CASE(gBattlerAttacker,
                                            gBattlerPartyIndexes[GetBattlerAtPosition(GET_BATTLER_SIDE(gBattlerAttacker))])
                break;
            case B_TXT_ATK_PARTNER_NAME: // attacker partner name
                if (GetBattlerSide(gBattlerAttacker) == B_SIDE_PLAYER)
                    GetMonData(
                        &gPlayerParty[gBattlerPartyIndexes[GetBattlerAtPosition(GET_BATTLER_SIDE(gBattlerAttacker)) +
                                                           2]], MON_DATA_NICKNAME, text);
                else
                    GetMonData(
                        &gEnemyParty[gBattlerPartyIndexes[GetBattlerAtPosition(GET_BATTLER_SIDE(gBattlerAttacker)) +
                                                          2]], MON_DATA_NICKNAME, text);

                StringGet_Nickname(text);
                toCpy = text;
                break;
            case B_TXT_ATK_NAME_WITH_PREFIX: // attacker name with prefix
                HANDLE_NICKNAME_STRING_CASE(gBattlerAttacker, gBattlerPartyIndexes[gBattlerAttacker])
                break;
            case B_TXT_DEF_NAME_WITH_PREFIX: // target name with prefix
                HANDLE_NICKNAME_STRING_CASE(gBattlerTarget, gBattlerPartyIndexes[gBattlerTarget])
                break;
            case B_TXT_EFF_NAME_WITH_PREFIX: // effect battlerId name with prefix
                HANDLE_NICKNAME_STRING_CASE(gEffectBattler, gBattlerPartyIndexes[gEffectBattler])
                break;
            case B_TXT_ACTIVE_NAME_WITH_PREFIX: // active battlerId name with prefix
                HANDLE_NICKNAME_STRING_CASE(gActiveBattler, gBattlerPartyIndexes[gActiveBattler])
                break;
            case B_TXT_SCR_ACTIVE_NAME_WITH_PREFIX: // scripting active battlerId name with prefix
                HANDLE_NICKNAME_STRING_CASE(gBattleScripting.battler, gBattlerPartyIndexes[gBattleScripting.battler])
                break;
            case B_TXT_CURRENT_MOVE: // current move name
                if (sBattleMsgDataPtr->currentMove >= MOVES_COUNT)
                    toCpy = (const u8 *)&sATypeMove_Table[gBattleStruct->stringMoveType];
                else
                    toCpy = gMoveNames[sBattleMsgDataPtr->currentMove];
                break;
            case B_TXT_LAST_MOVE: // originally used move name
                if (sBattleMsgDataPtr->originallyUsedMove >= MOVES_COUNT)
                    toCpy = (const u8 *)&sATypeMove_Table[gBattleStruct->stringMoveType];
                else
                    toCpy = gMoveNames[sBattleMsgDataPtr->originallyUsedMove];
                break;
            case B_TXT_LAST_ITEM: // last used item
                if (gBattleTypeFlags & BATTLE_TYPE_LINK)
                {
                    if (gLastUsedItem == ITEM_ENIGMA_BERRY)
                    {
                        if (!(gBattleTypeFlags & BATTLE_TYPE_MULTI))
                        {
                            if ((gBattleStruct->multiplayerId != 0 && (gPotentialItemEffectBattler & BIT_SIDE))
                                || (gBattleStruct->multiplayerId == 0 && !(gPotentialItemEffectBattler & BIT_SIDE)))
                            {
                                StringCopy(text, sText_BerryPrefix);
                                StringAppend(text, gEnigmaBerries[gPotentialItemEffectBattler].name);
                                toCpy = text;
                            }
                            else
                            {
                                toCpy = sText_EnigmaBerry;
                            }
                        }
                        else
                        {
                            if (gLinkPlayers[gBattleStruct->multiplayerId].id == gPotentialItemEffectBattler)
                            {
                                StringCopy(text, sText_BerryPrefix);
                                StringAppend(text, gEnigmaBerries[gPotentialItemEffectBattler].name);
                                toCpy = text;
                            }
                            else
                                toCpy = sText_EnigmaBerry;
                        }
                    }
                    else
                    {
                        CopyItemName(gLastUsedItem, text);
                        toCpy = text;
                    }
                }
                else
                {
                    CopyItemName(gLastUsedItem, text);
                    toCpy = text;
                }
                break;
            case B_TXT_LAST_ABILITY: // last used ability
                toCpy = gAbilityNames[gLastUsedAbility];
                break;
            case B_TXT_ATK_ABILITY: // attacker ability
                toCpy = gAbilityNames[sBattlerAbilities[gBattlerAttacker]];
                break;
            case B_TXT_DEF_ABILITY: // target ability
                toCpy = gAbilityNames[sBattlerAbilities[gBattlerTarget]];
                break;
            case B_TXT_SCR_ACTIVE_ABILITY: // scripting active ability
                toCpy = gAbilityNames[sBattlerAbilities[gBattleScripting.battler]];
                break;
            case B_TXT_EFF_ABILITY: // effect battlerId ability
                toCpy = gAbilityNames[sBattlerAbilities[gEffectBattler]];
                break;
            case B_TXT_TRAINER1_CLASS: // trainer class name
                if (gTrainerBattleOpponent_A == TRAINER_SECRET_BASE)
                    toCpy = gTrainerClassNames[GetSecretBaseTrainerNameIndex()];
                else if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                    toCpy = gTrainerClassNames[GetUnionRoomTrainerClass()];
                else if (gBattleTypeFlags & BATTLE_TYPE_BATTLE_TOWER)
                    toCpy = gTrainerClassNames[GetBattleTowerTrainerClassNameId()];
                else if (gBattleTypeFlags & BATTLE_TYPE_TRAINER_TOWER)
                    toCpy = gTrainerClassNames[GetTrainerTowerOpponentClass()];
                else if (gBattleTypeFlags & BATTLE_TYPE_EREADER_TRAINER)
                    toCpy = gTrainerClassNames[GetEreaderTrainerClassId()];
                else
                    toCpy = gTrainerClassNames[gTrainers[gTrainerBattleOpponent_A].trainerClass];
                break;
            case B_TXT_TRAINER1_NAME: // trainer1 name
                if (gTrainerBattleOpponent_A == TRAINER_SECRET_BASE)
                {
                    for (i = 0; i < (s32)NELEMS(gBattleResources->secretBase->trainerName); i++)
                        text[i] = gBattleResources->secretBase->trainerName[i];
                    text[i] = EOS;
                    toCpy = text;
                }
                if (gTrainerBattleOpponent_A == TRAINER_UNION_ROOM)
                {
                    toCpy = gLinkPlayers[multiplayerId ^ BIT_SIDE].name;
                }
                else if (gBattleTypeFlags & BATTLE_TYPE_BATTLE_TOWER)
                {
                    GetBattleTowerTrainerName(text);
                }
                else if (gBattleTypeFlags & BATTLE_TYPE_TRAINER_TOWER)
                {
                    GetTrainerTowerOpponentName(text);
                    toCpy = text;
                }
                else if (gBattleTypeFlags & BATTLE_TYPE_EREADER_TRAINER)
                {
                    CopyEReaderTrainerName5(text);
                    toCpy = text;
                }
                else
                {
                    if (gTrainers[gTrainerBattleOpponent_A].trainerClass == TRAINER_CLASS_RIVAL_EARLY
                     || gTrainers[gTrainerBattleOpponent_A].trainerClass == TRAINER_CLASS_RIVAL_LATE
                     || gTrainers[gTrainerBattleOpponent_A].trainerClass == TRAINER_CLASS_CHAMPION)
                        toCpy = GetExpandedPlaceholder(PLACEHOLDER_ID_RIVAL);
                    else
                        toCpy = gTrainers[gTrainerBattleOpponent_A].trainerName;
                }
                break;
            case B_TXT_LINK_PLAYER_NAME: // link player name
                toCpy = gLinkPlayers[multiplayerId].name;
                break;
            case B_TXT_LINK_PARTNER_NAME: // link partner name
                toCpy = gLinkPlayers[GetBattlerMultiplayerId(BATTLE_PARTNER(gLinkPlayers[multiplayerId].id))].name;
                break;
            case B_TXT_LINK_OPPONENT1_NAME: // link opponent 1 name
                toCpy = gLinkPlayers[GetBattlerMultiplayerId(BATTLE_OPPOSITE(gLinkPlayers[multiplayerId].id))].name;
                break;
            case B_TXT_LINK_OPPONENT2_NAME: // link opponent 2 name
                toCpy = gLinkPlayers[GetBattlerMultiplayerId(
                    BATTLE_PARTNER(BATTLE_OPPOSITE(gLinkPlayers[multiplayerId].id)))].name;
                break;
            case B_TXT_LINK_SCR_TRAINER_NAME: // link scripting active name
                toCpy = gLinkPlayers[GetBattlerMultiplayerId(gBattleScripting.battler)].name;
                break;
            case B_TXT_PLAYER_NAME: // player name
                toCpy = gSaveBlock2Ptr->playerName;
                break;
            case B_TXT_TRAINER1_LOSE_TEXT: // trainerA lose text
                if (gBattleTypeFlags & BATTLE_TYPE_TRAINER_TOWER)
                {
                    GetTrainerTowerOpponentLoseText(gStringVar4, 0);
                    toCpy = gStringVar4;
                }
                else
                {
                    toCpy = GetTrainerALoseText();
                }
                break;
            case B_TXT_TRAINER1_WIN_TEXT: // trainerA win text
                if (gBattleTypeFlags & BATTLE_TYPE_TRAINER_TOWER)
                {
                    GetTrainerTowerOpponentWinText(gStringVar4, 0);
                    toCpy = gStringVar4;
                }
                else
                {
                    toCpy = GetTrainerWonSpeech();
                }
                break;
            case B_TXT_TRAINER2_LOSE_TEXT:
                GetTrainerTowerOpponentLoseText(gStringVar4, 1);
                toCpy = gStringVar4;
                break;
            case B_TXT_TRAINER2_WIN_TEXT:
                GetTrainerTowerOpponentWinText(gStringVar4, 1);
                toCpy = gStringVar4;
                break;
            case B_TXT_26: // ?
                HANDLE_NICKNAME_STRING_CASE(gBattleScripting.battler, *(&gBattleStruct->scriptPartyIdx))
                break;
            case B_TXT_PC_CREATOR_NAME: // lanette pc
                if (FlagGet(FLAG_SYS_NOT_SOMEONES_PC))
                    toCpy = sText_Bills;
                else
                    toCpy = sText_Someones;
                break;
            case B_TXT_ATK_PREFIX2:
                if (GetBattlerSide(gBattlerAttacker) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix2;
                else
                    toCpy = sText_FoePkmnPrefix3;
                break;
            case B_TXT_DEF_PREFIX2:
                if (GetBattlerSide(gBattlerTarget) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix2;
                else
                    toCpy = sText_FoePkmnPrefix3;
                break;
            case B_TXT_ATK_PREFIX1:
                if (GetBattlerSide(gBattlerAttacker) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix;
                else
                    toCpy = sText_FoePkmnPrefix2;
                break;
            case B_TXT_DEF_PREFIX1:
                if (GetBattlerSide(gBattlerTarget) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix;
                else
                    toCpy = sText_FoePkmnPrefix2;
                break;
            case B_TXT_ATK_PREFIX3:
                if (GetBattlerSide(gBattlerAttacker) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix3;
                else
                    toCpy = sText_FoePkmnPrefix4;
                break;
            case B_TXT_DEF_PREFIX3:
                if (GetBattlerSide(gBattlerTarget) == B_SIDE_PLAYER)
                    toCpy = sText_AllyPkmnPrefix3;
                else
                    toCpy = sText_FoePkmnPrefix4;
                break;
            }

            // missing if (toCpy != NULL) check
            while (*toCpy != EOS)
            {
                dst[dstId++] = *toCpy;
                toCpy++;
            }
            if (*src == B_TXT_TRAINER1_LOSE_TEXT || *src == B_TXT_TRAINER1_WIN_TEXT
             || *src == B_TXT_TRAINER2_LOSE_TEXT || *src == B_TXT_TRAINER2_WIN_TEXT)
            {
                dst[dstId++] = EXT_CTRL_CODE_BEGIN;
                dst[dstId++] = EXT_CTRL_CODE_PAUSE_UNTIL_PRESS;
            }
        }
        else
        {
            dst[dstId++] = *src;
        }
        src++;
    }

    dst[dstId++] = *src;

    return dstId;
}

static void ExpandBattleTextBuffPlaceholders(const u8 *src, u8 *dst)
{
    u32 srcId = 1;
    u32 value = 0;
    u8 text[12];
    u16 hword;

    *dst = EOS;
    while (src[srcId] != B_BUFF_EOS)
    {
        switch (src[srcId])
        {
        case B_BUFF_STRING: // battle string
            hword = T1_READ_16(&src[srcId + 1]);
            StringAppend(dst, gBattleStringsTable[hword - BATTLESTRINGS_TABLE_START]);
            srcId += 3;
            break;
        case B_BUFF_NUMBER: // int to string
            switch (src[srcId + 1])
            {
            case 1:
                value = src[srcId + 3];
                break;
            case 2:
                value = T1_READ_16(&src[srcId + 3]);
                break;
            case 4:
                value = T1_READ_32(&src[srcId + 3]);
                break;
            }
            ConvertIntToDecimalStringN(dst, value, STR_CONV_MODE_LEFT_ALIGN, src[srcId + 2]);
            srcId += src[srcId + 1] + 3;
            break;
        case B_BUFF_MOVE: // move name
            StringAppend(dst, gMoveNames[T1_READ_16(&src[srcId + 1])]);
            srcId += 3;
            break;
        case B_BUFF_TYPE: // type name
            StringAppend(dst, gTypeNames[src[srcId + 1]]);
            srcId += 2;
            break;
        case B_BUFF_MON_NICK_WITH_PREFIX: // poke nick with prefix
            // PT-BR: the side word follows the name ("Rattata selvagem", "Pidgey inimigo");
            // gStringVar2/3[20] hold the 10-letter nickname plus the suffix
            if (GetBattlerSide(src[srcId + 1]) == B_SIDE_PLAYER)
            {
                GetMonData(&gPlayerParty[src[srcId + 2]], MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                StringAppend(dst, text);
            }
            else
            {
                GetMonData(&gEnemyParty[src[srcId + 2]], MON_DATA_NICKNAME, text);
                StringGet_Nickname(text);
                StringAppend(dst, text);
                StringAppend(dst, (gBattleTypeFlags & BATTLE_TYPE_TRAINER) ? sText_FoePkmnPrefix : sText_WildPkmnPrefix);
            }
            srcId += 3;
            break;
        case B_BUFF_STAT: // stats
            StringAppend(dst, gStatNamesTable[src[srcId + 1]]);
            srcId += 2;
            break;
        case B_BUFF_SPECIES: // species name
            GetSpeciesName(dst, T1_READ_16(&src[srcId + 1]));
            srcId += 3;
            break;
        case B_BUFF_MON_NICK: // poke nick without prefix
            if (GetBattlerSide(src[srcId + 1]) == B_SIDE_PLAYER)
                GetMonData(&gPlayerParty[src[srcId + 2]], MON_DATA_NICKNAME, dst);
            else
                GetMonData(&gEnemyParty[src[srcId + 2]], MON_DATA_NICKNAME, dst);
            StringGet_Nickname(dst);
            srcId += 3;
            break;
        case B_BUFF_NEGATIVE_FLAVOR: // flavor table
            StringAppend(dst, gPokeblockWasTooXStringTable[src[srcId + 1]]);
            srcId += 2;
            break;
        case B_BUFF_ABILITY: // ability names
            StringAppend(dst, gAbilityNames[src[srcId + 1]]);
            srcId += 2;
            break;
        case B_BUFF_ITEM: // item name
            hword = T1_READ_16(&src[srcId + 1]);
            if (gBattleTypeFlags & BATTLE_TYPE_LINK)
            {
                if (hword == ITEM_ENIGMA_BERRY)
                {
                    if (gLinkPlayers[gBattleStruct->multiplayerId].id == gPotentialItemEffectBattler)
                    {
                        StringCopy(dst, sText_BerryPrefix);
                        StringAppend(dst, gEnigmaBerries[gPotentialItemEffectBattler].name);
                    }
                    else
                    {
                        StringAppend(dst, sText_EnigmaBerry);
                    }
                }
                else
                {
                    CopyItemName(hword, dst);
                }
            }
            else
            {
                CopyItemName(hword, dst);
            }
            srcId += 3;
            break;
        }
    }
}

// Loads one of two text strings into the provided buffer. This is functionally
// unused, since the value loaded into the buffer is not read; it loaded one of
// two particles (either "は" or "の") which works in tandem with ChooseTypeOfMoveUsedString
// below to effect changes in the meaning of the line.
static void ChooseMoveUsedParticle(u8 *textBuff)
{
    s32 counter = 0;
    u32 i = 0;

    while (counter != MAX_MON_MOVES)
    {
        if (sGrammarMoveUsedTable[i] == 0)
            counter++;
        if (sGrammarMoveUsedTable[i++] == sBattleMsgDataPtr->currentMove)
            break;
    }

    if (counter >= 0)
    {
        if (counter <= 2)
            StringCopy(textBuff, sText_SpaceIs); // is
        else if (counter <= MAX_MON_MOVES)
            StringCopy(textBuff, sText_ApostropheS); // 's
    }
}

// Appends "!" to the text buffer `dst`. In the original Japanese this looked
// into the table of moves at sGrammarMoveUsedTable and varied the line accordingly.
//
// sText_ExclamationMark was a plain "!", used for any attack not on the list.
// It resulted in the translation "<NAME>'s <ATTACK>!".
//
// sText_ExclamationMark2 was "を つかった！". This resulted in the translation
// "<NAME> used <ATTACK>!", which was used for all attacks in English.
//
// sText_ExclamationMark3 was "した！". This was used for those moves whose
// names were verbs, such as Recover, and resulted in translations like "<NAME>
// recovered itself!".
//
// sText_ExclamationMark4 was "を した！" This resulted in a translation of
// "<NAME> did an <ATTACK>!".
//
// sText_ExclamationMark5 was " こうげき！" This resulted in a translation of
// "<NAME>'s <ATTACK> attack!".
static void ChooseTypeOfMoveUsedString(u8 *dst)
{
    s32 counter = 0;
    s32 i = 0;

    while (*dst != EOS)
        dst++;

    while (counter != MAX_MON_MOVES)
    {
        if (sGrammarMoveUsedTable[i] == MOVE_NONE)
            counter++;
        if (sGrammarMoveUsedTable[i++] == sBattleMsgDataPtr->currentMove)
            break;
    }

    switch (counter)
    {
    case 0:
        StringCopy(dst, sText_ExclamationMark);
        break;
    case 1:
        StringCopy(dst, sText_ExclamationMark2);
        break;
    case 2:
        StringCopy(dst, sText_ExclamationMark3);
        break;
    case 3:
        StringCopy(dst, sText_ExclamationMark4);
        break;
    case 4:
        StringCopy(dst, sText_ExclamationMark5);
        break;
    }
}

static const struct BattleWindowText sTextOnWindowsInfo_Normal[] = {
    [B_WIN_MSG] = {
        .fillValue = PIXEL_FILL(0xf),
        .fontId = FONT_NORMAL,
        .x = 2,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 1,
        .fgColor = 1,
        .bgColor = 15,
        .shadowColor = 6,
    },
    [B_WIN_ACTION_PROMPT] = {
        .fillValue = PIXEL_FILL(0xf),
        .fontId = FONT_NORMAL,
        .x = 2,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 1,
        .bgColor = 15,
        .shadowColor = 6,
    },
    [B_WIN_ACTION_MENU] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL_COPY_1,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_MOVE_NAME_1] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 1,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_MOVE_NAME_2] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 1,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_MOVE_NAME_3] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 1,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_MOVE_NAME_4] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 1,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_PP] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 12,
        .bgColor = 14,
        .shadowColor = 11,
    },
    [B_WIN_MOVE_TYPE] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_SMALL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_PP_REMAINING] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL_COPY_1,
        .x = 10,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 12,
        .bgColor = 14,
        .shadowColor = 11,
    },
    [B_WIN_DUMMY] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL_COPY_1,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_SWITCH_PROMPT] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL_COPY_1,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_LEVEL_UP_BOX] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 0,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_LEVEL_UP_BANNER] = {
        .fillValue = PIXEL_FILL(0x0),
        .fontId = FONT_SMALL,
        .x = 0x20,
        .y = 0,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 1,
        .bgColor = 0,
        .shadowColor = 2,
    },
    [B_WIN_YESNO] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 1,
        .lineSpacing = 2,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_PLAYER] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_OPPONENT] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_MULTI_PLAYER_1] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_MULTI_PLAYER_2] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_MULTI_PLAYER_3] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_MULTI_PLAYER_4] = {
        .fillValue = PIXEL_FILL(0xe),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 13,
        .bgColor = 14,
        .shadowColor = 15,
    },
    [B_WIN_VS_OUTCOME_DRAW] = {
        .fillValue = PIXEL_FILL(0x0),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 1,
        .bgColor = 0,
        .shadowColor = 6,
    },
    [B_WIN_VS_OUTCOME_LEFT] = {
        .fillValue = PIXEL_FILL(0x0),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 1,
        .bgColor = 0,
        .shadowColor = 6,
    },
    [B_WIN_VS_OUTCOME_RIGHT] = {
        .fillValue = PIXEL_FILL(0x0),
        .fontId = FONT_NORMAL,
        .x = 0,
        .y = 2,
        .letterSpacing = 0,
        .lineSpacing = 0,
        .speed = 0,
        .fgColor = 1,
        .bgColor = 0,
        .shadowColor = 6,
    },
    [B_WIN_OAK_OLD_MAN] = {
        .fillValue = PIXEL_FILL(0x1),
        .fontId = FONT_MALE,
        .x = 0,
        .y = 1,
        .letterSpacing = 0,
        .lineSpacing = 1,
        .speed = 1,
        .fgColor = 2,
        .bgColor = 1,
        .shadowColor = 3,
    }
};

static const u8 sNpcTextColorToFont[] = 
{
    [NPC_TEXT_COLOR_MALE]    = FONT_MALE, 
    [NPC_TEXT_COLOR_FEMALE]  = FONT_FEMALE, 
    [NPC_TEXT_COLOR_MON]     = FONT_NORMAL, 
    [NPC_TEXT_COLOR_NEUTRAL] = FONT_NORMAL,
};

// windowId: Upper 2 bits are text flags
//   x40: Use NPC context-defined font
//   x80: Inhibit window clear
void BattlePutTextOnWindow(const u8 *text, u8 windowId) {
    bool32 copyToVram;
    struct TextPrinterTemplate printerTemplate;
    u8 speed;
    int x;
    u8 color;

    u8 textFlags = windowId & 0xC0;
    windowId &= 0x3F;
    if (!(textFlags & 0x80))
        FillWindowPixelBuffer(windowId, sTextOnWindowsInfo_Normal[windowId].fillValue);
    if (textFlags & 0x40) {
        color = ContextNpcGetTextColor();
        printerTemplate.fontId = sNpcTextColorToFont[color];
    }
    else {
        printerTemplate.fontId = sTextOnWindowsInfo_Normal[windowId].fontId;
    }
    switch (windowId)
    {
    case B_WIN_VS_PLAYER:
    case B_WIN_VS_OPPONENT:
    case B_WIN_VS_MULTI_PLAYER_1:
    case B_WIN_VS_MULTI_PLAYER_2:
    case B_WIN_VS_MULTI_PLAYER_3:
    case B_WIN_VS_MULTI_PLAYER_4:
        x = (48 - GetStringWidth(sTextOnWindowsInfo_Normal[windowId].fontId, text,
                                 sTextOnWindowsInfo_Normal[windowId].letterSpacing)) / 2;
        break;
    case B_WIN_VS_OUTCOME_DRAW:
    case B_WIN_VS_OUTCOME_LEFT:
    case B_WIN_VS_OUTCOME_RIGHT:
        x = (64 - GetStringWidth(sTextOnWindowsInfo_Normal[windowId].fontId, text,
                                 sTextOnWindowsInfo_Normal[windowId].letterSpacing)) / 2;
        break;
    default:
        x = sTextOnWindowsInfo_Normal[windowId].x;
        break;
    }
    if (x < 0)
        x = 0;
    printerTemplate.currentChar = text;
    printerTemplate.windowId = windowId;
    printerTemplate.x = x;
    printerTemplate.y = sTextOnWindowsInfo_Normal[windowId].y;
    printerTemplate.currentX = printerTemplate.x;
    printerTemplate.currentY = printerTemplate.y;
    printerTemplate.letterSpacing = sTextOnWindowsInfo_Normal[windowId].letterSpacing;
    printerTemplate.lineSpacing = sTextOnWindowsInfo_Normal[windowId].lineSpacing;
    printerTemplate.unk = 0;
    printerTemplate.fgColor = sTextOnWindowsInfo_Normal[windowId].fgColor;
    printerTemplate.bgColor = sTextOnWindowsInfo_Normal[windowId].bgColor;
    printerTemplate.shadowColor = sTextOnWindowsInfo_Normal[windowId].shadowColor;
    if (windowId == B_WIN_OAK_OLD_MAN)
        gTextFlags.useAlternateDownArrow = FALSE;
    else
        gTextFlags.useAlternateDownArrow = TRUE;

    if ((gBattleTypeFlags & BATTLE_TYPE_LINK) || ((gBattleTypeFlags & BATTLE_TYPE_POKEDUDE) && windowId != B_WIN_OAK_OLD_MAN))
        gTextFlags.autoScroll = TRUE;
    else
        gTextFlags.autoScroll = FALSE;

    if (windowId == B_WIN_MSG || windowId == B_WIN_OAK_OLD_MAN)
    {
        if (gBattleTypeFlags & BATTLE_TYPE_LINK)
            speed = 1;
        else
            speed = GetTextSpeedSetting();
        gTextFlags.canABSpeedUpPrint = TRUE;
    }
    else
    {
        speed = sTextOnWindowsInfo_Normal[windowId].speed;
        gTextFlags.canABSpeedUpPrint = FALSE;
    }

    AddTextPrinter(&printerTemplate, speed, NULL);
    if (!(textFlags & 0x80))
    {
        PutWindowTilemap(windowId);
        CopyWindowToVram(windowId, COPYWIN_FULL);
    }
}

bool8 BattleStringShouldBeColored(u16 stringId)
{
    if (stringId == STRINGID_TRAINER1LOSETEXT
     || stringId == STRINGID_TRAINER2LOSETEXT
     || stringId == STRINGID_TRAINER1WINTEXT
     || stringId == STRINGID_TRAINER2WINTEXT)
        return TRUE;
    return FALSE;
}

void SetPpNumbersPaletteInMoveSelection(void)
{
    struct ChooseMoveStruct *chooseMoveStruct = (struct ChooseMoveStruct *)(&gBattleBufferA[gActiveBattler][4]);
    const u16 *palPtr = gPPTextPalette;
    u8 var = GetCurrentPpToMaxPpState(chooseMoveStruct->currentPp[gMoveSelectionCursor[gActiveBattler]],
                                      chooseMoveStruct->maxPp[gMoveSelectionCursor[gActiveBattler]]);

    gPlttBufferUnfaded[BG_PLTT_ID(5) + 12] = palPtr[(var * 2) + 0];
    gPlttBufferUnfaded[BG_PLTT_ID(5) + 11] = palPtr[(var * 2) + 1];

    CpuCopy16(&gPlttBufferUnfaded[BG_PLTT_ID(5) + 12], &gPlttBufferFaded[BG_PLTT_ID(5) + 12], PLTT_SIZEOF(1));
    CpuCopy16(&gPlttBufferUnfaded[BG_PLTT_ID(5) + 11], &gPlttBufferFaded[BG_PLTT_ID(5) + 11], PLTT_SIZEOF(1));
}

u8 GetCurrentPpToMaxPpState(u8 currentPp, u8 maxPp)
{
    if (maxPp == currentPp)
    {
        return 3;
    }
    else if (maxPp <= 2)
    {
        if (currentPp > 1)
            return 3;
        else
            return 2 - currentPp;
    }
    else if (maxPp <= 7)
    {
        if (currentPp > 2)
            return 3;
        else
            return 2 - currentPp;
    }
    else
    {
        if (currentPp == 0)
            return 2;
        if (currentPp <= maxPp / 4)
            return 1;
        if (currentPp > maxPp / 2)
            return 3;
    }

    return 0;
}
