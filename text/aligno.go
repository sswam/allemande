package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// IMPORTANT: Do not change any functionality. This file is a literal, exact
// translation of the provided Python code (aligno_py.py) following the style
// of hello_go.go and the guidelines in guidance-go.md.

// Version string
const version = "1.0.3"

// getEnv retrieves the environment variable for key and returns fallback if not set.
func getEnv(key, fallback string) string {
	val := os.Getenv(key)
	if val == "" {
		return fallback
	}
	return val
}

// defaultIndent returns the default indent string based on environment variables.
func defaultIndent() string {
	ft := os.Getenv("FILETYPE")
	if ft == "python" {
		return "4s"
	} else if ft == "c" {
		return "t"
	}
	return getEnv("INDENT", "t")
}

var DEFAULT_INDENT = defaultIndent()

// gcd computes the greatest common divisor of a and b.
func gcd(a, b int) int {
	for b != 0 {
		a, b = b, a%b
	}
	if a < 0 {
		return -a
	}
	return a
}

// findCommonFactor takes a slice of ints and returns their greatest common divisor.
func findCommonFactor(nums []int) int {
	if len(nums) == 0 {
		return 0
	}
	result := nums[0]
	for _, n := range nums[1:] {
		result = gcd(result, n)
	}
	return result
}

// pair is a helper type used for frequency counts.
type pair struct {
	Key   int
	Count int
}

// sortPairsDesc sorts pairs in descending order of Count.
func sortPairsDesc(pairs []pair) {
	sort.Slice(pairs, func(i, j int) bool {
		return pairs[i].Count > pairs[j].Count
	})
}

// detectIndent inspects the input text and returns (indent_size, indent_type, min_level).
// It returns an error on invalid conditions.
func detectIndent(text string) (int, string, int, error) {
	// Split text into lines.
	allLines := strings.Split(text, "\n")
	// Remove empty lines.
	var lines []string
	for _, line := range allLines {
		if strings.TrimSpace(line) != "" {
			lines = append(lines, line)
		}
	}

	// Find the common indentation among all lines
	var commonIndent string
	var haveCommonIndent bool
	for _, line := range lines {
		// Get the indent size by counting leading spaces/tabs
		indentSize := len(line) - len(strings.TrimLeft(line, " \t"))
		indent := line[:indentSize]

		if !haveCommonIndent {
			commonIndent = indent
			haveCommonIndent = true
		} else {
			// Find common prefix between current commonIndent and new indent
			commonLen := 0
			for i := 0; i < len(commonIndent) && i < len(indent); i++ {
				if commonIndent[i] != indent[i] {
					break
				}
				commonLen++
			}
			commonIndent = commonIndent[:commonLen]
		}
	}

	// Log common indentation.
	if debugLogging {
		log.Printf("DEBUG: commonIndent=%q", commonIndent)
	}

	// Check for mixed tabs and spaces.
	if strings.Contains(commonIndent, "\t") && strings.Contains(commonIndent, " ") {
		return 0, "", 0, fmt.Errorf("mixed tabs and spaces in common indentation")
	}

	commonIndentLength := len(commonIndent)

	// Remove common indentation from all lines.
	strippedLines := make([]string, len(lines))
	for i, line := range lines {
		if len(line) >= commonIndentLength {
			strippedLines[i] = line[commonIndentLength:]
		} else {
			strippedLines[i] = ""
		}
	}

	// Compile regex patterns for spaces and tabs.
	spaceRe := regexp.MustCompile(`^ +`)
	tabRe := regexp.MustCompile(`^\t+`)

	spaceCounts := make([]int, len(strippedLines))
	tabCounts := make([]int, len(strippedLines))
	totalSpaces := 0
	totalTabs := 0

	for i, line := range strippedLines {
		if m := spaceRe.FindString(line); m != "" {
			spaceCounts[i] = len(m)
		} else {
			spaceCounts[i] = 0
		}
		if m := tabRe.FindString(line); m != "" {
			tabCounts[i] = len(m)
		} else {
			tabCounts[i] = 0
		}
		totalSpaces += spaceCounts[i]
		totalTabs += tabCounts[i]
	}

	// Log debugging info.
	if debugLogging {
		log.Printf("DEBUG: spaceCounts=%v", spaceCounts)
		log.Printf("DEBUG: tabCounts=%v", tabCounts)
	}

	// Count frequency for indent sizes from spaces that are > 0 and <= 8.
	freq := make(map[int]int)
	for _, count := range spaceCounts {
		if count > 0 && count <= 8 {
			freq[count]++
		}
	}

	// Create a slice of pairs for sorting.
	var freqPairs []pair
	for k, v := range freq {
		freqPairs = append(freqPairs, pair{Key: k, Count: v})
	}
	sortPairsDesc(freqPairs)

	var indentType string
	var indentSize int

	if commonIndent == "" && totalSpaces == 0 && totalTabs == 0 {
		indentType = ""
		indentSize = 0
	} else if strings.Contains(commonIndent, "\t") || totalTabs*2 > totalSpaces {
		indentType = "t"
		indentSize = 1
	} else if len(freqPairs) == 0 {
		indentType = "s"
		if commonIndentLength%4 == 0 {
			indentSize = 4
		} else if commonIndentLength%2 == 0 {
			indentSize = 2
		} else {
			indentSize = 1
		}
	} else {
		indentType = "s"
		size1 := freqPairs[0].Key
		var nums []int
		nums = append(nums, size1)
		if len(freqPairs) > 1 {
			size2 := freqPairs[1].Key
			nums = append(nums, size2)
		}
		nums = append(nums, commonIndentLength)
		g := findCommonFactor(nums)
		if g == 1 {
			if debugLogging {
				log.Printf("DEBUG: Indent detected is one space, sounds like a bad idea")
			}
			indentSize = 4
		} else {
			indentSize = g
		}
	}

	var minLevel int
	if indentSize != 0 {
		minLevel = commonIndentLength / indentSize
	} else {
		minLevel = 0
	}

	if indentType == "t" && indentSize != 1 {
		return 0, "", 0, fmt.Errorf("indent type is tab but indent size is not 1: %d", indentSize)
	}

	if debugLogging {
		log.Printf("DEBUG: >> indentSize=%d, indentType=%s, minLevel=%d", indentSize, indentType, minLevel)
	}

	return indentSize, indentType, minLevel, nil
}

// applyIndent applies the specified indentation to the input text.
func applyIndent(text string, indentSize int, indentType string, minLevel int) (string, error) {
	// Detect the original indentation of the input text.
	origIndentSize, origIndentType, origMinLevel, err := detectIndent(text)
	if err != nil {
		return "", err
	}

	// remove "\n" from end of text
	text = strings.TrimSuffix(text, "\n")

	lines := strings.Split(text, "\n")

	// Create indent strings for original and new indentation.
	var origIndentStr string
	if origIndentType == "t" {
		origIndentStr = "\t"
	} else {
		origIndentStr = strings.Repeat(" ", origIndentSize)
	}
	origMinIndent := strings.Repeat(origIndentStr, origMinLevel)

	var newIndentStr string
	if indentType == "t" {
		newIndentStr = "\t"
	} else {
		newIndentStr = strings.Repeat(" ", indentSize)
	}
	minIndent := strings.Repeat(newIndentStr, minLevel)

	// Regex to capture leading whitespace and the rest.
	reLine := regexp.MustCompile(`^(\s*)(.*)$`)

	// reindentLine processes one line.
	reindentLine := func(line string) string {
		// Remove trailing whitespace.
		line = strings.TrimRight(line, " \t")
		// Remove original minimum indentation.
		line = strings.TrimPrefix(line, origMinIndent)
		matches := reLine.FindStringSubmatch(line)
		lead := ""
		content := ""
		if matches != nil && len(matches) >= 3 {
			lead = matches[1]
			content = matches[2]
		}
		var lineIndent int
		if origIndentSize > 0 {
			lineIndent = len(lead) / origIndentSize
		} else {
			lineIndent = 0
		}
		newLineIndent := minIndent + strings.Repeat(newIndentStr, lineIndent)
		return newLineIndent + content
	}

	var outputLines []string
	for _, line := range lines {
		// Process every line.
		outputLines = append(outputLines, reindentLine(line))
	}

	// Join all lines and ensure there is a final newline.
	return strings.Join(outputLines, "\n") + "\n", nil
}

// formatIndentCode converts the indentation parameters to a string representation.
func formatIndentCode(indentSize int, indentType string, minLevel int) (string, error) {
	minLevelStr := ""
	if minLevel != 0 {
		minLevelStr = strconv.Itoa(minLevel)
	}
	if indentType == "t" {
		if indentSize != 1 {
			return "", fmt.Errorf("invalid indent size for tab: %d", indentSize)
		}
		return "t" + minLevelStr, nil
	}
	return strconv.Itoa(indentSize) + "s" + minLevelStr, nil
}

// parseIndentCode parses the indent code into its components.
func parseIndentCode(indentCode string) (int, string, int, error) {
	// Extract indent size, type, and minimum level from the indent code string.
	re := regexp.MustCompile(`^(\d*)(t|s)(\d*)$`)
	matches := re.FindStringSubmatch(indentCode)
	if matches == nil || len(matches) < 4 {
		return 0, "", 0, fmt.Errorf("invalid indent code: %s", indentCode)
	}
	indentSizeStr := matches[1]
	indentType := matches[2]
	minLevelStr := matches[3]

	var indentSize int
	var err error
	if indentSizeStr == "" {
		if indentType == "s" {
			indentSize = 4
		} else {
			indentSize = 1
		}
	} else {
		indentSize, err = strconv.Atoi(indentSizeStr)
		if err != nil {
			return 0, "", 0, err
		}
	}
	if indentType == "t" && indentSize != 1 {
		return 0, "", 0, fmt.Errorf("invalid indent size for tab: %d", indentSize)
	}
	if indentType == "s" && indentSize > 8 {
		return 0, "", 0, fmt.Errorf("invalid indent size for spaces: %d", indentSize)
	}
	if indentType == "s" && indentSize != 1 && indentSize != 2 && indentSize != 4 {
		log.Printf("WARNING: inadvisable indent size for spaces: %d", indentSize)
	}
	var minLevel int
	if minLevelStr == "" {
		minLevel = 0
	} else {
		minLevel, err = strconv.Atoi(minLevelStr)
		if err != nil {
			return 0, "", 0, err
		}
	}
	return indentSize, indentType, minLevel, nil
}

// aligno performs detection or application of indentation as specified.
// Environment:
//   INDENT: default indent to use when not specified
//   FILETYPE: use standard indentation for this language (python or c)

// Examples:
//
//	aligno < input.txt
//	aligno --apply < input.c > output.c
//	aligno --apply 4s2 < input.py > output.py
func aligno(detect, apply bool, indentCode string) error {

	// Get all input from stdin.
	inputBytes, err := io.ReadAll(os.Stdin)
	if err != nil {
		return err
	}
	inputText := string(inputBytes)

	// Determine whether to detect or apply indentation.
	if indentCode == "" {
		indentCode = DEFAULT_INDENT
	}
	if apply && detect {
		return fmt.Errorf("cannot detect and apply indent at the same time")
	}
	if !apply && !detect {
		detect = true
	}

	if detect {
		// Detect and output the indentation of the input text.
		indentSize, indentType, minLevel, err := detectIndent(inputText)
		if err != nil {
			return err
		}
		code, err := formatIndentCode(indentSize, indentType, minLevel)
		if err != nil {
			return err
		}
		// If indent code starts with "0", use DEFAULT_INDENT.
		if strings.HasPrefix(code, "0") {
			code = DEFAULT_INDENT
		}
		fmt.Println(code)
	} else {
		// Apply the specified or default indentation to the input text.
		indentSize, indentType, minLevel, err := parseIndentCode(indentCode)
		if err != nil {
			return err
		}
		outputText, err := applyIndent(inputText, indentSize, indentType, minLevel)
		if err != nil {
			return err
		}
		fmt.Print(outputText)
	}
	return nil
}

// printUsage prints the usage instructions.
func printUsage(w io.Writer, programName string) {
	fmt.Fprintf(w, "Usage: %s [OPTIONS]\n", programName)
	fmt.Fprintln(w, "Options:")
	fmt.Fprintln(w, "  --detect, -D            detect indent type and minimum level")
	fmt.Fprintln(w, "  --apply, -a             apply specified indent type and minimum level")
	fmt.Fprintln(w, "  indent_code             indent code (e.g., '1t', '4s2')")
}

var debugLogging bool

func main() {
	// Set up command-line arguments.
	detectPtr := flag.Bool("detect", false, "detect indent type and minimum level")
	// Allow short flag -D for detect.
	dFlag := flag.Bool("D", false, "detect indent type and minimum level")
	applyPtr := flag.Bool("apply", false, "apply specified indent type and minimum level")
	// Allow short flag -a for apply.
	aFlag := flag.Bool("a", false, "apply specified indent type and minimum level")
	debugPtr := flag.Bool("debug", false, "enable debug logging")
	dDebug := flag.Bool("d", false, "enable debug logging")

	// Custom usage.
	flag.Usage = func() {
		printUsage(os.Stdout, os.Args[0])
	}

	// Parse flags.
	flag.Parse()

	debugLogging = *debugPtr || *dDebug

	// Combine flags for detect and apply.
	detect := *detectPtr || *dFlag
	apply := *applyPtr || *aFlag

	// Positional argument: indent_code.
	var indentCode string
	args := flag.Args()
	if len(args) > 0 {
		indentCode = args[0]
	}

	// If both are false then default to detect.
	if !detect && !apply {
		detect = true
	}

	// If help is requested, print usage and exit.
	if len(os.Args) > 1 {
		if os.Args[1] == "-h" || os.Args[1] == "--help" {
			printUsage(os.Stdout, os.Args[0])
			return
		}
	}

	// Call aligno.
	if err := aligno(detect, apply, indentCode); err != nil {
		log.Printf("Error: %v", err)
		os.Exit(1)
	}
}
