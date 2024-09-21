#!/bin/bash -eu
# ["some note"]
# Add a note to $NOTE/note.md or another file there.
# We can use subdirs and symlinks to put notes in the right place,
# i.e. a conceptual to filesystem mapping.

# Examples:
# note ["some note"]
# note -f details.md -e ["some note"]
# note -t bug ["some bug"]
# note -I ["some idea"]
# note -t project/todo ["some todo"]

# Notes file format is markdown:
# - one line between notes
# - assume file ends with newline
# - two blank lines between days
# - date format like: ## 2019-01-01
# - note format like: ### some note
# - blank line then details if given

t=note	# type of note (file stem or path)
l=	# choose from a list of note files
f=	# load note from file
e=	# edit the note file
v=	# view the note file in pager
c=	# cat the note file
d=	# show all notes from today
s=	# AI summary for the day
n=	# Show last n headings
A=	# don't add a note
timeout=  # time limit

# shortcuts for common note types

I=	# idea
T=	# todo
X=	# bug
P=	# personal development
B=	# bookmark
C=	# crazy
Z=	# naughty
W=	# waywo

D=${NOTE:-$HOME/note}	# notes dir

# bash aliases:

# alias idea='note -I'
# alias todo='note -T'
# alias bug='note -X'
# alias pdev='note -P'
# alias bookmark='note -B'
# alias crazy='note -C'
# alias naughty='note -Z'

. opts
. confirm

note=$*
details=

if [ -n "$timeout" ]; then
	timeout="-t $timeout"
fi

# shortcuts for common note types
# maybe these should be configurable
# not that this will ever be used by anyone else!

if [ -n "$I" ]; then
	t=idea
elif [ -n "$T" ]; then
	t=todo
elif [ -n "$X" ]; then
	t=bug
elif [ -n "$P" ]; then
	t=pdev
elif [ -n "$B" ]; then	# not sure if I will use this, need to think about a good boomark system
	t=bookmark
elif [ -n "$C" ]; then
	t=crazy
elif [ -n "$Z" ]; then
	t=naughty
elif [ -n "$W" ]; then
	t=waywo
fi


warn_int() {
	echo -n $'!   \b\b'
	trap - INT
}

trap 'warn_int' INT


# List the note files?
if [ -n "$l" ]; then
	readarray -t files < <(find "$D" -follow \( -name '.*' -o -name 'summary' \) -prune -o -type f -printf '%P\n' | sort)
	for i in "${!files[@]}"; do
		printf "%3s. %s\n" "$i" "${files[$i]%.*}"
	done
	echo

	# prompt for a note file
	read -e -p "? " num
	if [ -n "$num" ]; then
		t=${files[$num]}
		t=${t%.md}
	else
		exit 1
	fi
fi


show_all_notes() {
	readarray -t files < <(find "$D" -follow -name '.*' -prune -o -type f -printf '%P\n' | sort)
	date=$(day)
	for i in "${!files[@]}"; do
		printf "# %s\n\n" "${files[$i]%.*}"
		sed -n "/^## $date$/,\$p" "$D/${files[$i]}"
		printf "\n\n"
	done
	echo
	exit
}

# Show all notes from today?
if [ -n "$d" ]; then
	show_all_notes
fi


# AI summary for the day?
if [ -n "$s" ]; then
	mkdir -p "$D/summary"
	summary_file=$D/summary/$(day -s=-).md
	show_all_notes |
	summary.sh | fmt | tee "$summary_file"
	< "$summary_file" proc "How focused or distracted was I today? Please give advice to improve." |
	fmt | tee -a "$summary_file"
	exit
fi


# create notes directory
mkdir -p "$D"


# find the note file
# look for no extension (or given extension), .md, .txt in order

for ext in '' .md .txt; do
	note_file=$D/$t$ext
	if [ -e "$note_file" ]; then
		break
	fi
done


# create new markdown note file if not found
if [ ! -e "$note_file" ]; then
	note_file=$D/$t.md
	>> "$note_file"
fi


# Show last n headings?
if [ -n "$n" ]; then
	< "$note_file" grep '^### ' | tail -n "$n" | cut -c5-
fi


# Cat the note file?
if [ -n "$c" ]; then
	if which batcat >/dev/null 2>&1; then
		batcat --style plain "$note_file"
	else
		cat "$note_file"
	fi
	exit
fi


# View the note file?
if [ -n "$v" ]; then
	"${PAGER:-less}" "$note_file"
	exit
fi


# Load the note from a file?

if [ -n "$f" ]; then
	if [ ! -r "$f" ]; then
		echo >&2 "Can't read input file: $f"
		exit 1
	fi
	details=$(<"$f")
fi


# If details from a file, note defaults to the filename stem
if [ -z "$note" ] && [ -n "$details" ]; then
	note=$(basename "$f")
	note=${note%.*}

# If no note or details, and not editing, read note and optional details from stdin
elif [ -z "$A" ] && [ -z "$note" ] && [ -z "$details" ] && [ "$e" != 1 ]; then
	read -e -p ": " $timeout note
	if [ -t 0 -a -t 2 ]; then
		while read -e -p ". " line; do
			if [ "$line" = "." ]; then
				break
			fi
			details="$details$line"$'\n'
		done
	else
		details=$(cat)
	fi
fi


# add the note to the note file, if given

if [ -n "$note" ]; then
	# add a blank line between notes

	if [ -s "$note_file" ]; then
		printf "\n" >> "$note_file"
	fi

	# add date to note file if not already there

	date=$(day)

	if ! grep -q "^#* *$date$" "$note_file"; then
		if [ -s "$note_file" ]; then
			printf "\n" >> "$note_file"
		fi
		printf "## %s\n\n" "$date" >> "$note_file"
	fi

	# add the note to the note file

	printf "### %s\n" "$note" >> "$note_file"

	# strip leading and trailing whitespace from details
	details=${details##[[:space:]]}
	details=${details%%[[:space:]]}

	# add details to the note file

	if [ -n "$details" ]; then
		printf "\n%s\n" "$details" >> "$note_file"
	fi
fi


# edit the note file if requested
if [ "$e" = 1 ]; then
	$EDITOR "$note_file"
fi


# Idea, use Jewish idea that day starts at sunset, might work better than midnight
# as I often work late. Dinnertime is a good break point.
