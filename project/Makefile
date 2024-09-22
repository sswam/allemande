SHELL=bash

all: summary.txt overview.txt

files.txt:
	cd "$$ALLEMANDE_HOME" && git ls-files
project_log.txt:
	git log --reverse | sed -n '/sam@ucm.dev/,$$p' | grep -v -e '^commit' -e 'Author' -e '^Date' -e '^Merge' | indenter.py --apply t > $@
summary.txt: project_log.txt
	< $< summary.sh "$$(<task-summary.txt)" > $@
overview.txt: project_log.txt
	< $< summary.sh "$$(<task-overview.txt)" > $@

structure.txt: files.txt summary.txt


# cat_named.py $^ | process -m=4m "Please provide a detailed chronological summary of the project based on these git log messages. Include significant details like tools, apps, libraries, and tasks. Summarize trivial items. Aim for a comprehensive overview up to 20 pages or 10000 words." > $@

# diary.txt: project_log.txt files.txt
# 	cat_named.py $^ | process -m=$(model) "Please write a chronological summary or technical diary of the project, based on these git log messages, around 1200 words or two pages. Mention and describe the different tools, apps, libraries and tasks." > $@


.SECONDARY:
