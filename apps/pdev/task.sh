#!/bin/bash -eu

# Categorize tasks into the Eisenhower Matrix

task-process() {
	local edit= e= # edit only
	local no_edit= E= # skip editing
	local crisis= c= # show crisis tasks only
	local plan= p= # show plan only
	local interrupt= i= # interrupt only
	local distract= d= # distract only
	local all= a= # show all tasks

	eval "$(ally)"

	(
		cd "${TASK_DIR:-$HOME/task}"

		if [ "$crisis" = 1 ]; then exec cat 1-crisis.md; fi
		if [ "$plan" = 1 ]; then exec cat 2-plan.md; fi
		if [ "$interrupt" = 1 ]; then exec cat 3-interrupt.md; fi
		if [ "$distract" = 1 ]; then exec cat 4-distract.md; fi
		if [ "$all" = 1 ]; then exec cat-named -P"# " [1-4]-*.md; fi

		# Edit only case
		if [ "$edit" = 1 ]; then
			exec vim -S task.vim
		fi

		# Process input first
		cat-named --stdin-name "new tasks" comments.md mission.m [0-4]-*.md - |
			process "Please categorize new tasks (only) into the Eisenhower Matrix, compactly, and strictly following the same format as the input but omitting empty sections." |
			split-files -a -

		# Edit after processing unless disabled
		if [ "$no_edit" != 1 ]; then
			exec vim -S task.vim
		fi
	)
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	task-process "$@"
fi

# version: 0.1.1
