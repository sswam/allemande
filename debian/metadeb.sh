#!/usr/bin/env bash

# [package...]
# Create metapackages depending on specified packages

metadeb() {
	local maintainer= m=  # package maintainer
	local version= v=0.1  # package version
	local name= n=  # override package name (only with a single package)

	eval "$(ally)"

	# Check --name option is used only with a single package
	if [ -n "$name" ] && [ $# != 1 ]; then
		die "option --name can be used only with a single package"
	fi

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
	for pkgfile in "$@"; do
		printf >&2 "Processing %s...\n" "$pkgfile"

		# check pkg file exists	
		if [ ! -f "$pkgfile" ]; then
			die "package file not found: $pkgfile"
		fi

		# Get package name either from --name, or from the file without the extension
		if [ -n "$name" ]; then
			pkg="$name"
		else
			pkg=${pkgfile%.*}
		fi

		# deb file name
		deb_file="${pkg}_${version}_all.deb"

		# check newer?
		if ! [ "$pkgfile" -nt "$deb_file" ]; then
			echo >&2 "Package file is older than the deb file, skipping."
			continue
		fi

		# Clean old packages
		rm -f "${pkg}_"*.deb ".${pkg}_"*.deb

		# Create package directory
		pkg_dir="./.metadeb_$pkg"
		mkdir -p "$pkg_dir"

		# Create dependency list
		< "$pkgfile" sed 's/#.*$//' | tr -s ' \n' ',' | sed 's/,$//' > "$pkg_dir/deps.list"

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

		# Collect deb files
		debs+=(./"$deb_file")
	done

	# Install packages, if any
	if [ ${#debs[@]} -gt 0 ]; then
		sudo apt-get -y reinstall "${debs[@]}"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	metadeb "$@"
fi
