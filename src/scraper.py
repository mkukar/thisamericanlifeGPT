# scrapes data from This American Life and formats into trainable data
# Created by Michael Kukar 2023

import requests
from bs4 import BeautifulSoup
import logging
import json

class Scraper:

    SOUP_PARSER = 'html.parser'
    OUTPUT_FILENAME = '../episodes.json'
    SOURCE_URL = 'https://thisamericanlife.org/'
    TRANSCRIPT_URI = '{0}/transcript' # episode number

    def parse_transcript(self, episodeNumber):
        logging.debug('parsing transcript for episode {0}'.format(episodeNumber))
        transcriptData = {}
        
        url = self.SOURCE_URL + self.TRANSCRIPT_URI.format(str(episodeNumber))
        page = requests.get(url)
        soup = BeautifulSoup(page.content, self.SOUP_PARSER)

        transcriptData['episodeLinkName'] = soup.find('a', class_='full-episode goto goto-episode')['href']
        transcriptData['episodeName'] = soup.find('h1').text.split(':')[1].strip()
        transcriptData['Acts'] = {}
        for actData in soup.find('article').find('div', class_='content').findAll('div', class_='act'):
            transcriptData['Acts'][actData['id']] = {}
            transcriptData['Acts'][actData['id']]['text'] = self.parse_transcript_act(actData)
            transcriptData['Acts'][actData['id']]['name'] = self.act_id_to_name(actData['id'])
        return transcriptData

    def parse_transcript_act(self, actData):
        seperator = ' : '
        newline = '\n'
        # format will be SPEAKER_NAME : text\nSPEAKER_NAME: text\n...
        actStr = ""
        previousSpeaker = ""
        for dialogue in actData.find('div', class_='act-inner').findAll('div'):
            try:
                speaker = dialogue.find('h4').text.strip()
                previousSpeaker = speaker
            except AttributeError:
                # this means just use the previous speaker instead
                speaker = previousSpeaker
            speech = ""
            for speechParagraph in dialogue.findAll('p'):
                logging.debug(speechParagraph)
                speech += speechParagraph.text.strip()
            actStr += speaker + seperator + speech + newline
        return actStr

    def parse_summary(self, summaryLink, transcriptData):
        logging.debug('parsing summary for {0}'.format(summaryLink))
        url = self.SOURCE_URL + summaryLink
        page = requests.get(url)
        soup = BeautifulSoup(page.content, self.SOUP_PARSER)

        transcriptData['summary'] = ''
        summaryDiv = soup.find('header', class_='episode-header').find('div', class_='field field-name-body field-type-text-with-summary field-label-hidden')
        try:
            transcriptData['summary'] = summaryDiv.find('p').text
        except AttributeError as e:
            transcriptData['summary'] = summaryDiv.find('div', class_='field-item even').text
        
        for actLinks in soup.findAll('a', class_='goto goto-act'):
            for actId, actData in transcriptData['Acts'].items():
                if actLinks.text.strip() in actData['name']:
                    transcriptData['Acts'][actId]['summary'] = self.parse_act_summary(actLinks['href'])
        return transcriptData

    def parse_act_summary(self, actSummaryLink):
        logging.debug('parsing act summary for {0}'.format(actSummaryLink))
        url = self.SOURCE_URL + actSummaryLink
        page = requests.get(url)
        soup = BeautifulSoup(page.content, self.SOUP_PARSER)
        summaryDiv = soup.find('div', class_='field field-name-body field-type-text-with-summary field-label-hidden')
        try:
            return summaryDiv.find('p').text
        except AttributeError as e:
            # does not have a 'p' tag for some reason, just directly writes text
            return summaryDiv.find('div', class_='field-item even').text

    def act_id_to_name(self, actId):
        numToWord = {
            '0' : 'Zero',
            '1' : 'One',
            '2' : 'Two',
            '3' : 'Three',
            '4' : 'Four',
            '5' : 'Five',
            '6' : 'Six',
            '7' : 'Seven',
            '8' : 'Eight',
            '9' : 'Nine'
        }
        # go from act1 -> Act One, prologue -> Prologue
        if 'act' in actId:
            try:
                return 'Act ' + numToWord[actId.split('act')[1]]
            except KeyError as e:
                # cannot parse this number
                logging.error('Could not parse act to a name {0}'.format(actId))
                return ''
        else:
            return actId.capitalize()


    def parse(self, curEpisode):
        transcriptData = self.parse_transcript(curEpisode)
        fullData = self.parse_summary(transcriptData['episodeLinkName'], transcriptData)
        return fullData

    def save_data(self, episode_data, filename):
        with open(filename, 'w') as f:
            json.dump(episode_data, f, indent=4)

    def run(self, startEpisode=1, endEpisode=1, output_filename=OUTPUT_FILENAME):
        episodeData = []
        curEpisode = startEpisode
        while curEpisode <= endEpisode:
            try:
                episodeData.append(self.parse(curEpisode))
            except Exception as e:
                logging.error("Failed to parse episode {0}, skipping...".format(curEpisode))
                logging.error(e)
            curEpisode += 1
        self.save_data(episodeData, filename=output_filename)
