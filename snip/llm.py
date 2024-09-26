#	"gpt-3.5-turbo": {
#		"alias": "3+",
#		"description": "Most capable GPT-3.5 model and optimized for chat at 1/10th the cost of text-davinci-003. Will be updated with our latest model iteration.",
#		"cost": 0.002,
#	},

#	"gpt-4-orig": {
#		"alias": "4o",
#		"description": "More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with our latest model iteration.",
#		"cost": 0.03,
#	},
#	"claude-v1-100k": {
#		"alias": "c+",
#		"description": "Anthropic's Claude with an 100k token window.",
#		"cost": 0.0,  # at least for now!
#	},
#	"claude-instant-v1-100k": {
#		"alias": "i+",
#		"description": "Anthropic's Claude Instant with an 100k token window.",
#		"cost": 0.0,  # at least for now!
#	},
#	"gpt-4-32k": {
#		"alias": "4+",
#		"description": "Same capabilities as the base gpt-4 mode but with 4x the context length. Will be updated with our latest model iteration.",
#		"cost": 0.06,
#	},

#	"gpt-3.5-turbo-0301": {
#		"description": "Snapshot of gpt-3.5-turbo from March 1st 2023. Unlike gpt-3.5-turbo, this model will not receive updates, and will only be supported for a three month period ending on June 1st 2023.",
#		"cost": 0.002,
#	},
#	"gpt-4-0314": {
#		"description": "Snapshot of gpt-4 from March 14th 2023. Unlike gpt-4, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
#		"cost": 0.03,
#	},
#	"gpt-4-32k-0314": {
#		"description": "Snapshot of gpt-4-32 from March 14th 2023. Unlike gpt-4-32k, this model will not receive updates, and will only be supported for a three month period ending on June 14th 2023.",
#		"cost": 0.06,
#	},
#	"claude-v1.0": {
#		"description": "An earlier version of claude-v1.",
#		"cost": 0.0
#	},
#	"claude-v1.2": {
#		"description": "An improved version of claude-v1. It is slightly improved at general helpfulness, instruction following, coding, and other tasks. It is also considerably better with non-English languages. This model also has the ability to role play (in harmless ways) more consistently, and it defaults to writing somewhat longer and more thorough responses.",
#		"cost": 0.0
#	},
#	"claude-v1.3": {
#		"description": "A significantly improved version of claude-v1. Compared to claude-v1.2, it's more robust against red-team inputs, better at precise instruction-following, better at code, and better and non-English dialogue and writing.",
#		"cost": 0.0
#	},
#	"claude-instant-v1.0": {
#		"description": "Current default for claude-instant-v1.",
#		"cost": 0.0
#	}
}

#	"code-davinci-002": {
#		"alias": "x2",
#		"description": "Code completion model trained on 1.5 billion lines of code. Will be updated with our latest model iteration.",
#		"cost": 0,
#	},
#	"code-cushman-001": {
#		"alias": "x1",
#		"description": "Almost as capable as Davinci Codex, but slightly faster. This speed advantage may make it preferable for real-time applications.",
#		"cost": 0,
#	},

	if vendor == "bard":
		return await achat_bard(messages)

@argh.arg("-s", "--state-file", help="state file for Google Bard")

# def chat_bard(messages):
# 	""" Chat with Google Bard models """
# 	# We can only pass in the last user message; let's hope we have the right state file!
# 	# We can't run all the user messages again; Bard will likely not do the same thing so it would be a mess.
# 	# Perhaps we should save state in chat metadata.
# 	if not messages or messages[-1]["role"] == "assistant":
# 		raise ValueError("Bard requires a conversation ending with a user message.")
# 	bard = Bard(state_file=opts.state_file, auto_save=opts.auto_save)
# 	response = bard.aget_answer(messages[-1]["content"])
# 	completion = response["content"]
# 	message = { "role": "assistant", "content": completion }
# 	return message

		if kwargs.get("state_file") and kwargs.get("auto_save") is None:
			kwargs["auto_save"] = True
