#!/usr/bin/env bash

# [options] [filename.md|html [prompt]]
# 
# Write me a story!
#
# Examples:
#
# story pigs1.md "for children 5 years old. The three little pigs"
# story pigs2.md "for adults in the style of Fables, don't hold back. The three little pigs"
# story -i pigs3.md "for 12 years old, spice it up a bit and make it fun. The three little pigs"
# story -i godzilla.md "in the style of a TV news report, make it fun. Godzilla takes over Melbourne, Australia"
# combo -p="You can redo the pictures in the same syntax please" pigs3.md godzilla.md | tee combo.md
# story -i="cartoony for a children's book" ; mv story.md charlie.md
# story -i="horror, at night, realistic" horror.md "a scary horror story, with lots bit of blood and gore please"

story() {
	local model= m=	# model
	local edit= e=1	# open in the editor before illustrating
	local view= v=1	# view the result in Chrome with markdown plugin
	local illustrate= i=	# illustrate, prompt prefix for image generation, also shown to the LLM
	local positive0= p=	# extra positive prompts for image generation, prepended
	local positive1= q=	# extra positive prompts for image generation, appended
	local negative= n=	# negative prompt for image generation
	local module= M=	# path to a Python module with prompts(pos, neg) -> (pos, neg), to alter image prompts
	local count= c=4	# number of images to generate for each illustration
	local standard= s=1	# include the standard prompt "Please write a story"
	local continue= C=	# continue the story, give text to feed the AI from that text onwards
	local yes= y=	# answer yes to questions automatically, i.e. non-interactive
	local illustrate_only= I=	# illustrate an existing story containing image tags
	local delete_illustrations= d=	# delete illustrations from the story, optionally use before add
	local add_illustrations= a=	# add illustrations to an existing story
	local retry= r=3	# retry the LLM up to n times if it fails

	eval "$(ally)"

	local filename="${1:-story.md}"
	shift || true
	local user_prompt="$*"

	local generate_story=1
	if (( illustrate_only )); then
		generate_story=
		illustrate=1
	fi
	if (( add_illustrations )); then
		generate_story=
		illustrate=1
	fi

	local format="${filename##*.}"
	local prompts=()

	check_if_file_already_exists

	if (( generate_story )); then
		create_the_prompt
		confirm_the_prompt
		generate_the_story
		user_may_edit_the_story
	fi

	if (( delete_illustrations )); then
		backup_file "$filename"
		remove_images_from_story
	fi

	if (( add_illustrations )); then
		create_the_prompt
		confirm_the_prompt
		add_illustrations
		user_may_edit_the_story
	fi

	if [ "$illustrate" ]; then
		illustrate_the_story
	fi

	echo >&2 "Done, we hope you like it!"

	view_the_result
}

check_if_file_already_exists() {
	if [ -e "$filename" ] && [ ! "$continue" ] && (( generate_story )); then
		echo >&2 "File exists, if you continue the new story will be appended to the file: $filename"
		(( yes )) || confirm "Continue?" || exit
	fi

	if [ ! -e "$filename" ] && [ "$continue" ]; then
		echo >&2 "File does not exist, cannot continue the story: $filename"
		exit 1
	fi

	if [ ! -e "$filename" ] && [ "$add_illustrations" ]; then
		echo >&2 "File does not exist, cannot add illustrations: $filename"
		exit 1
	fi

	if [ ! -e "$filename" ] && [ "$illustrate_only" ]; then
		echo >&2 "File does not exist, cannot illustrate: $filename"
		exit 1
	fi
}

story_prompts() {
	if (( standard )); then
		if [ -n "$continue" ]; then
			prompts+=("Please continue the story")
		elif (( add_illustrations )); then
			prompts+=("Please add illustrations to the story")
		else
			prompts+=("Please write a story")
		fi
	fi

	if [ "$user_prompt" ]; then
		prompts+=("$user_prompt")
	fi

	if [ "$format" ]; then
		prompts+=("In .$format format")
	fi
}

illustration_prompts() {
	if [ -z "$illustrate" ]; then
		return
	fi

	local alt_syntax="detailed English description"
	local example_prefix=""

	example_text="A close-up of Jack's gaunt face, his sunken eyes filled with a mixture of desperation and determination. The background shows the dilapidated farmhouse and barren fields stretching to the horizon under a gloomy sky."
	example_filename="jacks_desperation.png"

	local img="<img src=\"image_name.png\" alt=\"$alt_syntax\" width=\"1200\" height=\"800\">"
	local example="<img src=\"$example_filename\" alt=\"$example_prefix$example_text\" width=\"1200\" height=\"800\">"

	case "$format" in
	md|txt)
		img="![$alt_syntax](image_name.png)<!--{width=1200 height=800}-->"
		example="![$example_prefix$example_text]($example_filename)<!--{width=1200 height=800}-->"
		;;
	html)
		;;
	*)
		echo >&2 "Unsupported file format: .$format, defaulting to HTML-style images."
		;;
	esac

	prompts+=("Please add illustrations using tags like \`$img\` with good filenames (PNG) in the same directory, and very detailed descriptive ALT text for AI image generation and accessibility. Choose a variety of suitable image dimensions as appropriate, aspect is important but we can adjust the scale. Include every detail in the image descripions, including scenery, characters, objects, the time of day, the weather, etc., as the image generator does not know any context beyond what you describe here.")

	if [ "${illustrate#1}" ]; then
		prompts+=("Regarding illustrations: ${illustrate#1}.")
	fi

	if (( add_illustrations )); then
		prompts+=("Please output only TSV, for the added images, do not output the story text: 1. line number after which to insert an image, 2. the image tags to insert. Preferably insert images after previously blank lines, or at the end of the file.")
	fi

	if (( add_illustrations )); then
		prompts+=("An example TSV output line, to insert an image after line 7 of the story. Please only output such TSV lines, to add illustrations, and nothing else. Note that this is just an example, don't use it directly in the story.

7	$example")
	else
		prompts+=("An example image tag. Note that this is just an example, don't use it directly in the story.

$example")
	fi
}

assemble_the_prompts() {
	prompt=""
	for p in "${prompts[@]}"; do
		if [ ! "$p" ]; then
			prompt+=$'\n'
		else
			last_char_of_p="${p: -1}"
			case "$last_char_of_p" in
			"."|","|";"|":"|"?"|"!")
				;;
			*)
				p="$p."
				;;
			esac
			prompt+="$p"$'\n'
		fi
	done
}

create_the_prompt() {
	story_prompts
	illustration_prompts
	assemble_the_prompts
}

confirm_the_prompt() {
	printf >&2 "prompt:\n\n%s\n" "$prompt"

	(( yes )) || confirm "Continue?" || exit
}

generate_the_story() {
	local new_content_filename="$filename.new_content.$$"

	if [ -e "$new_content_filename" ]; then
		echo >&2 "Temporary file exists, very unlikely, please remove it: $new_content_filename"
		exit 1
	fi

	for try in $(seq "$retry"); do
		echo >&2 "Generating story... try $try of $retry"
		if [ -n "$continue" ]; then
			if [ "$continue" = 1 ]; then
				continue=""
			fi
			continue=$(sed-escape "$continue")
			< "$filename" sed -n "/${continue:-.}/,\$p"
	 	fi |
			(llm process --model="$m" --empty-ok "$prompt"; echo) |
			story_correct_image_tags.py |
			tee -a "$new_content_filename.$try"
			if [ "$(< "$new_content_filename.$try" grep -c .)" -gt 2 ]; then
			mv "$new_content_filename.$try" "$new_content_filename"
			break
		fi
		echo >&2 "Failed to generate text..."
	done

	if [ ! -e "$new_content_filename" ]; then
		echo >&2 "Failed to generate text $retry times, giving up."
		exit 1
	fi

	cat "$new_content_filename" >> "$filename"

	echo >&2 "Story written to $filename"
}

backup_file() {
	local filename="$1"

	local cp_opts=(-a)
	if (( ! yes )); then
		cp_opts+=(-i)
	fi
	cp "${cp_opts[@]}" "$filename" "$filename~"
}

remove_images_from_story() {
	modify grep -v -e '^!\[' -e '^<img ' : "$filename"
	modify squeeze-blank-lines : "$filename"
}

add_illustrations() {
	local add_images_filename="$filename.add_images.$$.tsv"

	if [ -e "$add_images_filename" ]; then
		echo >&2 "Temporary file exists, very unlikely, please remove it: $add_images_filename"
		exit 1
	fi

	for try in $(seq "$retry"); do
		echo >&2 "Generating text for images... try $try of $retry"
		number-lines-all "$filename" |
		(llm process --model="$m" --empty-ok "$prompt"; echo) |
		story_correct_image_tags.py |
		tee -a "$add_images_filename.$try"
		if [ "$(< "$add_images_filename.$try" grep -c .)" -gt 2 ]; then
			mv "$add_images_filename.$try" "$add_images_filename"
			break
		fi
		echo >&2 "Failed to generate text for images..."
	done

	if [ ! -e "$add_images_filename" ]; then
		echo >&2 "Failed to generate text for images $retry times, giving up."
		exit 1
	fi

	# apply changes using ed
	# work in reverse order, so that line numbers remain valid
	sort -r -n -k1 "$add_images_filename" |
	(
		while IFS=$'\t' read -r line_number image_tags; do
			if [ -z "$image_tags" ]; then
				continue
			fi

			# remove any non-digit characters
			line_number="${line_number//[^0-9]/}"

			if [ -z "$line_number" ]; then
				echo >&2 "Invalid line number: $line_number"
				continue
			fi

			# ed commands
			echo "$line_number"
			echo "a"
			echo "$image_tags"
			echo "."
		done < "$add_images_filename"
		echo "w"
		echo "q"
	) |
	ed "$filename" 2>/dev/null
}

user_may_edit_the_story() {
	if (( ! edit )); then
		return
	fi

	${EDITOR:-vi} "$filename"
}

illustrate_the_story() {
	if [ -z "$illustrate" ]; then
		return
	fi

	illustration_count=$(grep -c -e '!\[.*\]\(.*\)' -e '<img .*>' "$filename")
	echo >&2 "Illustrating $filename with $illustration_count illustrations, $count alternative images for each illustration."
	echo >&2 "Existing images will not be regenerated, supposing you did not move them."

	(( yes )) || confirm "Continue?" || exit

	illustrate.py --debug --prompt0 "${illustrate#1} ${positive0}" --prompt1 "${positive1}" --negative "$negative" --module "$module" --count "$count" "$filename"
}

view_the_result() {
	if (( ! view )); then
		return
	fi
	echo >&2 "Viewing $filename in Chrome, the 'Markdown Viewer' plugin is recommended."
	chrome "$filename"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	story "$@"
fi

# version: 0.1.2
