#!/usr/bin/env bats

# test_hello_sh.bats v1.0.5
# Tests the hello_sh.sh script using BATS framework

# Set default value for RUN_AI_TESTS
RUN_AI_TESTS="${RUN_AI_TESTS:-false}"

program=./hello_sh.sh

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'
}

@test "Default greeting" {
	run $program -s,
	assert_output "Hello, world"
}

@test "Greeting with name" {
	run $program -s, John
	assert_output "Hello, John"
}

@test "French greeting" {
	run $program -s, -l=fr
	assert_output "Bonjour, world"
}

@test "German greeting" {
	run $program -s, -l=de
	assert_output "Hallo, world"
}

@test "Japanese greeting" {
	run $program -s, -l=jp
	assert_output "こんにちは, world"
}

@test "Chinese greeting" {
	run $program -s, -l=cn
	assert_output "你好, world"
}

@test "Shopping list" {
	run $program -s,apple,banana
	assert_line --index 0 "Hello, world"
	assert_line --index 1 "Shopping list:"
	assert_line --index 2 "- apple"
	assert_line --index 3 "- banana"
}

@test "AI greeting [AI]" {
	if [ "$RUN_AI_TESTS" != "true" ]; then
		skip "AI test skipped. Set RUN_AI_TESTS=true to include AI tests."
	fi
	run $program -a -m=s
	assert_success
	assert_output --partial "."
}

# Important Notes for AI:

# - With our `. opts` options parser, CLI options use =, like `-l=fr`. `-l fr` does not work.
# - Pass lists through options, like -s,foo,bar or -s,"foo bar"
# - If testing AI features with a model option, use `-m=s` for the 'small' model.
# - Use tools carefully and precisely, with -- to avoid confusion between args and options,
#   and use ^ $ for precise regexp matching where appropriate.
# - AI tests are optional, to run them use: RUN_AI_TESTS=true ./tests/test_hello_sh.bats
# - When writing other scripts based on this one, please do not include these notes!
