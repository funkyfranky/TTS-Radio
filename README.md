This python script converts text to speech using the Google Cloud engine. Furthermore, radio effects are added to the speech output.
The input text is read from an Excel or csv file.

# Data Table
![image](https://github.com/funkyfranky/MTTS/assets/28947887/79ca2b46-cd24-493e-84c4-598ef34b3958)

In the xlsx or csv files need to have the following columns:
* `Text`: The text that is converted to speech
* `File Name`: The output file name. This will be saved as in `.ogg` format.
* `Subtitle`: An optional subtitle if different from the `Text` column.
* `Voice Name`: The Google voice if other than the default voice.
* `Highpass`: The high pass filter frequency in Hz. Default 4000 Hz.
* `Lowpass`: The low pass filter frequency in Hz. Default 3000 Hz.
* `Nfilter`: Number of times the high and or low pass filters are applied. Default 3.
* `Volume Boost`: The volume boost in dB applied to the final normalized output. Default 0 dB.
* `Noise Boost`: The white noise boost in [dB]. Default `None`. If set, white noise is added. Try a negative value of -25 dB first.
* `Emphasis`: Add emphasis to the voice, c.f. https://cloud.google.com/text-to-speech/docs/ssml?hl=de#emphasis. 
* `Rate`: Adjust rate, c.f. https://cloud.google.com/text-to-speech/docs/ssml#prosody
* `Pitch`: Adjust the pitch of the voice, c.f. https://cloud.google.com/text-to-speech/docs/ssml#prosody
* `Click In`: Add a radio click at the beginning of the sound file.
* `Click Out`: Add a radio click at the end of the sound file.

# Usage:
Change to the directory, where the mtts.py file is located and type
```
python mtts.py
```
This will scan the current directory for all xlsx files and start the conversion process.

# Advanced 
