#!/bin/bash -eu
# netlogo-describe.sh: describe all the functions in the netlogo project

retry_delay=30

for A in `lsd`; do
	echo "$A"
	(
		cd "$A"
		touch "all.md"
		while read func; do
			if [ -e "$func.md" ]; then
				continue
			fi
			while true; do
				v netlogo-function-summary.sh "all.md" "$func" |
				tee -a "all.md" > "$func.md"
				if [ -s "$func.md" ]; then
					break
				fi
				sleep $retry_delay
				echo >&2 "Retrying $func"
			done
		done < order.txt
	)
done
