FONT = PhantomOpenEmoji

SRC = ./PhantomOpenEmoji
PNG = ./png
UNI = ./uni

PNGS_PREFIX = $(UNI)/uni

EMOJI_BUILDER = ../../emoji_builder.py
ADD_GLYPHS= ../../add_glyphs.py

%.ttx: %.ttx.tmpl $(ADD_GLYPHS) $(UNI)
	$(ADD_GLYPHS) "$<" "$@" "$(PNGS_PREFIX)"

%.ttf: %.ttx
	@rm -f "$@"
	ttx "$<"

$(FONT).ttf: $(FONT).tmpl.ttf $(EMOJI_BUILDER)
	$(EMOJI_BUILDER) -V $< "$@" "$(PNGS_PREFIX)"

clean:
	rm -rf $(FONT).ttf $(FONT).tmpl.ttf $(FONT).tmpl.ttx $(PNG) $(UNI)


$(SRC):
	@if ! test -d "$(SRC)"; then \
		echo "Please checkout $(SRC)"; >&2 \
		echo "You can do that by running:"; >&2 \
		echo "  git clone https://github.com/Genshin/PhantomOpenEmoji.git"; >&2 \
		exit 1; \
	fi

$(PNG): $(SRC)
	@echo "Generating PNGs..."
	@mkdir -p "$(PNG)"
	@for svg in "$(SRC)"/emoji/*.svg; do \
		base="`basename "$$svg"`"; \
		emoji="$${base//.svg}"; \
		echo "Generating $(PNG)/$$emoji.png"; \
		rsvg-convert -w 128 -h 128 -f png "$$svg" -o "$(PNG)/$$emoji.png"; \
	done

$(UNI): $(SRC) $(PNG)
	@echo "Generating symlinks..."
	@mkdir -p "$(UNI)"
	@cat "$(SRC)"/poe.json | \
	awk -F '"' ' \
	/^{/		{name="";unicode="";next;} \
	/"name"/	{name=$$4;next;} \
	/"unicode"/	{unicode=$$4;next;} \
	/^}/		{if(name && unicode)print "uni"unicode"	"name; next;} \
	{} \
	' | while read unicode emoji; do \
		if test -f "$(PNG)/$$emoji.png"; then \
			echo "Generating $(UNI)/$$unicode.png"; \
			ln -f -s "../$(PNG)/$$emoji.png" "$(UNI)/$$unicode.png"; \
		else \
			echo "Skipping $$unicode"; \
		fi \
	done
