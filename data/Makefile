all: tsv2txt

%: %.go
	go build -ldflags="-s -w" -trimpath "$<"
