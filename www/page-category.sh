#!/bin/bash -eu
# page-categories.sh:	use an LLM to get the categories for a page

m=4

. opts

page=$1
categories=${2:-categories-drool.txt}
name=${1%.*}

cat-sections "$page" "$categories" | llm process -m=$m "Please choose a short list of up to five of the best categories for this page about '$name', with the most specific and appropriate categories at the top. Please give the full path to the categories if possible. Only output the categories, no other commentary please! Don't invent any new categories, only use ones from the list. PLEASE DOUBLE-CHECK THAT THE OUTPUT CATEGORIES OCCUR VERBATIM IN THE INPUT LIST. Please try not not to use categories under the 'Discover' category group, except for towns. It would be better to use a more specific category such as 'Beaches & Coastlines'. Thanks for always being awesome.

For example:

- Foo / Bar / Baz
- Foo / Bar
- Quokka / Bing / Boop
- Quokka" |
tee "$name.cats.$m.txt"
