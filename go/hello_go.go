// This program is a simple example program that greets the user and optionally
// builds a shopping list. The program can optionally use AI.

package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
)

// Options holds the command-line configuration
type Options struct {
	language      string
	name          string
	shoppingItems []string
	useAI         bool
}

// printUsage prints the program usage information
func printUsage(w io.Writer, programName string) {
	fmt.Fprintf(w, "Usage: %s [OPTIONS]\n", programName)
	fmt.Fprintln(w, "Options:")
	fmt.Fprintln(w, "  -h, --help            Print this help message")
	fmt.Fprintln(w, "  -l, --language=LANG   Set the language (default: en)")
	fmt.Fprintln(w, "  -n, --name=NAME       Set the name (default: world)")
	fmt.Fprintln(w, "  -s, --shopping=ITEM   Add items to the shopping list (comma-separated)")
	fmt.Fprintln(w, "  -a, --use-ai          Use AI to help with the shopping list")
}

// getGreeting returns a greeting based on the language
func getGreeting(opts *Options) (string, error) {
	tlt_prompt := ""
	if opts.language != "en" {
		tlt_prompt = " Don't translate back to English."
	}
	if opts.useAI {
		query := fmt.Sprintf("Please greet %s in LANG=%s. Be creative, but not more than 50 words.%s",
			opts.name, opts.language, tlt_prompt)
		return llmQuery(query)
	}

	greeting := map[string]string{
		"fr": "Bonjour",
		"es": "Hola",
		"de": "Hallo",
		"jp": "こんにちは",
		"cn": "你好",
		"en": "Hello",
	}

	g, ok := greeting[opts.language]
	if !ok {
		return "Whoops, I don't know your language without AI! Hi", nil
	}
	return g, nil
}

// buildShoppingList creates a shopping list string
func buildShoppingList(opts *Options) (string, error) {
	if len(opts.shoppingItems) == 0 {
		return "", nil
	}

	list := "\nShopping list:\n"
	for _, item := range opts.shoppingItems {
		list += fmt.Sprintf("- %s\n", item)
	}

	if !opts.useAI {
		return list, nil
	}

	prompt := fmt.Sprintf("Please echo the input and add any extra items we might need, in LANG=%s. Don't translate back to English.",
		opts.language)
	return llmProcess(prompt, list)
}

// llmQuery sends a query to the LLM and returns the response
func llmQuery(query string) (string, error) {
	cmd := exec.Command("llm", "query", query)
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("LLM query failed: %w", err)
	}
	return string(output), nil
}

// llmProcess processes input through the LLM with a given prompt
func llmProcess(prompt, input string) (string, error) {
	cmd := exec.Command("llm", "process", prompt)
	stdin, err := cmd.StdinPipe()
	if err != nil {
		return "", fmt.Errorf("failed to create stdin pipe: %w", err)
	}

	errCh := make(chan error, 1)
	go func() {
		defer stdin.Close()
		_, err := io.WriteString(stdin, input)
		errCh <- err
	}()

	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("LLM process failed: %w", err)
	}

	if err := <-errCh; err != nil {
		return "", fmt.Errorf("failed to write to stdin: %w", err)
	}

	return string(output), nil
}

func main() {
	opts := &Options{}

	flag.StringVar(&opts.language, "l", "en", "Set the language")
	flag.StringVar(&opts.name, "n", "world", "Set the name")
	flag.BoolVar(&opts.useAI, "a", false, "Use AI for enhanced features")

	var shopping string
	flag.StringVar(&shopping, "s", "", "Add items to shopping list (comma-separated)")

	flag.Parse()

	if len(os.Args) > 1 && (os.Args[1] == "-h" || os.Args[1] == "--help") {
		printUsage(os.Stdout, os.Args[0])
		return
	}

	if shopping != "" {
		items := strings.Split(shopping, ",")
		for _, item := range items {
			trimmedItem := strings.TrimSpace(item)
			if trimmedItem != "" {
				opts.shoppingItems = append(opts.shoppingItems, trimmedItem)
			}
		}
	}

	greeting, err := getGreeting(opts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting greeting: %v\n", err)
		os.Exit(1)
	}

	if opts.useAI {
		fmt.Print(greeting)
	} else {
		fmt.Printf("%s, %s\n", greeting, opts.name)
	}

	list, err := buildShoppingList(opts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error building shopping list: %v\n", err)
		os.Exit(1)
	}

	if list != "" {
		fmt.Print(list)
	}
}
