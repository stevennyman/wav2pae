import verovio, base64, os

tk = verovio.toolkit()

tk.setOptions({"inputFrom": "pae"})

dest = input("Enter destination file name (without extension): ")

tk.loadData('''{
    "clef": "G-2",
    "keysig": "",
    "timesig": "4/4",
    "data": "'''+input("Enter PAE data: ")+'''"
}'''
)                           

o = tk.renderToMIDI()

open("tmp.mid", "wb").write(base64.b64decode(o))

os.system("fluidsynth -ni MuseScore_General.sf2 tmp.mid -F tmp.wav -r 16000")
os.system("ffmpeg -i tmp.wav -filter:a \"volume=8.0\" -ac 1 "+dest+".wav")