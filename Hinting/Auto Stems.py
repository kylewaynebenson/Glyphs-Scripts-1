# MenuTitle: Auto Stems
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Derive one H and one V stem value for all your masters by measuring certain shapes in your font.
"""

import vanilla
from Foundation import NSPoint
from GlyphsApp import Glyphs, GSMetric, GSInfoValue, Message
from mekkablue import mekkaObject, UpdateButton

whichMeasure = (
	"bounds",
	"diameter",
)

whichShape = (
	"first shape",
	"smallest shape",
	"largest shape",
)


class AutoStems(mekkaObject):
	prefDict = {
		# "prefName": defaultValue,
		"hMeasure": 0,
		"hShape": 1,
		"hStemGlyph": "f",
		"vMeasure": 1,
		"vShape": 0,
		"vStemGlyph": "idotaccent",
		"overwriteExisting": 1,
		"allFonts": 0,
	}

	def __init__(self):
		# Window 'self.w':
		windowWidth = 430
		windowHeight = 140
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight),  # default window size
			"Auto Stems",  # window title
			autosaveName=self.domain("mainwindow")  # stores last window position and size
		)

		# UI elements:
		linePos, inset, lineHeight = 12, 15, 22
		self.w.descriptionText = vanilla.TextBox((inset, linePos, -inset, 14), "Measure shapes in the font and derive stem entries", sizeStyle="small", selectable=True)
		linePos += lineHeight

		self.w.vText1 = vanilla.TextBox((inset, linePos + 2, 48, 14), "V Stem", sizeStyle="small", selectable=True)
		self.w.vMeasure = vanilla.PopUpButton((inset + 48, linePos, 82, 17), whichMeasure, sizeStyle="small", callback=self.SavePreferences)
		self.w.vMeasure.getNSPopUpButton().setToolTip_("Bounds: the width of the enclosing rectangle for the selected shape.\n\nDiameter: the distance between the outermost points of the shape when cut horizontally in the center.")
		self.w.vText2 = vanilla.TextBox((inset + 133, linePos + 2, 17, 14), "of", sizeStyle="small", selectable=True)
		self.w.vShape = vanilla.PopUpButton((inset + 150, linePos, 110, 17), whichShape, sizeStyle="small", callback=self.SavePreferences)
		self.w.vShape.getNSPopUpButton().setToolTip_("Which shape in the glyph to measure for the vertical stem.")
		self.w.vText3 = vanilla.TextBox((inset + 263, linePos + 2, 17, 14), "of", sizeStyle="small", selectable=True)
		self.w.vStemGlyph = vanilla.ComboBox((inset + 280, linePos - 1, -inset - 25, 19), [g.name for g in Glyphs.font.glyphs], sizeStyle="small", callback=self.SavePreferences)
		self.w.vStemGlyph.getNSComboBox().setToolTip_("Pick a glyph to measure for the vertical stem.")
		self.w.vReset = UpdateButton((-inset - 18, linePos - 1, -inset, 18), callback=self.update)
		resetToolTip = "Reload the glyph list of the frontmost font."
		self.w.vReset.getNSButton().setToolTip_(resetToolTip)
		linePos += lineHeight

		self.w.hText1 = vanilla.TextBox((inset, linePos + 2, 48, 14), "H Stem", sizeStyle="small", selectable=True)
		self.w.hMeasure = vanilla.PopUpButton((inset + 48, linePos, 82, 17), whichMeasure, sizeStyle="small", callback=self.SavePreferences)
		self.w.hMeasure.getNSPopUpButton().setToolTip_("Bounds: the height of the enclosing rectangle for the selected shape.\n\nDiameter: the distance between the outermost points of the shape when cut vertically in the center.")
		self.w.hText2 = vanilla.TextBox((inset + 133, linePos + 2, 17, 14), "of", sizeStyle="small", selectable=True)
		self.w.hShape = vanilla.PopUpButton((inset + 150, linePos, 110, 17), whichShape, sizeStyle="small", callback=self.SavePreferences)
		self.w.hShape.getNSPopUpButton().setToolTip_("Which shape in the glyph to measure for the horizontal stem.")
		self.w.hText3 = vanilla.TextBox((inset + 263, linePos + 2, 17, 14), "of", sizeStyle="small", selectable=True)
		self.w.hStemGlyph = vanilla.ComboBox((inset + 280, linePos - 1, -inset - 25, 19), [g.name for g in Glyphs.font.glyphs], sizeStyle="small", callback=self.SavePreferences)
		self.w.hStemGlyph.getNSComboBox().setToolTip_("Pick a glyph to measure for the horizontal stem.")
		self.w.hReset = UpdateButton((-inset - 18, linePos - 1, -inset, 18), callback=self.update)
		self.w.hReset.getNSButton().setToolTip_(resetToolTip)
		linePos += lineHeight

		self.w.overwriteExisting = vanilla.CheckBox((inset + 2, linePos - 1, -inset, 20), "⚠️ Overwrite existing stems", value=False, callback=self.SavePreferences, sizeStyle="small")
		self.w.overwriteExisting.getNSButton().setToolTip_("If checked, will delete existing stem values before adding its measurements. Be careful.")
		linePos += lineHeight

		self.w.allFonts = vanilla.CheckBox((inset + 2, linePos - 1, -inset, 20), "Process ⚠️ ALL open fonts", value=False, callback=self.SavePreferences, sizeStyle="small")
		self.w.allFonts.getNSButton().setToolTip_("If checked, will process all fonts currently opened in Glyphs. Otherwise just the frontmost font.")
		linePos += lineHeight

		# Run Button:
		self.w.runButton = vanilla.Button((-120 - inset, -20 - inset, -inset, -inset), "Add Stems", callback=self.AutoStemsMain)
		self.w.setDefaultButton(self.w.runButton)

		# Load Settings:
		self.LoadPreferences()

		# Open window and focus on it:
		self.w.open()
		self.w.makeKey()

	def update(self, sender=None):
		if sender == self.w.hReset:
			self.w.hStemGlyph.setItems([g.name for g in Glyphs.font.glyphs])
		if sender == self.w.vReset:
			self.w.vStemGlyph.setItems([g.name for g in Glyphs.font.glyphs])

	def measureLayer(self, layer, measure, shape, v=True):
		layerCopy = layer.copyDecomposedLayer()
		layerCopy.parent = layer.parent

		if shape == 0:  # first
			s = layerCopy.shapes[0]
		elif shape == 1:  # smallest
			s = sorted(layerCopy.shapes, key=lambda thisShape: thisShape.bounds.size.height * thisShape.bounds.size.width)[0]
		elif shape == 2:  # largest
			s = sorted(layerCopy.shapes, key=lambda thisShape: thisShape.bounds.size.height * thisShape.bounds.size.width * -1)[0]

		# reduce layer to just the shape we want to measure
		# l.setShapes_([s])
		for i in range(len(layerCopy.shapes) - 1, -1, -1):
			if layerCopy.shapes[i] != s:
				del layerCopy.shapes[i]

		bounds = layerCopy.bounds
		if v:
			if measure == 0:  # bounds
				return bounds.size.width
			elif measure == 1:  # diameter
				midY = bounds.origin.y + 0.5 * bounds.size.height
				x1 = bounds.origin.x - 50
				x2 = bounds.origin.x + bounds.size.width + 50
				cuts = layerCopy.intersectionsBetweenPoints(NSPoint(x1, midY), NSPoint(x2, midY), components=True)
				stemMeasurement = float(round(cuts[-2].x - cuts[1].x))
				return abs(stemMeasurement)
		else:  # h
			if measure == 0:  # bounds
				return bounds.size.height
			elif measure == 1:  # diameter
				midX = bounds.origin.x + 0.5 * bounds.size.width
				y1 = bounds.origin.y - 50
				y2 = bounds.origin.y + bounds.size.height + 50
				cuts = layerCopy.intersectionsBetweenPoints(NSPoint(midX, y1), NSPoint(midX, y2), components=True)
				stemMeasurement = float(round(cuts[-2].y - cuts[1].y))
				return abs(stemMeasurement)

	def AutoStemsMain(self, sender=None):
		try:
			# clear macro window log:
			Glyphs.clearLog()

			# update settings to the latest user input:
			self.SavePreferences()

			# read prefs:
			hMeasure = self.pref("hMeasure")
			hShape = self.pref("hShape")
			hStemGlyph = self.pref("hStemGlyph")
			vMeasure = self.pref("vMeasure")
			vShape = self.pref("vShape")
			vStemGlyph = self.pref("vStemGlyph")
			overwriteExisting = self.pref("overwriteExisting")
			allFonts = self.pref("allFonts")

			if allFonts:
				fonts = Glyphs.fonts
			else:
				fonts = (Glyphs.font, )

			if not fonts:
				Message(title="No Font Open", message="The script requires a font. Open a font and run the script again.", OKButton=None)
				return

			for f in fonts:
				filePath = f.filepath
				if filePath:
					reportName = f"{filePath.lastPathComponent()}\n📄 {filePath}"
				else:
					reportName = f"{f.familyName}\n⚠️ The font file has not been saved yet."
				print(f"Auto Stems Report for {reportName}")
				print()

				if overwriteExisting:
					f.setStems_(())

				stem = GSMetric()
				stem.name = "V"
				stem.horizontal = False
				stem.type = 0
				f.stems.append(stem)
				vID = stem.id

				stem = GSMetric()
				stem.name = "H"
				stem.horizontal = True
				stem.type = 0
				f.stems.append(stem)
				hID = stem.id

				vGlyph = f.glyphs[vStemGlyph]  # idotless
				hGlyph = f.glyphs[hStemGlyph]  # f

				for m in f.masters:
					mID = m.id

					# measure idotless
					vStem = self.measureLayer(vGlyph.layers[mID], vMeasure, vShape, v=True)

					# measure f
					hStem = self.measureLayer(hGlyph.layers[mID], hMeasure, hShape, v=False)

					# set stems:
					print(f"V {vStem} H {hStem}: {m.name}")
					vInfo = GSInfoValue.alloc().initWithValue_(vStem)
					hInfo = GSInfoValue.alloc().initWithValue_(hStem)
					m.setStemValue_forId_(vInfo, vID)
					m.setStemValue_forId_(hInfo, hID)

				print()

			if not allFonts and f is not None:
				f.parent.windowController().showFontInfoWindowWithTabSelected_(1) # master tab index

			self.w.close()  # delete if you want window to stay open
			print("\nDone.")

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print(f"Auto Stems Error: {e}")
			import traceback
			print(traceback.format_exc())


AutoStems()
