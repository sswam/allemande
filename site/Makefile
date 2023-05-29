all: pricing.html

%.html: %.md Makefile
	if [ "$<" = "pricing.md" ]; then \
		title="Introducing Ally Chat Pricing Plans"; \
	else \
		title="Allemande AI"; \
	fi; \
	pandoc --metadata title="$$title" -c /allychat.css -c /room.css -c /demo-theme.css -c /pricing.css -s -o $@ $<
