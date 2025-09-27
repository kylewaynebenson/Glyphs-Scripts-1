# MenuTitle: Parameter Reporter
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Searches in Custom Parameter names of all registered parameters in the current app version.
"""

import vanilla
from AppKit import NSPasteboard, NSStringPboardType
from GlyphsApp import Glyphs, GSLayer, GSGlyphsInfo
from mekkablue import setClipboard, mekkaObject


class ParameterReporter(mekkaObject):
	prefDict = {
		"filter": ""
	}
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3:
		fontParameters = GSGlyphsInfo.customFontParameters()
		masterParameters = GSGlyphsInfo.customMasterParameters()
		instanceParameters = GSGlyphsInfo.customInstanceParameters()
	else:
		# GLYPHS 2
		appInfo = GSGlyphsInfo.sharedManager()
		fontParameters = appInfo.customFontParameters()
		masterParameters = appInfo.customMasterParameters()
		instanceParameters = appInfo.customInstanceParameters()

	def __init__(self):

		# Window 'self.w':
		windowWidth = 250
		windowHeight = 200
		windowWidthResize = 400  # user can resize width by this value
		windowHeightResize = 650  # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight),  # default window size
			"Parameter Reporter",  # window title
			minSize=(windowWidth, windowHeight),  # minimum size (for resizing)
			maxSize=(windowWidth + windowWidthResize, windowHeight + windowHeightResize),  # maximum size (for resizing)
			autosaveName=self.domain("mainwindow")  # stores last window position and size
		)

		# UI ELEMENTS:

		# Filter:
		self.w.filter = vanilla.EditText((1, 1, -1, 22), "", callback=self.ParameterReporterMain)
		self.w.filter.getNSTextField().setToolTip_("Type one or more search terms here. Use * as wildcard.")

		# Listing of Parameters:
		self.w.ParameterList = vanilla.List((0, 24, -0, -0), dir(GSLayer), autohidesScrollers=False, drawVerticalLines=True, doubleClickCallback=self.copySelection, rowHeight=19)
		self.w.ParameterList.getNSTableView().tableColumns()[0].setWidth_(501)
		self.w.ParameterList.getNSTableView().setToolTip_("Double click an entry to copy the respective parameter into the clipboard.")

		# Load Settings:
		self.LoadPreferences()

		# Open window and focus on it:
		self.w.open()
		self.w.makeKey()
		self.ParameterReporterMain(None)

	def realmStringForParameter(self, parameterName):
		realms = []
		if parameterName in self.fontParameters:
			realms.append("F")
		if parameterName in self.masterParameters:
			realms.append("M")
		if parameterName in self.instanceParameters:
			realms.append("I")
		return "(%s)" % ",".join(realms)

	def copySelection(self, sender):
		try:
			indexes = self.w.ParameterList.getSelection()

			Parameters = []
			for index in indexes:
				ParameterName = self.w.ParameterList[index]
				parenthesisOffset = ParameterName.rfind("(")
				ParameterName = ParameterName[:parenthesisOffset].strip()
				clipboardPiece = '{"%s" = "";}' % ParameterName
				Parameters.append(clipboardPiece)

			# puts Parameters in clipboard:
			clipboardString = "(%s)" % ",".join(Parameters)

			if not setClipboard(clipboardString):
				print("Warning: could not set clipboard.")

			# Floating notification:
			Glyphs.showNotification(
				u"%i parameter%s copied" % (
					len(indexes),
					"" if len(indexes) == 1 else "s",
				),
				u"You can paste in Font Info.",
			)

		except Exception as e:
			Glyphs.showMacroWindow()
			print("Parameter Reporter Error:\nCould not copy to clipboard.\n%s" % e)

	def ParameterReporterMain(self, sender):
		try:
			filterStringEntry = self.w.filter.get().strip()
			filterStrings = filterStringEntry.split(" ")

			try:
				ParameterList = sorted(set(self.fontParameters + self.instanceParameters + self.masterParameters), key=lambda thisName: thisName.lower())
				for filterString in filterStrings:
					if "*" not in filterString:
						ParameterList = [f for f in ParameterList if filterString.lower() in f.lower()]
					elif filterString.startswith("*"):
						ParameterList = [f for f in ParameterList if f.lower().endswith(filterString.lower()[1:])]
					elif filterString.endswith("*"):
						ParameterList = [f for f in ParameterList if f.lower().startswith(filterString.lower()[:-1])]
					else:
						asteriskPos = filterString.find("*")
						beginning = filterString[:asteriskPos].lower()
						ending = filterString[asteriskPos + 1:].lower()
						ParameterList = [f for f in ParameterList if f.lower().startswith(beginning) and f.lower().endswith(ending)]
			except:
				ParameterList = []

			if ParameterList:
				ParameterList = ["%s %s" % (item, self.realmStringForParameter(item)) for item in ParameterList]

			self.w.ParameterList.set(ParameterList)

			self.SavePreferences()

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Parameter Reporter Error: %s" % e)
			import traceback
			print(traceback.format_exc())


ParameterReporter()
