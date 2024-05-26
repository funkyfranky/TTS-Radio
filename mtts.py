import os
import shutil
from pathlib import Path
from google.cloud import texttospeech
from pydub import AudioSegment, generators, silence, effects
import pandas as pd
import json


# Set google credentials from JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "F:/google-tts.json"

# Default High and low pass filter values [Hz]
HIGHPASS=4000
LOWPASS=3000

FILTER_BOOST =  20   # Volume adjustment [dB] for high/low pass filtered
NOISE_BOOST  = -25   # Volume adjustment [dB] for white noise
VOLUME       =   5   # Volume adjustment [dB] for whole autio after (filters and noise)

DEFAULT_VOICE="en-US-Studio-O"
DEFAULT_VOICE="en-US-Standard-A"
DEFAULT_VOICE="en-GB-Wavenet-F"
#DEFAULT_VOICE="ru-RU-Wavenet-E"

class TTS():
    def __init__(self, file: str, directory:str, voice: str=None, volume:int=VOLUME, filter:int=None, highpass=None, lowpass=None, noise=None):
        self.file=file
        self.directory=directory
        self.voice=DEFAULT_VOICE if pd.isna(voice) else voice
        self.volume=int(volume) if pd.notna(volume) else VOLUME
        self.filter=int(filter) if pd.notna(filter) else FILTER_BOOST
        self.highpass=int(highpass) if pd.notna(highpass) else HIGHPASS
        self.lowpass=int(lowpass) if pd.notna(lowpass) else LOWPASS
        self.noise=int(noise) if pd.notna(noise) else NOISE_BOOST

        if False:
            print(f"File={self.file}")
            print(f"Directory={self.directory}")
            print(f"Voice={self.voice}")        
            print(f"Highpass={self.highpass}")
            print(f"Lowpass={self.lowpass}")
            print(f"Volume={self.volume}")
            print(f"Filter={self.filter}")
            print(f"Noise={self.noise}")
            print()
            #quit()

        self._IN_WAV="./In.wav"
        self._OUT_WAV="./Out.wav"

    # Adds a couple filters, and adds static, and clicks to end/beginning of track
    def addRadioNoiseFilters(self, audio: AudioSegment):

        # Convinient lambdas found on SO
        _trim_leading_silence: AudioSegment = lambda x: x[silence.detect_leading_silence(x):]

        _trim_trailing_silence: AudioSegment = lambda x: _trim_leading_silence(x.reverse()).reverse()

        _strip_silence: AudioSegment = lambda x: _trim_trailing_silence(_trim_leading_silence(x))

        #in_Wave = AudioSegment.from_wav(self._IN_WAV)   - self._click_volume_decrease  # reduce volume
        #out_Wave = AudioSegment.from_wav(self._OUT_WAV) - self._click_volume_decrease  # reduce volume

        # Apply high and low pass filters
        for _ in range(3):
            if self.highpass>=0:
                print(f"highpass = {self.highpass}")
                audio=audio.high_pass_filter(self.highpass)
            if self.lowpass>=0:
                print(f"lowpass = {self.lowpass}")
                audio=audio.low_pass_filter(self.lowpass)
            audio=effects.normalize(audio)

        # Strip leading/trailing silence
        audio = _strip_silence(audio)

        #combined = in_Wave + filtered + out_Wave  # concatenate

        # Generate white noise.
        if False:
            whiteNoise = generators.WhiteNoise().to_audio_segment(duration=len(audio), volume=self.noise)

            # overlay white noise, dropping WN volume.
            #audio = audio.overlay(whiteNoise + self.noise)
            audio = audio.overlay(whiteNoise)

        # Bumb volume of all audio.
        audio = audio + self.volume

        return audio

    def ssml(self, text:str, emphasis:str="moderate", rate="default", pitch="medium"):
        #print(emphasis, pd.notna(emphasis))
        if pd.notna(emphasis):
            emphasis=emphasis
        else:
            emphasis=None
        if pd.notna(rate):
            rate=rate
        else:
            rate=None
        if pd.notna(pitch):
            pitch=pitch
        else:
            pitch=None

        if emphasis is not None:
            text=f'<emphasis level="{emphasis}">'+text+'</emphasis>'

        if (rate is not None) and (pitch is not None):
            text=f'<prosody pitch="{pitch}" rate="{rate}">'+text+'</prosody>'
        elif rate is not None:
            text=f'<prosody rate="{rate}">'+text+'</prosody>'
        elif pitch is not None:
            text=f'<prosody pitch="{pitch}">'+text+'</prosody>'

        text="<speak>"+text+"</speak>"

        print(text)
        print()
        return text

    def tts(self, text: str, emphasis: str = "moderate", rate="default", pitch="medium"):
        """
        Convert text to speech, which is saved as ogg file.
        """

        # Create a client.
        client=texttospeech.TextToSpeechClient()

        # Create input.
        blabla=texttospeech.SynthesisInput(ssml=self.ssml(text, emphasis=emphasis, rate=rate, pitch=pitch))

        # Setup voice.
        voice=texttospeech.VoiceSelectionParams(language_code=self.voice[0:5], name=self.voice)

        # Audio config.
        audio=texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Convert text to speech.
        speech=client.synthesize_speech(input=blabla, voice=voice, audio_config=audio)

        # Write output file as mp3.
        file="./"+self.file+".mp3"
        with open(file, "wb") as output:
            output.write(speech.audio_content)

        # Read mp3 as audio segment.
        audio = AudioSegment.from_mp3(file)

        # Add 
        audio:AudioSegment=self.addRadioNoiseFilters(audio)

        # Save as ogg.
        audio.export(self.directory / (self.file+".ogg"), format='ogg')

        # Remove mp3 file.
        os.remove(file)

        return audio

if __name__=='__main__':

    print("Text-To-Speech")
    print("==============")
    print()

    for file in Path('./').glob('*.xlsx'):

        if file.name.startswith("~") or file.name.startswith("_"):
            # Ignore excel temp files (opened files)
            continue

        print(f"* Processing file {file}")

        COLS=["text", "filename", "subtitle", "voice", "highpass", "lowpass", "volume", "filter", "noise", "emphasis", "rate", "pitch"]

        # Read excel into data frame
        df = pd.read_excel(file, header=None, names=COLS, skiprows=[0])

        print(df.head())
        print()

        directory=Path("./"+file.stem+"/")
        print(f"Creating directory {directory}")
        if directory.exists():
            shutil.rmtree(directory, ignore_errors=True)
        try:
            os.mkdir(directory)
        except:
            raise(f"Could not create directory {directory}")

        duration=[]
        for idx, row in df.iterrows():
            print(f'file={row["filename"]}, voice={row["voice"]}, emphasis={row.emphasis}, rate={row.rate}, pitch={row.pitch}: {row["text"]} ')

            tts=TTS(file=row.filename, directory=directory, voice=row.voice, volume=row.volume, filter=row["filter"], highpass=row.highpass, lowpass=row.lowpass, noise=row.noise)

            audio=tts.tts(row.text, row.emphasis, row.rate, row.pitch)

            # Set values explicitly for later reference
            df.at[idx, "volume"]=tts.volume
            df.at[idx, "voice"]=tts.voice
            df.at[idx, "highpass"]=tts.highpass
            df.at[idx, "lowpass"]=tts.lowpass
            df.at[idx, "filter"]=tts.filter
            df.at[idx, "noise"]=tts.noise

            duration.append(round(len(audio)/1000, 2))

        # Add duration column
        df["duration"]=duration

        #df.to_excel(directory / "result.xlsx")
        df.to_csv(directory / "parameters.csv", index=False, sep=";", na_rep="nil")
        df.to_json(directory / "parameters.json", index=False, orient="table", indent=4)
        #df.to_xml
