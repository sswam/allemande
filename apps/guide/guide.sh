#!/usr/bin/env bash

# [user's name]
# AI-Powered Personal Project Manager

guide() {
	local plan_file=plan.md
	local bio_file=bio.md
	local done_file=done.md
	local ideas_file=ideas.md
	local chat_file=chat.bb
	local model= m=	# LLM model

	eval "$(ally)"

	local user_name=${1:-user}
	[ -n "$user_name" ] || usage "User's name is required"

	# Initialize files if they don't exist
	for file in "$plan_file" "$bio_file" "$done_file" "$ideas_file" "$chat_file"; do
		[ -f "$file" ] || touch "$file"
	done

	# Start the chat
	chat "$user_name"
}

chat() {
	local user_name=$1
	local input

	echo "Guide: Hello $user_name! How can I assist you today?" >> "$chat_file"

	while true; do
		read -p "$user_name: " input
		echo "$user_name: $input" >> "$chat_file"

		case "$input" in
			quit|exit)
				echo "Guide: Goodbye, $user_name! Have a great day!" >> "$chat_file"
				break
				;;
			*)
				process_input "$input"
				;;
		esac
	done
}

process_input() {
	local input=$1
	local response

	response=$(query -m="$model" "Given this user input: '$input', provide a helpful response as an AI-powered personal project manager. Reference the contents of $plan_file, $bio_file, $done_file, and $ideas_file if needed.")

	echo "Guide: $response" >> "$chat_file"
	echo "Guide: $response"

	# TODO: Implement logic to update files based on the conversation
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	guide "$@"
fi

# version: 0.1.0

# Here's a simple prototype of the `guide.sh` script based on the requirements and style of `hello_sh.sh`:

# This prototype implements a basic interactive chat functionality and file structure as outlined in the `guide.md` file. Here's a breakdown of what it does:
#
# 1. It sets up the necessary files (`plan.md`, `bio.md`, `done_file`, `ideas.md`, and `chat.bb`) if they don't exist.
# 2. It starts a chat loop that allows the user to input messages.
# 3. It processes user input using the `query` tool to generate responses.
# 4. It saves the conversation to the `chat.bb` file.
#
# To improve this prototype, we should:
#
# 1. Implement file updating logic based on the conversation.
# 2. Add more specific commands for managing tasks, updating the plan, etc.
# 3. Implement better context management by reading and using the contents of the various files.
# 4. Add error handling and more robust input processing.
#
# This is a starting point that can be expanded upon to include more of the functionality described in the `guide.md` file.
