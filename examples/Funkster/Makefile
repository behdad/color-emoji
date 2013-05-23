FONT = Funkster
PNGS_PREFIX = ./png/

EMOJI_BUILDER = ../../emoji-builder.py

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(FONT).ttf: $(FONT).tmpl.ttf $(EMOJI_BUILDER) $(PNGS_PREFIX)*.png
	$(EMOJI_BUILDER) -V $< "$@" $(PNGS_PREFIX)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf
