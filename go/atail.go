package main

import (
	"bufio"
	"flag"
	"fmt"
	"github.com/fsnotify/fsnotify"
	"io"
	"os"
	"path/filepath"
)

type AsyncTail struct {
	filePath       string
	waitForCreate  bool
	n              int
	allLines       bool
	follow         bool
}

func NewAsyncTail(filePath string, waitForCreate bool, n int, allLines, follow bool) *AsyncTail {
	return &AsyncTail{
		filePath:       filePath,
		waitForCreate:  waitForCreate,
		n:              n,
		allLines:       allLines,
		follow:         follow,
	}
}

func isSeekable(file *os.File) bool {
	_, err := file.Seek(0, io.SeekCurrent)
	return err == nil
}

func (t *AsyncTail) Tail() error {
	if t.waitForCreate && !fileExists(t.filePath) {
		err := t.waitForFileCreation()
		if err != nil {
			return err
		}
	}

	file, err := os.Open(t.filePath)
	if err != nil {
		return err
	}
	defer file.Close()

	if t.allLines || t.n > 0 {
		lines, err := readLastNLines(file, t.n)
		if err != nil {
			return err
		}
		for _, line := range lines {
			fmt.Print(line)
		}
	} else if isSeekable(file) {
		_, err = file.Seek(0, io.SeekEnd)
		if err != nil {
			return err
		}
	}

	if t.follow {
		return t.followChanges(file)
	}

	return nil
}

func (t *AsyncTail) followChanges(file *os.File) error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer watcher.Close()

	done := make(chan bool)
	go func() {
		for {
			select {
			case event := <-watcher.Events:
				if event.Op&fsnotify.Write == fsnotify.Write {
					reader := bufio.NewReader(file)
					for {
						line, err := reader.ReadString('\n')
						if err != nil {
							break
						}
						fmt.Print(line)
					}
				}
			case err := <-watcher.Errors:
				fmt.Println("error:", err)
			}
		}
	}()

	err = watcher.Add(t.filePath)
	if err != nil {
		return err
	}
	<-done
	return nil
}

func (t *AsyncTail) waitForFileCreation() error {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return err
	}
	defer watcher.Close()

	dir := filepath.Dir(t.filePath)
	err = watcher.Add(dir)
	if err != nil {
		return err
	}

	done := make(chan bool)
	go func() {
		for {
			select {
			case event := <-watcher.Events:
				if event.Op&fsnotify.Create == fsnotify.Create || event.Op&fsnotify.Rename == fsnotify.Rename {
					if event.Name == t.filePath {
						done <- true
					}
				}
			case err := <-watcher.Errors:
				fmt.Println("error:", err)
			}
		}
	}()

	<-done
	return nil
}

func fileExists(filePath string) bool {
	info, err := os.Stat(filePath)
	if os.IsNotExist(err) {
		return false
	}
	return !info.IsDir()
}

func readLastNLines(file *os.File, n int) ([]string, error) {
	reader := bufio.NewReader(file)
	var lines []string
	for {
		line, err := reader.ReadString('\n')
		if err != nil && err != io.EOF {
			return nil, err
		}
		if err == io.EOF {
			break
		}
		lines = append(lines, line)
		if n > 0 && len(lines) > n {
			lines = lines[1:]
		}
	}
	return lines, nil
}

func main() {
	filePath := flag.String("filename", "/dev/stdin", "the file to tail")
	waitForCreate := flag.Bool("w", false, "wait for the file to be created")
	n := flag.Int("n", 0, "output the last N lines")
	allLines := flag.Bool("a", false, "output all lines")
	follow := flag.Bool("f", false, "follow the file")
	flag.Parse()

	tailer := NewAsyncTail(*filePath, *waitForCreate, *n, *allLines, *follow)
	err := tailer.Tail()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
