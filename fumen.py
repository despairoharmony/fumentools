import os, sys, struct, statistics

fumen2osu_version = "v1.4"

branchNames = ("normal", "advanced", "master")

def readFumen(inputFile, byteOrder=None, debug=False):
	if type(inputFile) is str:
		file = open(inputFile, "rb")
	else:
		file = inputFile
	size = os.fstat(file.fileno()).st_size
	
	noteTypes = {
		0x1: "Don", # ドン
		0x2: "Don", # ド
		0x3: "Don", # コ
		0x4: "Ka", # カッ
		0x5: "Ka", # カ
		0x6: "Drumroll",
		0x7: "DON",
		0x8: "KA",
		0x9: "DRUMROLL",
		0xa: "Balloon",
		0xb: "DON", # hands
		0xc: "Kusudama",
		0xd: "KA", # hands
		0x62: "Drumroll" # ?
	}
	song = {}
	
	def readStruct(format, seek=None):
		if seek:
			file.seek(seek)
		return struct.unpack(order + format, file.read(struct.calcsize(order + format)))
	
	if byteOrder:
		order = ">" if byteOrder == "big" else "<"
		totalMeasures = readStruct("I", 0x200)[0]
	else:
		order = ""
		measuresBig = readStruct(">I", 0x200)[0]
		measuresLittle = readStruct("<I", 0x200)[0]
		if measuresBig < measuresLittle:
			order = ">"
			totalMeasures = measuresBig
		else:
			order = "<"
			totalMeasures = measuresLittle
	
	hasBranches = getBool(readStruct("B", 0x1b0)[0])
	song["branches"] = hasBranches
	if debug:
		debugPrint("Total measures: {0}, {1} branches, {2}-endian".format(
			totalMeasures,
			"has" if hasBranches else "no",
			"Big" if order == ">" else "Little"
		))
	
	song["timingwindow"]  = readStruct("fff", 0xC)

	file.seek(0x208)
	for measureNumber in range(totalMeasures):
		measure = {}
		# measureStruct: bpm 4, offset 4, gogo 1, hidden 1, dummy 2, branchInfo 4 * 6, dummy 4
		measureStruct = readStruct("ffBBHiiiiiii")
		measure["bpm"] = measureStruct[0]
		measure["fumenOffset"] = measureStruct[1]
		if measureNumber == 0:
			measure["offset"] = measure["fumenOffset"] + 240000 / measure["bpm"]
		else:
			prev = song[measureNumber - 1]
			measure["offset"] = prev["offset"] + measure["fumenOffset"] + 240000 / measure["bpm"] - prev["fumenOffset"] - 240000 / prev["bpm"]
		measure["gogo"] = getBool(measureStruct[2])
		measure["hidden"] = getBool(measureStruct[3])
		
		for branchNumber in range(3):
			branch = {}
			# branchStruct: totalNotes 2, dummy 2, speed 4
			branchStruct = readStruct("HHf")
			totalNotes = branchStruct[0]
			branch["speed"] = branchStruct[2]
			
			if debug and (hasBranches or branchNumber == 0 or totalNotes != 0):
				branchName = " ({0})".format(
					branchNames[branchNumber]
				) if hasBranches or branchNumber != 0 else ""
				fileOffset = file.tell()
				debugPrint("")
				debugPrint("Measure #{0}{1} at {2}-{3} ({4})".format(
					measureNumber + 1,
					branchName,
					shortHex(fileOffset - 0x8),
					shortHex(fileOffset + 0x18 * totalNotes),
					nameValue(measure, branch)
				))
				debugPrint("Total notes: {0}".format(totalNotes))
			
			for noteNumber in range(totalNotes):
				if debug:
					fileOffset = file.tell()
					debugPrint("Note #{0} at {1}-{2}".format(
						noteNumber + 1,
						shortHex(fileOffset),
						shortHex(fileOffset + 0x17)
					), end="")
				
				note = {}
				# noteStruct: type 4, pos 4, item 4, dummy 4, init 2, diff 2, duration 4
				noteStruct = readStruct("ififHHf")
				noteType = noteStruct[0]
				
				if noteType not in noteTypes:
					if debug:
						debugPrint("")
					debugPrint("Error: Unknown note type '{0}' at offset {1}".format(
						shortHex(noteType).upper(),
						hex(file.tell() - 0x18))
					)
					break
				
				note["type"] = noteTypes[noteType]
				note["type_num"] = noteStruct[0]
				note["pos"] = noteStruct[1]
				
				if noteType == 0xa or noteType == 0xc:
					# Balloon hits
					note["hits"] = noteStruct[4]
				elif "scoreInit" not in song:
					song["scoreInit"] = noteStruct[4]
					song["scoreDiff"] = noteStruct[5] / 4.0
				
				if noteType == 0x6 or noteType == 0x9 or noteType == 0xa or noteType == 0xc:
					# Drumroll and balloon duration in ms
					note["duration"] = noteStruct[6]
				branch[noteNumber] = note
				
				if debug:
					debugPrint(" ({0})".format(nameValue(note)))
				
				if noteType == 0x6 or noteType == 0x9 or noteType == 0x62:
					# Drumrolls have 8 dummy bytes at the end
					file.seek(0x8, os.SEEK_CUR)
			
			branch["length"] = totalNotes
			measure[branchNames[branchNumber]] = branch
		
		song[measureNumber] = measure
		if file.tell() >= size:
			break
	
	song["length"] = totalMeasures
	
	file.close()
	return song

def shortHex(number):
	return hex(number)[2:]

def getBool(number):
	return True if number == 0x1 else False if number == 0x0 else number

def nameValue(*lists):
	string = []
	for list in lists:
		for name in list:
			if name == "type":
				string.append(list[name])
			elif name != "length" and type(name) is not int:
				value = list[name]
				if type(value) == float and value % 1 == 0.0:
					value = int(value)
				string.append("{0}: {1}".format(name, value))
	return ", ".join(string)

def debugPrint(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)
	
def calculateShinUtiGen3(song):
	DonKas = 0
	BigDonKas = 0
	BaloonsTotal = 0
	BaloonsHits = 0

	if song["branches"] == True:
		totalnotes = {
			branchNames[0]: 0,
      		branchNames[1]: 0,
      		branchNames[2]: 0,
		}

		for i in range(song["length"]):
			for j in range(3):
				slBranch = branchNames[j]
				branch = song[i][slBranch]
				for j in range(branch["length"]):
					note = branch[j]
					noteType = note["type"]
					if noteType == "Don" or noteType == "Ka" or noteType == "DON" or noteType == "KA":
						totalnotes[slBranch] += 1

		selectedBranch = max(totalnotes, key=totalnotes.get)
	else:
		selectedBranch = branchNames[0]
	
	for i in range(song["length"]):
		measure = song[i]
		branch = measure[selectedBranch]
		for j in range(branch["length"]):
			note = branch[j]
			noteType = note["type"]
			if noteType == "Don" or noteType == "Ka":
				DonKas += 1
			elif noteType == "DON" or noteType == "KA":
				BigDonKas += 1
			elif noteType == "Balloon" or noteType == "Kusudama":
				BaloonsTotal += 1
				BaloonsHits += note["hits"]
			#elif noteType == "Drumroll" or noteType == "DRUMROLL":
			# 	BaloonsHits += 1
	
	score = 1000000
	score -= (BaloonsTotal * 5000) + (BaloonsHits * 300)
	score /= (DonKas + (BigDonKas * 2))

	score = round(score / 10.0) * 10
	return score

def listNotes(song, slb):
	a = 0
	notes = {}

	for i in range(song["length"]):
		measure = song[i]
		branch = measure[branchNames[slb]]
		for j in range(branch["length"]):
			note = {}
			basenote = branch[j]
			note["type"] = basenote["type_num"]
			note["offset"] = basenote["pos"] + measure["offset"]
			if "duration" in basenote:
				note["length"] = basenote["duration"]
			else:
				note["length"] = 0
			if "hits" in basenote:
				note["hits"] = basenote["hits"]
			else:
				note["hits"] = 0
			note["timing1"] = song["timingwindow"][0]
			note["timing2"] = song["timingwindow"][1]
			note["timing3"] = song["timingwindow"][2]

			notes[a] = note
			a += 1
	
	notes['size'] = a
	return notes

def findModeBPM(song):
	bpms = []
	for i in range(song["length"]):
		measure = song[i]
		bpms.append(measure["bpm"])
	mode = statistics.mode(bpms)
	return mode
