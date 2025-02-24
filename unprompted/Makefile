all: unprompted/lib_unprompted/config_user.json unprompted/shortcodes/allemande

unprompted/lib_unprompted/config_user.json: config_user.json
	ln -s $$PWD/$< $@
unprompted/shortcodes/allemande: shortcodes
	ln -s $$PWD/$< $@
