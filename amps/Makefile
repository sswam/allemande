export PATH:=$(PWD)/boot:$(PATH)

bootstrap: sub/.tsort_commands .AMPS_shell

sub/.tsort_commands: sub/tsort_commands
	sub/tsort_commands </dev/null
.AMPS_shell:	AMPS_shell
	./AMPS_shell AMPS_shell >/dev/null

clean:
	rm -f .AMPS_shell sub/.tsort_commands
