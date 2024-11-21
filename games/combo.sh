#!/bin/bash
#
# combine brainstorming ideas for math in game dev, demos and programming

unit= u=	# unit

eval "$(ally)"

combo -p="Please select and combine the best ideas, avoiding duplication. Try to keep the codes like ACMMM001 next to each idea. We are looking for fairly low-level applications for math in game dev, demos and programming; not so much complete game ideas yet. Although we might as well include the best of them. Please avoid duplicate or extremely similar ideas, just combine them." storm$unit-*  > storm$unit-combo.md
