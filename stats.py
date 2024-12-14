original = "{,6G3AB}/'4C--8-{,6G3AB}/'4C--8-{,6G3AB}/'4C-2-/"
generated = "{'6.G,3AB}'4.C{6.G,3AB'6.C}''4C{'6.G,3AB}'4.C"

notes = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
octave = ['\'', ',']
timing = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

def parsePAE(pae):
    letters = []
    timings = []

    currOctave = ''
    gettingOctave = False
    currTiming = None
    nextDot = False
    for c in pae:
        if c in octave:
            if gettingOctave == False:
                currOctave = ''

            currOctave += c
            gettingOctave = True
        
        elif gettingOctave:
            gettingOctave = False
        
        if c in timing:
            currTiming = int(c)
        
        elif c == '.':
            nextDot = True
        
        elif c in notes:
            letters.append(c + currOctave + str(currTiming))
            if nextDot:
                nextDot = False
                timings.append(currTiming + 0.5) # Point of contention - dots
            else:
                timings.append(currTiming)
        
            
    return (letters, timings)

def comparePAE(orig, new):
    notesOrig, timesOrig = parsePAE(orig)
    notesNew, timesNew = parsePAE(new)

    return (percentDiff(notesOrig, notesNew), percentDiff(timesOrig, timesNew))

def percentDiff(orig, new):
    from collections import Counter

    orig = Counter(orig)
    new = Counter(new)

    origCount = 0
    newCount = 0
    for key in orig.keys():
        n = 0
        if key in new:
            n = new[key]
        
        origCount += orig[key]
        newCount += n
    
    return abs(origCount - newCount) / origCount * 100

import pandas as pd
import numpy as np

df = pd.read_csv('incipit_pairs.csv')

notesError = []
timingError = []
for i, row in df.iterrows():
    noteerror, timingerror = comparePAE(row['original_pae'], row['generated_pae'])

    notesError.append(noteerror)
    timingError.append(timingerror)

notesError = np.array(notesError)
timingError = np.array(timingError)

print('Avg Note Error:', np.average(notesError))
print('Median Note Error:', np.median(notesError))
print('Avg Timing Error:', np.average(timingError))
print('Median Timing Error:', np.median(timingError))
# print(len(ids), len(origs), len(gens))

# data = {'id': ids, 'original_pae': origs, 'generated_pae': gens}
# df = pd.DataFrame(data)

# print(df)