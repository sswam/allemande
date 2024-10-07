#!/bin/bash

# Script to generate and print eval commands for each argument
# Usage: e VARIABLE 'COMMAND' ARG1 ARG2 ...
# Example: e A 'echo touch $A/.keep' *

# Assign the first argument to V (variable name)
varname="$1"

# Assign the second argument to X (command to execute)
command_line="$2"

# Shift the first two arguments off, leaving only the remaining args
shift 2

# Loop through each remaining argument
for arg; do
	# Print shell code that sets the variable to the current argument
	# and then executes the specified command
	printf "$varname=%q; $command_line\n" "$arg"
done

# Here's the bash script with added comments explaining its functionality:

# This script generates eval commands that set a variable to each provided argument and then execute a specified command. It's useful for performing operations on multiple items where you need to reference each item within the command.

