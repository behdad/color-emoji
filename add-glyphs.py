#!/usr/bin/python

import glob
from fontTools import ttx

img_prefix = "uni/uni"
out_file = "PhantomOpenEmoji.tmpl.ttx"
in_file = out_file + ".tmpl"

font = ttx.TTFont()
font.importXML (in_file)

img_files = {}
glb = "%s*.png" % img_prefix
print "Looking for images matching '%s'." % glb
for img_file in glob.glob (glb):
	u = int (img_file[len (img_prefix):-4], 16)
	img_files[u] = img_file
if not img_files:
	raise Exception ("No image files found in '%s'." % glb)

g = font['GlyphOrder'].glyphOrder
c = font['cmap'].tables[0].cmap
h = font['hmtx'].metrics
metrics = h[g[0]]
for u in img_files.keys ():
	print "Adding glyph for U+%04X" % u
	n = "uni%04x" % u
	g.append (n)
	c[u] = n
	h[n] = metrics

font.saveXML (out_file)
