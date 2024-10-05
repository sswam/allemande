#!/usr/bin/env bats

setup() {
    # Source the script
    source ./guide.sh

    # Create temporary directory for test files
    export TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"

    # Mock the 'ally' function
    ally() { echo "ALLY_MOCKED=true"; }

    # Mock the 'query' function
    query() { echo "Mocked response from Guide"; }
}

teardown() {
    # Remove temporary directory
    rm -rf "$TEST_DIR"
}

@test "guide function creates necessary files" {
    run guide "TestUser"
    [ "$status" -eq 0 ]
    [ -f "plan.md" ]
    [ -f "bio.md" ]
    [ -f "done.md" ]
    [ -f "ideas.md" ]
    [ -f "chat.bb" ]
}

@test "chat function handles user input correctly" {
    echo "test input" | guide "TestUser"
    run cat chat.bb
    [ "$status" -eq 0 ]
    [[ "${output}" == *"Guide: Hello TestUser! How can I assist you today?"* ]]
    [[ "${output}" == *"TestUser: test input"* ]]
    [[ "${output}" == *"Guide: Mocked response from Guide"* ]]
}

@test "chat function exits on 'quit' command" {
    echo "quit" | guide "TestUser"
    run cat chat.bb
    [ "$status" -eq 0 ]
    [[ "${output}" == *"Guide: Goodbye, TestUser! Have a great day!"* ]]
}

@test "process_input function calls query and updates chat file" {
    process_input "test question"
    run cat chat.bb
    [ "$status" -eq 0 ]
    [[ "${output}" == *"Guide: Mocked response from Guide"* ]]
}

@test "guide function uses provided username" {
    echo "quit" | guide "CustomUser"
    run cat chat.bb
    [ "$status" -eq 0 ]
    [[ "${output}" == *"Guide: Hello CustomUser!"* ]]
    [[ "${output}" == *"Guide: Goodbye, CustomUser!"* ]]
}

@test "guide function fails without username" {
    run guide
    [ "$status" -ne 0 ]
    [[ "$output" == *"User's name is required"* ]]
}
