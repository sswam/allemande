#!/bin/bash -eu
# tz:	what timezone is that place?!

timezones="$(dirname "$(readlink -f "$0")")/country_city_timezone.tsv"

field-grep() {
	local ignore_case=0
	if [ $1 == -i ]; then
		shift
		ignore_case=1
	fi
	local field_number=$1 expression=$2
	awk -F'\t' "BEGIN{IGNORECASE=$ignore_case} \$$field_number ~ /$expression/"
}

for place; do
	field-grep -i 1 "$place" < "$timezones"
	echo >&2
	field-grep -i 2 "$place" < "$timezones"
	echo >&2
	echo >&2
done
