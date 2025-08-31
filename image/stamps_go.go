// Program to extract image prompts and output in plain or markdown format
package main

import (
    "bufio"
//    "errors"
    "flag"
    "fmt"
    "os"
    "path/filepath"
    "regexp"
    "strconv"
    "strings"

    "github.com/rwcarlsen/goexif/exif"
)

// Options holds command line flags
type Options struct {
    markdown bool
}

// gets the prompt from an image file using exif lib
func extractMetadata(filename string) (string, error) {
    ext := strings.ToLower(filepath.Ext(filename))

    f, err := os.Open(filename)
    if err != nil {
        return "", fmt.Errorf("failed to open file: %w", err)
    }
    defer f.Close()

    switch ext {
    case ".jpg", ".jpeg", ".tiff", ".tif":
        x, err := exif.Decode(f)
        if err != nil {
            return "", fmt.Errorf("failed to decode exif: %w", err)
        }
        comment, err := x.Get("UserComment")
        fmt.Println("EXIF comment raw:", comment) // Debug line to see raw comment
        if err != nil {
            // if errors.Is(err, exif.ErrNotFound) {
            //     return "", nil // No comment is not an error
            // }
            return "", fmt.Errorf("no UserComment found: %w", err)
        }

        // comment.String() returns a Go-syntax quoted string, which we need to unquote.
        unquoted, err := strconv.Unquote(comment.String())
        if err != nil {
            // Fallback for safety, maybe it's not quoted in some cases.
            return strings.TrimSpace(comment.String()), nil
        }
        return strings.TrimSpace(unquoted), nil

    case ".png", ".webp":
        // PNG/WebP handling would need a different library
        return "", fmt.Errorf("format %s not yet supported with internal library", ext)

    default:
        return "", fmt.Errorf("unsupported file format: %s", ext)
    }
}

// parses the image metadata to extract seed, model, and cleaned prompts
func parseMetadata(metadata, filename string) (seed, model, prompt, expandedPrompt string) {
    // Compile regexps for extraction
    seedRe := regexp.MustCompile(`Seed: (\d+)`)
    modelRe := regexp.MustCompile(`Model: ([^,]+)`)
    unPromptRe := regexp.MustCompile(`Unprompted Prompt: "((?:[^"\\]|\\.)*)"`)
    negPromptRe := regexp.MustCompile(`Unprompted Negative Prompt: "((?:[^"\\]|\\.)*)"`)

    // Extract seed
    if match := seedRe.FindStringSubmatch(prompt); len(match) > 1 {
        seed = match[1]
    }

    // Extract and map model name
    var modelName string
    if match := modelRe.FindStringSubmatch(prompt); len(match) > 1 {
        model := match[1]
        switch model {
        case "cyberrealisticPony_v85":
            modelName = "Coni"
        case "juggernautXL_juggXIByRundiffusion":
            modelName = "Jily"
        default:
            modelName = model
        }
    }

    // Extract unprompted prompt
    var unPrompt string
    if match := unPromptRe.FindStringSubmatch(prompt); len(match) > 1 {
        unPromptContent := match[1]
        // Remove score prefix if present
        if strings.HasPrefix(unPromptContent, "(score") {
            if parts := strings.SplitN(unPromptContent, ",\n", 2); len(parts) > 1 {
                unPrompt = parts[1]
            } else {
                unPrompt = unPromptContent
            }
        } else {
            unPrompt = unPromptContent
        }
        // Clean up newlines and spaces
        unPrompt = strings.ReplaceAll(unPrompt, "\n", " ")
        unPrompt = strings.Join(strings.Fields(unPrompt), " ")
    }

    // Extract negative prompt
    var negPrompt string
    if match := negPromptRe.FindStringSubmatch(prompt); len(match) > 1 {
        negPromptContent := match[1]
        // Remove score prefix if present
        if strings.HasPrefix(negPromptContent, "score") {
            if parts := strings.SplitN(negPromptContent, ",\n", 2); len(parts) > 1 {
                negPrompt = parts[1]
            } else {
                negPrompt = negPromptContent
            }
        } else {
            negPrompt = negPromptContent
        }
        // Clean up newlines and spaces
        negPrompt = strings.ReplaceAll(negPrompt, "\n", " ")
        negPrompt = strings.Join(strings.Fields(negPrompt), " ")
    }

    // Format output
    output := fmt.Sprintf("#%s %s, %s", seed, modelName, strings.TrimSpace(unPrompt))
    if negPrompt != "" {
        output += " NEGATIVE " + strings.TrimSpace(negPrompt)
    }

    // Extract original full prompt (positive and negative parts) from before parameters
    var fullOrigPrompt string
    if endParamsIdx := strings.Index(prompt, "\nSteps:"); endParamsIdx != -1 {
        fullOrigPrompt = prompt[:endParamsIdx]
    } else {
        // If no Steps, maybe the whole thing is a prompt. This is a guess.
        fullOrigPrompt = prompt
    }

    // Clean up and format original prompt
    fullOrigPrompt = strings.TrimSpace(fullOrigPrompt)
    fullOrigPrompt = strings.ReplaceAll(fullOrigPrompt, "\nNegative prompt: ", " NEGATIVE ")
    fullOrigPrompt = strings.ReplaceAll(fullOrigPrompt, "\n", " ")
    fullOrigPrompt = strings.Join(strings.Fields(fullOrigPrompt), " ") // Normalize spaces

    if fullOrigPrompt != "" {
        output += " ---- " + fullOrigPrompt
    }

    return seed, modelName, strings.TrimSpace(unPrompt), output
}

func main() {
    opts := &Options{}
    flag.BoolVar(&opts.markdown, "m", false, "Output in markdown format")
    flag.BoolVar(&opts.markdown, "markdown", false, "Output in markdown format")
    flag.Parse()

    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        filename := scanner.Text()
        metadata, err := extractMetadata(filename)
        fmt.Println("Metadata:", metadata) // Debug line to see extracted metadata
        seed, model, prompt, expandedPrompt := "", "", "", ""
        errStr := ""
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error processing %s: %v\n", filename, err)
            errStr = "\t" + err.Error()
        } else if metadata == "" {
            fmt.Fprintf(os.Stderr, "No metadata found in %s\n", filename)
            errStr = "\tno metadata"
        } else {
            seed, model, prompt, expandedPrompt = parseMetadata(metadata, filename)
        }
        if opts.markdown {
            fmt.Printf("![#%s %s, %s ---- %s](%s)%s\n", seed, model, prompt, expandedPrompt, filename, errStr)
        } else {
            fmt.Printf("%s\t%s\t%s\t%s\t%s\t%s\n", filename, errStr, seed, model, prompt, expandedPrompt)
        }
    }

    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error reading input: %v\n", err)
        os.Exit(1)
    }
}
