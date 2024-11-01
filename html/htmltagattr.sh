#!/bin/sh
tag=$1 ; shift
htmltag "$tag" | htmlattr "$@"
