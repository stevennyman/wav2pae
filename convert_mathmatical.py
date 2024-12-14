# strategy: bpm doesn't matter here, they're all the same
# use note proportions to create the encoding in

# pitches repeat (with ') to indicate octaves

# repetitions of the same note would be difficult
# repeated notes are difficult to identify

# rests would be difficult to support, maybe need to implement decibel tracking

# count for measure division

# pick up measures unsupported

# in this sample, 40 is 1 measure

# 5 392.0 10 523.25 10 587.33 3 659.26 2 523.25 10 783.99 5 493.88 10 523.25 10 587.33 3 659.26 2 523.25 10 783.99 5 493.88 10 523.25 10 587.33 10 659.26 	'8G/''4CDt{6EC}4G'8B/''4CD{6EC}4G'8B/''4CDEF/

# todo: fix .00? nope

# fix missing last character
# notes right after each other

import json, verovio, os

from pitch_file_pair_convert_number import mainloop

from multiprocessing import Process


from tempfile import TemporaryDirectory
tmpd = TemporaryDirectory()

logfile = open("convert_log.txt", "a")

SOURCE_CSV = "G-2__c_v3.csv"
WAV_BASE = "output_G-2__c_v4/"
measure_length = 160

DETECT_RESTS = False
DETECT_MEASURES = False # doesn't work with pickup notes
DO_POSTPROCESS = True
USE_COMPARABLE = True

SVG_NO_POPUP = True

nflist = json.load(open("pitch_to_note.json", "r"))

def displayPAE(outs, title, y=None):
    displayPAE_inner(outs, title, y)
    # mythread = Process(target=displayPAE_inner, args=(outs,title,y))
    # mythread.start()

def displayPAE_inner(outs, title, y=None):
    tk = verovio.toolkit()

    tk.setOptions({"inputFrom": "pae"})

    tk.loadData('''{
        "clef": "G-2",
        "keysig": "",
        "timesig": "4/4",
        "data": "'''+outs+'''"
    }'''
    )

    if SVG_NO_POPUP:
        o = tk.renderToSVGFile("out_"+title+".svg")
        # os.system("pythonw.exe view_pae.py "+title+" out_"+title+".svg")
        return

    o = tk.renderToSVG()

    html_content = f"""
    <html>
        <body>
            {o}
        </body>
    </html>
    """

    import webview
    webview.create_window(title, html=html_content, width=1400, y=y)
    webview.start()

def mainloop_convert(songid):
    if USE_COMPARABLE:
        # get the song from pitchmap, load its file and show the original incipit
        songid = str(songid).zfill(9)
        if "_" not in songid:
            if ".wav" in songid:
                songid = songid.replace(".wav", "_0.wav")
            else:
                songid = songid + "_0.wav"
        
        if ".wav" not in songid:
            songid = songid + ".wav"
        
        found_csv = False

        for line in open(SOURCE_CSV, "r"):
            if line.startswith(songid+","):
                original_incipit = line.split(",", 2)[-1].replace('"', '')
                print("\nORIGINAL INCIPIT:", original_incipit)
                found_csv = True
                displayPAE(original_incipit, "Original", y=0)
                

        if not found_csv:
            print("FAILED to find ID")
            return

    BAR_ELIGIBLE_SYMBOLS = "86357"

    # Section 4.2 of PAE spec
    symbols = {
        measure_length/1: "1",
        (measure_length/2)*1.5: "2.",
        measure_length/2: "2",
        (measure_length/4)*1.5: "4.",
        measure_length/4: "4",
        (measure_length/8)*1.5: "8.",
        measure_length/8: "8",
        (measure_length/16)*1.5: "6.",
        measure_length/16: "6", # this is where it starts getting weird
        (measure_length/32)*1.5: "3.", # this is the lowest the current setup can likely resolve?
        measure_length/32: "3",
        # measure_length/64: "5", # 0.3% of sample data
        # measure_length/128: "7" # 0.02% of sample data; disabled because they happen extremely rarely in music
    }

    def normalize_symlen(symlen):
        prevval = measure_length
        for v in reversed(symbols.keys()):
            if v >= symlen:
                if abs(symlen-prevval) < v-symlen:
                    return symbols[prevval], prevval
                else:
                    return symbols[v], v
            prevval = v
        return symbols[measure_length/1], measure_length

    # also need to support ".", which multiplies the pitch by 1.5. Up to ".." is common in sample data, with a few occurrences of "...".

    # input_str = "5 392.0 10 523.25 10 587.33 3 659.26 2 523.25 10 783.99 5 493.88 10 523.25 10 587.33 3 659.26 2 523.25 10 783.99 5 493.88 10 523.25 10 587.33 10 659.26"
    # desired output: '8G/''4CDt{6EC}4G'8B/''4CD{6EC}4G'8B/''4CDEF/

    #input_str = "3 523.25 2 392.0 3 440.0 2 493.88 3 523.25 2 587.33 3 659.26 2 587.33 15 523.25 5 783.99 5 523.25 3 659.26 2 587.33 3 523.25 2 659.26 3 587.33 14 523.25"
    # desired output: {''6C'GAB}{''CDED}8C4C8G/!{C6ED}!f8C4C8E

    songpath = songid
    if USE_COMPARABLE:
        songpath = WAV_BASE+songid

    input_str = mainloop(songpath, tmpd, measure_length, detect_rests=DETECT_RESTS, do_postprocess=DO_POSTPROCESS)

    # input_str = "6 - 17 392.0 7 - 9 246.94 13 261.63 3 523.25 17 261.63 87 - 16 392.0 7 - 9 246.94 14 261.63 3 523.25 18 261.63 87 - 15 392.0 8 - 8 246.94 15 261.63 3 523.25 17 261.63 "

    input_str_mod = input_str

    current_symbol = ""
    current_octave = ""

    outs = ""

    measure_total = 0

    unclosed_bracket = False
    bracket_total = 0

    while input_str_mod:
        input_str_mod_tmp = input_str_mod.split(" ", 1)
        lencode = int(input_str_mod_tmp[0])
        input_str_mod = input_str_mod_tmp[1]
        input_str_mod_tmp = input_str_mod.split(" ", 1)
        pitchcode = input_str_mod_tmp[0] # no type conversion here
        if len(input_str_mod_tmp) == 2:
            input_str_mod = input_str_mod_tmp[1]
        else:
            input_str_mod = ""

        add_sym = False

        # match the lencode to the symbol
        symtmp, symval = normalize_symlen(lencode)
        measure_total += symval #lencode
        presym = ""
        if symtmp[0] in BAR_ELIGIBLE_SYMBOLS:
            bracket_total += 1
        if symtmp != current_symbol:
            if (symtmp[0] in BAR_ELIGIBLE_SYMBOLS) and ((current_symbol and (current_symbol[0] not in BAR_ELIGIBLE_SYMBOLS)) or not current_symbol):
                presym = "{"
                unclosed_bracket = True
            elif (symtmp[0] not in BAR_ELIGIBLE_SYMBOLS) and current_symbol and (current_symbol[0] in BAR_ELIGIBLE_SYMBOLS):
                presym = "}"
                unclosed_bracket = False
                if bracket_total == 1:
                    outs = "".join(outs.rsplit("{", 1))
                    presym = ""
                bracket_total = 0
            current_symbol = symtmp
            add_sym = True
        
        add_octave = ""

        if pitchcode != "-":
            pitchtmp, octtmp = nflist[pitchcode]
            if current_octave != octtmp:
                add_octave = octtmp
                current_octave = octtmp
        else:
            pitchtmp = "-"

        if add_sym:
            outs += str(presym)+str(add_octave)+str(current_symbol)
        elif add_octave:
            outs += str(add_octave)

        outs += pitchtmp

        if measure_total == measure_length:
            measure_total = 0
            if DETECT_MEASURES:
                if unclosed_bracket:
                    outs += "}"
                outs += "/"
                if unclosed_bracket:
                    outs += "{"

    if unclosed_bracket:
        outs += "}"

    outs = outs.replace("{}", "")

    print("GENERATED INCIPIT:", outs)
    displayPAE(outs, "Result", y=600)

import sys
from record import recordSample
import subprocess

if __name__ == "__main__":
    sampled = False
    if len(sys.argv) > 1 and sys.argv[1] == '-R':
        recordSample('recordedSample.wav')
        USE_COMPARABLE = not USE_COMPARABLE

        # Run sox
        subprocess.run(["sox", "recordedSample.wav", "recordSampleShortened.wav" , "silence", "-l", "1", "0.1", "0.5%", "-1", "0.1", "0.5%"])

        mainloop_convert('recordSampleShortened.wav')

        sys.exit(0)

    try:
        while True:
            print("Detect [R]ests: "+str(DETECT_RESTS)+", Detect [M]easures: "+str(DETECT_MEASURES)+", Do [P]ost-processing: "+str(DO_POSTPROCESS)+", Use [C]ompareable: "+str(USE_COMPARABLE))
            userinput = input("Input song id: ")
            luserinput = userinput.lower()
            if luserinput == "r":
                DETECT_RESTS = not DETECT_RESTS
            elif luserinput == "m":
                DETECT_MEASURES = not DETECT_MEASURES
            elif luserinput == "p":
                DO_POSTPROCESS = not DO_POSTPROCESS
            elif luserinput == "c":
                USE_COMPARABLE = not USE_COMPARABLE
            elif luserinput == "q" or luserinput == "x":
                break
            else:
                mainloop_convert(userinput)
            logfile.write(userinput+"\n")
    except:
        tmpd.cleanup()
        logfile.close()
        raise

    tmpd.cleanup()
    logfile.close()
