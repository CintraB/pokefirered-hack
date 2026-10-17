# Runner do mGBA usado pela esteira de testes (roda dentro do WSL): headless por padrão, com
# janela SDL2 em tempo real no modo --window ("assistir").
# Requer: libmgba-dev (0.10.5), libpng-dev e libsdl2-dev.

CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra -std=gnu11
SDL_CFLAGS := $(shell sdl2-config --cflags)
SDL_LIBS := $(shell sdl2-config --libs)
LDLIBS = -lmgba $(SDL_LIBS)

all: mgba_runner

mgba_runner: mgba_runner.c
	$(CC) $(CFLAGS) $(SDL_CFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f mgba_runner

.PHONY: all clean
