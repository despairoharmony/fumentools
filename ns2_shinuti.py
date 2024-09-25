import os, json, fumen
from tkinter import messagebox
from tkinter.filedialog import askdirectory

strutura = [
    ["_e.bin", "shinutiEasy"],
    ["_n.bin", "shinutiNormal"],
    ["_h.bin", "shinutiHard"],
    ["_m.bin", "shinutiMania"],
    ["_x.bin", "shinutiUra"],
    ["_e_1.bin", "shinutiEasyDuet"],
    ["_n_1.bin", "shinutiNormalDuet"],
    ["_h_1.bin", "shinutiHardDuet"],
    ["_m_1.bin", "shinutiManiaDuet"],
    ["_x_1.bin", "shinutiUraDuet"]
]

path = askdirectory(title='Select "StreamingAssets" Folder')

fumenpath = path + '/fumen'

if os.path.exists(fumenpath):
    files = [f for f in os.listdir(fumenpath) if os.path.isdir(fumenpath + '/' + f)]

    maindata = {"items": []}

    for f in files:
        data = {
            "id": f,
            "shinutiEasy": 1000,
              "shinutiNormal": 1000,
              "shinutiHard": 1000,
              "shinutiMania": 1000,
              "shinutiUra": 1000,
              "shinutiEasyDuet": 1000,
              "shinutiNormalDuet": 1000,
              "shinutiHardDuet": 1000,
              "shinutiManiaDuet": 1000,
              "shinutiUraDuet": 1000
        }

        try:
            isadd = True
            for g in strutura:
                fullpath = fumenpath + '/' + f + '/' + f + g[0]
                if os.path.exists(fullpath):
                    song = fumen.readFumen(fullpath)
                    if song != False:
                        score = fumen.calculateShinUtiGen3(song)
                        data[g[1]] = score
                    else:
                        isadd = False
                        print(f"[ID: {f}] Could not proccess: {fullpath}")
            if isadd:
                maindata["items"].append(data)
        except Exception as e:
            print(f"[ID: {f}] An error occurred: {e}")
    
    out = path + '/musicdata.json'
    with open(out, 'w') as file:
        json.dump(maindata, file, indent=4)
    
    messagebox.showinfo(title="FumenTools", message="Shinuti calculated and saved at musicdata.json")
else:
    messagebox.showerror(title="FumenTools", message="Couldn't find fumen folder to proccess.")
