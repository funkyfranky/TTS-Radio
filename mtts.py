import os
import shutil
import argparse
from pathlib import Path
from google.cloud import texttospeech
from pydub import AudioSegment, generators, silence, effects
import pandas as pd

# Default voice (used if no voice specified in Voice Name column)
DEFAULT_VOICE="en-US-Studio-O"
DEFAULT_VOICE="en-US-Standard-A"
DEFAULT_VOICE="en-GB-Wavenet-F"
#DEFAULT_VOICE="ru-RU-Wavenet-E"

# Default High and low pass filter values [Hz]
HIGHPASS=4000
LOWPASS=3000

# Number of times to apply high/low pass filters. Default 3.
NFILTER=3

# Volume boost
NOISE_BOOST  = -25   # Volume adjustment [dB] for white noise. Default -25 dB.
VOLUME       =   0   # Volume adjustment [dB] for whole autio after (filters and noise). Default 0 dB.

# Column names (do not change!)
COLS=["text", "filename", "subtitle", "voice", "highpass", "lowpass", "nfilter", "volume", "noise", "emphasis", "rate", "pitch", "clickin", "clickout"]

class TTS():
    def __init__(self, file: str, directory:str, voice: str=None, volume:int=VOLUME, nfilter:int=None, highpass=None, lowpass=None, noise=None, clickin=None, clickout=None):

        self.file=file
        self.directory=directory
        self.voice=DEFAULT_VOICE if pd.isna(voice) else voice
        self.volume=int(volume) if pd.notna(volume) else VOLUME
        self.nfilter=int(nfilter) if pd.notna(nfilter) else NFILTER
        self.highpass=int(highpass) if pd.notna(highpass) else HIGHPASS
        self.lowpass=int(lowpass) if pd.notna(lowpass) else LOWPASS
        self.noise=int(noise) if pd.notna(noise) else None

        _clickIn=Path("./assets/In.wav")
        _clickOut=Path("./assets/Out.wav")

        # Radio click sounds
        self.clickIn:AudioSegment=None
        self.clickOut:AudioSegment=None

        _click_volume_decrease=5

        if pd.notna(clickin):
            self.clickIn=AudioSegment.from_wav(_clickIn.absolute()) - _click_volume_decrease  # reduce volume
        
        if pd.notna(clickout):
            self.clickOut=AudioSegment.from_wav(_clickOut.absolute()) - _click_volume_decrease  # reduce volume


    # Adds a couple filters, and adds static, and clicks to end/beginning of track
    def addRadioNoiseFilters(self, audio: AudioSegment):

        # Convinient lambdas found on SO
        _trim_leading_silence: AudioSegment = lambda x: x[silence.detect_leading_silence(x):]
        _trim_trailing_silence: AudioSegment = lambda x: _trim_leading_silence(x.reverse()).reverse()
        _strip_silence: AudioSegment = lambda x: _trim_trailing_silence(_trim_leading_silence(x))

        # Apply high and low pass filters
        for _ in range(self.nfilter):
            if self.highpass>=0:
                audio=audio.high_pass_filter(self.highpass)
            if self.lowpass>=0:
                audio=audio.low_pass_filter(self.lowpass)

            # Normalize audio after applying filter(s)
            audio=effects.normalize(audio)

        # Strip leading/trailing silence
        audio = _strip_silence(audio)

        # Click sounds
        if self.clickIn is not None:
            audio = self.clickIn + audio
        if self.clickOut is not None:
            audio = audio + self.clickOut

        # White noise
        if self.noise is not None:

            # Generate white noise
            whiteNoise = generators.WhiteNoise().to_audio_segment(duration=len(audio), volume=self.noise)

            # Overlay white noise
            audio = audio.overlay(whiteNoise)

        # Normalize audio after applying noise
        audio=effects.normalize(audio)            

        # Bump volume of all audio.
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
        audio=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # Convert text to speech.
        speech=client.synthesize_speech(input=blabla, voice=voice, audio_config=audio)

        # Write output file as mp3.
        file="./"+self.file+".mp3"
        with open(file, "wb") as output:
            output.write(speech.audio_content)

        # Read mp3 as audio segment.
        audio = AudioSegment.from_mp3(file)

        # Add filters and white noise
        audio:AudioSegment=self.addRadioNoiseFilters(audio)

        # Save as ogg.
        audio.export(self.directory / (self.file+".ogg"), format='ogg')

        # Remove mp3 file.
        os.remove(file)

        return audio

if __name__=='__main__':

    print()
    print("Text-To-Speech")
    print("==============")
    print()

    parser=argparse.ArgumentParser(description="MTTS arg parser")
    parser.add_argument("--credentials", default=None, type=str, nargs="?")
    parser.add_argument("--filetype", default=None, nargs="?", choices=["xlsx", "csv"])
    parser.add_argument("--inputdir", default="./", nargs="?")
    parser.add_argument("--inputfile", default=None, type=str, nargs="?")
    parser.add_argument("--voice", default=None, type=str, nargs="?")

    args=parser.parse_args()

    if args.credentials is not None:        
        # Set credentials env variable.
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credentials        
    else:
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            pass
        else:
            raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS not set!")
    # Check that credentials file exists
    credentials=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"- Google credentials file: {credentials}")
    if not Path(credentials).is_file():
        raise FileExistsError(f"File {credentials} does not exist!")

    if args.filetype is not None:
        filetype=args.filetype
        print("Hallo")
    else:
        filetype="xlsx, csv"
    print(f"- data input file type: {filetype}")

    # Set intput dir
    if args.inputdir is not None:
        inputdir=args.inputdir
    else:
        inputdir="./"
    print(f"- Input directory of {filetype} files: {inputdir}")
    if not Path(inputdir).is_dir():
        raise FileExistsError(f"Directory {inputdir} does not exist!")
    
    # Set input file
    if args.inputfile is not None:
        inputfiles=[Path(args.inputfile)]
    else:
        if args.filetype is not None:
            inputfiles=Path(inputdir).glob(f'*.{args.filetype}')
        else:
            inputfiles=Path(inputdir).glob('*.[xlsx csv]*')
    print(f"- Input files: {inputfiles}")

    # Input voice
    if args.voice is not None:
        inputvoice=args.voice
        print(f"- Voice (overrules): {inputvoice}")
    else:
        intputvoice=None

    print()

    # Loop over intput files
    for file in inputfiles:

        # Ignore excel temp files (opened files) and files that start with an underscore
        if file.name.startswith("~") or file.name.startswith("_"):
            continue
        else:
            print(f"* Processing file {file.absolute()}")

        # Read excel into data frame
        if file.suffix==".xlsx":
            df = pd.read_excel(file, header=None, names=COLS, skiprows=[0])
        elif file.suffix==".csv":
            df = pd.read_csv(file, header=None, names=COLS, skiprows=[0], delimiter=";")
        else:
            raise NotImplementedError(f"Unknown file type {file.suffix}")

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
        print()

        # Loop over all rows in data frame
        duration=[]
        for idx, row in df.iterrows():
            if inputvoice is None:
                voice=row["voice"]
            else:
                voice=inputvoice


            print(f'file={row["filename"]}, voice={voice}, emphasis={row.emphasis}, rate={row.rate}, pitch={row.pitch}: {row["text"]} ')

            tts=TTS(file=row.filename, directory=directory, voice=voice, volume=row.volume, nfilter=row["nfilter"], 
                    highpass=row.highpass, lowpass=row.lowpass, noise=row.noise, clickin=row["clickin"], clickout=row["clickout"])
            
            if pd.isna(row.text):
                continue

            audio=tts.tts(row.text, row.emphasis, row.rate, row.pitch)

            # Set values explicitly for later reference
            df.at[idx, "volume"]=tts.volume
            df.at[idx, "voice"]=tts.voice
            df.at[idx, "highpass"]=tts.highpass
            df.at[idx, "lowpass"]=tts.lowpass
            df.at[idx, "nfilter"]=tts.nfilter
            df.at[idx, "noise"]=tts.noise
            df.at[idx, "clickin"]=tts.clickIn
            df.at[idx, "clickout"]=tts.clickOut

            duration.append(round(len(audio)/1000, 2))

        # Add duration column
        df["duration"]=duration

        # Save file
        print()
        pfile=directory / f"parameters-{file.stem}.csv"
        print(f"* Saving parameter csv file as {pfile}")
        df.to_csv(pfile, index=False, sep=";", na_rep="nil")        

    print()
    print("*** FIN ***")
    print()
