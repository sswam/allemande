// Package main converts TSV (Tab-Separated Values) to formatted text.
// It supports multiple tables in input with the -m option.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"
	"unicode/utf8"
)

const Version = "1.1.13"

// Options holds the command-line configuration
type Options struct {
	multiTable    bool
	gap           string
	formatOptions []string
	tabs          bool
}

func getTsvFormat() *regexp.Regexp {
	// Return the TSV format regex based on environment variable.
	tsvFormat := os.Getenv("TSV_FORMAT")
	switch tsvFormat {
	case "spaces_ok":
		return regexp.MustCompile(`\s{2,}|\t`)
	case "strict":
		return regexp.MustCompile(`\t`)
	default:
		return regexp.MustCompile(` *\t`)
	}
}

func processRow(row []string, widths []int, options []string) []int {
	// Process a single row, updating column widths.

	// Extend widths slice if needed
	if len(widths) < len(row) {
		widths = append(widths, make([]int, len(row)-len(widths))...)
	}

	for i, cell := range row {
		if cell == "\x00" {
			cell = "[NULL]"
			row[i] = cell
			// debug log on stderr that we are here
			fmt.Fprintf(os.Stderr, "Found null value in row: %v\n", row)
		}

		var opt string
		if i < len(options) {
			opt = options[i]
		} else {
			opt = "{}"
		}

		formattedCell := cell
		if strings.Contains(opt, "%") {
			formattedCell = fmt.Sprintf(opt, cell)
		}

		length := utf8.RuneCountInString(formattedCell)
		if i == 0 {
			leadingTabs := len(cell) - len(strings.TrimLeft(cell, "\t"))
			length += leadingTabs * 7  // 7 because the tab itself counts as 1
		}

		if length > widths[i] {
			widths[i] = length
		}
	}
	return widths
}

func adjustOptions(options []string, widths []int) []string {
	// Adjust format options based on column widths.
	result := make([]string, len(widths))
	for i := range widths {
		if i < len(options) && options[i] != "" {
			result[i] = options[i]
		} else {
			result[i] = fmt.Sprintf("%%-%ds", widths[i])
		}
	}
	return result
}

func printFormattedRows(rows [][]string, formatStr string, optionCount int, w io.Writer) {
	// Print formatted rows.
	if optionCount == 0 {
		return
	}

	for _, row := range rows {
		if len(row) == 0 {
			fmt.Fprintln(w)
			continue
		}

		// Preserve leading tabs in first column
		firstCol := row[0]
		leadingTabs := len(firstCol) - len(strings.TrimLeft(firstCol, "\t"))
		dedented := strings.TrimLeft(firstCol, "\t")
		row[0] = strings.Repeat(" ", leadingTabs*8) + dedented

		// Ensure we have enough values for formatting
		args := make([]interface{}, optionCount)
		for i := 0; i < optionCount; i++ {
			if i < len(row) {
				args[i] = row[i]
			} else {
				args[i] = ""
			}
		}

		line := fmt.Sprintf(formatStr, args...)

		// Restore leading tabs
		if leadingTabs > 0 && len(line) >= leadingTabs*8 {
			line = strings.Repeat("\t", leadingTabs) + line[leadingTabs*8:]
		}

		fmt.Fprintln(w, strings.TrimRight(line, " "))
	}
}

func processTable(table []string, gap string, formatOptions []string, w io.Writer) {
	// Process a table of TSV data.
	widths := []int{}
	rows := [][]string{}
	rxSplit := getTsvFormat()

	for _, line := range table {
		dedented := strings.TrimLeft(line, "\t")
		leadingTabs := len(line) - len(dedented)
		row := rxSplit.Split(dedented, -1)

		if len(row) > 0 {
			row[0] = strings.Repeat("\t", leadingTabs) + row[0]
		}

		widths = processRow(row, widths, formatOptions)
		rows = append(rows, row)
	}

	options := adjustOptions(formatOptions, widths)
	formatStr := strings.Join(options, gap)
	printFormattedRows(rows, formatStr, len(options), w)
}

func splitIntoTables(r io.Reader, multiTable bool) [][]string {
	// Split input stream into tables based on multi-table option.
	var tables [][]string
	var currentTable []string
	rxSplit := getTsvFormat()
	scanner := bufio.NewScanner(r)

	for scanner.Scan() {
		line := scanner.Text()
		if multiTable && !rxSplit.MatchString(line) {
			if len(currentTable) > 0 {
				tables = append(tables, currentTable)
				currentTable = nil
			}
			tables = append(tables, []string{line})
		} else {
			currentTable = append(currentTable, line)
		}
	}

	if len(currentTable) > 0 {
		tables = append(tables, currentTable)
	}

	return tables
}

func main() {
	// Main entry point and command-line processing.
	opts := &Options{}

	flag.BoolVar(&opts.multiTable, "m", false, "Support multiple tables in input")
	flag.StringVar(&opts.gap, "g", "  ", "Set gap between columns")
	flag.BoolVar(&opts.tabs, "t", false, "Use tabs in gap")

	flag.Parse()
	opts.formatOptions = flag.Args()

	// Process gap option
	if n, err := fmt.Sscanf(opts.gap, "%d", &opts.gap); err == nil {
		opts.gap = strings.Repeat(" ", n)
	}

	if opts.tabs {
		if strings.HasSuffix(opts.gap, " ") {
			opts.gap = opts.gap[:len(opts.gap)-1] + "\t"
		} else {
			opts.gap += "\t"
		}
	}

	// Process tables
	tables := splitIntoTables(os.Stdin, opts.multiTable)
	for _, table := range tables {
		processTable(table, opts.gap, opts.formatOptions, os.Stdout)
	}
}
