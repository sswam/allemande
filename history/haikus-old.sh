shuf /usr/share/dict/words |
grep -i '^[a-z]*$' |
head -n 5 |
(
	while read A; do
		for m in 4 3+ c i; do
			(v query -m=$m "Please write a beautiful haiku on the topic of '$A'." 2>&1; echo) &
		done
	done
	wait
)
