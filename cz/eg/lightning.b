#!/usr/local/bin/cz --

use b

int duration = 5 * 60

Main:
	getargs(int, duration)
	# any remaining args are a command to run at timeout
	space(200, 100)
	gprint_anchor(0,0)
	font("helvetica-medium", 120)

	home() ; move() ; north(20)
	gsayf("%d", duration)
	Paint()

	gr_do_delay(time_forever)

	num start = rtime()
	repeat:
		num now = rtime()
		int elapsed = now - start
		int remaining = duration - elapsed
		clear()
		home() ; move() ; north(20)
		gsayf("%d", remaining)
		Paint()
		Rsleep(0.1)
		if remaining == 0:
			break
	Systemv(arg[0], arg)
	gr_exit(0)
