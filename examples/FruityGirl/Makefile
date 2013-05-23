FONT = FruityGirl
PNGS_PREFIX = ./png/

EMOJI_BUILDER = ../../emoji-builder.py
ADD_GLYPHS= ../../add-glyphs.py

%.ttx: %.ttx.tmpl $(ADD_GLYPHS) $(UNI)
	$(ADD_GLYPHS) "$<" "$@" "$(PNGS_PREFIX)"

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(FONT).ttf: $(FONT).tmpl.ttf $(EMOJI_BUILDER) $(PNGS_PREFIX)*.png
	$(EMOJI_BUILDER) -V $< "$@" $(PNGS_PREFIX)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf $(FONT).tmpl.ttx
