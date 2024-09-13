#!/bin/bash -eu
# llm-program:	Write a program based on an example, a spec, and possible other documents

m=$ALLEMANDE_LLM_DEFAULT	# LLM model
e=	# example
E=	# no example
x=	# extension
n=	# name
a='Please write a'	# appelation
l="python"	# language
w="program"	# what
tn='called `%s`'	# program name
t='to say "Hello, world"'	# task
te='in the style of `%s`, with the same sort of boilerplate features'	# prompt example
g='Include debug logging, comments, -h usage with argh, and documentation if needed. Use stdio if practicable. Make the program usable as a CLI tool and also as a library. Please write top-quality, simple, clear, general, correct and complete code if possible'	# prompt guidance
c='Thanks for being awesome!'	# conclusion
p='%s %s %s %s %s, %s. %s. %s'	# prompt template

. opts

inputs=( "$@" )

model=$m
example=$e
no_example=$E
extension=$x
name=$n
appelation=$a
language=$l
what=$w
template_name=$tn
task=$t
template_example=$pe
guidance=$pg
conclusion=$c
template_prompt=$p

# extension mapping, TODO put this in a library

extension=$language

if [ -z "$ext" ]; then
	case $language in
		python)	extension=py ;;
		perl)	extension=pl ;;
		ruby)	extension=rb ;;
		rust)	extension=rs ;;
		c++)	extension=cpp ;;
		javascript)	extension=js ;;
	esac
fi

if [ -z "$example" -a -z "$no_example" ]; then
	example="$ALLEMANDE_HOME/$language/hello.$extension"
	if [ ! -f "$example" ]; then
		echo >&2 "No example found for $language"
		example=
		example_pr
	fi
fi

query=`printf "$prompt" "$appelation" "$language" "$what" "$prompt_example" "$task" "$guidance" "$conclusion"`

if [ -z "$prompt" ]; then

	prompt='Write a $language script in the style of the example script, with the same general features `map-find-goog.py`, to read markdown in this format into a sensible data structure. Include comments, and a small example of the data structure include keys title, introduction, see_subheading, see, etc.' | tee place_md_to_wordpress_2
example_prompt='in the style of the example script `$example`, with the same sort of boilerplate features, to read markdown in this format into a sensible data structure. Include comments, and a small example of the data structure include keys title, introduction, see_subheading, see, etc.'

cat-sections "$example" "${inputs[@]}" |
| process 'Write a $language script in the style of the example script, with the same general features `map-find-goog.py`, to read markdown in this format into a sensible data structure. Include comments, and a small example of the data structure include keys title, introduction, see_subheading, see, etc.' | tee place_md_to_wordpress_2



# NOTE: Much of this is applicable to any LLM task, not just programming; e.g. creative writing, documentation, etc.

# NOTE: We might be able to do many of these just with different prompt options, no code changes.

# TODO Suggest names for the program
# TODO Combine several programs into one program
# TODO Split one program into several programs
# TODO LLM can suggest ideas to improve the program; both sensible and out-of-the-box
# TODO add logging
# TODO add -h usage
# TODO write documentation
# TODO write tests
# TODO write a README
# TODO write a MANIFEST
# TODO write a setup.py
# TODO write a requirements.txt
# TODO write a Makefile
# TODO improve code quality
# TODO add new features
# TODO code review
# TODO add comments

# See also ideas/llm-program.txt
