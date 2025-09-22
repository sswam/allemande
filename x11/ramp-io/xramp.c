#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int iclamp(int x, int a, int b) {
	return x < a ? a : (x > b ? b : x);
}

int ramp_range(float f) {
	return iclamp((int)(f * 65536), 0, 65535);
}

void xramp(float r0, float r1, float g0, float g1, float b0, float b1) {
	int rr0 = ramp_range(r0);
	int rr1 = ramp_range(r1);
	int rg0 = ramp_range(g0);
	int rg1 = ramp_range(g1);
	int rb0 = ramp_range(b0);
	int rb1 = ramp_range(b1);

	char command[256];
	snprintf(command, sizeof(command), "ramp-gen %d %d %d %d %d %d | ramp-io >/dev/null", rr0, rr1, rg0, rg1, rb0, rb1);
	system(command);
}

void usage() {
	printf("Usage:	xramp [args]\n"
		"	xramp f                 - set all channels to f\n"
		"	xramp f0 f1             - set all channels to f0, f1\n"
		"	xramp r1 g1 b1          - set red to r1, green to g1, blue to b1\n"
		"	xramp r0 r1 g0 g1 b0 b1 - set red to r0, r1, green to g0, g1, blue to b0, b1\n");
}

int main(int argc, char *argv[]) {
	if (argc == 2 && strcmp(argv[1], "-h") == 0) {
		usage();
	} else if (argc == 1) {
		xramp(0, 1, 0, 1, 0, 1);
	} else if (argc == 2) {
		float f = atof(argv[1]);
		xramp(0, f, 0, f, 0, f);
	} else if (argc == 3) {
		float f0 = atof(argv[1]);
		float f1 = atof(argv[2]);
		xramp(f0, f1, f0, f1, f0, f1);
	} else if (argc == 4) {
		float r1 = atof(argv[1]);
		float g1 = atof(argv[2]);
		float b1 = atof(argv[3]);
		xramp(0, r1, 0, g1, 0, b1);
	} else if (argc == 7) {
		float r0 = atof(argv[1]);
		float r1 = atof(argv[2]);
		float g0 = atof(argv[3]);
		float g1 = atof(argv[4]);
		float b0 = atof(argv[5]);
		float b1 = atof(argv[6]);
		xramp(r0, r1, g0, g1, b0, b1);
	} else {
		usage();
		return 1;
	}

	return 0;
}
