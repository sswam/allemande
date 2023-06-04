#!/usr/bin/make -f

CC      = gcc -std=gnu99
CFLAGS  = -Wall -Wextra -Werror -g

PREFIX  = /usr/local

LDLIBS  = -lws2_32
EXE     =

sshc$(EXE): sshc.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<
	hide-file $@
