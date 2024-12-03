# An algorithm for converting WAV audio to sheet music

Implementation By Steven Nyman

## Installation and Requirements
Some components required to run this project are not included in the main repository.
You'll need:
* WSL or a non-Windows system
* Python 3.12
* (Recommended) A way to create virtual environments, such as `uv`
* The following Python modules (from `requirements.txt`) to run the basic algorithm (installable with `pip` or `uv pip`):
    * `verovio` (doesn't support Plaine and Easie (PAE) code on Windows)
    * `scipy`
    * `numpy`
* The following system packages are required to run the basic algorithm:
    * `ffmpeg`
    * `python3` (Python 3.12 is tested)
* The following Visual Studio Code extension is recommended:
    * `@analytic-signal.preview-html` for live-updating SVG preview
* The following files should be made available in the working directory when running/evaluating the scripts:
    * an extracted copy of [output_G-2__c_v3.zip](https://drive.google.com/file/d/1UsxXUPUxAVm7Wa8YMOCR5gUUwqsnI4cy/view). The root directory from the zip file should be preserved when extracting. Zip file is a 10GB download, extracts to about 16.4GB and contains approximately 81,000 sample audio files generated from the Plaine and Easie incipits in the RISM database with leading/trailing silences removed. This selection is all songs in the database that are in the `4/4` or `c` time signatures, in the clef of `G-2`, in the key of concert C (key signature is blank). The PAE code data for these files is included in the repository in `G-2__c_v3.csv`.
* (Optional) The following modules are only required for certain types of usage:
    * `pywebview` if you would like the original and result music SVG files to be rendered in a pop-up window (disabled by default, can change with `SVG_NO_POPUP`). Works poorly under WSL. `pywebview` requires installation of various additional system dependencies using both `pip` and `apt`. Additionally required if using `view_pae.py`.
    * `lxml` if generating test CSVs/WAVs from a RISM database export
* (Optional) System package for generating audio from PAE snippets:
    * `fluidsynth`
    * `sox` (to remove silence from generated audio snippets, ex: `for file in *.wav; do sox "$file" "../output_G-2__c_v3/$file" silence -l 1 0.1 0.5% -1 0.1 0.5%; done`)
* (Optional) [Soundfont file for generating audio from PAE snippets](https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2), place in working directory
* (Optional) [RISM database](https://opac.rism.info/fileadmin/user_upload/lod/update/rismAllMARCXML.zip), ([source webpage](https://opac.rism.info/main-menu-/kachelmenu/data)). The currently used version of the file is `rism_240119.xml`, released in January 2024.
* (Optional) Additional useful system packages:
    * `git` for repo updates
    * `bash`
    * Visual Studio Code

## Explanation/Basic Usage of Repo Files
* `.gitignore`, `.python-version`, `requirements.txt` serve their usual purpose
* `convert_mathmatical.py` is the main script to run (explained in [Usage](#usage))
* `createblanksvg.py` helper script to create blank-like SVG files, useful as a starting point for demonstrations.
* `G-2__c_v3.csv` provides a list of sample files and the ground-truth PAE code used to generate them, see additional info in prior section
* `midi_csv_from_xml.py`, when combined with the above listed `sox` command for removing silences, can be used to generate the sample audio and a CSV file from the RISM database export. On Linux, it is highly recommended to create a RAM-based file system for usage with this script as it creates a number of temporary/intermediate files which can cause SSD wear: `mkdir /mnt/tmpfs570`, `sudo mount -o size=128M -t tmpfs none /mnt/tmpfs570`
* `notes-frequencies.json`, `pitch_to_node.json` map frequencies/pitches to note letters and PAE octaves
* `notes.txt` contains some scratch notes
* `paetowav.py` can convert a PAE string to a WAV file, useful for audibly comparing how close a generated PAE file sounds to its original source file. This file requires some of the optional requirements listed above. Takes no arguments, requests parameters interactively. Does not currently remove trailing silence from conversion process.
* `pitch_file_pair_convert_number.py` is not intended for direct interactive usage but is imported as a module for the main `convert_mathmatical.py` script
* `README.md` is this file
* `view_pae.py` display an SVG string in a popup window. This file requires some of the optional requirements listed above. First CLI argument is window title, second CLI argument is SVG string. Not recommended for use.

## Usage
This section focuses on the main `convert_mathmatical.py` script. The script takes no arguments.

The script will loop, asking for a song id each time. In its default mode, it will only take song IDs as listed in `G-2__c_v3.csv`, including leading zeroes or `.wav` is optional. If `_` is not included in the provided song ID, `_0` is assumed (these are sub IDs when multiple incipits are provided for a RISM entry). The script will first update `out_Original.svg` with the ground truth music notation, then will run the algorithm and update `out_Result.svg`.

A significant amount of output is printed to console, including the original, ground truth incipit and `ffmpeg` conversion output (reduction to 0.25x speed). Next, lines of output for each 50ms interval representing the frequency index in the pitch list, the normalized frequency, the original frequency, and the intensity of the frequency are printed. Next a nearly-raw frequency sequence is printed (the number of 50ms intervals followed by the dominant frequency at that interval). (End of first loop in `pitch_file_pair_convert_number.py`.) At this point the only processing is that some intervals with the same frequency appear next to each other, this is an indication that the same note was likely played twice as the intensity increased significantly after decreasing. The following lines are effectively a repetition of the previous line of output but are printed as they are processed by the heuristic algorithm. Next, a processed frequency sequence is printed. (End of second loop in `pitch_file_pair_convert_number.py`) followed by the resulting PAE code (loop in `convert_mathmatical.py`).

Before each song ID prompt, the current configuration of options is printed. Enter the indicated letter as a song ID to toggle a given option.
* `Detect [R]ests`: attempt to detect low intensity moments in the music as likely rests. Not very accurate, disabled by default. Leaving this disabled does not guarantee you will see no rests in the output. If a music file is completely silent with no dominant frequencies for a certain time, a rest will be emitted.
* `Detect [M]easures`: attempt to detect measures using the number of beats in a measure, assuming a `4/4` or `c` time signature. More accurate than rest detection, but cannot account for pickup notes, and if a note length is detected wrongly, the measure detection may also be incorrect. Disabled by default.
* `Do [P]ost-processing`: use a number of heuristics to significantly improve algorithm output. Enabled by default. Can be disabled to demonstrate the effects of the heuristics and also to debug the heuristics. Note that disabling this does not disable repeated note detection.
* `Use [C]omparable`: enabled by default, assume song ID is present in `G-2__c_v3.csv` and wav files are located in the `G-2__c_v3/` directory, and use the csv files to generate a ground truth original music representation. If disabled, consider song ID to be a wav file (with required `.wav` extension) located in the working directory with no available ground truth representation (`out_Original.svg` would not be updated).
* `x` or `q` can exit the script

The script logs commands entered into `convert_log.txt`.

Audio files provided to the script should be 16khz mono, ex: `ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav` Additional useful ffmpeg arguments: `-ss 00:19:02.000 -to 00:19:32.000` (start and end time), `-filter:a "volume=8.0"` (increase volume)

Implemented heuristics/improvements over raw data include, but are not necessarily limited to:
* 50 ms chunks
* Measures detected by adding up beats (doesn't work for pickup measures)
* Duplicate of same note when intensity significantly greater than previous intensity and was decreasing - saved to prevent later merging
* Shared bars are just grouped around eligible notes
* Writes as sharp, never flat. Unable to detect both. JSON frequency/octave mapping.
* Add octave oscillation detection with accidentals; go to lower
* Short notes off by a half step (sharp/flat only) are converted to the natural note
* Rests are not really detectable - try when below certain intensity and decreasing or already rest
* Slow down song to 0.25x (ffmpeg)
Many but not all of these are controlled by `Do [P]ost-processing` option.

Other notes/known limitations:
* Last note sometimes too long.
* Sometimes heuristics conflict with each other.
* Sensitivity to background noise.
* 64th and 128th notes as well as grace notes are disabled.

## Demonstrating results in VSCode
* If not using the `pywebview` option, install the `@analytic-signal.preview-html` plugin in VSCode, then open `out_Original.svg` and `out_Result.svg` in a split window one on top of the other. On Windows and possibly Linux or macOS, they will live-update as commands are run. Use the Zoom buttons available when each file is the selected subwindow to zoom both files to the same level. Because the SVGs have no background, it is recommended to switch to light theme.

## Song IDs used in testing/development
* `100477`
* `100744`
* `109603`
* `650009151`
* `651003431`
