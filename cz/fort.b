#!/usr/local/bin/cz --
use b

Main():
	let(n, 1)
	cstr choice = NULL
	Eachline(l):
		if randi(n) == 0:
			Free(choice)
			choice = strdup(l)
		++n
	if choice:
		Say(choice)
