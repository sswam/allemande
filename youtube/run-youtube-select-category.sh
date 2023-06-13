(for A in YOUTUBE/yt/*.txt; do
	N=`basename "$A"`
	N=${N%.txt}
	youtube-select-category.pl "$N" < "$A" |
		tee "${A%.txt}.md"
done)

(
cd YOUTUBE/yt
for A in *.md; do
	N=${A%.md}
	ln -f "$A" ../../generated/tourism/"$N"/youtube.md
done
)
