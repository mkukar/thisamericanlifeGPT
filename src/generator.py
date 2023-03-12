# generates a complete script and audio file
# Created by Michael Kukar in 2023

import openai
import json
from TTS.api import TTS

from tamtrainer import TAMTrainer

class Generator:

    VOICE_MODEL = 'tts_models/en/vctk/vits'
    FIXED_VOICES = {
        'Ira Glass' : 'p241'
    }
    EXCLUDED_VOICES = ['ED\n']
    PRONUNCIATION_FIXES = {
        'Ira' : 'eyera',
        'Kukar' : 'coocar',
        'thisamericanlifegpt' : 'this american life g p t',
        'WBEZ' : 'W B E Z',
        'Malatia' : 'mala tia',
        'PRI' : 'P R I'
    }
    POST_CREDITS_DIALOGUE = [
        'This episode was generated using thisamericanlifegpt',
        'Created by Michael Kukar in 2023',
        'Thank you for listening!'
    ]

    EPISODE_FOLDER = '../episodes/episode {0}'

    def __init__(self, apiKey, modelId):
        openai.api_key = apiKey
        self.trainer = TAMTrainer()
        self.modelId = modelId
    
    def query_episode_data(self, summaryPrompt, numberOfActs=1):
        episodeData = []
        acts = ['prologue', 'credits']
        acts[1:1] = ['act ' + str(x) for x in range(1, numberOfActs+1)]
        for act in acts:
            episodeData.append(self.run_query(self.build_prompt(summaryPrompt, act)))
        episodeData.append(self.add_postcredits(summaryPrompt))
        return episodeData

    def add_postcredits(self, summaryPrompt):
        speakerPrefix = 'Ira Glass : '
        speakerPostfix = '\n'
        postCreditsText = self.POST_CREDITS_DIALOGUE
        postCreditsText.insert(1, 'The prompt for this episode was {0}'.format(summaryPrompt))
        formattedText = ""
        for postcredits in postCreditsText:
            formattedText += speakerPrefix + postcredits + speakerPostfix
        postcreditsData = { #openai response format, stripped of anything but text
            'choices' : [
                {'text' : formattedText}
            ]
        }
        return postcreditsData

    def build_prompt(self, summaryPrompt, actName):
        return TAMTrainer.PROMPT.format(actName.lower(), summaryPrompt, TAMTrainer.PROMPT_END_TOKEN)

    def run_query(self, prompt):
        return openai.Completion.create(
            model=self.modelId,
            prompt=prompt,
            stop=TAMTrainer.COMPLETION_END_TOKEN,
            max_tokens=(TAMTrainer.MAX_TOKENS - self.trainer.count_tokens(prompt))
        )

    def parse_episode_data_to_script(self, episodeData):
        scriptData = [] # { 'ACT1' : []} where [] is ordered speaking entries {'VOICE', 'TEXT'} (if an action, voice is ACTION)
        for i, act in enumerate(episodeData): # first act is prologue, then acts 1,2,3,etc. then last is credits
            if i == 0:
                actName = 'prologue'
            elif i == len(episodeData) - 1:
                actName = 'post-credits'
            elif i == len(episodeData) -2 :
                actName = 'credits'
            else:
                actName = 'act {0}'.format(str(i))
            actData = {actName.upper() : self.parse_text_into_act_data(act['choices'][0]['text'])}
            scriptData.append(actData)
        return scriptData

    def parse_text_into_act_data(self, openaiText):
        # format is SPEAKER : SPEECH\nSPEAKER : SPEECH\n, etc.
        # output is {'VOICE' : 'TEXT'} pairs in order
        actData = []
        speakingSegments = openaiText.split('\n')
        for speech in speakingSegments:
            if '[' in speech and ']' in speech: # this is an action (e.g. [ACKNOWLEDGEMENTS]), so it needs to be split out
                actionSpeech = speech.split('[')[1]
                actionSpeech = actionSpeech.split(']')[0]
                actData.append({'ACTION' : actionSpeech})
                speech = speech.replace('[{0}]'.format(actionSpeech), '')
            if ':' not in speech: # likely end of segment
                continue
            splitSpeech = speech.split(':')
            actData.append({splitSpeech[0].strip() : splitSpeech[1].strip()})
        return actData

    def generate_script(self, scriptData, filename):
        with open(filename, 'w') as f:
            f.write('# THIS AMERICAN LIFE GPT\n\n')
            for actData in scriptData:
                actName = list(actData.keys())[0]
                actSpeeches = list(actData.values())[0]
                f.write('\n## {0}\n'.format(actName))
                for speech in actSpeeches:
                    speaker = list(speech.keys())[0]
                    speech = list(speech.values())[0]
                    if speaker == 'ACTION':
                        f.write('__[{0}]__\n\n'.format(speech))
                    else:
                        f.write('__{0}__  :  {1}\n\n'.format(speaker, speech))

    def generate_audio(self, scriptData, filename):
        wavData = []
        assignedVoices = {}
        tts = TTS(self.VOICE_MODEL)
        for actData in scriptData:
            actSpeeches = list(actData.values())[0]
            for speech in actSpeeches:
                speaker = list(speech.keys())[0]
                speech = list(speech.values())[0]
                speaker_voice = self.assign_voice(speaker, assignedVoices, tts)
                fixed_speech = self.change_pronunciation(speech)
                if speaker == 'ACTION' or len(fixed_speech) == 0:
                    # skips actions, long-term could play sound effect, etc.
                    continue
                else:
                    wavData.extend(tts.tts(fixed_speech, speaker=speaker_voice))
        tts.synthesizer.save_wav(wav=wavData, path=filename)
        
    def assign_voice(self, name, assignedVoices, tts):
        if name in assignedVoices.keys():
            return assignedVoices[name]
        elif name in self.FIXED_VOICES.keys():
            return self.FIXED_VOICES[name]
        else:
            randomVoice = None
            from random import randrange
            while randomVoice is None or randomVoice in assignedVoices.keys() or randomVoice in self.FIXED_VOICES.keys() or randomVoice in self.EXCLUDED_VOICES:
                randIndex = randrange(len(tts.speakers))
                randomVoice = tts.speakers[randIndex]
            assignedVoices[name] = randomVoice
            return randomVoice

    def change_pronunciation(self, text):
        # some voices are said weird (notably Ira Glass), so lets fix it
        for word, pronunciation in self.PRONUNCIATION_FIXES.items():
            if word in text:
                text = text.replace(word, pronunciation)
        return text

    def save_data(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_data(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)

    def run(self, summaryPrompt, episodeNumber, numberOfActs=2, episodeFolder=EPISODE_FOLDER):
        outputFolder = episodeFolder.format(episodeNumber)
        episodeData = self.query_episode_data(summaryPrompt, numberOfActs=numberOfActs)
        self.save_data(episodeData, '{0}/episodeData.json'.format(outputFolder))
        episodeData = self.load_data('{0}/episodeData.json'.format(outputFolder))
        scriptData = self.parse_episode_data_to_script(episodeData)
        self.generate_script(scriptData, '{0}/script.md'.format(outputFolder))
        self.generate_audio(scriptData, '{0}/audio.wav'.format(outputFolder))

