#!/usr/bin/python
#
# Copyright 2013 Google, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Google Author(s): Behdad Esfahbod, Stuart Gill
#

import sys, glob, re, os, struct, io, cairo
from fontTools import ttx, ttLib

drop_glyf = False
if "-d" in sys.argv:
	drop_glyf = True
	sys.argv.remove ("-d")

uncompressed = False
if "-u" in sys.argv:
	uncompressed = True
	sys.argv.remove ("-u")

if len (sys.argv) != 4:
	print >>sys.stderr, """
Usage: emjoi-builder.py [-d] [-u] img-prefix font.ttf out-font.ttf

This will search for files that have img-prefix followed by a hex number,
and end in ".png".  For example, if img-prefix is "icons/", then files
with names like "icons/1f4A9.png" will be loaded.  All images must have
the same size (preferably square).

The script then embeds color bitmaps in the font, for characters that the
font already supports, and writes the new font out.

If the -u parameter is given, uncompressed images are stored (imageFormat=1).
Otherwise, PNG images are stored (imageFormat=17).

If the -d parameter is given, the 'glyf', 'CFF ',  and related tables are
dropped from the font.
"""
	sys.exit (1)

img_prefix = sys.argv[1]
font_file = sys.argv[2]
out_file = sys.argv[3]
del sys.argv

def encode_smallGlyphMetrics (font_metrics, strike_metrics, width, height, stream):
	x_bearing = 0
	# center vertically
	line_height = (font_metrics.ascent + font_metrics.descent) * strike_metrics.y_ppem / float (font_metrics.upem)
	line_ascent = font_metrics.ascent * strike_metrics.y_ppem / float (font_metrics.upem)
	y_bearing = int (round (line_ascent - .5 * (line_height - height)))
	advance = width
	# smallGlyphMetrics
	# Type	Name
	# BYTE	height
	# BYTE	width
	# CHAR	BearingX
	# CHAR	BearingY
	# BYTE	Advance
	stream.extend (struct.pack ("BBbbB", height, width, x_bearing, y_bearing, advance))

# http://www.microsoft.com/typography/otspec/ebdt.htm
def encode_ebdt_format1 (img_file, font_metrics, strike_metrics, stream):

	img = cairo.ImageSurface.create_from_png (img_file)

	if img.get_format () != cairo.FORMAT_ARGB32:
		raise Exception ("Expected FORMAT_ARGB32, but image has format %d" % img.get_format ())

	width = img.get_width ()
	height = img.get_height ()
	stride = img.get_stride ()
	data = img.get_data ()

	encode_smallGlyphMetrics (font_metrics, strike_metrics, width, height, stream)

	if sys.byteorder == "little" and stride == width * 4:
		# Sweet.  Data is in desired format, ship it!
		stream.extend (data)
		return

	# Unexpected stride or endianness, do it the slow way
	offset = 0
	for y in range (height):
		for x in range (width):
			pixel = data[offset + 4 * x: offset + 4 * (x + 1)]
			# Convert to little endian
			pixel = struct.pack ("<I", struct.unpack ("@I", pixel)[0])
			stream.extend (pixel)
		offset += stride

# XXX http://www.microsoft.com/typography/otspec/ebdt.htm
def encode_ebdt_format17 (img_file, font_metrics, strike_metrics, stream):

	img = cairo.ImageSurface.create_from_png (img_file)

	width = img.get_width ()
	height = img.get_height ()

	png = bytearray (open (img_file, 'rb').read ())

	encode_smallGlyphMetrics (font_metrics, strike_metrics, width, height, stream)

	# ULONG data length
	stream.extend (struct.pack(">L", len (png)))
	stream.extend (png)

encode_ebdt_image_funcs = {
	1  : encode_ebdt_format1,
	17 : encode_ebdt_format17,
}


img_files = {}
for img_file in glob.glob ("%s*.png" % img_prefix):
	uchar = int (img_file[len (img_prefix):-4], 16)
	img_files[uchar] = img_file
if not img_files:
	raise Exception ("No image files found: '%s*.png'" % img_prefix)
print "Found images for %d characters in '%s*.png'." % (len (img_files), img_prefix)

font = ttx.TTFont (font_file)
print "Loaded font '%s'." % font_file


glyph_metrics = font['hmtx'].metrics
unicode_cmap = font['cmap'].getcmap (3, 10)

glyph_imgs = {}
advance = width = height = 0
for uchar, img_file in img_files.items ():
	if uchar in unicode_cmap.cmap:
		glyph_name = unicode_cmap.cmap[uchar]
		glyph_id = font.getGlyphID (glyph_name)
		glyph_imgs[glyph_id] = img_file

		advance += glyph_metrics[glyph_name][0]
		img = cairo.ImageSurface.create_from_png (img_file)
		width += img.get_width ()
		height += img.get_height ()

glyphs = sorted (glyph_imgs.keys ())
if not glyphs:
	raise Exception ("No common characteres found between font and image dir.")
print "Embedding images for %d glyphs." % len (glyphs)

advance, width, height = (int (round (float (x) / len (glyphs))) for x in (advance, width, height))

class FontMetrics:
	def __init__ (self, upem, ascent, descent):
		self.upem = upem
		self.ascent = ascent
		self.descent = descent

font_metrics = FontMetrics (font['head'].unitsPerEm,
			    font['hhea'].ascent,
			    -font['hhea'].descent)

class StrikeMetrics:
	def __init__ (self, font_metrics, advance, bitmap_width, bitmap_height):
		self.width = bitmap_width # in pixels
		self.height = bitmap_height # in pixels
		self.advance = advance # in font units
		self.x_ppem = self.y_ppem = int (round (float (bitmap_width) * font_metrics.upem / advance))

strike_metrics = StrikeMetrics (font_metrics, advance, width, height)


ebdt = bytearray (struct.pack (">L", 0x00020000))
bitmap_offsets = []
image_format = 1 if uncompressed else 17

encode_ebdt_image_func = encode_ebdt_image_funcs[image_format]
for glyph in glyphs:
	img_file = glyph_imgs[glyph]
	#print "Embedding %s for glyph #%d" % (img_file, glyph)
	sys.stdout.write ('.')
	offset = len (ebdt)
	encode_ebdt_image_func (img_file, font_metrics, strike_metrics, ebdt)
	bitmap_offsets.append ((glyph, offset))
bitmap_offsets.append ((None, len (ebdt)))
print
print "EBDT table synthesized: %d bytes." % len (ebdt)


def encode_indexSubTable1 (offsets, image_format, stream):
	stream.extend (struct.pack(">H", 1)) # USHORT indexFormat
	stream.extend (struct.pack(">H", image_format)) # USHORT imageFormat
	imageDataOffset = offsets[0][1]
	stream.extend (struct.pack(">L", imageDataOffset)) # ULONG imageDataOffset
	for gid, offset in offsets[:-1]:
		stream.extend (struct.pack(">L", offset - imageDataOffset)) # ULONG offsetArray
	stream.extend (struct.pack(">L", offsets[-1][1]))

def encode_sbitLineMetrics_hori (stream, font_metrics, strike_metrics):
	# sbitLineMetrics
	# Type	Name
	# CHAR	ascender
	# CHAR	descender
	# BYTE	widthMax
	# CHAR	caretSlopeNumerator
	# CHAR	caretSlopeDenominator
	# CHAR	caretOffset
	# CHAR	minOriginSB
	# CHAR	minAdvanceSB
	# CHAR	maxBeforeBL
	# CHAR	minAfterBL
	# CHAR	pad1
	# CHAR	pad2
	line_height = int (round ((font_metrics.ascent + font_metrics.descent) * strike_metrics.y_ppem / font_metrics.upem))
	ascent = int (round (font_metrics.ascent * strike_metrics.y_ppem / font_metrics.upem))
	descent = - (line_height - ascent)
	stream.extend (struct.pack ("bbBbbbbbbbbb", ascent, descent, strike_metrics.width, 0, 0, 0, 0, 0, 0, 0, 0, 0))

def encode_sbitLineMetrics_vert (stream, font_metrics, strike_metrics):
	encode_sbitLineMetrics_hori (stream, font_metrics, strike_metrics) # XXX


# http://www.microsoft.com/typography/otspec/eblc.htm
def encode_bitmapSizeTable (offsets, image_format, font_metrics, strike_metrics, stream):
	# count number of ranges
	count = 1
	start = offsets[0][0]
	last = start
	for gid, offset in offsets[1:-1]:
		if last + 1 != gid:
			count += 1
		last = gid
	headersLen = count * 8

	headers = bytearray ()
	subtables = bytearray ()
	start = offsets[0][0]
	start_id = 0
	last = start
	last_id = 0
	for gid, offset in offsets[1:-1]:
		if last + 1 != gid:
			headers.extend (struct.pack(">HHL", start, last, headersLen + len (subtables)))
			encode_indexSubTable1 (offsets[start_id:last_id+2], image_format, subtables)

			start = gid
			start_id = last_id + 1
		last = gid
		last_id += 1
	headers.extend (struct.pack(">HHL", start, last, headersLen + len (subtables)))
	encode_indexSubTable1 (offsets[start_id:last_id+2], image_format, subtables)

	indexTablesSize = len (headers) + len (subtables)
	numberOfIndexSubTables = count
	bitmapSizeTableSize = 48

	# bitmapSizeTable
	# Type	Name	Description
	# ULONG	indexSubTableArrayOffset	offset to index subtable from beginning of EBLC.
	stream.extend (struct.pack(">L", len (stream) + bitmapSizeTableSize))
	# ULONG	indexTablesSize	number of bytes in corresponding index subtables and array
	stream.extend (struct.pack(">L", indexTablesSize))
	# ULONG	numberOfIndexSubTables	an index subtable for each range or format change
	stream.extend (struct.pack(">L", numberOfIndexSubTables))
	# ULONG	colorRef	not used; set to 0.
	stream.extend (struct.pack(">L", 0))
	# sbitLineMetrics	hori	line metrics for text rendered horizontally
	encode_sbitLineMetrics_hori (stream, font_metrics, strike_metrics)
	encode_sbitLineMetrics_vert (stream, font_metrics, strike_metrics)
	# sbitLineMetrics	vert	line metrics for text rendered vertically
	# USHORT	startGlyphIndex	lowest glyph index for this size
	stream.extend (struct.pack(">H", offsets[0][0]))
	# USHORT	endGlyphIndex	highest glyph index for this size
	stream.extend (struct.pack(">H", offsets[-2][0]))
	# BYTE	ppemX	horizontal pixels per Em
	stream.extend (struct.pack(">B", strike_metrics.x_ppem))
	# BYTE	ppemY	vertical pixels per Em
	stream.extend (struct.pack(">B", strike_metrics.y_ppem))
	# BYTE	bitDepth	the Microsoft rasterizer v.1.7 or greater supports the following bitDepth values, as described below: 1, 2, 4, and 8.
	stream.extend (struct.pack(">B", 32))
	# CHAR	flags	vertical or horizontal (see bitmapFlags)
	stream.extend (struct.pack(">b", 0x01))

	stream.extend (headers)
	stream.extend (subtables)

eblc = bytearray (struct.pack (">L", 0x00020000))
eblc.extend (struct.pack(">L", 1)) # ULONG numSizes
encode_bitmapSizeTable (bitmap_offsets, image_format, font_metrics, strike_metrics, eblc)
print "EBLC table synthesized: %d bytes." % len (eblc)

def add_table (font, tag, data):
	tab = ttLib.tables.DefaultTable.DefaultTable (tag)
	tab.data = str(data)
	font[tag] = tab

add_table (font, 'CBDT', ebdt)
add_table (font, 'CBLC', eblc)

if drop_glyf:
	for tag in ['cvt ', 'fpgm', 'glyf', 'loca', 'prep', 'CFF ', 'VORG']:
		try:
			del font[tag]
		except KeyError:
			pass
	print "Dropped 'glyf', 'CFF ', and related tables."

font.save (out_file)
print "Output font '%s' generated." % out_file
