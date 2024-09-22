#!/usr/bin/env bats

# test_image_comment.bats
# Tests the image_comment.sh script using BATS framework

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'

	# Create temporary test files
	TEMP_DIR=$(mktemp -d)
	TEST_JPG="$TEMP_DIR/test.jpg"
	TEST_PNG="$TEMP_DIR/test.png"
	TEST_METADATA="$TEMP_DIR/metadata.txt"

	# Create test images
	convert -size 100x100 xc:white "$TEST_JPG"
	convert -size 100x100 xc:white "$TEST_PNG"

	# Create test metadata file
	echo "Test metadata" > "$TEST_METADATA"
}

teardown() {
	# Remove temporary files
	rm -rf "$TEMP_DIR"
}

@test "Extract metadata from JPG (empty)" {
	run ./image_comment.sh extract "$TEST_JPG"
	assert_output "No Comment metadata found in $TEST_JPG."
}

@test "Extract metadata from PNG (empty)" {
	run ./image_comment.sh extract "$TEST_PNG"
	assert_output "No Comment metadata found in $TEST_PNG."
}

@test "Insert metadata into JPG" {
	run ./image_comment.sh insert -i="$TEST_METADATA" "$TEST_JPG"
	assert_success
	assert_output --partial "Metadata inserted into $TEST_JPG."
}

@test "Insert metadata into PNG" {
	run ./image_comment.sh insert -i="$TEST_METADATA" "$TEST_PNG"
	assert_success
	assert_output --partial "Metadata inserted into $TEST_PNG."
}

@test "Extract inserted metadata from JPG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_JPG"
	run ./image_comment.sh extract "$TEST_JPG"
	assert_success
	assert_output "Test metadata"
}

@test "Extract inserted metadata from PNG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_PNG"
	run ./image_comment.sh extract "$TEST_PNG"
	assert_success
	assert_output "Test metadata"
}

@test "Erase metadata from JPG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_JPG"
	run ./image_comment.sh erase "$TEST_JPG"
	assert_success
	assert_output --partial "Metadata erased from $TEST_JPG."

	run ./image_comment.sh extract "$TEST_JPG"
	assert_output "No Comment metadata found in $TEST_JPG."
}

@test "Erase metadata from PNG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_PNG"
	run ./image_comment.sh erase "$TEST_PNG"
	assert_success
	assert_output --partial "Metadata erased from $TEST_PNG."

	run ./image_comment.sh extract "$TEST_PNG"
	assert_output "No Comment metadata found in $TEST_PNG."
}

@test "Copy metadata from JPG to PNG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_JPG"
	run ./image_comment.sh copy "$TEST_JPG" "$TEST_PNG"
	assert_success
	assert_output --partial "Metadata copied from $TEST_JPG to $TEST_PNG."

	run ./image_comment.sh extract "$TEST_PNG"
	assert_output "Test metadata"
}

@test "Copy metadata from PNG to JPG" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_PNG"
	run ./image_comment.sh copy "$TEST_PNG" "$TEST_JPG"
	assert_success
	assert_output --partial "Metadata copied from $TEST_PNG to $TEST_JPG."

	run ./image_comment.sh extract "$TEST_JPG"
	assert_output "Test metadata"
}

@test "Convert JPG to PNG with metadata" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_JPG"
	CONVERTED_PNG="$TEMP_DIR/converted.png"
	run ./image_comment.sh convert -f=png "$TEST_JPG" "$CONVERTED_PNG"
	assert_success
	assert_output --partial "Metadata copied from $TEST_JPG to $CONVERTED_PNG."

	run ./image_comment.sh extract "$CONVERTED_PNG"
	assert_output "Test metadata"
}

@test "Convert PNG to JPG with metadata" {
	./image_comment.sh insert -i="$TEST_METADATA" "$TEST_PNG"
	CONVERTED_JPG="$TEMP_DIR/converted.jpg"
	run ./image_comment.sh convert -f=jpg "$TEST_PNG" "$CONVERTED_JPG"
	assert_success
	assert_output --partial "Metadata copied from $TEST_PNG to $CONVERTED_JPG."

	run ./image_comment.sh extract "$CONVERTED_JPG"
	assert_output "Test metadata"
}

# Here's a `test_image_comment.bats` file to test `image_comment.sh`, following the style of `test_hello.bats` and including comprehensive tests for jpg and png files, including erasing metadata in both formats:

# This test file includes comprehensive tests for both JPG and PNG files, covering all the main functionalities of `image_comment.sh`:
#
# 1. Extracting metadata (when empty)
# 2. Inserting metadata
# 3. Extracting inserted metadata
# 4. Erasing metadata
# 5. Copying metadata between JPG and PNG
# 6. Converting images with metadata preservation
#
# The tests use temporary files created in the `setup()` function and cleaned up in the `teardown()` function to ensure a clean testing environment for each test.
