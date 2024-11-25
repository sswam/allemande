CFLAGS=-Wall -Wextra -Werror `pkg-config --cflags sdl2 SDL2_mixer`
LD_LIBS=-lglut -lGL -lGLU -lm -lSDL2 -lSDL2_mixer
CC=gcc

game1: game1.o
	$(CC) -o $@ $< $(LD_LIBS)
