#!/usr/bin/env bash

# [package...]
# Create metapackages depending on specified packages

metadeb() {
	local maintainer= m=  # package maintainer
	local version= v=0.1  # package version

	eval "$(ally)"

	# Get maintainer info
	if [ -z "$maintainer" ]; then
		maintainer="$USER_NAME <$USER_EMAIL>"
		if [ -z "$maintainer" ]; then
			maintainer="$(git config --get user.name) <$(git config --get user.email)>"
		fi
		if [ -z "$maintainer" ] || [[ "$maintainer" = " <>" ]]; then
			read -r -p "Enter maintainer name: " name
			read -r -p "Enter maintainer email: " email
			maintainer="$name <$email>"
		fi
	fi

	debs=()

	# Process each package
	for pkg in "$@"; do
		printf "Processing %s...\n" "$pkg"

		# check pkg file exists	
		if [ ! -f "$pkg" ]; then
			die "package file not found: $pkg"
		fi

		# Clean old packages
		rm -f "${pkg}_"*.deb

		# Create package directory
		pkg_dir="./.metadeb_$pkg"
		mkdir -p "$pkg_dir"

		# Create dependency list
		sed 's/#.*$//' "$pkg" | tr -s ' \n' ',' | sed 's/,$//' > "$pkg_dir/deps.list"

		# Generate control file
		cat << EOT > "$pkg_dir/control"
Depends: $(cat "$pkg_dir/deps.list")
Section: misc
Priority: optional
Standards-Version: 3.6.2

Package: $pkg
Version: $version
Maintainer: $maintainer
Architecture: all
Description: depends on other packages
EOT

		# Build package
		equivs-build "$pkg_dir/control"

		deb_file="${pkg}_${version}_all.deb"

		# Check that deb file was created
		if [ ! -f "$deb_file" ]; then
			die "package build failed"
		fi

		# Hide the deb file
		mv "$deb_file" ".$deb_file"
		ln -s ".$deb_file" "$deb_file"

		# Remove unneeded buildinfo and changes files
		arch=$(dpkg --print-architecture)
		rm -f "${pkg}_${version}_${arch}.buildinfo" "${pkg}_${version}_${arch}.changes"

		# Collect package files
		debs+=(./"$deb_file")
	done

	# Install packages
	sudo apt-get -y reinstall "${debs[@]}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	metadeb "$@"
fi
