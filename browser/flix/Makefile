PROJECT := $(notdir $(CURDIR))

../$(PROJECT).xpi ../$(PROJECT).zip: . $(wildcard *)
	zip -r ../$(PROJECT).xpi * -x Makefile
	ln -f ../$(PROJECT).xpi ../$(PROJECT).zip
