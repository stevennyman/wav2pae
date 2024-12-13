import pandas as pd

# df = pd.read_csv('G-2__c_v3.csv')
# sampledf = df.sample(n=1000)

# files = sampledf['wav_filename'].to_list()
# ids = []
# for f in files:
#     idName, _ = f.split('.')
#     ids.append(idName)

with open('temp.txt') as f:
    ids = eval(f.readline())

# Launch proc to start conversions
from subprocess import Popen, PIPE, STDOUT
import pandas as pd
import sys
# from time import sleep
p = Popen(['python', 'convert_mathmatical.py'], stdout=PIPE, stdin=PIPE)
p.stdout.readline()

df = pd.DataFrame(columns=['id', 'original_pae', 'generated_pae'])
for i in ids:
    originalpae = ''
    generatedpae = ''

    p.stdin.write(f'{i}\n'.encode('utf-8'))
    p.stdin.flush()
    while True:
        line = p.stdout.readline().decode('utf-8').rstrip()

        # Find original and generated incipit
        origIdent = "ORIGINAL INCIPIT: "
        if len(line) > len(origIdent) and line[:len(origIdent)] == origIdent:
            originalpae = line[len(origIdent):]

        genIdent = "GENERATED INCIPIT: "
        if len(line) > len(genIdent) and line[:len(genIdent)] == genIdent:
            generatedpae = line[len(genIdent):]

        # print(line)
        endOfOutput = 'Detect [R]ests: '
        if len(line) > len(endOfOutput) and line[:len(endOfOutput)] == endOfOutput:
            df.loc[-1] = [i ,originalpae, generatedpae]
            df.index = df.index + 1
            df = df.sort_index()
            break

p.kill()

df.to_csv('incipit_pairs.csv', index=False)