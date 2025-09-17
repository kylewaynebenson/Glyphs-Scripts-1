# MenuTitle: Fill Up with Rectangles
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Inserts Rectangles in all empty, selected glyphs. Verbose report in Macro Window.
"""

from GlyphsApp import Glyphs, GSPath, GSNode, GSLINE, GSUppercase, GSLowercase

thisFont = Glyphs.font
selectedLayers = thisFont.selectedLayers


def drawRect(myBottomLeft, myTopRight):
	try:
		myRect = GSPath()
		myCoordinates = [[myBottomLeft[0], myBottomLeft[1]], [myTopRight[0], myBottomLeft[1]], [myTopRight[0], myTopRight[1]], [myBottomLeft[0], myTopRight[1]]]

		for thisPoint in myCoordinates:
			newNode = GSNode()
			newNode.type = GSLINE
			newNode.position = (thisPoint[0], thisPoint[1])
			myRect.nodes.append(newNode)

		myRect.closed = True
		return myRect

	except Exception as e:  # noqa: F841
		return False


def process(thisLayer):
	layerIsEmpty = (len(thisLayer.paths) == 0 and len(thisLayer.components) == 0)
	thisGlyph = thisLayer.parent
	bottom = 0
	insetPercentage = 9
	try:
		# Glyphs 3
		case = thisGlyph.case
		if thisGlyph.category == "Mark":
			height = 100
			bottom = 600
			insetPercentage = 30
			if case == GSUppercase:
				bottom = 750
		else:
			if case == GSLowercase:
				height = 500
			elif case == GSUppercase:
				height = 700
			else:
				height = 600
	except:
		# Glyphs 2
		subCategory = thisGlyph.subCategory
		if subCategory == "Lowercase":
			height = 500
		elif subCategory == "Uppercase":
			height = 700
		else:
			height = 600

	if layerIsEmpty:
		inset = thisLayer.width / 100.0 * insetPercentage
		bottomLeft = (inset, bottom)
		topRight = (thisLayer.width - inset, bottom + height)
		layerRect = drawRect(bottomLeft, topRight)
		if layerRect:
			try:
				# Glyphs 2:
				thisLayer.paths.append(layerRect)
			except:
				# Glyphs 3:
				thisLayer.shapes.append(layerRect)
			return f"✅ 🔽 {bottom} ↕️ {height} ↔️ {thisLayer.width-2*inset}"
		else:
			return "❌ error"
	else:
		return "🆗 not empty, skipped"


Glyphs.clearLog()  # clears macro window log
print(f"‘Fill Up with Rectangles’ report for: {thisFont.familyName}\n")

thisFont.disableUpdateInterface()
try:
	for thisLayer in selectedLayers:
		thisGlyph = thisLayer.parent
		if thisGlyph:
			# thisGlyph.beginUndo()  # undo grouping causes crashes
			print(f"Filling {thisGlyph.name}: {process(thisLayer)}.")
			# thisGlyph.endUndo()  # undo grouping causes crashes
except Exception as e:
	Glyphs.showMacroWindow()
	import traceback
	print(f"\n⚠️ Script Error:\n\n{traceback.format_exc()}\n")
	raise e
finally:
	thisFont.enableUpdateInterface()  # re-enables UI updates in Font View
	thisFont.postProcess()  # circumvent display bug in builds 34xx

print("\nDone.")
