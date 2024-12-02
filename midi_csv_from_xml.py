import base64, verovio, os, json
from lxml import etree

tk = verovio.toolkit()

tk.setOptions({"inputFrom": "pae"})

context = etree.iterparse("/home/steven/rism_240119.xml", events=("start", "end"))

songlist = {}

songinfo = {
    "clef": "",
    "keysig": "",
    "timesig": "",
    "data": ""
}

songid = ""

hasincip = False
incipcnt = 0

total = 0

statcnt = {}

csvf = open("G-2__c_v2.csv", "w")

csvf.write("wav_filename,wav_filesize,transcript\n")

try:
    for event, elem in context:
        if event == "start":
            pass
            # print("START", elem.tag)
        elif event == "end":
            if elem.tag == "{http://www.loc.gov/MARC21/slim}controlfield" and elem.attrib["tag"] == "001":
                songid = elem.text
            elif (elem.tag == "{http://www.loc.gov/MARC21/slim}record"):
                for subel in elem:
                    # print(subel.tag, subel.text)
                    if subel.tag == "{http://www.loc.gov/MARC21/slim}datafield":
                        innertype = subel.attrib["tag"]
                        if innertype == "031":
                            hasincip = False
                            for subsubel in subel:
                                inner2tag = subsubel.attrib["code"]
                                if inner2tag == "g":
                                    songinfo["clef"] = subsubel.text
                                    hasincip = True
                                elif inner2tag == "n":
                                    songinfo["keysig"] = subsubel.text
                                    hasincip = True
                                elif inner2tag == "o":
                                    songinfo["timesig"] = subsubel.text
                                    # hasincip = True # entries with only time signature are useless here
                                elif inner2tag == "p":
                                    songinfo["data"] = subsubel.text
                                    hasincip = True
                                # print(subsubel.tag, subsubel.text)
                            if hasincip and songinfo["timesig"] and (songinfo["timesig"] == "c" or songinfo["timesig"] == "4/4") and songinfo["keysig"] == "" and songinfo["clef"] == "G-2" and songinfo["data"]:
                                total += 1
                                
                                tk.loadData(json.dumps(songinfo))

                                o = tk.renderToMIDI()

                                open("/mnt/tmpfs570/out.mid", "wb").write(base64.b64decode(o))

                                os.system("fluidsynth -ni MuseScore_General.sf2 /mnt/tmpfs570/out.mid -F /mnt/tmpfs570/out.wav -r 16000")
                                os.system("ffmpeg -i /mnt/tmpfs570/out.wav -filter:a \"volume=8.0\" -ac 1 output_G-2__c_v2/"+songid+"_"+str(incipcnt)+".wav")
                                outfsize = os.path.getsize("output_G-2__c_v2/"+songid+"_"+str(incipcnt)+".wav")
                                csvf.write("/home/steven/College/Senior Fall 2024/cse570/music_transcribe/output_G-2__c_v2/"+songid+"_"+str(incipcnt)+".wav,"+str(outfsize)+",\""+songinfo["data"]+"\"\n")
                                incipcnt += 1
                            # if hasincip and songinfo["timesig"] and songinfo["data"]:
                            #     total += 1
                            #     if songinfo["clef"] == None:
                            #         songinfo["clef"] = ""
                            #     if songinfo["keysig"] == None:
                            #         songinfo["keysig"] = ""
                            #     if songinfo["timesig"] == None:
                            #         songinfo["timesig"] = ""
                            #     elif songinfo["timesig"] == "4/4":
                            #         songinfo["timesig"] = "c"
                            #     elif songinfo["timesig"] == "2/2":
                            #         songinfo["timesign"] = "c/"
                            #     statstr = songinfo["clef"]+"_"+songinfo["keysig"]+"_"+songinfo["timesig"]
                            #     try:
                            #         statcnt[statstr] += 1
                            #     except:
                            #         statcnt[statstr] = 1
                            songinfo = {
                                "clef": "",
                                "keysig": "",
                                "timesig": "",
                                "data": ""
                            }
                incipcnt = 0
                hasincip = False
                elem.clear()
                songid = ""
except etree.XMLSyntaxError as e:
    print("xml parser error")

print(total)
ds = {k: v for k, v in sorted(statcnt.items(), key=lambda item: item[1])}
print(ds)