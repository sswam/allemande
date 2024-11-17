all: opts_long opts_help

%: %.go
	go build -ldflags="-s -w" -trimpath "$<"
