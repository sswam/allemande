# word_freq - Doug McIlroy's pipeline to show most frequent words
# warning: derived file, from word_freq

number_of_words= n=10	# number of frequent words to output

. AMPS_shell_init

[ $# = 2 ] || { echo >&2 usage: "$prog document most_frequent_n"; exit 2; }
[ -n "${1}" ] && ln -s "$(readlink -f "${1}")" "$work_dir/document"
[ -n "${2}" ] && ln -s "$(readlink -f "${2}")" "$work_dir/most_frequent_n"

cd "$work_dir"

tr	-cs	A-Za-z	'\n'	<document	>words
tr	A-Z	a-z	<words	>words_lc
sort	<words_lc	>words_sorted
uniq	-c	<words_sorted	>word_counts
sort	-rn	<word_counts	>by_frequency
head	-n "$number_of_words"	<by_frequency	>most_frequent_n
