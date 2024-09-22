#!/usr/bin/env bats

# test_hello.bats v1.0.4
# Tests the hello.sh script using BATS framework

# Set default value for RUN_AI_TESTS
RUN_AI_TESTS="${RUN_AI_TESTS:-false}"

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'
}

@test "Default greeting" {
	run ./hello.sh
	assert_output "Hello, world"
}

@test "Greeting with name" {
	run ./hello.sh John
	assert_output "Hello, John"
}

@test "French greeting" {
	run ./hello.sh -l=fr
	assert_output "Bonjour, world"
}

@test "German greeting" {
	run ./hello.sh -l=de
	assert_output "Hallo, world"
}

@test "Japanese greeting" {
	run ./hello.sh -l=jp
	assert_output "こんにちは, world"
}

@test "Chinese greeting" {
	run ./hello.sh -l=cn
	assert_output "你好, world"
}

@test "Shopping list" {
	run ./hello.sh -s,apple,banana
	assert_line --index 0 "Hello, world"
	assert_line --index 1 "Shopping list:"
	assert_line --index 2 "- apple"
	assert_line --index 3 "- banana"
}

@test "AI greeting [AI]" {
	if [ "$RUN_AI_TESTS" != "true" ]; then
		skip "AI test skipped. Set RUN_AI_TESTS=true to include AI tests."
	fi
	run ./hello.sh -a -m=s
	assert_success
	assert_output --partial "."
}

# Important Notes for AI:

# - With our `. opts` options parser, CLI options use =, like `-l=fr`. `-l fr` does not work.
# - Pass lists through options, like -s,foo,bar or -s,"foo bar"
# - If testing AI features with a model option, use `-m=s` for the 'small' model.
# - Use tools carefully and precisely, with -- to avoid confusion between args and options,
#   and use ^ $ for precise regexp matching where appropriate.
# - AI tests are optional, to run them use: RUN_AI_TESTS=true ./tests/test_hello.bats
# - When writing other scripts based on this one, please do not include these notes!
