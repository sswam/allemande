#!/bin/bash -e
printf '%s' "${STY:+${STY#*.} }$USER@$HOSTNAME:$PWD"
