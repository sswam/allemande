#!/usr/bin/env bats

# test_shell_template.bats v1.0.1
# Tests the shell_template.sh script using BATS framework

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'

	# Create a temporary template file for testing
	TEST_TEMPLATE=$(mktemp)
	echo "Hello, \$USER!" > "$TEST_TEMPLATE"
}

teardown() {
	# Remove the temporary template file
	rm -f "$TEST_TEMPLATE"
}

@test "Default execution" {
	run ./shell_template.sh "$TEST_TEMPLATE"
	assert_success
	assert_output "Hello, $USER!"
}

@test "Debug mode" {
	run ./shell_template.sh -d "$TEST_TEMPLATE"
	assert_success
	assert_line --index 0 "cat <<EOF"
	assert_line --index 1 "Hello, \$USER!"
	assert_line --index 2 "EOF"
}

@test "Permissive mode" {
	echo "\$UNDEFINED_VAR" > "$TEST_TEMPLATE"
	run ./shell_template.sh -p "$TEST_TEMPLATE"
	assert_success
	assert_output ""  # Expecting empty output as the variable is undefined
}

@test "Non-permissive mode (should fail)" {
	echo "echo \$UNDEFINED_VAR" > "$TEST_TEMPLATE"
	run ./shell_template.sh "$TEST_TEMPLATE"
	assert_failure
}

@test "Template with multiple lines" {
	cat <<EOF > "$TEST_TEMPLATE"
Hello, \$USER!
Today is \$(date +%A).
Your home directory is \$HOME.
EOF
	run ./shell_template.sh "$TEST_TEMPLATE"
	assert_success
	assert_line --index 0 "Hello, $USER!"
	assert_line --index 1 "Today is $(date +%A)."
	assert_line --index 2 "Your home directory is $HOME."
}

@test "Template with command substitution" {
	echo "The current working directory is: \$(pwd)" > "$TEST_TEMPLATE"
	run ./shell_template.sh "$TEST_TEMPLATE"
	assert_success
	assert_output "The current working directory is: $(pwd)"
}

@test "Non-existent template file" {
	run ./shell_template.sh "non_existent_file.txt"
	assert_failure
	assert_output --partial "No such file or directory"
}
