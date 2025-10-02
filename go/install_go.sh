#!/usr/bin/env bash

# [go_arch]
# Installs or updates Go programming language from official source

install-go() {
  local go_arch=${1:-}
  local go_path="/usr/local/go/bin"
  local machine
  local os
  local go_url
  local latest_version
  local current_version

  # guess architecture if not given
  if [ -z "$go_arch" ]; then
    machine=$(dpkg --print-architecture 2>/dev/null || uname -m)
    case "$machine" in
    amd64|x86_64) go_arch="amd64" ;;
    ?86|i?86) go_arch="386" ;;
    *) go_arch="$machine" ; echo >&2 "Warning: Using architecture '$go_arch'" ;;
    esac
  fi

  # operating system
  os=$(uname | tr '[:upper:]' '[:lower:]')

  # Download and install Go
  go_url=$(curl https://go.dev/dl/ | sed -n "/href=\"\/dl\/go.*$os-$go_arch/ { s/.*href=\"//; s/\".*//; p; q; }")

  # TODO Scraping HTML with sed is brittle; Go provides a JSON endpoint
  # (https://go.dev/dl/?mode=json) that’s more reliable.

  # Check if URL was found
  if [ -z "$go_url" ]; then
    echo >&2 "Could not find Go download URL for $os-$go_arch"
    return 1
  fi

  latest_version=$(echo "$go_url" | sed -n 's/.*go\([0-9.]*\).*/\1/p')
  current_version=$(go version 2>/dev/null | sed 's/.*go\([0-9.]*\).*/\1/')

  if [ -z "$latest_version" ]; then
    echo >&2 "Could not determine latest Go version"
    return 1
  fi

  # Check if Go is already installed and up-to-date
  if [ "$current_version" = "$latest_version" ]; then
    echo >&2 "Go is already installed and up-to-date (version $current_version)"
    return 0
  fi

  if [ -n "$current_version" ]; then
    echo >&2 "Updating Go from version $current_version to $latest_version"
  else
    echo "Installing Go version $latest_version"
  fi

  rm -f go*."$os"-"$go_arch".tar.gz
  wget "https://go.dev$go_url"
  sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go*."$os"-"$go_arch".tar.gz
  rm go*."$os"-"$go_arch".tar.gz

  # Check if Go path already exists in PATH
  if command -v go >/dev/null; then
    return 0
  fi

  # Add Go to PATH in bashrc
  if [ ! -f ~/.bashrc ]; then
    echo >&2 "Warning: ~/.bashrc not found"
    return 0
  fi

  printf "\n%s\n" "export PATH=\$PATH:$go_path" >> ~/.bashrc

  printf >&2 "Go installed. Please restart your terminal to update your PATH, or:\n\n. ~/.bashrc\n"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  install-go "$@"
fi

# version: 0.1.2
