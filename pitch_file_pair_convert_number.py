import scipy.io.wavfile as wavfile
import scipy
import numpy as np
import json
from os import system

nflist = json.load(open("notes-frequencies.json", "r"))
pilist = json.load(open("pitch_to_note.json", "r"))
nfvalues = list(nflist.values())
pikeys = list(pilist.keys())

JUMP_THRESHOLD_REPEATED_NOTE = 200000

def normalize_freq(freq):
    if (freq == "-"):
        return "-"
    if (freq == 0):
        return 0
    prevval = 16.35
    for v in nfvalues:
        if v >= freq:
            if freq-prevval < v-freq:
                return prevval
            else:
                return v
        prevval = v
    return 0

def mainloop(desfile, tmpd, measure_length, detect_rests=False, do_postprocess=True):
    # y, samplerate = librosa.load(desfile, sr=None)
    # data = librosa.effects.time_stretch(y, rate=0.25)
    # data = np.int16(data / np.max(np.abs(data)) * 32767)
    # samplerate, data = wavfile.read('/mnt/F4BAF3A5BAF36292/Steven/College Archive/Senior Fall 2024/cse570/output_G-2__c_v3/'+desfile)
    outloc = tmpd.name+desfile.split("/")[-1].replace(".wav", "_slow25.wav")
    system('ffmpeg -y -i "'+desfile+'" -filter:a "atempo=0.5,atempo=0.5" "'+outloc+'"')
    samplerate, data = wavfile.read(outloc)
    #samplerate, data = wavfile.read('/home/steven/College/Senior Fall 2024/cse570/music_transcribe/sampleaudio_slow/000100477_0_slow25.wav')
    # samplerate, data = wavfile.read('/mnt/F4BAF3A5BAF36292/Steven/College Archive/Senior Fall 2024/cse570/output_G-2__c_v3/000100477_0.wav')
    # samplerate, data = wavfile.read('/home/steven/College/Senior Fall 2024/cse570/music_transcribe/sampleaudio_v3/000100338_0.wav')

    chunk_duration_ms = 50
    samples_per_chunk = int(samplerate * chunk_duration_ms / 1000)

    chunks = [data[i:i + samples_per_chunk] for i in range(0, len(data), samples_per_chunk)]
    # chunks.append(np.ndarray((0,))) # add fake chunk to end to ensure last note is counted

    # max_merge_eligible = (measure_length/8)+(measure_length/8/2)

    outd = []
    outdb = []
    outdbb = []

    outl = []
    outs = ""

    current = 0
    currentcnt = 0

    currentb = 0
    currentcntb = 0

    lastintensity = 0

    was_decreasing = 0
    was_decreasing_prev = 0

    chunkcnt = 0
    for chunk in chunks:
        padded_chunk = np.pad(chunk, (0, 4800 - len(chunk)), 'constant')
        fft_spectrum = scipy.fft.rfft(padded_chunk)
        freqs = scipy.fft.fftfreq(len(padded_chunk), 1/samplerate)
        absarr = np.abs(fft_spectrum)
        maxind = np.argmax(absarr)
        print(maxind, normalize_freq(freqs[maxind]), freqs[maxind], absarr[maxind])
        curintensity = absarr[maxind]
        dominant_freq = freqs[maxind]
        if dominant_freq == 0:
            dominant_freq = "-"
        if detect_rests and curintensity < 300000 and ((curintensity <= (lastintensity)) or (current == "-")):
            dominant_freq = "-"
        # TODO consider looking at other peaks as well to find other potential dominant frequencies
        if dominant_freq != current or ((curintensity > (lastintensity+JUMP_THRESHOLD_REPEATED_NOTE)) and (was_decreasing > 1)): # or was_decreasing_prev > 3)): # and currentcntb > 8): # or (curintensity > (lastintensity+900000)):
            outdb.append((current, currentcnt))
            current = dominant_freq
            currentcnt = 0
        converted_freq = normalize_freq(dominant_freq)
        if converted_freq != currentb or chunkcnt == (len(chunks)-1) or ((curintensity > (lastintensity+JUMP_THRESHOLD_REPEATED_NOTE)) and (was_decreasing > 1)): # or was_decreasing_prev > 3)): # and currentcntb > 8): # or (curintensity > (lastintensity+900000)):
            outdbb.append((currentb, currentcntb))
            if (currentcntb != 0):
                force_reset = currentcntb > (((measure_length/8)*1.5)) and (curintensity > (lastintensity+JUMP_THRESHOLD_REPEATED_NOTE)) and (was_decreasing > 1)
                outl.append((currentcntb, currentb, curintensity, force_reset))
                outs += str(currentcntb) + " " + str(currentb) + " " # outs is deprecated
            currentb = converted_freq
            currentcntb = 0
        # was_decreasing_prev = was_decreasing
        if curintensity < lastintensity:
            was_decreasing += 1
        else:
            was_decreasing_prev = was_decreasing
            was_decreasing = 0
        # was_decreasing = curintensity < lastintensity
        lastintensity = curintensity
        currentcnt += 1
        currentcntb += 1
        chunkcnt += 1
        outd.append(dominant_freq)
        

    outdb.append((current, currentcnt))
    outdbb.append((currentb, currentcntb))

    print()
    print(outs)
    if not do_postprocess:
        return outs
    print()

    # normalize output (doing it now does cause us to lose access to the other frequencies)
    outs_new = ""
    merge_eligible_notes = []
    merge_eligible_notes_prev = []

    mergeable_set = []
    
    indlist = [12, -12] #[-1, 1, 11, 12, 13, -11, -12, -13]

    print("===============")


    outlcnt = 0
    while outlcnt < len(outl):
        lencode = outl[outlcnt][0]
        pitchcode = str(outl[outlcnt][1])
        force_reset = outl[outlcnt][3]

        print(lencode, pitchcode)

        while_ran = False

        # merge 1 frame with next if a half step above/below other (accidental/sharp)
        while outlcnt != len(outl)-1 and outl[outlcnt+1][1] != "-" and pitchcode != "-" and abs(pikeys.index(str(outl[outlcnt+1][1])) - pikeys.index(pitchcode)) == 1:
            while_ran = True
            do_cont = False
            if pilist[str(outl[outlcnt+1][1])][0][0] == "x": # and outl[outlcnt+1][1] < 4:
                outl[outlcnt+1] = (outl[outlcnt+1][0]+ outl[outlcnt][0], outl[outlcnt][1], outl[outlcnt][2], outl[outlcnt][3])
                # continue
                do_cont = True
            elif pilist[pitchcode][0][0] == "x": # and lencode < 4:
                outl[outlcnt+1] = (outl[outlcnt+1][0]+ outl[outlcnt][0], outl[outlcnt+1][1], outl[outlcnt][2], outl[outlcnt][3])
                # continue
                do_cont = True
            
            if do_cont:
                # continue
                outl.pop(outlcnt)
                # outlcnt -= 1
                # if a merge has been performed, possibly update the length of a previous value in outs
                # TODO: was_decreasing check not replicated here
                if outl[outlcnt-1][1] == outl[outlcnt][1]: # and outl[outlcnt][2] <= (outl[outlcnt-1][2]+JUMP_THRESHOLD_REPEATED_NOTE):
                    outl[outlcnt-1] = (outl[outlcnt-1][0]+ outl[outlcnt][0], outl[outlcnt-1][1], outl[outlcnt-1][2], outl[outlcnt-1][3])
                    outl.pop(outlcnt)
                    # outlcnt -= 1
                    outstmpl = outs_new.rsplit(" ", 3)
                    outs_new = outstmpl[0] + " " + str(outl[outlcnt][0]) + " " + outstmpl[-2] + " "
                lencode = outl[outlcnt][0]
                pitchcode = str(outl[outlcnt][1])
                force_reset = outl[outlcnt][3]

            outlcnt += 1

        if while_ran:
            outlcnt -= 1

        merge_eligible_notes_prev = merge_eligible_notes
        merge_eligible_notes = []

        if pitchcode != "-":
            pitchindex = pikeys.index(str(pitchcode))
            for ind in indlist:
                merge_eligible_notes.append(pikeys[pitchindex+ind])
            merge_eligible_notes.append(pikeys[pitchindex])
        
        must_do_merge = False

        # TODO FIX THESE NEXT TWO (THREE) CONDITIONALS

        merge_len_eligible = lencode > (((measure_length/8)*1.5))
        for item in mergeable_set:
            if item[0] > (((measure_length/8)*1.5)):
                merge_len_eligible = True

        did_append = False
        if (pitchcode in merge_eligible_notes_prev or merge_eligible_notes_prev == []) and (merge_len_eligible or lencode < 7):
            mergeable_set.append((lencode, pitchcode))
            did_append = True

        # if merge_len_eligible:
        #     must_do_merge = True

        # force a merge completion if would normally be an intensity division
        if force_reset:
            if did_append:
                mergeable_set.pop()
                did_append = False
            must_do_merge = True

        if merge_eligible_notes != merge_eligible_notes_prev or outlcnt == len(outl)-1 or must_do_merge:
            # rescan mergeable set, if there is a note in there that isn't merge eligible, begin the merge process
            # and clear or trim the mergeable set
            
            # pick the lowest frequency
            total = 0


            if outlcnt == len(outl)-1:
                must_do_merge = True

            if len(mergeable_set) >= 1 and (outlcnt < len(outl)-2 and pitchcode == outl[outlcnt+1][1]):
                # mergeable_set.pop()
                must_do_merge = True

            for lc, pc in mergeable_set:
                if pc not in merge_eligible_notes:
                    must_do_merge = True

            if must_do_merge:
                if mergeable_set:
                    minpc = mergeable_set[0][1]
                else:
                    minpc = 0
                for lc, pc in mergeable_set:
                    total += lc
                    if minpc != "-" and float(pc) < float(minpc):
                        minpc = pc
                if minpc != 0:
                    outs_new += str(total) + " " + str(minpc) + " "
                mergeable_set = []

        if did_append == False:# ((pitchcode not in merge_eligible_notes_prev and merge_eligible_notes_prev != []) and (merge_len_eligible or lencode < 7)) or mergeable_set == []:
           mergeable_set.append((int(lencode), pitchcode))
           if outlcnt == len(outl) - 1:
               outs_new += str(lencode) + " " + str(pitchcode)
        
        outlcnt += 1


    print(outs_new)

    return outs_new
