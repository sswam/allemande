#!/bin/bash

# [test_hello]
# Tests the hello.sh script

test_hello() {
	local errors=0

	# Test default behavior
	if [ "$(./hello.sh)" != "Hello, world" ]; then
		echo "Error: Default greeting failed"
		((errors++))
	fi

	# Test with a name
	if [ "$(./hello.sh John)" != "Hello, John" ]; then
		echo "Error: Greeting with name failed"
		((errors++))
	fi

	# Test different languages
	if [ "$(./hello.sh -l=fr)" != "Bonjour, world" ]; then
		echo "Error: French greeting failed"
		((errors++))
	fi

	if [ "$(./hello.sh -l=de)" != "Hallo, world" ]; then
		echo "Error: German greeting failed"
		((errors++))
	fi

	if [ "$(./hello.sh -l=jp)" != "こんにちは, world" ]; then
		echo "Error: Japanese greeting failed"
		((errors++))
	fi

	if [ "$(./hello.sh -l=cn)" != "你好, world" ]; then
		echo "Error: Chinese greeting failed"
		((errors++))
	fi

	# Test shopping list
	output=$(./hello.sh -s,apple,banana)
	if ! echo "$output" | grep -q '^Shopping list:$'; then
		echo "Error: Shopping list header missing"
		((errors++))
	fi
	if ! echo "$output" | grep -q -- '^- apple$'; then
		echo "Error: Shopping list item 'apple' missing"
		((errors++))
	fi
	if ! echo "$output" | grep -q -- '^- banana$'; then
		echo "Error: Shopping list item 'banana' missing"
		((errors++))
	fi

	# Test AI greeting (this is a basic test, as we can't predict the exact output)
	if [ "$RUN_AI_TESTS" = true ] && ! ./hello.sh -a -m="s" | grep -q '.'; then
		echo "Error: AI greeting failed to produce any output"
		((errors++))
	fi

	# Print test results
	if [ $errors -eq 0 ]; then
		echo "All tests passed successfully!"
		return 0
	else
		echo "Tests failed with $errors error(s)"
		return 1
	fi
}

if [ "$BASH_SOURCE" = "$0" ]; then
	test_hello
fi

# Important Notes for AI:
# - With our `. opts` options parser, CLI options use =, like `-l=fr`. `-l fr` does not work.
# - Pass lists through options, like -s,foo,bar or -s,"foo bar"
# - If testing AI features with a model option, use `-m=s` for the 'small' model.
# - Use tools carefully and precisely, with -- to avoid confusion between args and options,
#   and use ^ $ for precise regexp matching where appropriate.
# - AI tests are optional, to run them use: RUN_AI_TESTS=true ./tests/test_hello.sh
