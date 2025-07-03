#!/usr/bin/env bash
for path; do
	realpath --canonicalize-missing "$path"
done
