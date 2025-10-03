# MenuTitle: Find and Replace in Instance Parameters
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Finds and Replace in Custom Parameters of selected instances of the current font or project file.
"""

import vanilla
import objc
from Foundation import NSString, NSMutableArray
from GlyphsApp import Glyphs, GSProjectDocument
from mekkablue import mekkaObject


class FindAndReplaceInInstanceParameters(mekkaObject):
	prefDict = {
		"availableParameters": "0",
		"find": "",
		"replace": ""
	}

	def __init__(self):
		# Window 'self.w':
		windowWidth = 320
		windowHeight = 180
		windowWidthResize = 300  # user can resize width by this value
		windowHeightResize = 400  # user can resize height by this value
		self.w = vanilla.FloatingWindow(
			(windowWidth, windowHeight),  # default window size
			"Find and Replace In Instance Parameters",  # window title
			minSize=(windowWidth, windowHeight),  # minimum size (for resizing)
			maxSize=(windowWidth + windowWidthResize, windowHeight + windowHeightResize),  # maximum size (for resizing)
			autosaveName=self.domain("mainwindow")  # stores last window position and size
		)

		# UI elements:
		self.w.text_1 = vanilla.TextBox((15 - 1, 12 + 2, 130, 14), "Replace in parameters", sizeStyle='small')
		self.w.availableParameters = vanilla.PopUpButton((145, 12, -15, 17), self.setAvailableParameters(None), callback=self.SavePreferences, sizeStyle='small')
		self.w.find = vanilla.TextEditor((15, 40, 100, -50), text="find", callback=self.SavePreferences, checksSpelling=False)
		self.w.replace = vanilla.TextEditor((110, 40, 100, -50), text="replace", callback=self.SavePreferences, checksSpelling=False)
		self.windowResize(None)

		# Run Button:
		self.w.rescanButton = vanilla.Button((-200, -20 - 15, -110, -15), "Rescan", callback=self.setAvailableParameters)
		self.w.runButton = vanilla.Button((-80 - 15, -20 - 15, -15, -15), "Replace", callback=self.FindAndReplaceInInstanceParametersMain)
		self.w.setDefaultButton(self.w.runButton)

		self.w.bind("resize", self.windowResize)

		# Load Settings:
		self.LoadPreferences()

		# Open window and focus on it:
		self.w.open()
		self.w.makeKey()

	def windowResize(self, sender):
		windowWidth = self.w.getPosSize()[2]
		adaptedWidth = windowWidth / 2 - 20
		self.w.find.setPosSize((15, 40, adaptedWidth, -50))
		self.w.replace.setPosSize((-adaptedWidth - 15, 40, adaptedWidth, -50))

	def getInstances(self):
		# get instances from project or font:
		frontmostDoc = Glyphs.orderedDocuments()[0]
		if isinstance(frontmostDoc, GSProjectDocument):
			return frontmostDoc.instances()
		elif Glyphs.font:
			return Glyphs.font.instances
		else:
			return None

	def setAvailableParameters(self, sender):
		instances = self.getInstances()
		if instances:
			# collect parameters:
			parameters = []
			for thisInstance in instances:
				for thisParameter in thisInstance.customParameters:
					parameters.append(thisParameter.name)
			# avoid duplicates:
			parameters = list(set(parameters))

			if sender:
				# Rescan button
				self.w.availableParameters.setItems(sorted(parameters))
				self.w.availableParameters.set(0)
			else:
				# sort and return:
				return sorted(parameters)
		else:
			return None

	def FindAndReplaceInInstanceParametersMain(self, sender):
		try:
			instances = self.getInstances()
			selectedIndex = self.w.availableParameters.get()
			parameterItems = self.w.availableParameters.getItems()
			
			# Ensure we have valid items and selection
			if selectedIndex < 0 or selectedIndex >= len(parameterItems):
				print("Error: No parameter selected")
				return
				
			parameterName = str(parameterItems[selectedIndex])  # Convert to string to ensure proper type
			findText = self.w.find.get()
			replaceText = self.w.replace.get()

			if parameterName and instances:
				for thisInstance in instances:  # loop through instances
					parameter = thisInstance.customParameters[parameterName]
					if parameter is not None:
						
						# Special handling for Axis Location and similar structured parameters
						if parameterName in ("Axis Location", "Axes Coordinates") and hasattr(parameter, "__iter__"):
							if findText and replaceText:
								# Work with structured axis data (array of dictionaries)
								parameterList = NSMutableArray.arrayWithArray_(parameter)
								changesMade = False
								
								# Remove any stray non-dict items that may have been added by accident
								itemsToRemove = []
								for i, item in enumerate(parameterList):
									if not (isinstance(item, dict) or str(type(item)).find('Dictionary') != -1):
										itemsToRemove.append(i)
								
								# Remove in reverse order to maintain indices
								for i in reversed(itemsToRemove):
									parameterList.removeObjectAtIndex_(i)
									changesMade = True
								
								# Now search and replace within the Location values
								for item in parameterList:
									if isinstance(item, dict) or str(type(item)).find('Dictionary') != -1:
										if 'Location' in item:
											locationValue = item['Location']
											locationStr = str(locationValue)
											if findText in locationStr:
												try:
													# Try to replace as number
													if isinstance(locationValue, int):
														newLocation = int(replaceText)
													else:
														newLocation = float(replaceText)
													item['Location'] = newLocation
													changesMade = True
													print(f"{thisInstance.name}: replaced Location {locationValue} → {newLocation} in {parameterName}")
												except ValueError:
													print(f"Warning: Could not convert '{replaceText}' to number for Location value")
								
								if changesMade:
									thisInstance.customParameters[parameterName] = parameterList
							continue  # Skip the regular string/array handling below
						
						# Check if it's a boolean or integer type (compatible with different PyObjC versions)
						if isinstance(parameter, bool) or (isinstance(parameter, int) and not isinstance(parameter, bool)):
							onOff = False
							if replaceText.lower() in ("1", "yes", "on", "an", "ein", "ja", "true", "wahr"):
								onOff = True
							thisInstance.customParameters[parameterName] = onOff
							onOrOff = "on" if onOff else "off"
							print("%s: switched %s %s" % (thisInstance.name, onOrOff, parameterName))

						elif findText:
							if isinstance(parameter, (objc.pyobjc_unicode, NSString, str)):
								newValue = parameter.replace(findText, replaceText)
								thisInstance.customParameters[parameterName] = newValue
								print("%s: replaced in %s" % (thisInstance.name, parameterName))
							elif hasattr(parameter, "__iter__") and not isinstance(parameter, str):
								# For array-like parameters, use NSMutableArray to maintain compatibility
								parameterList = NSMutableArray.arrayWithArray_(parameter)
								findList = findText.splitlines()
								replaceList = replaceText.splitlines()
								for findItem in findList:
									while findItem in parameterList:
										parameterList.removeObject_(findItem)
								for replaceItem in replaceList:
									parameterList.addObject_(replaceItem)
								thisInstance.customParameters[parameterName] = parameterList
								print("%s: replaced in %s" % (thisInstance.name, parameterName))

						elif replaceText:
							if isinstance(parameter, (objc.pyobjc_unicode, NSString, str)):
								newValue = parameter + replaceText
								thisInstance.customParameters[parameterName] = newValue
								print("%s: appended to %s" % (thisInstance.name, parameterName))
							elif hasattr(parameter, "__iter__") and not isinstance(parameter, str):
								# For array-like parameters, use NSMutableArray to maintain compatibility
								parameterList = NSMutableArray.arrayWithArray_(parameter)
								replaceList = replaceText.splitlines()
								for replaceItem in replaceList:
									parameterList.addObject_(replaceItem)
								thisInstance.customParameters[parameterName] = parameterList
								print("%s: appended to %s" % (thisInstance.name, parameterName))

			self.SavePreferences()

		except Exception as e:
			# brings macro window to front and reports error:
			Glyphs.showMacroWindow()
			print("Find and Replace In Instance Parameters Error: %s" % e)
			import traceback
			print(traceback.format_exc())


FindAndReplaceInInstanceParameters()
