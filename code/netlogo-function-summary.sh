#!/bin/bash -eu
# netlogo-function-summary.sh: 

all=$1
func=$2

func_name=${func%.*}

m=4

. opts

prompt1="We are writing an ODD in markdown for a netlogo project. Please help us summarize some code."

input="Here are the descriptions of other functions we are using:
`cat "$all"`

Here is the function we are summarizing:
`cat "$func"`

Please give a summary of that function $func_name for the ODD, starting with a level-3 heading being just the function name, i.e. ### $func_name
"

echo "$input" | llm process -m $m "$prompt1"
echo
echo
