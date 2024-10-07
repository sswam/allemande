#!/bin/bash -eua
# searchalot:	Search a lot, using cross-product queries, using a lot of search engines and AIs

s="0.05"	# seconds to sleep between each search, plus a random suffix
a="type place"	# axes
t='$type in $place, $context'	# query template
l='Please list $query, as many as possible, in this format, i.e. a markdown dot-point list, with no additional commentary:

- Foo Bar
- Baz Quokka
- ...


Thanks for being awesome!'
r="results"	# directory for results
c="Vic, AU"	# context to add to each search
e="google youtube claude gpt4 tripadvisor"
S=	# don't sleep between searches
p=100	# number of parallel jobs

. opts

sleep=$s
axes=($a)
template=$t
template_llm=$l
results=$r
context=$c
engines=$e
no_sleep=$S
PARALLEL_MAX=$p
	
# -------- search engines ---------------------------------------------------

s_google() {
	local query=$1
	search -e google "$query"
}

s_youtube() {
	local query=$1
	search -e youtube "$query"
}

s_claude() {
	local query_llm=$2
	llm query -m c "$query_llm"
}

s_gpt4() {
	local query_llm=$2
	llm query -m 4 "$query_llm"
}

s_tripadvisor() {
	local query=$1
	search -e google "site:tripadvisor.com $query"
}

# -------- end search engines ------------------------------------------------

searchalot_search() {
	local engine=$1 query=$2 out=$3
	query_llm=$(eval 'printf %s "$template_llm"')
	"s_$engine" "$query" "$query_llm" | tee "$out"
}

searchalot_searches() {
	local crosspath=("$@")
	local query
	query=$(eval 'printf %s "$template"')
	echo >&2 "searchalot for: $query"
	query_esc=$(slugify "$query")
	n=0
	for engine in $engines; do
		out="$engine.$query_esc.txt"
		if [ -s "$out" ]; then
			echo >&2 "-     $engine: $query"
			continue
		fi
		echo >&2 "RUN   $engine: $query"
		. para searchalot_search "$engine" "$query" "$out"
		n=$[$n+1]
	done
	echo "$n"
	if [ "$n" != "0" ]; then
		if [ "$no_sleep" != "1" ]; then
			v sleep "$sleep$RANDOM"
		fi
	fi
}

searchalot_recurse() {
	# search through the cross-product space recursively
	local crosspath=("$@")
	local plen item list
	plen=${#crosspath[@]}
	if [ "$plen" = "$n_axes" ]; then
		searchalot_searches "${crosspath[@]}"
		return
	fi
	list=${lists[$plen]}
	while read item; do
		searchalot_recurse "${crosspath[@]}" "$item"
	done < "$list"
}

searchalot() {
	local lists=("$@")
	for list; do
		lists+=( $(readlink -f "$list") )
	done
	mkdir -p "$results"
	cd "$results"
	n_axes=${#axes[@]}
	I=0
	searchalot_recurisve "${lists[@]}"
	wait
}

if [ "$0" = "$BASH_SOURCE" ]; then
	searchalot "$@"
fi
