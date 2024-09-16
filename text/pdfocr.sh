#!/usr/bin/env bash

set -euo pipefail

# PDF to OCR Text Converter

# Usage:
#   $0 <input.pdf> [output_prefix]
# Example:
#   $0 scanned_document.pdf my_document

# Function to display usage information
usage() {
    echo "Usage: $0 <input.pdf> [output_prefix]" >&2
    echo "Example: $0 scanned_document.pdf my_document" >&2
    exit 1
}

# Check for correct number of arguments
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    usage
fi

input_pdf="$1"
output_prefix="${2:-${input_pdf%.*}}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
for cmd in pdftoppm ocr; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is not installed or not in PATH" >&2
        exit 1
    fi
done

# Split PDF into PNG images
echo "Splitting PDF into images..."
pdftoppm -png "$input_pdf" "${output_prefix}_page"

# Perform OCR on each image
echo "Performing OCR on images..."
for image in "${output_prefix}_page"*.png; do
    page_number=${image##*_page-}
    page_number=${page_number%.png}
    page_number=${page_number##0}   # avoid octal issue with printf
    page_number=$(printf "%03d" "$page_number")
    out="${output_prefix}_${page_number}.txt"
    if [ ! -e "$out" ]; then
        ocr "$image" "$out"
    fi
done

# Concatenate all text files
echo "Concatenating OCR results..."
catpg "${output_prefix}"_???.txt > "${output_prefix}.txt"

# Clean up temporary files
echo "Cleaning up..."
rm "${output_prefix}_page"*.png "${output_prefix}"_*.txt

echo "OCR process complete. Output saved to ${output_prefix}.txt"
