import requests
import re
import json
from datetime import date
from os import path, listdir, unlink
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from play.models import Deck

class Command(BaseCommand):
    """
    Syncronize the database before starting the server.
    """

    def goldfish_outdated(self):
        deck_count = Deck.objects.count()
        if deck_count < 10:
            return True
        latest_deck = Deck.objects.all().order_by('date', 'id').first()
        if latest_deck == None:
            return True
        today = date.today()
        if (today - latest_deck.date).days > 0:
            return True
        return False

    def update_goldfish(self):
        """
        Fetches the top 10 modern meta decks from mtggoldfish and store into db.
        """
        page = requests.get('https://www.mtggoldfish.com/metagame/modern')
        soup = BeautifulSoup(page.content, 'html.parser')
        mdc = soup.find('div', id='metagame-decks-container')
        scraped_decks = mdc.find_all('div', class_='archetype-tile')
        decks = []
        for i, deck in enumerate(scraped_decks):
            if i == 10:
                break
            title = deck.find('div', class_='archetype-tile-title').find('a', href=True)
            name = title.text
            meta = float(deck.find('div', class_='archetype-tile-statistics').find('div', class_='archetype-tile-statistic-value').find_next(string=True).strip('% \t\n\r'))
            url = 'https://www.mtggoldfish.com' + title['href']
            decks.append({'name': name, 'meta': meta, 'url': url})
            print(f'Fetched metadata of {name}')
        # fetch decklist with url
        for deck in decks:
            page = requests.get(deck['url'])
            soup = BeautifulSoup(page.content, 'html.parser')
            dropdown = soup.find('a', href=re.compile('^/deck/download'))
            response = requests.get('https://www.mtggoldfish.com' + dropdown.get('href'))
            deck['decklist'] = response.content.decode('utf-8')
            print(f"Fetched decklist of {deck['name']}")
        # bulk create and save
        deck_objs = [Deck(name=d.get('name', ''), meta=d.get('meta', 0), url=d.get('url', ''), decklist=d.get('decklist', '')) for d in decks]
        reply = Deck.objects.bulk_create(deck_objs)
        print(f'Bulk objects inserted: {reply}')

    def scryfall_outdated(self):
        """
        Checks scryfall API for latest default card bulk data; if there is unseen bulk data available, download it and save it in scryfall/; all other files in scryfall/ will be purged.
        """
        # fetch the metadata from scryfall api
        response = requests.get('https://api.scryfall.com/bulk-data')
        r_json = json.loads(response.content.decode('utf-8'))
        data = r_json['data']
        uri = ''
        for record in data:
            if record['type'] == 'default_cards':
                uri = record['download_uri']
        fname = uri.split('/')[-1]
        directory = 'scryfall'
        fpath = path.join(directory, fname)
        if path.exists(fpath):
            # TODO: check the proof of db update instead
            return False
        # delete everything in scryfall/
        for fname_ in listdir(directory):
            fpath_ = path.join(directory, fname_)
            try:
                if path.isfile(fpath_) or path.islink(fpath_):
                    unlink(fpath_)
            except OSError as e:
                print(f'Failed to delete {fpath_}. Reason: {e}')
        # download bulk data from scryfall
        response = requests.get(uri)
        with open(fpath, 'wb') as f:
            f.write(response.content)
        print(fpath)
        return True

    def update_scryfall(self):
        """
        Update Card table with downloaded json file.
        """
        directory = 'scryfall'
        fname = listdir(directory)[0]
        fpath = path.join(directory, fname)
        data = ''
        with open(fpath, 'rb') as f:
            data = f.read()
        data = json.loads(data.decode('utf-8'))
        for card in data:
            if card.get('legalities', {}).get('modern', '') == 'legal':
                print(card.get('name', 'NaN'))
        print(len(data))

    def handle(self, *args, **kwargs):
        try:
            if self.goldfish_outdated():
                Deck.objects.all().delete()
                print('Updating mtggoldfish...')
                self.update_goldfish()
                print('Update mtggoldfish done!')
            if self.scryfall_outdated():
                print('Updating scryfall...')
                self.update_scryfall()
            self.update_scryfall()
            """
            decks = Deck.objects.all().order_by('meta')[:10]
            for deck in decks:
                print(f'[{deck.name}]')
                print(deck.decklist)
            """
        except Exception as e:
            raise CommandError('syncdb failed:', e)
