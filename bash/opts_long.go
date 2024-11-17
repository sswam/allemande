// opts_long processes shell script option declarations and generates
// corresponding long-to-short option mappings

package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strings"
)

const Version = "0.1.3"

// processLine handles a single line of input, converting option declarations
// to shell variable assignments
func processLine(line string) (string, error) {
	// Remove leading whitespace and 'local'
	line = strings.TrimSpace(line)
	line = strings.TrimPrefix(line, "local ")

	// Compile regex patterns
	pattern := regexp.MustCompile(`(\w+)=(\S*)\s+(\w+)=(\S*)(?:\s+#\s*(.*))?`)
	matches := pattern.FindStringSubmatch(line)

	if matches == nil {
		return "", nil
	}

	longOpt := matches[1]
	shortOpt := matches[3]
	default2 := matches[4]

	// Check if the default value indicates an array
	if strings.HasPrefix(default2, "(") {
		return fmt.Sprintf("%s=(${%s[@]} ${%s[@]}); unset %s",
			longOpt, longOpt, shortOpt, shortOpt), nil
	}

	// Regular variable assignment
	return fmt.Sprintf("%s=${%s:-$%s}; unset %s",
		longOpt, longOpt, shortOpt, shortOpt), nil
}

// optsLong processes the input script file and outputs option mappings
func optsLong(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return fmt.Errorf("cannot open %s: %w", filename, err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()

		// Stop conditions
		if strings.Contains(line, ". opts") ||
			strings.Contains(line, "eval ") {
			break
		}

		processed, err := processLine(line)
		if err != nil {
			return fmt.Errorf("error processing line: %w", err)
		}

		if processed != "" {
			fmt.Println(processed)
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading file: %w", err)
	}

	return nil
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <script>\n", os.Args[0])
		os.Exit(1)
	}

	if err := optsLong(os.Args[1]); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
