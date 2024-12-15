from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from os import listdir
ROOT = "output_G-2__c_v2"
OUT_ROOT = "output_G-2__c_v4"
def trim_silence_end(audio_file, silence_thresh=-40, chunk_size=10):
    audio = AudioSegment.from_file(audio_file)
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=chunk_size, silence_thresh=silence_thresh)
    if nonsilent_ranges:
        end_of_sound = nonsilent_ranges[-1][1]
        trimmed_audio = audio[:end_of_sound]
        return trimmed_audio
    else:
        return AudioSegment.silent(duration=0)
for fname in listdir(ROOT):
    trim_silence_end(ROOT+"/"+fname).export(OUT_ROOT+"/"+fname, format="wav")