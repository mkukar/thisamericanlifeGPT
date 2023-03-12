# thisamericanlifeGPT
 Generates This American Life podcast episodes using gpt3

# Setup/Requirements

## Requirements
- OpenAI Account and API Key
- Python 3.7 to 3.10 (TSS dependency on windows does not support all versions)
- espeak
  - https://github.com/espeak-ng/espeak-ng/releases

## Setup

Install requirements.txt file

`pip install -r requirements.txt`


# Usage

## Scraping
First you must scrape data from thisamericanlife.org to use in the training set.

`thisamericanlifegpt --action scrape --max-episodes <X>`

As each episode will consist of a minimum of a prologue, act and credits, you can roughly expect each episode to equate to a minimum of three training entries.

## Training
Next you must create a jsonl fine-tuning data file to upload to openAI

`thisamericanlifegpt --action train --max-training-entries <X>`

Since each training entry adds to the cost of the fine-tuning, you can limit the number of training entries. It is recommended to at minimum use 500 entries for your model.

### Uploading to openAI

Use the jsonl file to upload to openAI following their guide or use the command below:

`openai api fine_tunes.create -t {0} -m <BASE_MODEL>`

_Note you must first set the environent variable OPENAI_API_KEY=YOURAPIKEYGOESHERE_

The recommended base model is `davinci` as it is the most advanced.

## Running
Now the fun part! After your model is fine-tuned you can now use it to create an episode. Since each episode is very large, it requires several prompts to run. The prompts follow this format:

`Write a <PROLOGUE/ACT/CREDITS> for an episode of the This American Life podcast with the summary <SUMMARY>`

Example:

`Write a act for an episode of This American Life podcast with the summary An episode on ai written by an ai`

You can run this by using the following command:

`thisamericanlifegpt --action run --episode-number <EPISODE_NUMBER> --acts <NUMBER_OF_ACTS> --api-key <OPENAI_API_KEY> --model-id <MODEL_NAME_FROM_OPEN_AI> --prompt <PROMPT_IN_QUOTES>`

Using the above example prompt:

`thisamericanlifegpt --action run --episode-number 1 --acts 2 --api-key <OPENAI_API_KEY> --model-id <MODEL_NAME_FROM_OPEN_AI> --prompt "An episode on ai written by an ai"`

This would generate Episode 1 with 2 acts (so Prologue, Act 1, Act 2, Credits) and create both the script and audio file.

# Resources
https://platform.openai.com/docs/guides/fine-tuning

https://github.com/coqui-ai/TTS

https://github.com/espeak-ng/espeak-ng/releases

# Author
Created by Michael Kukar in 2023

# License
See LICENSE file