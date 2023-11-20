import requests
from bs4 import BeautifulSoup 
from numpy.random import choice
from numpy import array
from urllib.request import urlretrieve
import re

class Goldfish:
    def __init__(self, url='https://www.mtggoldfish.com', endpoint='/metagame/modern'):
        self.URL = url
        self.ENDPOINT = endpoint
        page = requests.get(self.URL + self.ENDPOINT)
        soup = BeautifulSoup(page.content, "html.parser")
        meta_decks = soup.find('div', id='metagame-decks-container')
        decks = meta_decks.find_all('div', class_='archetype-tile')
        self.deck_options = {}
        for deck in decks:
            title = deck.find('div', class_='archetype-tile-title').find('a', href=True)
            deck_link = self.URL + title['href']
            meta = deck.find('div', class_='archetype-tile-statistics').find('div', class_='archetype-tile-statistic-value').find_next(string=True).strip(' \t\n\r')
            self.deck_options[title.text] = {'name': title.text, 'meta': float(meta.strip('%'))/100, 'link': deck_link}
        self.deck_names = [*self.deck_options.keys()]
        self.probabilities = array([stat['meta'] for deck, stat in self.deck_options.items()])
    def random_meta_deck(self):
        probabilities = self.probabilities / self.probabilities.sum()
        [chosen] = choice(self.deck_names, 1, p=probabilities)
        return {chosen: self.deck_options[chosen]}
    def fetch_decklist(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")
        dropdown = soup.find('a', href=re.compile('^/deck/download'))
        download_endpoint = dropdown.get('href')
        response = requests.get(self.URL + download_endpoint)
        data = response.headers.get('content-disposition', 'filename=\"decklist.txt\"')
        filename = data.split('filename=')[1].strip('\"')
        with open('neds_decks/' + filename, 'wb') as f:
            f.write(response.content)
        return filename

if __name__ == '__main__':
    goldfish = Goldfish()
    chosen_deck = goldfish.random_meta_deck()
    [chosen_deck_name] = chosen_deck.keys()
    print(chosen_deck_name)
    print(f'{chosen_deck[chosen_deck_name]["meta"]:.1%}')
    chosen_link = chosen_deck[chosen_deck_name]['link']
    print(chosen_link)
    decklist_path = goldfish.fetch_decklist(chosen_link)
    print(decklist_path)
