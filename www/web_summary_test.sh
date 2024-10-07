#!/bin/bash -euv
# web-summary-test: summarise a web page in various ways,
# and produce stats to help estimate costs

# TODO:
# - We might want to remove links and certain other markdown if we are not going to make use of them in the summaries.

name=$1
url=$2

mkdir "$name"
cd "$name"

printf "%s\n" "$url" > url.txt

points_prompt="Please make a comprehensive dot point summary of this text from a web page, in markdown, including the main topic, and all significant points relating to the main topic, up to 20 dot points as needed. Don't include extraneous info about the web page such as navigation or technical details on how the web page works. Thanks for doing a great job!"
summary_prompt="Please write a 2 or 3 paragraph summary, in markdown, including any important links if given. No more than 250 words. The summary should be clear and easy to read, in fairly simple, concise language for a wide audience, and using fairly short sentences. Please include most of the facts given, and do not add additional facts, opinions or commentary (other than what might be unambiguously implied or well known). Please preserve quotes. Thanks for doing a great job!

Please follow this output format, including the three given headings and replacing the text between square brackets:

# Type:

[the type of content, e.g. News, Article, Product, Company, Information, Personal, Paper, Review, ...]

# Topic:

[the topic, a single phrase or sentence summing up the content]

# Summary:

[the requested summary of the content]

----"

text_cutoff=16000

wg -O=page.html "$url"
pandoc-dump page.html "$url" | tee page-full.txt

head -c "$text_cutoff" < page-full.txt > page.txt

chars=`wc -c < page.txt | tee page-chars`
words=`wc -w < page.txt | tee page-words`
tokens_claude=`llm count -m i < page.txt | tee page-tokens`
chars_per_token=`calc $chars/$tokens_claude`
chars_per_word=`calc $chars/$words`
tokens_per_word=`calc $tokens_claude/$words`

time llm process -m i "$points_prompt" < page.txt |
perl -e 'undef $/; $_ = <>; s/\A[a-z].*:\n+//is; print' |  # strip any intro heading
tee points.txt

points_prompt_tokens_claude=`printf "%s\n\n" "$points_prompt" | llm count -m i`
summary_prompt_tokens_claude=`printf "%s\n\n" "$summary_prompt" | llm count -m i`
summary_prompt_tokens_chatgpt=`printf "%s\n\n" "$summary_prompt" | llm count -m 4`

points_chars=`wc -c < points.txt | tee points-chars`
points_words=`wc -w < points.txt | tee points-words`
points_tokens_claude=`llm count -m i < points.txt | tee points-tokens-claude`
points_tokens_chatgpt=`llm count -m 4 < points.txt | tee points-tokens-chatgpt`

for model in i c 4; do
	time llm process -m "$model" "$summary_prompt" < points.txt | tee summary.$model.txt
	wc -c < summary.$model.txt | tee summary-chars-$model
	wc -w < summary.$model.txt | tee summary-words-$model
	llm count -m "$model" < summary.$model.txt | tee summary-tokens-$model
done

for model in i c; do
	time llm process -m "$model" "$summary_prompt" < page.txt | tee summary-one-step.$model.txt
	wc -c < summary-one-step.$model.txt | tee summary-one-step-chars-$model
	wc -w < summary-one-step.$model.txt | tee summary-one-step-words-$model
	llm count -m "$model" < summary-one-step.$model.txt | tee summary-one-step-tokens-$model
done

header() {
	local text=$1
	echo
	echo
	echo "$text"
	echo "$text" | sed 's/./-/g'
	echo
}

(
	header "Info"
	echo "name: $name"
	echo "url: $url"

	header "Text"
	cat page.txt

	header "Points"
	cat points.txt

	for model in i c 4; do
		header "Summary ($model)"
		cat summary.$model.txt
	done

	for model in i c; do
		header "Summary One Step ($model)"
		cat summary-one-step.$model.txt
	done

	header "Prompt Stats"
	echo "points_prompt_tokens_claude: $points_prompt_tokens_claude"
	echo "summary_prompt_tokens_claude: $summary_prompt_tokens_claude"
	echo "summary_prompt_tokens_chatgpt: $summary_prompt_tokens_chatgpt"

	header "Text Stats"
	echo "chars: $chars"
	echo "words: $words"
	echo "tokens_claude: $tokens_claude"
	echo "chars_per_token: $chars_per_token"
	echo "chars_per_word: $chars_per_word"
	echo "tokens_per_word: $tokens_per_word"

	header "Points Stats"
	echo "points_chars: $points_chars"
	echo "points_words: $points_words"
	echo "points_tokens_claude: $points_tokens_claude"
	echo "points_tokens_chatgpt: $points_tokens_chatgpt"

	for model in i c 4; do
		header "Summary Stats ($model)"
		echo "summary_chars_$model: `cat summary-chars-$model`"
		echo "summary_words_$model: `cat summary-words-$model`"
		echo "summary_tokens_$model: `cat summary-tokens-$model`"
	done

	for model in i c; do
		header "Summary One Step Stats ($model)"
		echo "summary_one_step_chars_$model: `cat summary-one-step-chars-$model`"
		echo "summary_one_step_words_$model: `cat summary-one-step-words-$model`"
		echo "summary_one_step_tokens_$model: `cat summary-one-step-tokens-$model`"
	done
) | tee report.txt

echo
echo

(
	printf "%s\t" "$name" "$url" "$points_prompt_tokens_claude" \
		"$summary_prompt_tokens_claude" "$summary_prompt_tokens_chatgpt" \
		"$chars" "$words" "$tokens_claude" \
		"$points_chars" "$points_words" "$points_tokens_claude" "$points_tokens_chatgpt" \
		"`cat summary-chars-i`" "`cat summary-words-i`" "`cat summary-tokens-i`" \
		"`cat summary-chars-c`" "`cat summary-words-c`" "`cat summary-tokens-c`" \
		"`cat summary-chars-4`" "`cat summary-words-4`" "`cat summary-tokens-4`" \
		"`cat summary-one-step-chars-i`" "`cat summary-one-step-words-i`" "`cat summary-one-step-tokens-i`" \
		"`cat summary-one-step-chars-c`" "`cat summary-one-step-words-c`" "`cat summary-one-step-tokens-c`"
	echo
) | tee row.tsv
