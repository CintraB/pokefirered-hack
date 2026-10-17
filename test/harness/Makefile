# Runner do mGBA usado pela esteira de testes (roda dentro do WSL): headless por padrão, com
# janela SDL2 em tempo real no modo --window ("assistir").
# Requer: libmgba-dev (0.10.5) e libpng-dev. libsdl2-dev é OPCIONAL: sem ela (sdl2-config ausente)
# o runner compila sem --window (que então sai com código 2 e uma mensagem); o pipeline e o
# modo rápido não dependem de janela.

CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra -std=gnu11
LDLIBS = -lmgba

# `sdl2-config` ausente ou falhando = sem SDL2 (silencioso: nem `make clean` reclama).
SDL_LIBS := $(shell sdl2-config --libs 2>/dev/null)
ifneq ($(strip $(SDL_LIBS)),)
SDL_CFLAGS := -DUSE_SDL $(shell sdl2-config --cflags 2>/dev/null)
LDLIBS += $(SDL_LIBS)
endif

all: mgba_runner

mgba_runner: mgba_runner.c
	$(CC) $(CFLAGS) $(SDL_CFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f mgba_runner

.PHONY: all clean
