@ POK-44: o aviso de conquista. Conquistas_TentarAviso (src/conquistas_aviso.c) põe este script no campo quando há
@ prêmio a entregar; o special entrega o prêmio, mostra a janela e reativa o script ao fechar (waitstate).
EventScript_AvisoConquista::
	goto_if_questlog EventScript_ReleaseEnd
	lockall
	special Conquistas_MostrarAviso
	waitstate
	releaseall
	end

