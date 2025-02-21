package main

import (
	"bytes"
	"io"
	"os"
	"strings"
	"testing"
)

// Use explicit string literals (with \n and no extra formatting from raw-string indents).
const (
	spaceIndented = "def hello():\n    print(\"Hello, world!\")\n    if True:\n        print(\"Nested block\")\n"
	tabIndented   = "def hello():\n\tprint(\"Hello, world!\")\n\tif True:\n\t\tprint(\"Nested block\")\n"
	mixedIndented = "def hello():\n    print(\"Hello, world!\")\n\tif True:\n\t\tprint(\"Nested block\")\n"
	unindented    = "def hello():\nprint('Hello, world!')\n"
	commonIndented = "    def hello():\n        print(\"Hello, world!\")\n        if True:\n            print(\"Nested block\")\n"
	bogusCommon = "\t    def hello():\n\t        print(\"Hello, world!\")\n\t        if True:\n\t            print(\"Nested block\")\n"
)

// Helper: create a temporary file containing the given content.
func stringToTempFile(t *testing.T, content string) *os.File {
	f, err := os.CreateTemp("", "stdin-temp")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := f.WriteString(content); err != nil {
		f.Close()
		t.Fatal(err)
	}
	if _, err := f.Seek(0, 0); err != nil {
		f.Close()
		t.Fatal(err)
	}
	return f
}

// Test detectIndent function
func TestDetectIndent(t *testing.T) {
	tests := []struct {
		input      string
		size       int
		indentType string
		minLevel   int
		shouldErr  bool
	}{
		// All nonempty lines must have a common indent.
		{spaceIndented, 4, "s", 0, false},
		{tabIndented, 1, "t", 0, false},
		{mixedIndented, 1, "t", 0, false},
		{unindented, 0, "", 0, false},
		{commonIndented, 4, "s", 1, false},
		{bogusCommon, 0, "", 0, true},
	}
	for _, test := range tests {
		size, typ, level, err := detectIndent(test.input)
		if test.shouldErr {
			if err == nil {
				t.Errorf("Expected error for input %q but got none", test.input)
			}
			continue
		}
		if err != nil {
			t.Errorf("Unexpected error for input %q: %v", test.input, err)
			continue
		}
		if size != test.size || typ != test.indentType || level != test.minLevel {
			t.Errorf("For input %q expected (%d, %q, %d) but got (%d, %q, %d)",
				test.input, test.size, test.indentType, test.minLevel,
				size, typ, level)
		}
	}
}

// Test applyIndent function
func TestApplyIndent(t *testing.T) {
	tests := []struct {
		input      string
		indentSize int
		indentType string
		minLevel   int
		expected   string
	}{
		// Converting from spaces to tabs.
		{spaceIndented, 1, "t", 0, tabIndented},
		// Converting from tabs to spaces.
		{tabIndented, 4, "s", 0, spaceIndented},
		// When the input has no indent.
		{unindented, 2, "s", 1, "  def hello():\n  print('Hello, world!')\n"},
		// With a common indent baseline.
		{commonIndented, 2, "s", 0, strings.ReplaceAll(spaceIndented, "    ", "  ")},
	}
	for _, test := range tests {
		output, err := applyIndent(test.input, test.indentSize, test.indentType, test.minLevel)
		if err != nil {
			t.Fatalf("Error applying indent: %v", err)
		}
		if output != test.expected {
			t.Errorf("Expected:\n%q\nGot:\n%q", test.expected, output)
		}
	}
}

// Test CLI detect functionality
func TestMainDetect(t *testing.T) {
	input := spaceIndented
	// When detected, aligno calls formatIndentCode and then if the result starts with "0", DEFAULT_INDENT is used.
	// For our input, detectIndent should yield (4, "s", 0) and then formatIndentCode returns "4s" (does not start with "0"),
	// so expected output is "4s\n"
	expected := "4s\n"

	oldStdin := os.Stdin
	oldStdout := os.Stdout
	defer func() {
		os.Stdin = oldStdin
		os.Stdout = oldStdout
	}()

	// Create temporary file for stdin.
	f := stringToTempFile(t, input)
	defer func() {
		f.Close()
		os.Remove(f.Name())
	}()
	os.Stdin = f

	// Use a pipe to capture stdout.
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = w

	if err := aligno(true, false, ""); err != nil {
		t.Fatalf("Error while detecting indent: %v", err)
	}
	w.Close()

	var buf bytes.Buffer
	if _, err := io.Copy(&buf, r); err != nil {
		t.Fatal(err)
	}

	result := buf.String()
	if result != expected {
		t.Errorf("Expected %q but got %q", expected, result)
	}
}

// Test CLI apply functionality
func TestMainApply(t *testing.T) {
	input := spaceIndented
	expected := tabIndented

	oldStdin := os.Stdin
	oldStdout := os.Stdout
	defer func() {
		os.Stdin = oldStdin
		os.Stdout = oldStdout
	}()

	// Create a temporary file for stdin.
	f := stringToTempFile(t, input)
	defer func() {
		f.Close()
		os.Remove(f.Name())
	}()
	os.Stdin = f

	// Use a pipe for stdout.
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = w

	err = aligno(false, true, "t")
	if err != nil {
		t.Fatalf("Error while applying indent: %v", err)
	}
	w.Close()

	var buf bytes.Buffer
	if _, err := io.Copy(&buf, r); err != nil {
		t.Fatal(err)
	}

	result := strings.TrimSuffix(buf.String(), "\n")
	if result != expected[:len(expected)-1] { // remove the trailing newline from expected for the comparison
		t.Errorf("Expected %q but got %q", expected, result+"\n")
	}
}

// Test empty input
func TestEmptyInput(t *testing.T) {
	// detectIndent on an empty string should return zeros.
	size, typ, level, err := detectIndent("")
	if err != nil {
		t.Errorf("Unexpected error on empty input: %v", err)
	}
	if size != 0 || typ != "" || level != 0 {
		t.Errorf("Expected (0,\"\",0) but got (%d,%q,%d)", size, typ, level)
	}

	// applyIndent on empty input should produce only the minimum indent plus a final newline.
	// For parameters (4, "s", 2), minIndent is 8 spaces.
	expected := "        \n"
	applyResult, err := applyIndent("", 4, "s", 2)
	if err != nil {
		t.Fatalf("Error during apply indent: %v", err)
	}

	if applyResult != expected {
		t.Errorf("Expected apply result %q but got %q", expected, applyResult)
	}
}

// Test single line
func TestSingleLine(t *testing.T) {
	line := "print('Hello')"
	// detectIndent on a single unindented line should return zeros.
	size, typ, level, err := detectIndent(line)
	if err != nil {
		t.Errorf("Unexpected error on single line: %v", err)
	}
	if size != 0 || typ != "" || level != 0 {
		t.Errorf("Expected (0,\"\",0) for single line but got (%d,%q,%d)", size, typ, level)
	}

	expected := "  print('Hello')\n"
	applyResult, err := applyIndent(line, 2, "s", 1)
	if err != nil {
		t.Fatalf("Error during apply indent: %v", err)
	}

	if applyResult != expected {
		t.Errorf("Expected apply result %q but got %q", expected, applyResult)
	}
}

// Test parseIndentCode and formatIndentCode
func TestParseFormatIndentCode(t *testing.T) {
	tests := []struct {
		indentCode string
		expected   struct {
			size       int
			indentType string
			minLevel   int
		}
	}{
		{"t", struct {
			size       int
			indentType string
			minLevel   int
		}{1, "t", 0}},
		{"4s", struct {
			size       int
			indentType string
			minLevel   int
		}{4, "s", 0}},
		{"2s1", struct {
			size       int
			indentType string
			minLevel   int
		}{2, "s", 1}},
		{"t2", struct {
			size       int
			indentType string
			minLevel   int
		}{1, "t", 2}},
	}

	for _, test := range tests {
		size, indentType, minLevel, err := parseIndentCode(test.indentCode)
		if err != nil {
			t.Fatalf("Error parsing indent code %q: %v", test.indentCode, err)
		}

		if size != test.expected.size || indentType != test.expected.indentType || minLevel != test.expected.minLevel {
			t.Errorf("Mismatch for %q. Expected (%d, %q, %d) but got (%d, %q, %d)",
				test.indentCode, test.expected.size, test.expected.indentType, test.expected.minLevel,
				size, indentType, minLevel)
		}

		formatted, err := formatIndentCode(size, indentType, minLevel)
		if err != nil {
			t.Fatalf("Error formatting indent code %q: %v", test.indentCode, err)
		}

		if formatted != test.indentCode {
			t.Errorf("Expected formatted result %q but got %q", test.indentCode, formatted)
		}
	}
}
