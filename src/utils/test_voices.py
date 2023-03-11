# create snapshots of all the voices to test them out locally

from TTS.api import TTS

MODEL_NAME = 'tts_models/en/vctk/vits'
OUTPUT_FOLDER = 'tts_samples'
SAMPLE_TEXT = 'Hello this is This American Life. I am your host, Eyera Glass. Stay with us.'

if __name__ == "__main__":
    tts = TTS(MODEL_NAME)
    for speaker in tts.speakers:
        try:
            file_path = OUTPUT_FOLDER + '/' + speaker + ".wav"
            tts.tts_to_file(text=SAMPLE_TEXT, speaker=speaker, file_path=file_path)
        except Exception as e:
            print("ERROR: Could not generate text for speaker {0}. Skipping...".format(speaker))
            print(e)