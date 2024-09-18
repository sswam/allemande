#!/bin/bash -eua
# searchalot:	Search for a lot of things, in a lot of places, using a lot of search engines
s="0.05"	# seconds to sleep between each search, plus a random suffix
p="places.txt"	# file containing places to search in
t="types.txt"	# file containing types of things to search for
r="results"	# directory for results
c="Vic, AU"	# context to add to each search
S=	# don't sleep between searches

. opts

places=$p
types=$t
results=$r
sleep=$s
no_sleep=$S
context=$c

places=$(readlink -f "$places")
types=$(readlink -f "$types")

mkdir -p "$results"
cd "$results"

# WARNING: runs `wc -l places.txt` jobs in parallel, each with 6 processes, i.e. 132 jobs in parallel at the moment!

I=0

while read type; do
	echo >&2 "searchalot for: $type"
	while read place; do
		query="$type in $place, $context"
		echo >&2 "searchalot for: $query"
		llm_query="Please list $query, as many as possible, in this format:
- Foo Bar
- Baz Quokka
- ...
Thanks for being awesome!
"""
		query_esc=$(echo "$query" | sed 's/[^a-zA-Z0-9]/_/g; s/__*/_/g; s/^_//; s/_$//')
		n=0
		if [ ! -s "google.$query_esc.txt" ]; then
			echo >&2 "RUN   google: $query"
			search -e google "$query" | tee google.$query_esc.txt &
			n=$[$n+1]
		else
			echo >&2 "-     google: $query"
		fi
		if [ ! -s "youtube.$query_esc.txt" ]; then
			echo >&2 "RUN   youtube: $query"
			search -e youtube "$query" | tee youtube.$query_esc.txt &
			n=$[$n+1]
		else
			echo >&2 "-     youtube: $query"
		fi
		if [ ! -s "claude.$query_esc.txt" ]; then
			echo >&2 "RUN   claude: $query"
			llm query -m c "$llm_query" | tee claude.$query_esc.txt &
			n=$[$n+1]
		else
			echo >&2 "-     claude: $query"
		fi
		if [ ! -s "gpt4.$query_esc.txt" ]; then
			echo >&2 "RUN   gpt4: $query"
			llm query -m 4 "$llm_query" | tee gpt4.$query_esc.txt &
			n=$[$n+1]
		else
			echo >&2 "-     gpt4: $query"
		fi
		if [ ! -s "tripadvisor.$query_esc.txt" ]; then
			echo >&2 "RUN   tripadvisor: $query"
			search -e google "site:tripadvisor.com $query" | tee tripadvisor.$query_esc.txt &
			n=$[$n+1]
		else
			echo >&2 "-     tripadvisor: $query"
		fi
		echo "$n"
		if [ "$n" != "0" ]; then
			if [ "$no_sleep" != "1" ]; then
				v sleep "$sleep$RANDOM"
			fi
		fi
	done < "$places"

	I=$[$I+1]

	if [ $(( I % 1 )) = 0 ]; then
		echo "Waiting for all jobs to finish..."
		wait
	fi
done < "$types"
wait
