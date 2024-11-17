// tsv2txt_test.go

package main

import (
	"bytes"
	"os"
	"strings"
	"testing"
)

func TestGetTsvFormat(t *testing.T) {
	tests := []struct {
		name     string
		envVar   string
		testStr  string
		expected int
	}{
		{"default", "", "a\tb", 2},
		{"default_with_spaces", "", "a \tb", 2},
		{"spaces_ok", "spaces_ok", "a  b", 2},
		{"strict", "strict", "a\tb", 2},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			os.Setenv("TSV_FORMAT", tt.envVar)
			defer os.Unsetenv("TSV_FORMAT")

			rx := getTsvFormat()
			parts := rx.Split(tt.testStr, -1)
			if len(parts) != tt.expected {
				t.Errorf("Expected %d parts, got %d", tt.expected, len(parts))
			}
		})
	}
}

func TestProcessRow(t *testing.T) {
	tests := []struct {
		name     string
		row      []string
		options  []string
		widths   []int
		expected []int
	}{
		{
			name:     "basic row",
			row:      []string{"abc", "def"},
			options:  []string{},
			widths:   []int{},
			expected: []int{3, 3},
		},
		{
			name:     "null value",
			row:      []string{"\x00", "def"},
			options:  []string{},
			widths:   []int{},
			expected: []int{6, 3}, // [NULL] is 6 characters
		},
		{
			name:     "with format option",
			row:      []string{"123"},
			options:  []string{"%4s"},
			widths:   []int{},
			expected: []int{4},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			widths := make([]int, len(tt.widths))
			copy(widths, tt.widths)
			// Capture the returned widths from processRow
			widths = processRow(tt.row, widths, tt.options)

			if len(widths) != len(tt.expected) {
				t.Fatalf("Expected %d widths, got %d", len(tt.expected), len(widths))
			}
			for i, w := range widths {
				if w != tt.expected[i] {
					t.Errorf("Width[%d]: expected %d, got %d", i, tt.expected[i], w)
				}
			}
		})
	}
}

func TestSplitIntoTables(t *testing.T) {
	tests := []struct {
		name       string
		input      string
		multiTable bool
		expected   int
	}{
		{
			name:       "single table",
			input:      "a\tb\nc\td\n",
			multiTable: false,
			expected:   1,
		},
		{
			name:       "multiple tables",
			input:      "a\tb\nheader\nc\td\n",
			multiTable: true,
			expected:   3,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			reader := strings.NewReader(tt.input)
			tables := splitIntoTables(reader, tt.multiTable)
			if len(tables) != tt.expected {
				t.Errorf("Expected %d tables, got %d", tt.expected, len(tables))
			}
		})
	}
}

func TestProcessTable(t *testing.T) {
	tests := []struct {
		name     string
		input    []string
		gap      string
		options  []string
		expected string
	}{
		{
			name:     "simple table",
			input:    []string{"a\tb", "c\td"},
			gap:      "  ",
			options:  []string{},
			expected: "a  b\nc  d\n",
		},
		{
			name:     "with tabs",
			input:    []string{"\ta\tb"},
			gap:      "  ",
			options:  []string{},
			expected: "\ta  b\n",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var buf bytes.Buffer
			processTable(tt.input, tt.gap, tt.options, &buf)
			result := buf.String()
			if result != tt.expected {
				t.Errorf("Expected:\n%q\nGot:\n%q", tt.expected, result)
			}
		})
	}
}

func TestAdjustOptions(t *testing.T) {
	tests := []struct {
		name     string
		options  []string
		widths   []int
		expected []string
	}{
		{
			name:     "no options",
			options:  []string{},
			widths:   []int{3, 4},
			expected: []string{"%-3s", "%-4s"},
		},
		{
			name:     "with format option",
			options:  []string{"%04d", ""},
			widths:   []int{4, 3},
			expected: []string{"%04d", "%-3s"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := adjustOptions(tt.options, tt.widths)
			if len(result) != len(tt.expected) {
				t.Fatalf("Expected %d options, got %d", len(tt.expected), len(result))
			}
			for i, opt := range result {
				if opt != tt.expected[i] {
					t.Errorf("Option[%d]: expected %q, got %q", i, tt.expected[i], opt)
				}
			}
		})
	}
}
