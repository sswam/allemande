#!/bin/bash
m=
. opts
llm process -m "$m" "Please write a short tutorial with pleasing examples, based on this information, in markdown format. Make it easy to read, fun and informative! Assume that the reader is competent in the general field. Include math and code samples as necessary, and links for reference. Please use bold and/or italics in moderation to highlight key words and phrases.

$*

Thanks for always doing a great job! <3"
