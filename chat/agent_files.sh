#!/usr/bin/env bash
# [folders]...
# Lists agent YAML files in specified folders or defaults

# shellcheck disable=SC2034  # Disable shellcheck for ally options parser syntax

agent-files() {
	local stem= s=   # output stems (basename without .yml)
	local at= a=     # output stems prefixed with @
	local comma= c=  # output on single line joined with ', ' (implies -a if -s not set)
	local yaml= y=   # output as a YAML list (implies -s)

	eval "$(ally)"

	if [ "$comma" = 1 ] && [ "$stem" != 1 ]; then
		at=1
	fi
	if [ "$at" = 1 ] || [ "$yaml" = 1 ]; then
		stem=1
	fi

	local args=()
	if [ $# -gt 0 ]; then
		args=("${@/%//}")
	else
		args=("$ALLEMANDE_AGENTS/" "$ALLEMANDE_ROOMS/")
		args+=(-path "*/agents/*")
	fi

	local rel_paths=()
	mapfile -t rel_paths < <(find "${args[@]}" -type f -name "*.yml" | sed "s:^$ALLEMANDE_HOME/::")

	first=1
	for rel_path in "${rel_paths[@]}"; do
		local result
		result="$rel_path"
		if [ "$stem" = 1 ]; then
			result="$(basename "$result" | sed 's/\.yml$//')"
		fi
		if [ "$at" = 1 ]; then
			result="@$result"
		fi
		if [ "$comma" = 1 ] && [ $first -eq 0 ]; then
			printf ", "
		fi
		if [ "$yaml" = 1 ]; then
			result="  - $result"
		fi
		printf "%s" "$result"
		if [ "$comma" != 1 ]; then
			printf "\n"
		fi
		first=0
	done
	if [ "$comma" = 1 ]; then
		printf "\n"
	fi

}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	agent-files "$@"
fi

# version: 1.0.1
