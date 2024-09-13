#!/usr/bin/make -f

# This downloads info from the geonames site, and produces a list of cities with their timezones.

SRC="https://download.geonames.org/export/dump/"

SHELL=bash

all: country_city_timezone.tsv

clean: tidier
	rm -f country_city_timezone.tsv

tidier: tidy
	rm -f countryInfo.txt cities15000.zip readme.txt

tidy:
	rm -f geoname.txt header.txt cities15000.txt cities15000.rec city_timezone.tsv country.tsv country_code.tsv

cities%.zip:
	curl "$(SRC)/$@" >$@

countryInfo.txt:
	curl "$(SRC)/$@" >$@

%.txt: %.zip
	unzip $<

readme.txt:
	curl "$(SRC)/$@" >$@

geoname.txt: readme.txt
	<$< sed -n "/^The main 'geoname' table has the following fields/,/^\$$/p" | \
		tail -n +3 | head -n -1 | \
		sed 's/ *: /\t/' >$@

header.txt: geoname.txt
	<$< cut -f 1 | tr '\n' '\t' | sed 's/\t$$/\n/' >$@

cities15000.rec: cities15000.txt header.txt
	cat header.txt $< | tsv2recs >$@

city_timezone.tsv: cities15000.rec
	<$< grep -E '^(country code:|asciiname:|timezone:|$$)' | recs2tsv | kut 2 1 3 >$@

country.tsv: countryInfo.txt
	<$< sed -n '/^#ISO\t/,$$ {s/^#//; p}' >$@

country_code.tsv: country.tsv
	<$<  tsvproc -o ISO,Country '' >$@

country_city_timezone.tsv: city_timezone.tsv country_code.tsv
	joine <(< country_code.tsv nohead | order) <(< city_timezone.tsv nohead | order) | \
		addhead code country city timezone | \
		kutout 1 >"$@"
