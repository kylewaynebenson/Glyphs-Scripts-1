# MenuTitle: Webfont Test HTML
# -*- coding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
__doc__ = """
Create a Test HTML for the current font inside the current Webfont Export folder, or for the current Glyphs Project in the project’s export path.
"""

from GlyphsApp import Glyphs, GSProjectDocument, INSTANCETYPESINGLE, Message
from AppKit import NSBundle, NSClassFromString
from os import system, path
import codecs
Glyphs.registerDefault("com.mekkablue.WebFontTestHTML.includeEOT", 0)


def saveFileInLocation(content="Sorry, no content generated.", fileName="test.txt", filePath="~/Desktop"):
	saveFileLocation = "%s/%s" % (filePath, fileName)
	saveFileLocation = saveFileLocation.replace("//", "/")
	with codecs.open(saveFileLocation, "w", "utf-8") as thisFile:
		print("Exporting to:", thisFile.name)
		thisFile.write(content)
		thisFile.close()
	return True


def currentFileFormats():
	if Glyphs.versionNumber < 3.0:
		# GLYPHS 2
		fileFormats = ["woff", "woff2"]
		if Glyphs.defaults["com.mekkablue.WebFontTestHTML.includeEOT"]:
			fileFormats.append("eot")
	else:
		# GLYPHS 3
		fileFormats = []
		if Glyphs.defaults["OTFExportPlain"]:
			if Glyphs.defaults["OTFExportOutlineformat"] == 2:  # TTF
				fileFormats.append("ttf")
			else:
				fileFormats.append("otf")
		if Glyphs.defaults["OTFExportWOFF"]:
			fileFormats.append("woff")
		if Glyphs.defaults["OTFExportWOFF2"]:
			fileFormats.append("woff2")
	return tuple(fileFormats)


def currentWebExportPath():
	if Glyphs.versionNumber < 3.0:
		# GLYPHS 2
		exportPath = Glyphs.defaults["WebfontPluginExportPathManual"]
		if Glyphs.defaults["WebfontPluginUseExportPath"]:
			exportPath = Glyphs.defaults["WebfontPluginExportPath"]
	else:
		# GLYPHS 3
		exportPath = Glyphs.defaults["OTFExportPathManual"]
		if Glyphs.defaults["OTFExportUseExportPath"]:
			exportPath = Glyphs.defaults["OTFExportPath"]
	return exportPath


def replaceSet(text, setOfReplacements):
	for thisReplacement in setOfReplacements:
		searchFor = thisReplacement[0]
		replaceWith = thisReplacement[1]
		text = text.replace(searchFor, replaceWith)
	return text


def allUnicodeEscapesOfFont(thisFont):
	importedGlyphs = thisFont.importedGlyphs()
	if not importedGlyphs:
		importedGlyphs = []
	allUnicodes = ["&#x%s;" % g.unicode for g in thisFont.glyphs + importedGlyphs if g.unicode and g.export and g.subCategory != "Nonspacing"]
	allUnicodes += [" &#x%s;" % g.unicode for g in thisFont.glyphs + importedGlyphs if g.unicode and g.export and g.subCategory == "Nonspacing"]
	return "".join(allUnicodes)


def getInstanceInfo(thisFont, activeInstance, fileFormat):
	# Determine Family Name

	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		familyName = activeInstance.familyName
		if not familyName:
			familyName = thisFont.familyName
	else:
		# GLYPHS 2
		familyName = thisFont.familyName
		individualFamilyName = activeInstance.customParameters["familyName"]
		if individualFamilyName is not None:
			familyName = individualFamilyName

	# Determine Style Name
	activeInstanceName = activeInstance.name
	
	# Verify file format
	if fileFormat in ("otf", "ttf"): # otherwise woff, woff2 or eot
		ttParameter = activeInstance.customParameterActiveForKey_("Save as TrueType")
		if ttParameter:
			if ttParameter.value:
				fileFormat = "ttf"
			else:
				fileFormat = "otf"

	# Determine font and file names for CSS
	menuName = "%s %s-%s" % (fileFormat.upper(), familyName, activeInstanceName)

	# 3 approaches for determining the file names:
	firstPartOfFileName = ".".join(activeInstance.fileName().split(".")[:-1])  # removes ".otf" at the end
	if not firstPartOfFileName:
		firstPartOfFileName = activeInstance.customParameters["fileName"]
	if not firstPartOfFileName:
		firstPartOfFileName = "%s-%s" % (familyName.replace(" ", ""), activeInstanceName.replace(" ", ""))

	fileName = "%s.%s" % (firstPartOfFileName, fileFormat)

	exportFolderParameter = activeInstance.customParameterActiveForKey_("Export Folder")
	exportFolderParameterFontWide = thisFont.customParameterActiveForKey_("Export Folder")
	for parameter in (exportFolderParameter, exportFolderParameterFontWide):
		if parameter:
			exportFolder = parameter.value
			fileName = path.join(exportFolder, fileName)
			menuName = f"📁 {exportFolder} ⏵ {menuName}"
			break

	return fileName, menuName, activeInstanceName


def instanceIsActive(instance):
	if Glyphs.buildNumber > 3198:
		return instance.exports
	else:
		return instance.active


def allActiveInstancesOfFont(thisFont):
	activeInstances = [i for i in thisFont.instances if instanceIsActive(i) and isSingleInstance(i)]
	return activeInstances


def allActiveInstancesOfProject(thisProject):
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		activeInstances = [i for i in thisProject.instances if instanceIsActive(i) and isSingleInstance(i)]
	else:
		# GLYPHS 2
		activeInstances = [i for i in thisProject.instances() if instanceIsActive(i) and isSingleInstance(i)]
	return activeInstances


def isSingleInstance(instance):
	if Glyphs.versionNumber >= 3:
		# GLYPHS 3
		return instance.type == INSTANCETYPESINGLE
	else:
		# GLYPHS 2
		return True


def activeInstancesByFormat(thisFont, activeInstances, fileFormats, availableFormats=("otf", "ttf", "woff", "woff2", "eot")):
	instanceInfos = {}
	for availableFormat in availableFormats:
		instanceInfos[availableFormat] = []
		
	for activeInstance in activeInstances:
		for fileFormat in fileFormats:
			webParameter = activeInstance.customParameterActiveForKey_("Webfont Formats")
			if webParameter:
				webFormats = list(webParameter.value)
				if "plain" in webFormats:
					webFormats[webFormats.index("plain")] = fileFormat
			else:
				webFormats = [fileFormat]
			
			for webFormat in webFormats:
				if webFormat not in availableFormats:
					print("Error: cannot identify format", webFormat)
					continue
				fileName, menuName, activeInstanceName = getInstanceInfo(thisFont, activeInstance, webFormat)
				instanceInfos[webFormat.lower().strip()].append((fileName, menuName, activeInstanceName))
				
	orderedInstanceInfos = []
	for availableFormat in availableFormats:
		for info in instanceInfos[availableFormat]:
			orderedInstanceInfos.append(info)
	return orderedInstanceInfos


def activeInstancesOfFontByFormat(thisFont, fileFormats=("woff", "woff2")):
	activeInstances = allActiveInstancesOfFont(thisFont)
	listOfInstanceInfo = activeInstancesByFormat(thisFont,activeInstances,  fileFormats)
	return listOfInstanceInfo


def activeInstancesOfProjectByFormat(thisProject, fileFormats=("woff", "woff2")):
	thisFont = thisProject.font()
	activeInstances = allActiveInstancesOfProject(thisProject)
	listOfInstanceInfo = activeInstancesByFormat(thisFont, activeInstances, fileFormats)
	return listOfInstanceInfo


def optionListForInstances(instanceList):
	returnString = ""
	for thisInstanceInfo in instanceList:
		returnString += '			<option value="%s">%s</option>\n' % (thisInstanceInfo[0], thisInstanceInfo[1])
		# <option value="fileName">baseName</option>
	return returnString


def fontFaces(instanceList):
	returnString = ""
	for thisInstanceInfo in instanceList:
		fileName = thisInstanceInfo[0]
		nameOfTheFont = thisInstanceInfo[1]
		returnString += "\t\t@font-face { font-family: '%s'; src: url('%s'); }\n" % (nameOfTheFont, fileName)

	return returnString


def featureListForFont(thisFont):
	returnString = ""
	featureList = [(f.name, f.notes) for f in thisFont.features if f.name not in ("ccmp", "aalt", "locl", "kern", "calt", "liga", "clig") and not f.disabled()]
	doneFeatures = []
	for (f, n) in featureList:
		if f not in doneFeatures:  # avoid duplicates
			doneFeatures.append(f)
			if f.startswith("ss") and n and n.startswith("Name:"):
				# stylistic set name:
				setName = n.splitlines()[0][5:].strip()
				returnString += '\t\t<input type="checkbox" id="%s" value="%s" class="otFeature" onchange="updateFeatures()"><label for="%s" class="otFeatureLabel">%s<span class="tooltip">%s</span></label>\n' % (
					f, f, f, f, setName
				)
			else:
				returnString += '\t\t<input type="checkbox" id="%s" value="%s" class="otFeature" onchange="updateFeatures()"><label for="%s" class="otFeatureLabel">%s</label>\n' % (
					f, f, f, f
				)
	return returnString


htmlContent = """<head>
	<!--<base href="..">--> <!-- uncomment for keeping the HTML in a subfolder -->
	<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
	<meta http-equiv="Content-type" content="text/html; charset=utf-8" />
	<meta http-equiv="X-UA-Compatible" content="IE=9" />
	<title>familyName</title>
	<style type="text/css" media="screen">
		<!-- fontFaces -->
		body {
			background: white;
			color: black;
		}
		.features, .label, a, #controls {
			font: normal normal normal small sans-serif;
		}
		.features .emojiButton {
			vertical-align: -5%;
			font-size: small;
		}
		.emojiButton {
			cursor: pointer;
		}
		#flexbox {
			display: flex;
			flex-flow: column;
			height: 100%;
		}
		#controls {
			flex: 0 1 auto;
			margin: 0;
			padding: 0;
			width: 100%;
			border: 0px solid transparent;
			height: auto;
			user-select: none;
			-moz-user-select: none;
			-webkit-user-select: none;
		}
		#metricsLine {
			background-color: #EEE;
			border-top: 1px solid #AAA;
			border-bottom: 1px solid #AAA;
			width: 100%;
			margin: 0.2em 0;
			padding: 0 0;
			font-size: 6em;
			white-space: nowrap;
			overflow-x: auto;
			overflow-y: hidden;
			text-overflow: none;
			display: none;
			scrollbar-width: none; /* Firefox */
			-ms-overflow-style: none;  /* Internet Explorer 10+ */
		}
		#metricsLine::-webkit-scrollbar { /* WebKit */
			width: 0;
			height: 0;
		}
		#waterfall {
			flex: 1 1 auto;
			border: 0 solid transparent;
			margin: 0;
			padding: 0;
			width: 100%;
			color: black;
			overflow-x: hidden;
			overflow-y: scroll;
			font-family: "nameOfTheFont";
			font-feature-settings: "kern" on, "liga" on, "calt" on;
			-moz-font-feature-settings: "kern" on, "liga" on, "calt" on;
			-webkit-font-feature-settings: "kern" on, "liga" on, "calt" on;
			-ms-font-feature-settings: "kern" on, "liga" on, "calt" on;
			-o-font-feature-settings: "kern" on, "liga" on, "calt" on;
		}
		div, p	{
			padding: 0;
			margin: 0;
		}
		#waterfall p {
			margin-bottom: 0.8em;
			overflow-wrap: break-word;
		}
		.○ .sampletext {
			-webkit-text-stroke: 1px black;
			-webkit-text-fill-color: #FFF0;
		}
		.features, .label, a {
			color: #888;
		}
		.label {
			background-color: #ddd;
			padding: 2px 3px;
		}

		span#p08 { font-size: 08pt; padding: 08pt 0; }
		span#p09 { font-size: 09pt; padding: 09pt 0; }
		span#p10 { font-size: 10pt; padding: 10pt 0; }
		span#p11 { font-size: 11pt; padding: 11pt 0; }
		span#p12 { font-size: 12pt; padding: 12pt 0; }
		span#p13 { font-size: 13pt; padding: 13pt 0; }
		span#p14 { font-size: 14pt; padding: 14pt 0; }
		span#p15 { font-size: 15pt; padding: 15pt 0; }
		span#p16 { font-size: 16pt; padding: 16pt 0; }
		span#largeParagraph { font-size: 32pt; padding: 32pt 0; }
		span#veryLargeParagraph { font-size: 100pt; padding: 100pt 0; }

		.otFeatureLabel {
			color: #666;
			background-color: #ddd;
			padding: 0.2em 0.5em 0.3em 0.5em;
			margin: 0 .04em;
			line-height: 2em;
			border-radius: 0.3em;
			border: 0;
			text-align:center;
		}
		.otFeatureLabel, .otFeature {
			position: relative;
			opacity: 1;
			pointer-events: auto;
			white-space: nowrap;
		}
		.otFeatureLabel {
			padding: 0.2em 0.5em 0.3em 0.5em;
			margin: 0 .04em;
			line-height: 2em;
			color: #666;
			background-color: #ddd;
			border-radius: 0.3em;
			border: 0;
			text-align: center;
			z-index: 6;
		}
		.wrapper {
			width: auto;
			overflow: hidden;
			border: 0 solid transparent;
		}
		select {
			float: left;
			margin: 0 0.5em 0 0;
			padding: 0;
		}
		input[type=text] {
			border: 1px solid #999;
			margin: 0;
			width: 100%;
		}
		.features {
			clear: left;
		}
		input[type=checkbox]:checked + label {
			visibility: visible;
			color: #fff;
			background-color: #888;
		}
		.otFeature {
			visibility: collapse;
			margin: 0 -1em 0 0;
		}
		.otFeatureLabel .tooltip {
			visibility: hidden;
			background-color: #333;
			color: white;
			text-align: center;
			padding: 0px 5px;
			top: -2em;
			left: 0;
			position: absolute;
			z-index: 8;
		}
		.otFeatureLabel:hover .tooltip {
			visibility: visible;
		}
		#featureLine {
			display: none;
			border-bottom: 1px solid #999;
			padding: 0.5em 0;
			margin-bottom: 0.5em;
		}

		/* Footer paragraph: */
		#helptext {
			color: black;
			background-color: #ddd;
			position: fixed;
			bottom: 0;
			padding: 2px;
			width: 100%;
			font: x-small sans-serif;
		}

		/* Dark Mode */
		@media (prefers-color-scheme: dark) {
			body {
				background: #333;
			}
			.features, .label, a, body, p, #metricsLine {
				color: white;
			}
			.label {
				background-color: black;
				padding: 2px 3px;
			}
			.otFeatureLabel, input[type=text] {
				color: white;
				background-color: black;
			}
			input[type=checkbox]:checked + label {
				color: black;
				background-color: #aaa;
			}
			#helptext {
				background-color: #777;
			}
			.○ .sampletext {
				-webkit-text-stroke: 1px white;
				-webkit-text-fill-color: #0000;
			}
			#metricsLine {
				background-color: #222;
				border-color: #777;
			}
		}
	</style>
</head>
<body onload="document.getElementById('textInput').focus();setCharset();">
<div id="flexbox">
<div id="controls">
	<div>
		<select size="1" id="fontFamilySelector" name="fontFamilySelector" onchange="changeFont()">
		<!-- moreOptions -->
		</select>
		<div class="wrapper" spellcheck="false">
			<input type="text" value="Type Text Here." id="textInput" onkeyup="updateParagraph()" />
		</div>
	</div>
	<p class="features">
		<a href="javascript:setCharset();">Charset</a>
		<a href="javascript:setLat1();">Lat1</a>
		&ensp;
		<a href="https://caniuse.com/#feat=woff">woff</a>
		<a href="https://caniuse.com/#feat=woff2">woff2</a>
		&ensp;
		<a onclick="toggleInverse();" id="invert" class="emojiButton">🔲</a>
		<label><input type="checkbox" id="kern" value="kern" class="otFeature" onchange="updateFeatures()" checked><label for="kern" class="otFeatureLabel">kern</label>
		<label><input type="checkbox" id="liga" value="liga" class="otFeature" onchange="updateFeatures()" checked><label for="liga" class="otFeatureLabel">liga/clig</label>
		<label><input type="checkbox" id="calt" value="calt" class="otFeature" onchange="updateFeatures()" checked><label for="calt" class="otFeatureLabel">calt</label>
		<!-- moreFeatures -->
		<label><input type="checkbox" value="show" onchange="updateFeatures();document.getElementById('featureLine').style.display=this.checked?'block':'none'">CSS</label>
		<label><input type="checkbox" value="show" onchange="updateFeatures();document.getElementById('metricsLine').style.display=this.checked?'block':'none'">Metrics</label>
	</p>
	<p class="features" id="featureLine">font-feature-settings: "kern" on, "liga" on, "calt" on;</p>
</div>
<div id="waterfall" class="●">
	<div id="metricsLine"></div>
	<p><span class="label">08</span>&nbsp;<span class="sampletext" id="p08"></span></p>
	<p><span class="label">09</span>&nbsp;<span class="sampletext" id="p09"></span></p>
	<p><span class="label">10</span>&nbsp;<span class="sampletext" id="p10"></span></p>
	<p><span class="label">11</span>&nbsp;<span class="sampletext" id="p11"></span></p>
	<p><span class="label">12</span>&nbsp;<span class="sampletext" id="p12"></span></p>
	<p><span class="label">13</span>&nbsp;<span class="sampletext" id="p13"></span></p>
	<p><span class="label">14</span>&nbsp;<span class="sampletext" id="p14"></span></p>
	<p><span class="label">15</span>&nbsp;<span class="sampletext" id="p15"></span></p>
	<p><span class="label">16</span>&nbsp;<span class="sampletext" id="p16"></span></p>
	<p><span class="sampletext" id="largeParagraph"></span></p>
	<p><span class="sampletext" id="veryLargeParagraph"></span></p>
</div>
</div>

<!-- Disclaimer -->
<p id="helptext" onmouseleave="vanish(this);">
	Ctrl-R: Reset Charset. Ctrl-L: Latin1. Ctrl-J: LTR/RTL. Ctrl-comma/period: step through fonts. Pull mouse across this note to make it disappear.
</p>

<script type="text/javascript">
	const selector = document.getElementById("fontFamilySelector");
	const selectorOptions = selector.options;
	const selectorLength = selectorOptions.length;

	document.addEventListener('keyup', keyAnalysis);

	function keyAnalysis(event) {
		if (event.ctrlKey) {
			if (event.code == 'KeyR') {
				setCharset();
			} else if (event.code == 'KeyL') {
				setLat1();
			} else if (event.code == 'KeyJ') {
				toggleLeftRight();
			} else if (event.code == 'Period') {
				selector.selectedIndex = (selector.selectedIndex + 1) % selectorLength;
				changeFont();
			} else if (event.code == 'Comma') {
				var newIndex = selector.selectedIndex - 1;
				if (newIndex<0) {
					newIndex = selectorLength - 1;
				}
				selector.selectedIndex = newIndex;
				changeFont();
			}
		}
	}
	function updateParagraph() {
		// update paragraph text based on user input:
		const txt = document.getElementById('textInput');
		const paragraphs = document.getElementsByClassName('sampletext');
		for (i = 0; i < paragraphs.length; i++) {
			paragraph = paragraphs[i];
			paragraph.textContent = txt.value;
		}

		// update other elements:
		document.getElementById('metricsLine').textContent = txt.value;
	}
	function updateFeatures() {
		// update features based on user input:
		// first, get feature on/off line:
		var cssCode = "";
		var codeLine = "";
		var checkboxes = document.getElementsByClassName("otFeature")
		for (i = 0; i < checkboxes.length; i++) {
			var checkbox = checkboxes[i];
			codeLine += '"'+checkbox.id+'" ';
			codeLine += checkbox.checked ? 'on, ' : 'off, ';
			if (checkbox.name=="kern") {
				cssCode += "font-kerning: "
				cssCode += checkbox.checked ? 'normal; ' : 'none; ';
			} else if (checkbox.name=="liga") {
				codeLine += '"clig" '
				codeLine += checkbox.checked ? 'on, ' : 'off, ';
				cssCode += "font-variant-ligatures: "
				cssCode += checkbox.checked ? 'common-ligatures contextual; ' : 'no-common-ligatures no-contextual; ';
			} else if (checkbox.name=="dlig") {
				cssCode += "font-variant-ligatures: "
				cssCode += checkbox.checked ? 'discretionary-ligatures; ' : 'no-discretionary-ligatures; ';
			} else if (checkbox.name=="hlig") {
				cssCode += "font-variant-ligatures: "
				cssCode += checkbox.checked ? 'historical-ligatures; ' : 'no-historical-ligatures; ';
			} else if (checkbox.name=="case") {
				testtext.style.textTransform = checkbox.checked ? "uppercase" : "none";
			}
		}
		codeLine = codeLine.slice(0, -2)

		// then, apply line for every browser:
		const prefixes = ["","-moz-","-webkit-","-ms-","-o-",];
		const suffix = "font-feature-settings: "
		for (i = 0; i < prefixes.length; i++) {
			var prefix = prefixes[i];
			cssCode += prefix
			cssCode += suffix
			cssCode += codeLine
			cssCode += "; "
		}

		document.getElementById('waterfall').style.cssText = cssCode;
		document.getElementById('featureLine').innerHTML = cssCode.replace(/;/g,";<br/>");
		changeFont();
	}
	function changeFont() {
		var selected_index = selector.selectedIndex;
		var selected_option_text = selector.options[selected_index].text;
		document.getElementById('waterfall').style.fontFamily = `'${selected_option_text}'`;
	}
	function setDefaultText(defaultText) {
		document.getElementById('textInput').value = decodeEntities(defaultText);
		updateParagraph();
	}
	function setLat1() {
		const lat1 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz &Agrave;&Aacute;&Acirc;&Atilde;&Auml;&Aring;&AElig;&Ccedil;&Egrave;&Eacute;&Ecirc;&Euml;&Igrave;&Iacute;&Icirc;&Iuml;&ETH;&Ntilde;&Ograve;&Oacute;&Ocirc;&Otilde;&Ouml;&Oslash;&OElig;&THORN;&Ugrave;&Uacute;&Ucirc;&Uuml;&Yacute;&Yuml; &agrave;&aacute;&acirc;&atilde;&auml;&aring;&aelig;&ccedil;&egrave;&eacute;&ecirc;&euml;&igrave;&iacute;&icirc;&iuml;&eth;&ntilde;&ograve;&oacute;&ocirc;&otilde;&ouml;&oslash;&oelig;&thorn;&szlig;&ugrave;&uacute;&ucirc;&uuml;&yacute;&yuml; .,:;&middot;&hellip;&iquest;?&iexcl;!&laquo;&raquo;&lsaquo;&rsaquo; /|&brvbar;\\()[]{}_-&ndash;&mdash;&sbquo;&bdquo;&lsquo;&rsquo;&ldquo;&rdquo;&quot;&#x27; #&amp;&sect;@&bull;&shy;*&dagger;&Dagger;&para; +&times;&divide;&plusmn;=&lt;&gt;&not;&mu; ^~&acute;`&circ;&macr;&tilde;&uml;&cedil; &yen;&euro;&pound;$&cent;&curren;&fnof; &trade;&reg;&copy; 1234567890 &ordf;&ordm;&deg;%&permil; &sup1;&sup2;&sup3;&frac14;&frac12;&frac34;";
		return setDefaultText(lat1);
	}
	function setCharset() {
		const completeCharSet = 'The Quick Brown Fox Jumps Over The Lazy Dog.';
		setDefaultText(completeCharSet);
	}
	function decodeEntities(string){
		var elem = document.createElement('div');
		elem.innerHTML = string;
		return elem.textContent;
	}
	function vanish(item) {
		item.style.setProperty("display", "none");
	}
	function toggleLeftRight() {
		const waterfall = document.getElementById("waterfall");
		if (waterfall.dir != "rtl") {
			waterfall.dir = "rtl";
			waterfall.align = "right";
		} else {
			waterfall.dir = "";
			waterfall.align = "";
		}
	}
	function toggleInverse() {
		const testText = document.getElementById("waterfall");
		if (testText) {
			const link = document.getElementById("invert");
			if (testText.className == "●") {
				testText.className = "○";
				link.textContent = "🔳";
			} else {
				testText.className = "●";
				link.textContent = "🔲";
			}
		}
	}
</script>
</body>
"""

# brings macro window to front and clears its log:
Glyphs.clearLog()
# Glyphs.showMacroWindow()

# Query app version:
GLYPHSAPPVERSION = NSBundle.bundleForClass_(NSClassFromString("GSMenu")).infoDictionary().objectForKey_("CFBundleShortVersionString")
appVersionHighEnough = not GLYPHSAPPVERSION.startswith("1.")

fileFormats = currentFileFormats()
if not appVersionHighEnough:
	print("This script requires Glyphs 2 or higher. Sorry.")
else:
	firstDoc = Glyphs.orderedDocuments()[0]
	if isinstance(firstDoc, GSProjectDocument):
		# Frontmost doc is a .glyphsproject file:
		thisFont = firstDoc.font()  # type: ignore
		activeFontInstances = activeInstancesOfProjectByFormat(firstDoc, fileFormats=fileFormats)
		exportPath = firstDoc.exportPath()
	else:
		# Frontmost doc is a .glyphs file:
		thisFont = Glyphs.font  # frontmost font
		activeFontInstances = activeInstancesOfFontByFormat(thisFont, fileFormats=fileFormats)
		exportPath = currentWebExportPath()

	familyName = thisFont.familyName

	if not activeFontInstances:
		if Glyphs.versionNumber >= 3:
			# GLYPHS 3
			exports = "Exports"
		else:
			# GLYPHS 2
			exports = "Instances"

		Message(
			title="⚠️ No exporting fonts found",
			message="No active font instances are set in Font Info > %s. Cannot create HTML for %s." % (exports, familyName),
			OKButton=None,
		)
		print("❌ %s: No instances set in Font Info. Aborting." % familyName)
	else:
		print("Preparing Test HTML for:")
		for thisFontInstanceInfo in activeFontInstances:
			print("  %s" % thisFontInstanceInfo[1])

		optionList = optionListForInstances(activeFontInstances)
		fontFacesCSS = fontFaces(activeFontInstances)
		firstFileName = activeFontInstances[0][0]
		firstFontName = activeFontInstances[0][1]

		replacements = (
			("familyName", familyName),
			("nameOfTheFont", firstFontName),
			("The Quick Brown Fox Jumps Over The Lazy Dog.", allUnicodeEscapesOfFont(thisFont)),
			("fileName", firstFileName),
			("		<!-- moreOptions -->\n", optionList),
			("		<!-- moreFeatures -->\n", featureListForFont(thisFont)),
			("		<!-- fontFaces -->\n", fontFacesCSS)
		)

		htmlContent = replaceSet(htmlContent, replacements)

		# Write file to disk:
		if exportPath:
			filepath = thisFont.filepath
			if filepath:
				filename = filepath.lastPathComponent().stringByDeletingDotSuffix()
			else:
				filename = thisFont.familyName
			htmlFileName = f"{filename} fonttest.html"

			if saveFileInLocation(content=htmlContent, fileName=htmlFileName, filePath=exportPath):
				print("Successfully wrote file to disk.")
				terminalCommand = f'cd "{exportPath}"; open .; open "{htmlFileName}"'
				system(terminalCommand)
			else:
				print("Error writing file to disk.")
		else:
			Message(
				title="⚠️ Webfont Test HTML Error",
				message="Could not determine export path. You need to export webfonts first.",
				OKButton=None,
			)
