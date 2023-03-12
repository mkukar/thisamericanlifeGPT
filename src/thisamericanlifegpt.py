# thisamericanlifeGPT
# Created by Michael Kukar 2023

from scraper import Scraper
from tamtrainer import TAMTrainer
from generator import Generator

import argparse
import logging
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog = 'thisamericanlifeGPT',
        description = 'Generates This American Life podcast episodes using gpt3'
    )
    parser.add_argument('--action', choices=['scrape', 'train', 'run'], required=True)
    parser.add_argument('--max-episodes', type=int, default=750, help='Max episodes to scrape (default 750)')
    parser.add_argument('--max-training-entries', type=int, default=1000, help='Max training entries')
    parser.add_argument('--prompt', help='Prompt to run against trained model (required for run)')
    parser.add_argument('--model-id', help='ID of trained model (required for run)')
    parser.add_argument('--api-key', help='OpenAI API key (required for run)')
    parser.add_argument('--episode-number', type=int, help='Episode number to store output (required for run)')
    parser.add_argument('--acts', type=int, default=1, help='Number of acts to generate (default 1)')
    parser.add_argument('--debug', action='store_true', default=False, help='Prints debug logging messages')
    args = parser.parse_args()

    print('thisamericanlifeGPT')
    print('Arguments:')
    print('\tAction               : {0}'.format(args.action))
    if args.action == 'scrape':
        print('\tMax Episodes         : {0}'.format(args.max_episodes))
    elif args.action == 'train':
        print('\tMax Training Entries : {0}'.format(args.max_training_entries))
    elif args.action == 'run':
        print('\tPrompt               : {0}'.format(args.prompt))
        print('\tModel ID             : {0}'.format(args.model_id))
        print('\tActs                 : {0}'.format(args.acts))
        print('\tEpisode Number       : {0}'.format(args.episode_number))
    print('\tDebug Mode           : {0}'.format(args.debug))
    return args

if __name__ == "__main__":
    args = parse_arguments()

    logging.basicConfig(format='%(levelname)s - %(asctime)s - %(message)s', level=logging.DEBUG if args.debug else logging.INFO, force=True)

    if args.action == 'scrape':
        print('Running scraper (this may take a while)...')
        scraper = Scraper()
        scraper.run(startEpisode=1, endEpisode=args.max_episodes)
        print('Done! Output generated at {0}'.format(scraper.OUTPUT_FILENAME))

    elif args.action == 'train':
        print('Running trainer (this may take a while)...')
        trainer = TAMTrainer()
        trainer.run(max_training_set=args.max_training_entries)
        print('Done! Output generated at {0}'.format(trainer.OUTPUT_FILENAME))
        print('Now that training data has been created, confirm the data was prepared correctly and then upload it to OpenAI')
        print('1. Prepare: openai tools fine_tunes.prepare_data -f {0}'.format(trainer.OUTPUT_FILENAME))
        print('2. Upload: openai api fine_tunes.create -t {0} -m <BASE_MODEL>'.format(trainer.OUTPUT_FILENAME))

    elif args.action == 'run':
        print('Creating your episode (this may take a while)...')
        if args.prompt is None or args.model_id is None or args.api_key is None or args.episode_number is None:
            logging.error("--api-key, --episode_number, --prompt, and --model-id are required for run action")
            sys.exit(1)
        generator = Generator(args.api_key, args.model_id)
        if generator.run(args.prompt, args.episode_number, numberOfActs=args.acts):
            print('Done! Episode generated at {0}'.format(Generator.EPISODE_FOLDER.format(args.episode_number)))
