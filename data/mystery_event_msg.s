@ These are event scripts. They should not be moved to C.

#include "constants/global.h"
#include "constants/flags.h"
#include "constants/moves.h"
#include "constants/songs.h"
#include "constants/species.h"
#include "constants/vars.h"
#include "constants/items.h"
#include "constants/region_map_sections.h"
	.include "asm/macros.inc"
	.include "asm/macros/event.inc"
	.include "constants/constants.inc"

	.section .rodata
	
	.align 2
MysteryEventScript_StampCard::
	setvaddress MysteryEventScript_StampCard
	setorcopyvar VAR_RESULT, 1
	specialvar VAR_0x8008, GetMysteryGiftCardStat
	setorcopyvar VAR_RESULT, 0
	specialvar VAR_0x8009, GetMysteryGiftCardStat
	subvar VAR_0x8008, VAR_0x8009
	buffernumberstring STR_VAR_1, VAR_0x8008
	lock
	faceplayer
	vmessage sText_MysteryGiftStampCard
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftStampCard:
	.string "Agradecemos por usar o sistema\n"
	.string "Cartão de Selos.\p"
	.string "Faltam {STR_VAR_1} para você\n"
	.string "completar o seu Cartão de Selos.$"

MysteryEventScript_SurfPichu::
	setvaddress MysteryEventScript_SurfPichu
	vgoto_if_unset FLAG_MYSTERY_GIFT_DONE, SurfPichu_GiveIfPossible
	returnram

SurfPichu_GiveIfPossible:
	specialvar VAR_EVENT_PICHU_SLOT, CalculatePlayerPartyCount
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, PARTY_SIZE, SurfPichu_FullParty
	setflag FLAG_MYSTERY_GIFT_DONE
	vcall SurfPichu_GiveEgg
	lock
	faceplayer
	vmessage sText_MysteryGiftEgg
	waitmessage
	waitbuttonpress
	playfanfare MUS_OBTAIN_ITEM
	waitfanfare
	release
	end

SurfPichu_FullParty:
	lock
	faceplayer
	vmessage sText_FullParty
	waitmessage
	waitbuttonpress
	release
	end

SurfPichu_GiveEgg:
	giveegg SPECIES_PICHU
	setmonmodernfatefulencounter VAR_EVENT_PICHU_SLOT
	setmonmetlocation VAR_EVENT_PICHU_SLOT, METLOC_FATEFUL_ENCOUNTER
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 1, SurfPichu_Slot1
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 2, SurfPichu_Slot2
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 3, SurfPichu_Slot3
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 4, SurfPichu_Slot4
	vgoto_if_eq VAR_EVENT_PICHU_SLOT, 5, SurfPichu_Slot5
	return

SurfPichu_Slot1:
	setmonmove 1, 2, MOVE_SURF
	return

SurfPichu_Slot2:
	setmonmove 2, 2, MOVE_SURF
	return

SurfPichu_Slot3:
	setmonmove 3, 2, MOVE_SURF
	return

SurfPichu_Slot4:
	setmonmove 4, 2, MOVE_SURF
	return

SurfPichu_Slot5:
	setmonmove 5, 2, MOVE_SURF
	return

sText_MysteryGiftEgg:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "O Centro Pokémon tem um\n"
	.string "presente: um Ovo de Pokémon!\p"
	.string "Crie-o com amor e carinho.$"

sText_FullParty:
	.string "Ah, parece que a sua equipe\n"
	.string "está cheia.\p"
	.string "Venha me ver depois de guardar\n"
	.string "um Pokémon no PC.$"

MysteryEventScript_VisitingTrainer::
	setvaddress MysteryEventScript_VisitingTrainer
	special ValidateEReaderTrainer
	vgoto_if_eq VAR_RESULT, 0, MysteryEventScript_VisitingTrainerArrived
	lock
	faceplayer
	vmessage sText_MysteryGiftVisitingTrainer
	waitmessage
	waitbuttonpress
	release
	end

MysteryEventScript_VisitingTrainerArrived:
	lock
	faceplayer
	vmessage sText_MysteryGiftVisitingTrainer_2
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftVisitingTrainer:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Com este Cartão Maravilha, você\n"
	.string "pode participar de uma pesquisa\l"
	.string "num Poké Mart.\p"
	.string "Use essas pesquisas para convidar\n"
	.string "Treinadores para as Ilhas Sevii.\p"
	.string "…Vou lhe dar uma senha secreta\n"
	.string "para a pesquisa:\p"
	.string "“Me dá\n"
	.string "Treinador incrível”\p"
	.string "Escreva isso na pesquisa e envie\n"
	.string "pela Comunicação Sem Fio.$"

sText_MysteryGiftVisitingTrainer_2:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Um Treinador chegou às Ilhas Sevii\n"
	.string "procurando por você.\p"
	.string "Esperamos que você goste de\n"
	.string "batalhar com o Treinador visitante.\p"
	.string "Você pode convidar outros\n"
	.string "Treinadores inserindo outras senhas.\p"
	.string "Tente descobrir outras senhas\n"
	.string "que possam funcionar.$"

MysteryEventScript_BattleCard::
	setvaddress MysteryEventScript_BattleCard
	vgoto_if_set FLAG_MYSTERY_GIFT_DONE, MysteryEventScript_BattleCardInfo
	setorcopyvar VAR_RESULT, 2
	specialvar VAR_0x8008, GetMysteryGiftCardStat
	vgoto_if_ne VAR_0x8008, 3, MysteryEventScript_BattleCardInfo
	lock
	faceplayer
	vmessage sText_MysteryGiftBattleCountCard_2
	waitmessage
	waitbuttonpress
	giveitem ITEM_POTION
	release
	setflag FLAG_MYSTERY_GIFT_DONE
	end

MysteryEventScript_BattleCardInfo:
	lock
	faceplayer
	vmessage sText_MysteryGiftBattleCountCard
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftBattleCountCard:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "O seu Cartão Contador de Batalhas\n"
	.string "registra o seu retrospecto contra\l"
	.string "Treinadores com o mesmo cartão.\p"
	.string "Procure e batalhe com Treinadores\n"
	.string "que tenham o mesmo cartão que você.\p"
	.string "Você pode conferir o ranking geral\n"
	.string "lendo as Notícias.\p"
	.string "Experimente, por favor!$"

sText_MysteryGiftBattleCountCard_2:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Parabéns!\p"
	.string "Você ganhou um prêmio por vencer\n"
	.string "três batalhas!\p"
	.string "Esperamos que isso inspire você\n"
	.string "a batalhar ainda mais.$"

MysteryEventScript_AuroraTicket::
	setvaddress MysteryEventScript_AuroraTicket
	lock
	faceplayer
	vgoto_if_set FLAG_RECEIVED_AURORA_TICKET, AuroraTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_DEOXYS, AuroraTicket_Obtained
	checkitem ITEM_AURORA_TICKET, 1
	vgoto_if_eq VAR_RESULT, TRUE, AuroraTicket_Obtained
	vmessage sText_AuroraTicket1
	waitmessage
	waitbuttonpress
	checkitemspace ITEM_AURORA_TICKET, 1
	vgoto_if_eq VAR_RESULT, FALSE, AuroraTicket_NoBagSpace
	giveitem ITEM_AURORA_TICKET
	setflag FLAG_ENABLE_SHIP_BIRTH_ISLAND
	setflag FLAG_RECEIVED_AURORA_TICKET
	vmessage sText_AuroraTicket2
	waitmessage
	waitbuttonpress
	release
	end

AuroraTicket_NoBagSpace:
	vmessage sText_AuroraTicketNoPlace
	waitmessage
	waitbuttonpress
	release
	end

AuroraTicket_Obtained:
	vmessage sText_AuroraTicketGot
	waitmessage
	waitbuttonpress
	release
	end

sText_AuroraTicket1:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Você deve ser {PLAYER}.\n"
	.string "Há um bilhete aqui para você.$"

sText_AuroraTicket2:
	.string "Parece que é para usar no\n"
	.string "Porto Vermilion.\p"
	.string "Que tal experimentar e descobrir\n"
	.string "do que se trata?$"

sText_AuroraTicketGot:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.$"

sText_AuroraTicketNoPlace:
	.string "Ah, sinto muito, {PLAYER}.\n"
	.string "O Bolso Itens-chave da sua\l"
	.string "Bolsa está cheio.\p"
	.string "Guarde algo no PC e depois\n"
	.string "volte para buscar isto.$"

MysteryEventScript_MysticTicket::
	setvaddress MysteryEventScript_MysticTicket
	lock
	faceplayer
	vgoto_if_set FLAG_RECEIVED_MYSTIC_TICKET, MysticTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_LUGIA, MysticTicket_Obtained
	vgoto_if_set FLAG_FOUGHT_HO_OH, MysticTicket_Obtained
	checkitem ITEM_MYSTIC_TICKET, 1
	vgoto_if_eq VAR_RESULT, TRUE, MysticTicket_Obtained
	vmessage sText_MysticTicket2
	waitmessage
	waitbuttonpress
	checkitemspace ITEM_MYSTIC_TICKET, 1
	vgoto_if_eq VAR_RESULT, FALSE, MysticTicket_NoBagSpace
	giveitem ITEM_MYSTIC_TICKET
	setflag FLAG_ENABLE_SHIP_NAVEL_ROCK
	setflag FLAG_RECEIVED_MYSTIC_TICKET
	vmessage sText_MysticTicket1
	waitmessage
	waitbuttonpress
	release
	end

MysticTicket_NoBagSpace:
	vmessage sText_MysticTicketNoPlace
	waitmessage
	waitbuttonpress
	release
	end

MysticTicket_Obtained:
	vmessage sText_MysticTicketGot
	waitmessage
	waitbuttonpress
	release
	end

sText_MysticTicket2:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Você deve ser {PLAYER}.\n"
	.string "Há um bilhete aqui para você.$"

sText_MysticTicket1:
	.string "Parece que é para usar no\n"
	.string "Porto Vermilion.\p"
	.string "Que tal experimentar e descobrir\n"
	.string "do que se trata?$"

sText_MysticTicketGot:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.$"

sText_MysticTicketNoPlace:
	.string "Ah, sinto muito, {PLAYER}.\n"
	.string "O Bolso Itens-chave da sua\l"
	.string "Bolsa está cheio.\p"
	.string "Guarde algo no PC e depois\n"
	.string "volte para buscar isto.$"

MysteryEventScript_AlteringCave::
	setvaddress MysteryEventScript_AlteringCave
	addvar VAR_ALTERING_CAVE_WILD_SET, 1
	vgoto_if_ne VAR_ALTERING_CAVE_WILD_SET, 10, MysteryEventScript_AlteringCave_
	setvar VAR_ALTERING_CAVE_WILD_SET, 0
MysteryEventScript_AlteringCave_:
	lock
	faceplayer
	vmessage sText_MysteryGiftAlteringCave
	waitmessage
	waitbuttonpress
	release
	end

sText_MysteryGiftAlteringCave:
	.string "Agradecemos por usar o sistema\n"
	.string "Presente Misterioso.\p"
	.string "Recentemente, houve rumores de\n"
	.string "aparições de Pokémon raros.\p"
	.string "Os rumores são sobre a\n"
	.string "Caverna Mutante, na\l"
	.string "Ilha Proscrita.\p"
	.string "Que tal ir até lá conferir se os\n"
	.string "rumores são mesmo verdadeiros?$"
