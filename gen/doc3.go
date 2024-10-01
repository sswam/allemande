package main

import (
	"fmt"
	"os"
	"os/exec"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run doc2.go [file1] [file2] ...")
		os.Exit(1)
	}

	// Prepare arguments for cat-named command
	catArgs := append([]string{"cat-named"}, os.Args[1:]...)

	// Create a pipe
	catCmd := exec.Command(catArgs[0], catArgs[1:]...)
	processCmd := exec.Command("process", "Please write some basic documentation for this code.")

	// Connect the pipe
	processCmd.Stdin, _ = catCmd.StdoutPipe()
	processCmd.Stdout = os.Stdout
	processCmd.Stderr = os.Stderr

	// Start the commands
	_ = processCmd.Start()
	err := catCmd.Run()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error running cat-named: %v\n", err)
		os.Exit(1)
	}

	// Wait for process to finish
	err = processCmd.Wait()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error running process: %v\n", err)
		os.Exit(1)
	}
}
