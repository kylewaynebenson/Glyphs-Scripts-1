# MenuTitle: BlueFuzzer
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Extends all alignment zones (except for the baseline zone that should stay at 0).
"""

import vanilla
from GlyphsApp import Glyphs
from mekkablue import mekkaObject

windowHeight = 110


class BlueFuzzer(mekkaObject):
	prefDict = {
		"fuzzValue": 1,
		"allMasters": True,
	}

	def __init__(self):
		self.w = vanilla.FloatingWindow(
			(300, windowHeight), "BlueFuzzer", minSize=(250, windowHeight), maxSize=(500, windowHeight), autosaveName=self.domain("mainwindow")
		)

		self.w.text_1 = vanilla.TextBox((15, 12 + 2, 120, 18), "Extend zones by", sizeStyle='small')
		self.w.fuzzValue = vanilla.EditText((120, 12, -15, 18), "1", sizeStyle='small')
		self.w.allMasters = vanilla.CheckBox((15, 35, -15, 20), "Apply to all masters", value=True, callback=self.SavePreferences, sizeStyle='small')

		self.w.runButton = vanilla.Button((-80 - 15, -20 - 15, -15, -15), "Fuzz", callback=self.BlueFuzzerMain)
		self.w.setDefaultButton(self.w.runButton)

		self.LoadPreferences()
		self.w.open()

	def BlueFuzzerMain(self, sender):
		try:
			Font = Glyphs.font

			fuzzValue = int(self.w.fuzzValue.get())
			allMasters = bool(self.w.allMasters.get())

			if allMasters:
				masterList = Font.masters
			else:
				masterList = [Font.selectedFontMaster]

			for m in masterList:
				numOfZones = len(m.alignmentZones)
				for i in range(numOfZones):
					thisZone = m.alignmentZones[i]
					factor = 1
					if thisZone.size < 0:  # negative zone
						factor = -1
					if thisZone.position == 0 and factor == -1:  # baseline zone must stay where it is
						thisZone.setSize_(thisZone.size + fuzzValue * factor)
					else:
						thisZone.setPosition_(thisZone.position - fuzzValue * factor)
						thisZone.setSize_(thisZone.size + (fuzzValue * 2) * factor)

			self.SavePreferences()
			self.w.close()
			Font.parent.windowController().showFontInfoWindowWithTabSelected_(1) # master tab index
		except Exception as e:
			raise e


BlueFuzzer()
