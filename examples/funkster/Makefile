FONT = Funkster
PNGS = ./

EMOJI_BUILDER = ../../emoji-builder.py

%.ttf: %.sfd
	python -c 'import fontforge; fontforge.open ("$<").generate ("$@")'

$(FONT).ttf: $(FONT).tmpl.ttf $(PNGS)*.png
	$(EMOJI_BUILDER) $< $@ $(PNGS)

clean:
	rm -f $(FONT).ttf $(FONT).tmpl.ttf
