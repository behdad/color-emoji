FONT = Funkster
PNGS = ./

EMOJI_BUILDER = ../../emoji-builder.py

%.ttf: %.ttx
	ttx $<

$(FONT).ttf: $(FONT).tmpl.ttf $(PNGS)*.png
	$(EMOJI_BUILDER) $< $@ $(PNGS)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf
