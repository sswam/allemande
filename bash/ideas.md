# how to make shell scripts nicer?

- assume -e -u -o pipefail are on by default
- use a "check" function to run commands that must not fail
- use a better shell
- make my own shell, maybe compiled: brace / net2sh ...
- fix problem with long options and . opts
	- maybe don't use long options, but it's good to have long var-names...
	- could make opts more clever to automatically set the long option values
	- could use a different synax for varnames, like m_model=claude
