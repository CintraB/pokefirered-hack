# Runner headless do mGBA usado pela esteira de testes (roda dentro do WSL).
# Requer: libmgba-dev (0.10.5) e libpng-dev.

CC ?= cc
CFLAGS ?= -O2 -g -Wall -Wextra -std=gnu11
LDLIBS = -lmgba

all: mgba_runner

mgba_runner: mgba_runner.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f mgba_runner

.PHONY: all clean
