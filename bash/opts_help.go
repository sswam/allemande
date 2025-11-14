// Package main provides tools for generating help messages from shell script option declarations
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

const Version = "0.1.5"

// Compile regexps once outside functions where they are used repeatedly
var (
	secondCommentRe    = regexp.MustCompile(`(=.+?)\s+#.*`)
	arrayPattern       = regexp.MustCompile(`\b(\w)=\((.*?)\)`)
	longArrayPattern   = regexp.MustCompile(`\b(\w\w+)=\((.*?)\)`)
	shortOptPattern    = regexp.MustCompile(`\b(\w)=`)
	longOptPattern     = regexp.MustCompile(`\b(\w\w+)=`)
	commentSpaceRe     = regexp.MustCompile(`(\S)(\s+)#`)
	shortOptSpaceRe    = regexp.MustCompile(`\s(-\w)`)
	functionDeclRe     = regexp.MustCompile(`^[a-zA-Z0-9_-]+\(\)\s*\{`)
	commentedOptRe     = regexp.MustCompile(`^\s*#\s*(local )?\w+=`)
)

// processLine handles a single line from the script and formats it for help output
func processLine(line, scriptName string) string {
	// Remove leading whitespace and 'local'
	line = strings.TrimSpace(line)
	line = strings.TrimPrefix(line, "local ")

	// Strip second comment (e.g., for shellcheck disable)
	line = secondCommentRe.ReplaceAllString(line, "$1")

	// Replace $0 with script name
	line = strings.ReplaceAll(line, "$0 ", scriptName+" ")

	// Handle comment-only lines
	if strings.HasPrefix(line, "#") {
		return strings.TrimPrefix(strings.TrimPrefix(line, "#"), " ")
	}

	// Process option declarations
	if line == "" {
		return ""
	}

	// Handle array declarations
	line = arrayPattern.ReplaceAllStringFunc(line, func(match string) string {
		parts := arrayPattern.FindStringSubmatch(match)
		return fmt.Sprintf("-%s,%s", parts[1], processArray(parts[2]))
	})

	// Handle long array declarations
	line = longArrayPattern.ReplaceAllStringFunc(line, func(match string) string {
		parts := longArrayPattern.FindStringSubmatch(match)
		return fmt.Sprintf("--%s,%s", parts[1], processArray(parts[2]))
	})

	// Handle short and long options
	line = shortOptPattern.ReplaceAllString(line, "-$1=")
	line = longOptPattern.ReplaceAllString(line, "--$1=")

	// Replace underscores with dashes
	parts := strings.SplitN(line, "#", 2)
	parts[0] = strings.ReplaceAll(parts[0], "_", "-")
	if len(parts) > 1 {
		line = parts[0] + "#" + parts[1]
	} else {
		line = parts[0]
	}

	// Format comments
	line = commentSpaceRe.ReplaceAllString(line, "$1\t#")

	// Handle option columns
	if shortOptSpaceRe.MatchString(line) {
		line = shortOptSpaceRe.ReplaceAllString(line, "\t$1")
	} else {
		line = strings.ReplaceAll(line, "\t", "\t\t")
	}

	return line
}

// processArray formats array contents for help output
func processArray(content string) string {
	if strings.Contains(content, ",") {
		return fmt.Sprintf("%q", content)
	}
	return strings.ReplaceAll(content, " ", ",")
}

// optsHelp generates help documentation from a shell script
func optsHelp(scriptPath string) error {
	script := filepath.Clean(scriptPath)

	// Follow symlinks (up to 10 levels)
	for i := 0; i < 10; i++ {
		info, err := os.Lstat(script)
		if err != nil {
			return fmt.Errorf("failed to stat %s: %w", script, err)
		}

		if info.Mode()&os.ModeSymlink == 0 {
			break
		}

		if filepath.Base(filepath.Dir(script)) == "canon" {
			break
		}

		link, err := os.Readlink(script)
		if err != nil {
			return fmt.Errorf("failed to read symlink %s: %w", script, err)
		}

		script = filepath.Join(filepath.Dir(script), link)
	}

	scriptName := filepath.Base(script)

	file, err := os.Open(script)
	if err != nil {
		return fmt.Errorf("cannot open %s: %w", script, err)
	}
	defer file.Close()

	var output strings.Builder
	output.WriteString(scriptName + " ")

	scanner := bufio.NewScanner(file)
	skipBlanks := false
	blanks := 0

	for scanner.Scan() {
		line := scanner.Text()

		// Skip fully commented out option lines
		trimmed := strings.TrimSpace(line)
		if commentedOptRe.MatchString(trimmed) {
			continue
		}

		// Skip shebang
		if strings.HasPrefix(line, "#!") {
			skipBlanks = true
			continue
		}

		// Stop conditions
		if strings.Contains(line, ". opts") ||
			strings.Contains(line, "eval ") {
			break
		}

		// Skip function declarations and special lines
		if functionDeclRe.MatchString(line) ||
			strings.HasPrefix(strings.TrimSpace(line), ". ") ||
			strings.HasPrefix(strings.TrimSpace(line), "# shellcheck disable=") {
			continue
		}

		isBlank := strings.TrimSpace(line) == ""
		if isBlank {
			blanks++
			continue
		}

		if blanks > 0 && !skipBlanks {
			output.WriteString("\n")
		}
		blanks = 0
		skipBlanks = false

		processed := processLine(line, scriptName)
		if processed != "" {
			output.WriteString(processed + "\n")
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading file: %w", err)
	}

	// Try to format with tsv2txt if available
	cmd := exec.Command("tsv2txt", "-m")
	cmd.Stdin = strings.NewReader(output.String())
	if formatted, err := cmd.Output(); err == nil {
		fmt.Print(string(formatted))
	} else {
		fmt.Print(output.String())
	}

	return nil
}

func main() {
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [script]\n", os.Args[0])
		fmt.Fprintln(os.Stderr, "Generate a help message for command-line options based on the script's content.")
		flag.PrintDefaults()
	}

	flag.Parse()

	if flag.NArg() != 1 {
		flag.Usage()
		os.Exit(1)
	}

	if err := optsHelp(flag.Arg(0)); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
