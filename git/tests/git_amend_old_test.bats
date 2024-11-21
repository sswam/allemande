#!/usr/bin/env bats

# git_amend_old_test.bats
# Tests the git_amend_old.sh script using BATS framework

program=$(realpath git_amend_old.sh)

setup() {
	load 'test_helper/bats-support/load'
	load 'test_helper/bats-assert/load'

	# Create temporary directory for test repository
	TEST_DIR="$(mktemp -d)"
	cd "$TEST_DIR"

	# Initialize git repo and configure user
	git init
	git config user.name "Test User"
	git config user.email "test@example.com"

	# Create initial commit
	echo "initial" > file1.txt
	git add file1.txt
	git commit -m "Initial commit"

	# Create second commit
	echo "second" > file2.txt
	git add file2.txt
	git commit -m "Second commit"
}

teardown() {
	# Clean up temporary directory
	rm -rf "$TEST_DIR"
}

@test "Fails when not in a git repository" {
	tmpdir="$(mktemp -d)"
	cd "$tmpdir"
	run $program 1
	assert_failure
	assert_output --partial "not a git repository"
	cd -
	rmdir "$tmpdir"
}

@test "Amends previous commit with new message" {
	run $program -m="Updated message" 1
	assert_success

	# Verify the commit message was changed
	run git log -1 --pretty=%B
	assert_output "Updated message"
}

@test "Dry run doesn't modify repository" {
	original_head=$(git rev-parse HEAD)
	run $program -d 1
	assert_success
	assert_output --partial "Would rebase interactively"

	# Verify HEAD hasn't changed
	current_head=$(git rev-parse HEAD)
	[ "$original_head" = "$current_head" ]
}

@test "Can amend commit using relative reference" {
	run $program -m="Updated old commit" 1
	assert_success

	# Verify the first commit message was changed
	run git log HEAD~1 -1 --pretty=%B
	assert_output "Updated old commit"
}

@test "Can amend commit using commit hash" {
	commit_hash=$(git rev-parse HEAD~1)
	run $program -m="Updated via hash" "${commit_hash:0:7}"
	assert_success

	# Verify the commit message was changed
	run git log HEAD~1 -1 --pretty=%B
	assert_output "Updated via hash"
}

@test "Handles uncommitted changes" {
	echo "uncommitted" > file3.txt
	run $program -m="Updated message with uncommitted changes" 1
	assert_success

	# Verify the commit message was changed
	run git log -1 --pretty=%B
	assert_output "Updated message with uncommitted changes"

	# Verify uncommitted changes are restored
	[ -f file3.txt ]
	run cat file3.txt
	assert_output "uncommitted"
}
