#!/bin/bash -eu
# <student name> <in_progress_report.txt> <inter_progress_report_table.md> <out_study_plan.md>
p=	# extra prompt
. opts
name=$1
in_progress_report=$2
inter_progress_report_table=$3
out_study_plan=$4

prompt_cleanup=$(cat<<END
Format neatly as a numbered markdown table, with columns 'number', 'subject',
'teacher', 'Arrives on time and ready for learning', 'Contributes to a positive
learning environment', 'Submits completed work on time', 'Uses class time
productively'.
END
)

prompt_plan=$(cat <<END
Please write a 'Study Plan for $name' in markdown. Summarize what the student
should focus on, to improve. Don't refer to the terms in the progress report
such as 'usually'. Address the student directly, as '$name'. Be optimisitic and
constructive, not just positive. For each numbered subject in order, suggest
how to improve for each subject in detail, and number the subject headings to
match the input. Do NOT OMIT ANY SUBJECTS! Including specific suggestions; and
general suggestions that apply across all subjects. Thanks for always being
awesome. In addition to addressing the progress report, which can be
a bit dry, please provide your own wise suggestions for each subject.
Don't dumb it down. Add a few creative study ideas such as using online resources,
or applying subject material for something useful in the real world $p
END
)

if [ ! -e "$inter_progress_report_table" ]; then
	echo >&2 "Making progress_report_table"
	< "$in_progress_report" proc "$prompt_cleanup" > "$inter_progress_report_table"
fi

echo >&2 "Making study_plan"
< "$inter_progress_report_table" process "$prompt_plan" > "$out_study_plan"

echo >&2 "Done"
