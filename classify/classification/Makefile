.PHONY: graph
graph: quality-map-2.tsv
	./fit.py $<
quality-map-2.tsv: quality-map.tsv
	< $< kut 1 2 > $@
