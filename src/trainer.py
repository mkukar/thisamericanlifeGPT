# fine tunes gpt3 using data from scraper

import json
import logging
from transformers import GPT2TokenizerFast

logging.basicConfig(format='%(levelname)s - %(asctime)s - %(message)s', level=logging.DEBUG)

class Trainer:

    PROMPT_END_TOKEN = '\n\n###\n\n'
    COMPLETION_END_TOKEN = '###'
    COMPLETION_START_TOKEN = ' '
    MAX_TOKENS = 2048

    def __init__(self):
        self.tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

    def load_scraper_data(self, filename='../episodes.json'):
        with open(filename, 'r') as f:
            return json.load(f)

    def format_data_for_training(self, scraperData):
        trainingSet = [] # format is {"prompt": "<prompt text>", "completion": "<ideal generated text>"},
        for episodeData in scraperData:
            trainingCandidates = self.format_by_episode(episodeData)
            validatedEntries = [x for x in trainingCandidates if self.is_valid_entry(x)] # only allows in validated entries
            trainingSet.extend(validatedEntries)
        return trainingSet

    def format_by_episode(self, episodeData):
        # prompt: Write a <ACTNAME/PROLOGUE/CREDITS> for an episode of the This American Life podcast with the summary <SUMMARY>
        # completion: <text>
        trainingEntries = []
        for actId in episodeData['Acts'].keys():
            trainingEntry = {
                'prompt' : self.format_by_episode_prompt(actId, episodeData),
                'completion' : self.format_by_episode_completion(actId, episodeData)
            }
            trainingEntries.append(trainingEntry)
        return trainingEntries

    def format_by_episode_prompt(self, actId, episodeData):
        if 'act' in actId:
            actName = 'Act'
        else:
            actName = episodeData['Acts'][actId]['name']
        return 'Write a {0} for an episode of the This American Life podcast with the summary {1}{2}'.format(
            actName.lower(), 
            episodeData['summary'], 
            self.PROMPT_END_TOKEN)

    def format_by_episode_completion(self, actId, episodeData):
        return "{0}{1}{2}".format(
            self.COMPLETION_START_TOKEN,
            episodeData['Acts'][actId]['text'],
            self.COMPLETION_END_TOKEN
        )

    def count_tokens(self, data):
        return len(self.tokenizer(data)['input_ids'])

    def is_valid_entry(self, trainingEntry):
        entryStr = trainingEntry['prompt'] + trainingEntry['completion']
        tokenCount = self.count_tokens(entryStr)
        if tokenCount <= self.MAX_TOKENS:
            return True
        else:
            logging.warn('Detected an invalid entry (token count {0} is over max of {1} tokens), check your training data: {2}...'.format(tokenCount, self.MAX_TOKENS, entryStr[:50]))
            return False

    # must be saved in JSONL format ({"prompt": "<prompt text>", "completion": "<ideal generated text>"} on each line)
    def save_training_data(self, trainingData, filename='../training_data.jsonl'):
        with open(filename, 'w') as f:
            for entry in trainingData:
                f.write(json.dumps(entry) + '\n')


    def run(self, filename='../training_data.jsonl', max_training_set=500):
        data = self.load_scraper_data()
        trainingData = self.format_data_for_training(data)
        if len(trainingData) > max_training_set:
            logging.warning('Training data size is {0} which is above max set size of {1}, limiting to {1}'.format(len(trainingData), max_training_set))
            trainingData = trainingData[:max_training_set]
        self.save_training_data(trainingData, filename=filename)
        logging.debug('Training data saved with size of {0} to {1}'.format(len(trainingData), filename))        

if __name__ == "__main__":
    trainer = Trainer()
    trainer.run(max_training_set=1000)