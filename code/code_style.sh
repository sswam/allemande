#!/bin/bash -eu
# code-style:	rewrite a script using my code style
r=`which map-find-google`
p="Please rewrite the second program '%s' in the style of the first '%s', include argh, logging, and stdio if possible. Please reorder ifs and such as needed to check for errors and negatives first, and reduce indentation. Thanks for always doing a great job!"
. opts
reference=$r
prompt=$p

# TODO other alt prompt: Please change the code to check for errors and negatives first or such as to reduce indentation.

input="$1"

input_basename=`basename "$input"`
reference_basename=`basename "$reference"`

prompt2=`printf "$prompt" "$input_basename" "$reference_basename"`

cat-sections "$reference" "$input" | process "$prompt2"
