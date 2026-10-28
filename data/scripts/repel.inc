@ Repel automático: ao acabar o efeito, oferece usar outro repelente da bolsa
@ (o último usado, ou outro que houver; GetRepelToReuse em field_specials.c).
EventScript_RepelWoreOff::
	lockall
	specialvar VAR_RESULT, GetRepelToReuse
	goto_if_eq VAR_RESULT, ITEM_NONE, EventScript_RepelWoreOffNoneLeft
	copyvar VAR_0x8004, VAR_RESULT
	bufferitemname STR_VAR_2, VAR_0x8004
	msgbox Text_RepelWoreOffUseAnother, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, EventScript_RepelWoreOffEnd
	special UseRepelFromField
	playse SE_REPEL
	msgbox Text_PlayerUsedRepel
	waitse
EventScript_RepelWoreOffEnd:
	closemessage
	releaseall
	end

EventScript_RepelWoreOffNoneLeft:
	msgbox Text_RepelWoreOff
	goto EventScript_RepelWoreOffEnd

Text_RepelWoreOff::
	.string "O efeito do Repelente acabou…$"

Text_RepelWoreOffUseAnother::
	.string "O efeito do Repelente acabou…\p"
	.string "Usar outro {STR_VAR_2}?$"

Text_PlayerUsedRepel::
	.string "{PLAYER} usou {STR_VAR_2}.$"
