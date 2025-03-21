# Text-to-Speech Radio
This python script converts text to speech using the Google Cloud engine. Furthermore, radio effects (high, low pass filters and white noise) can be added to the speech output.
The input text is read from an Excel or csv file.

# Installation
You need to have python and pip installed. Furthermore, the script requires the following packages, which can be easily installed via pip:
* pydub
* google-cloud
* pandas

# Data Table
The input data is provided as a table in either `xlsx` or `csv` format:

![image](https://github.com/funkyfranky/MTTS/assets/28947887/79ca2b46-cd24-493e-84c4-598ef34b3958)

The `xlsx` or `csv` files need to have the following columns:
* `Text`: The text that is converted to speech. This can contain SSML syntax.
* `File Name`: The output file name. This will be saved as in `.ogg` format.
* `Subtitle`: An optional subtitle if different from the `Text` column.
* `Voice Name`: The Google voice if other than the default voice `en-US-Standard-A`.
* `Highpass`: The high pass filter frequency in Hz. Default 4000 Hz.
* `Lowpass`: The low pass filter frequency in Hz. Default 3000 Hz.
* `Nfilter`: Number of times the high and or low pass filters are applied. Default 3.
* `Volume Boost`: The volume boost in dB applied to the final normalized output. Default 0 dB.
* `Noise Boost`: The white noise boost in [dB]. Default `None`. If set, white noise is added. Try a negative value of -25 dB first.
* `Emphasis`: Add emphasis to the voice, c.f. https://cloud.google.com/text-to-speech/docs/ssml#emphasis.
* `Rate`: Adjust speech rate, c.f. https://cloud.google.com/text-to-speech/docs/ssml#prosody
* `Pitch`: Adjust the pitch of the voice, c.f. https://cloud.google.com/text-to-speech/docs/ssml#prosody
* `Click In`: Add a radio click at the beginning of the sound file.
* `Click Out`: Add a radio click at the end of the sound file.

# Usage
Change to the directory, where the ttsr.py file is located and type
```
python ttsr.py --credentials X:\<Path to JSON file>\google-credentials.json
```
where the parameter `--credentials` points to your Google cloud credentials file. Alternatively, you can set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to point to the credentials file.

This will scan the current directory for all `xlsx` and `csv `files and start the conversion process.
For each input file, a directory named as the input file is created that contains the sound `.ogg` files.
Additionally, a `csv` file with the parameters is created that also contains the duration of the sound file as additional column.
This `csv` file can be used as input for various MOOSE classes (*e.g.* ATIS, RANGE, AIRBOSS) as described below.

## Command Line Parameters
The following command line parameters can be used:
* `--filetype`: Specify whether you want Excel `xlsx` or comma-separated value `csv` files as input.
* `--inputdir`: Specify the path of the directory where the input files are located.
* `--inputfile`: Specify the path to a single input file (if you do not want to convert all files in a directory).
* `--credentials`: Path to your Google credentials file.

### Specify File Type
Process only csv files in the current directory
```
python ttsr.py --filetype csv
```
### Specify Input Directory
Process all xlsx and csv files in a certain directory
```
python ttsr.py --inputdir <Path To Input Files>
```
### Specify Input File
Process only one specific input file
```
python ttsr.py --inputfile <Path to Input File>
```
### Specify Voice
Use a specific voice for all input files (overrules setting in input files)
```
python ttsr.py --voice en-GB-Wavenet-F
```
### Specify Noise
Use a white noise for all input files (overrules setting in input files)
```
python ttsr.py --noise -25
```
The white noise volume is reduced by -25 dB.

# MOOSE Classes
The generated sound files can of course be used in DCS, when included in a mission miz file. Add the generated sound files to your mission (open the miz with 7-zip and drag & drop the folder).
The output of the csv files that contain the duration of the sound file can be used in some MOOSE classes.

## ATIS
A simple ATIS script can look like:
```lua
local atis=ATIS:New("Batumi", 305)  
atis:SetSoundfilesPath("ATIS-en-GB-Wavenet-F/", "Caucasus-en-GB-Wavenet-F/", "NATO Alphabet-en-GB-Wavenet-F/")
atis:SetSoundfilesInfo("D:/DCS/Scripts/My_Missions/parameters-ATIS-en-GB-Wavenet-F.csv")
-- More custom input...
atis:Start()
```
The `parameters-ATIS-en-GB-Wavenet-F.csv` is the output file generated by the script and needs to be located on your local hard drive (*i.e.* not in the miz file).

## RANGE
```lua
local range=RANGE:New("Test")
range:SetSoundfilesPath("Range/")
range:SetSoundfilesInfo("D:/DCS/Scripts/My_Missions/_Classes/MSRS/parameters-Range.csv")
-- More custom input...  
range:Start()
```

## AIRBOSS
WIP, not supported yet.

# Ackknowledgements
This script is based on https://github.com/adamclmns/DCS_RadioComm_VoiceLineGenerator
