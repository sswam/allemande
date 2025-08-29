// Async message gatherer with debouncing

package main

import (
    "bufio"
    "flag"
    "fmt"
    "io"
    "os"
    "strings"
    "time"
)

// Options holds command-line configuration
type Options struct {
    wait float64
}

// Gatherer collects messages and forwards them after a timeout
type Gatherer struct {
    inputChan  chan string
    outputChan chan string
    wait      time.Duration
    builder   strings.Builder
}

// NewGatherer creates a new message gatherer
func NewGatherer(wait time.Duration) *Gatherer {
    return &Gatherer{
        inputChan:  make(chan string, 100),
        outputChan: make(chan string, 100),
        wait:      wait,
    }
}

// Run starts the message gathering process
func (g *Gatherer) Run() {
    timer := time.NewTimer(g.wait)
    defer timer.Stop()

    for {
        select {
        case msg, ok := <-g.inputChan:
            if !ok { // Channel closed
                if g.builder.Len() > 0 {
                    g.outputChan <- g.builder.String()
                }
                close(g.outputChan)
                return
            }

            if !timer.Stop() {
                select {
                case <-timer.C:
                default:
                }
            }
            g.builder.WriteString(msg)
            timer.Reset(g.wait)

        case <-timer.C:
            if g.builder.Len() > 0 {
                g.outputChan <- g.builder.String()
                g.builder.Reset()
            }
        }
    }
}

// ProcessInput reads from stdin and sends to gatherer
func processInput(g *Gatherer) {
    reader := bufio.NewReader(os.Stdin)
    for {
        line, err := reader.ReadString('\n')
        if err != nil {
            if err != io.EOF {
                fmt.Fprintf(os.Stderr, "Error reading input: %v\n", err)
            }
            close(g.inputChan)
            return
        }
        g.inputChan <- line
    }
}

// ProcessOutput handles gathered messages
func processOutput(g *Gatherer) {
    for msg := range g.outputChan {
        fmt.Print(msg)
    }
}

func main() {
    opts := Options{}
    flag.Float64Var(&opts.wait, "w", 0.2, "Wait before forwarding messages (seconds)")
    flag.Parse()

    gatherer := NewGatherer(time.Duration(opts.wait * float64(time.Second)))

    // Start the gatherer
    go gatherer.Run()

    // Start input processing
    go processInput(gatherer)

    // Process output in main thread
    processOutput(gatherer)
}
