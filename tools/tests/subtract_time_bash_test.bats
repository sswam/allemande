#!/usr/bin/env bats

# test_subtract_time.bats v1.0.0
# Tests the subtract_time.sh script using BATS framework

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'
}

@test "Subtract 1 hour" {
	run ./subtract_time.sh "2023-05-01 10:00:00" "2023-05-01 09:00:00"
	assert_output "01:00"
}

@test "Subtract 30 minutes" {
	run ./subtract_time.sh "2023-05-01 10:30:00" "2023-05-01 10:00:00"
	assert_output "00:30"
}

@test "Subtract across midnight" {
	run ./subtract_time.sh "2023-05-02 00:30:00" "2023-05-01 23:45:00"
	assert_output "00:45"
}

@test "Subtract across days" {
	run ./subtract_time.sh "2023-05-03 12:00:00" "2023-05-01 12:00:00"
	assert_output "48:00"
}

@test "Zero difference" {
	run ./subtract_time.sh "2023-05-01 12:00:00" "2023-05-01 12:00:00"
	assert_output "00:00"
}

@test "Negative time difference" {
	run ./subtract_time.sh "2023-05-01 12:00:00" "2023-05-01 13:00:00"
	assert_failure
	assert_output "Time difference is negative"
}

@test "Invalid time format" {
	run ./subtract_time.sh "2023-05-01 12:00:00" "invalid_time"
	assert_failure
}

@test "Missing arguments" {
	run ./subtract_time.sh
	assert_failure
}

# Here's a `test_subtract_time.bats` file to test `subtract_time.sh`, following the style of `test_hello.bats`:

# This test file includes several test cases to cover different scenarios for the `subtract_time.sh` script:
#
# 1. Subtracting 1 hour
# 2. Subtracting 30 minutes
# 3. Subtracting across midnight
# 4. Subtracting across multiple days
# 5. Zero time difference
# 6. Negative time difference (which should fail)
# 7. Invalid time format
# 8. Missing arguments
#
# Each test case uses the `run` command to execute the script and then asserts the expected output or failure condition. The `assert_output` function is used to check the script's output, while `assert_failure` is used to ensure the script fails when it should (e.g., for negative time differences or invalid inputs).
#
# This test file follows the structure and style of the `test_hello.bats` example, including the use of the `bats-support` and `bats-assert` libraries for improved assertions and error reporting.
