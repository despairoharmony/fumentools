import os, struct, io, csv, acb, fumen
from tkinter import messagebox
from tkinter.filedialog import askdirectory

branchNamesJP = ("普通", "玄人", "達人")

def convert_to_hex_string(note):
    # Packing the data
    # A and B are integers (4 bytes each)
    # C, D, E, F, G are floats (4 bytes each)
    # H is an integer (4 bytes)
    hex_string = (
        struct.pack('<I', note["type"]) +       # A (4 bytes, little-endian unsigned int)
        struct.pack('<I', note["type"]) +       # B (4 bytes, little-endian unsigned int)
        struct.pack('<f', note["offset"]) +     # C (4 bytes, little-endian float)
        struct.pack('<f', note["length"]) +     # D (4 bytes, little-endian float)
        struct.pack('<f', note["timing1"]) +    # E (4 bytes, little-endian float)
        struct.pack('<f', note["timing2"]) +    # F (4 bytes, little-endian float)
        struct.pack('<f', note["timing3"]) +    # G (4 bytes, little-endian float)
        struct.pack('<I', note["hits"])         # H (4 bytes, little-endian unsigned int)
    )
    
    # Convert to hex and format the string
    hex_string = hex_string.hex().upper() + "/"
    return hex_string

def extract_audiotime(id, path):
	soundpath = path + '/Sound/song/SONG_' + id.upper() + '.acb' 
	r = open(soundpath, "rb")
	utf = acb.UTFTable(r)
	cue_handle = io.BytesIO(utf.rows[0]["CueTable"])
	cues = acb.UTFTable(cue_handle)
	length = cues.rows[0]["Length"]

	return length

def gen_csv_line(id, note, difficulty, branch, time, bpm, uniqueid):
	div = 5

	fraction = time / div

	startimebox = []
	endtimebox = []
	notecount = []
	hexstring = []

	for i in range(div):
		startimebox_i = fraction * (i)
		endtimebox_i = fraction * (i + 1)
		notecount_i = 0
		hexstring_i = ""
		for j in range(note["size"]):
			if note[j]["offset"] >= startimebox_i and note[j]["offset"] < endtimebox_i:
				notecount_i += 1
				hexstring_i = hexstring_i + convert_to_hex_string(note[j])
		
		startimebox.append(startimebox_i)
		endtimebox.append(endtimebox_i)
		notecount.append(notecount_i)
		hexstring.append(hexstring_i)


	data = [
    	uniqueid, id, branchNamesJP[branch], difficulty, div,
        f'時間: {(endtimebox[0]/1000):.5f} 音符数: {notecount[0]}', 
		f'時間: {(endtimebox[1]/1000):.5f} 音符数: {notecount[1]}', 
		f'時間: {(endtimebox[2]/1000):.5f} 音符数: {notecount[2]}', 
        f'時間: {(endtimebox[3]/1000):.5f} 音符数: {notecount[3]}', 
		f'時間: {(endtimebox[4]/1000):.5f} 音符数: {notecount[4]}', 
		"", "", "", "", "",
        f"変化値: {bpm:.0f} 時間: 0", "", "", "", "", 
		hexstring[0], hexstring[1], hexstring[2], hexstring[3], hexstring[4],
		"", "", "", "", ""
    ]

	return data

strutura = [
    ["_e.bin", "かんたん"],
    ["_n.bin", "ふつう"],
    ["_h.bin", "難しい"],
    ["_m.bin", "鬼"],
    ["_x.bin", "裏鬼"]
]

header = [
        "ID", "名前", "分岐", "難易度", "分割数", 
        "チャプター1", "チャプター2", "チャプター3", "チャプター4", "チャプター5", 
        "チャプター6", "チャプター7", "チャプター8", "チャプター9", "チャプター10", 
        "BPM変化1", "BPM変化2", "BPM変化3", "BPM変化4", "BPM変化5", 
        "音符データ1", "音符データ2", "音符データ3", "音符データ4", "音符データ5", 
        "音符データ6", "音符データ7", "音符データ8", "音符データ9", "音符データ10"
    ]

path = askdirectory(title='Select "StreamingAssets" Folder')

fumenpath = path + '/fumen'
csvpath = path + '/csv'
if os.path.exists(fumenpath):
	files = [f for f in os.listdir(fumenpath) if os.path.isdir(fumenpath + '/' + f)]
	if not os.path.exists(csvpath):
		os.mkdir(csvpath)

	for f in files:
		print(f"[ID: {f}] Generating CSV")
		songlength = extract_audiotime(f, path)
		database = []
		cont = 1

		isUra = os.path.exists(fumenpath + '/' + f + '/' + f + strutura[4][0])
		step = 5 if isUra else 4

		try:
			for g in strutura:
				fullpath = fumenpath + '/' + f + '/' + f + g[0]
				if os.path.exists(fullpath):
					song = fumen.readFumen(fullpath)
					if song != False:
						bpm = fumen.findModeBPM(song)
						if song["branches"] == True:
							note1 = fumen.listNotes(song, 0)
							data1 = gen_csv_line(f, note1, g[1], 0, songlength, bpm, cont)
							note2 = fumen.listNotes(song, 1)
							data2 = gen_csv_line(f, note2, g[1], 1, songlength, bpm, cont + step)
							note3 = fumen.listNotes(song, 2)
							data3 = gen_csv_line(f, note3, g[1], 2, songlength, bpm, cont + (step * 2))

							database.append(data1)
							database.append(data2)
							database.append(data3)
						else:
							notes = fumen.listNotes(song, 0)
							data1 = gen_csv_line(f, notes, g[1], 0, songlength, bpm, cont)
							data2 = gen_csv_line(f, notes, g[1], 1, songlength, bpm, cont + step)
							data3 = gen_csv_line(f, notes, g[1], 2, songlength, bpm, cont + (step * 2))

							database.append(data1)
							database.append(data2)
							database.append(data3)

						cont += 1

					else:
						print(f"[ID: {f}] Could not proccess: {fullpath}")
			database.sort()
			csvfilename = csvpath + '/' + f + ".csv"
			# Write the data to the CSV file
			with open(csvfilename, mode='w', newline='', encoding='utf-8') as file:
				writer = csv.writer(file)
	
    	    	# Write the header
				writer.writerow(header)
	
    	    	# Write the data rows
				writer.writerows(database)
		except Exception as e:
			print(f"[ID: {f}] An error occurred: {e}")
	messagebox.showinfo(title="FumenTools", message="All CSV from fumen generated with success!")
else:
	messagebox.showerror(title="FumenTools", message="Couldn't find fumen folder to proccess.")


	
	