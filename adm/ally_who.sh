#!/bin/bash -eu
# ally_who.sh:	
grep -o '^[^	:#<]*:' | grep -v -e '^-' -e '^Select Characters:$' | tr -d : | uniqoc | order 1rn
