/* ramp-io
   license: GPL by infection from redshift :(
   this file is in the public domain
*/

#include <stdio.h>
#include <string.h>
#include "gamma-randr.h"

static randr_state_t _state;
static randr_state_t *state = &_state;
static int n_screens;
static char buf[256];

void die(char *s)
{
	fprintf(stderr, "%s\n", s);
	exit(1);
}

void say(char *s)
{
	printf("%s\n", s);
}

void sayn(int d)
{
	printf("%d\n", d);
}

void nl(void)
{
	printf("\n");
}

void chomp(char *buf)
{
	int l = strlen(buf);
	if (l > 0 && buf[l-1] == '\n')
		buf[l-1] = '\0';
}

int getn(void)
{
	if (!fgets(buf, sizeof(buf), stdin))
		exit(0);
	chomp(buf);
	return atoi(buf);
}

char *get(void)
{
	if (!fgets(buf, sizeof(buf), stdin))
		exit(0);
	chomp(buf);
	return buf;
}

void getnl(void)
{
	if (!fgets(buf, sizeof(buf), stdin))
		exit(0);
	chomp(buf);
	if (*buf)
		die("missing nl");
}

void output(void)
{
	sayn(n_screens);
	nl();
	for (int i=0; i<n_screens; ++i) {
		sayn(i);
		int ramp_size = state->crtcs[i].ramp_size;
		sayn(ramp_size);
		say("R");
		for (int j=0; j<ramp_size; ++j) {
			sayn(state->crtcs[i].saved_ramps[j]);
		}
		say("G");
		for (int j=ramp_size; j<ramp_size*2; ++j) {
			sayn(state->crtcs[i].saved_ramps[j]);
		}
		say("B");
		for (int j=ramp_size*2; j<ramp_size*3; ++j) {
			sayn(state->crtcs[i].saved_ramps[j]);
		}
		nl();
	}
}

void input(void)
{
	if (getn() != n_screens)
		die("wrong n_screens");
	getnl();
	for (int i=0; i<n_screens; ++i) {
		if (getn() != i)
			die("wrong screen number");
		int ramp_size = state->crtcs[i].ramp_size;
		if (getn() != ramp_size)
			die("wrong ramp size");
		if (strcmp(get(), "R"))
			die("missing R");
		for (int j=0; j<ramp_size; ++j) {
			state->crtcs[i].saved_ramps[j] = (uint16_t)getn();
		}
		if (strcmp(get(), "G"))
			die("missing G");
		for (int j=ramp_size; j<ramp_size*2; ++j) {
			state->crtcs[i].saved_ramps[j] = (uint16_t)getn();
		}
		if (strcmp(get(), "B"))
			die("missing B");
		for (int j=ramp_size*2; j<ramp_size*3; ++j) {
			state->crtcs[i].saved_ramps[j] = (uint16_t)getn();
		}
		getnl();
	}
}

int main(int argc, char *argv[])
{
	if (randr_init(state) != 0)
		die("failed: randr_init");
	if (randr_start(state) != 0)
		die("failed: randr_start");
	n_screens = state->crtc_count;
	output();
	input();
	randr_restore(state);
	randr_free(state);
	return 0;
}

