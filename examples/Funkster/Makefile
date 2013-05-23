FONT = Funkster
PNGS = ./

EMOJI_BUILDER = ../../emoji-builder.py

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(FONT).ttf: $(FONT).tmpl.ttf $(PNGS)*.png $(EMOJI_BUILDER)
	$(EMOJI_BUILDER) $< "$@" $(PNGS)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf
