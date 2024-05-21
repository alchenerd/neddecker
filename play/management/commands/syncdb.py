import requests
import re
import json
import ijson
from datetime import date
from os import path, listdir, unlink, utime
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db.models.functions import Length
from django.contrib.postgres.search import TrigramSimilarity
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from play.models import Deck, Card, Face

class Command(BaseCommand):
    """
    Syncronize the database before starting the server.
    """

    def is_goldfish_outdated(self):
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
            art = deck.find('div', class_='card-image-tile')['style'].split("('")[1].split("')")[0]
            decks.append({'name': name, 'meta': meta, 'url': url, 'art': art})
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
        deck_objs = [Deck(name=d.get('name', ''), meta=d.get('meta', 0), url=d.get('url', ''), decklist=d.get('decklist', ''), art=d.get('art', ''),) for d in decks]
        reply = Deck.objects.bulk_create(deck_objs)
        print(f'Bulk objects inserted: {reply}')

    def is_scryfall_outdated(self):
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
        if path.exists(fpath + '.done'):
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
        obj_cards = []
        obj_faces = []
        with open(fpath, 'r', encoding='utf-8') as f:
            for cards in ijson.items(f, ''):
                for card in cards:
                    if card['booster'] == False or card['textless'] == True:
                        continue
                    print(f"Processing {card['name']}")
                    obj_card = Card(
                            cmc=card.get('cmc', 0.0),
                            colors=''.join(card.get('colors', '')),
                            defense=card.get('defense', ''),
                            loyalty=card.get('loyalty', ''),
                            mana_cost=card.get('mana_cost', ''),
                            name=card.get('name', ''),
                            oracle_text=card.get('oracle_text', ''),
                            power=card.get('power', ''),
                            produced_mana=card.get('produced_mana', ''),
                            toughness=card.get('toughness', ''),
                            type_line=card.get('type_line', ''),
                            card_image_uri=card.get('image_uris', {}).get('normal', ''),
                            layout=card.get('layout', ''),
                            )
                    obj_cards.append(obj_card)
                    if card.get('card_faces', None):
                        print(f"Processing faces of {card['name']}")
                        faces = card['card_faces']
                        for face in faces:
                            obj_face = Face(
                                    card=obj_card,
                                    cmc=face.get('cmc', 0.0),
                                    colors=''.join(face.get('colors', '')),
                                    defense=face.get('defense', ''),
                                    loyalty=face.get('loyalty', ''),
                                    mana_cost=face.get('mana_cost'),
                                    name=face.get('name', ''),
                                    oracle_text=face.get('oracle_text', ''),
                                    power=face.get('power', ''),
                                    toughness=face.get('toughness', ''),
                                    type_line=face.get('type_line', ''),
                                    card_image_uri=face.get('image_uris', {}).get('normal', ''),
                            )
                            obj_faces.append(obj_face)
        Card.objects.bulk_create(obj_cards, batch_size=100)
        Face.objects.bulk_create(obj_faces, batch_size=100)
        print(f'Scyfall JSON file parsed and added.')
        with open(fpath + '.done', 'a'):
            try:
                utime(fname, None)
            except OSError:
                pass

    def mtggoldfish_align_card_name(self):
        for deck in Deck.objects.all():
            new_decklist = ''
            for line in deck.decklist.split('\r\n'):
                if line == '':
                    new_decklist += '\r\n'
                    continue
                splitted = line.split(' ')
                count = splitted[0]
                name = ' '.join(splitted[1:])
                searched_card = Card.objects.filter(name=name).first()
                if not searched_card:
                    print(f'Before: {name}')
                    trig_card = Card.objects.annotate(similarity=TrigramSimilarity('name', name),).filter(similarity__gt=0.3).order_by('-similarity', Length('card_image_uri').desc()).first()
                    name = trig_card.name
                    print(f'After: {name}')
                new_decklist += ' '.join((count, name)) + '\r\n'
            deck.decklist = new_decklist
            deck.save()

    def get_comprehensive_rules(self):
        rules_page = 'https://magic.wizards.com/en/rules'
        page = requests.get(rules_page)
        soup = BeautifulSoup(page.content, 'html.parser')
        txt_spans = soup.find_all('span', 'txt')
        txt = [x for x in txt_spans if x.text == 'TXT'][0]
        a = txt.find('a', href=True)
        comprehensive_rules_link = a['href']
        print('Fetching Comprehension Rules from', comprehensive_rules_link)
        directory = 'wotc'
        fname = 'comprehensive_rules.txt'
        fpath = path.join(directory, fname)
        print(fpath)
        response = requests.get(comprehensive_rules_link)
        with open(fpath, 'wb') as f:
            f.write(response.content)

    def create_rag_database(self):
        with open('wotc/comprehensive_rules.txt') as f:
            raw_document = f.read()
        regex_expr = r"\d+\.\d+\. \w+"
        text_splitter = RecursiveCharacterTextSplitter(regex_expr, chunk_size=1000, chunk_overlap=200)
        documents = text_splitter.create_documents([raw_document])
        db = Chroma.from_documents(documents, OpenAIEmbeddings(), persist_directory='./rag')
        print('Chroma db is made')
        docs = db.similarity_search('Detailed definition of keyword Ninjutsu that starts with 701 or 702')
        print(docs[0])
        content = '\n'.join(p.page_content for p in (docs[0], docs[1]))
        print(content)
        title_line = [x for x in content.split('\n') if x.endswith('. Ninjutsu')][0]
        print(title_line)
        header = title_line.split(' ')[0][:-1]
        print(header)
        filtered = '\n\n'.join(x for x in content.split('\n') if x.startswith(header))
        print(filtered)

    def make_rag(self):
        """Make a RAG vector database for searching comprehensive rules."""
        self.get_comprehensive_rules()
        self.create_rag_database()

    def add_arguments(self, parser):
        parser.add_argument('--rag', action='store_true', help='Make a RAG database from comprehensive rules')

    def handle(self, *args, **kwargs):
        try:
            if self.is_goldfish_outdated():
                print('Goldfish data is outdated; discarding table Deck...')
                Deck.objects.all().delete()
                print('Updating mtggoldfish...')
                self.update_goldfish()
                print('Update mtggoldfish done!')
            if self.is_scryfall_outdated():
                print('Scryfall data is outdated; discarding table Card and Face...')
                Card.objects.all().delete()
                Face.objects.all().delete()
                print('Updating scryfall...')
                self.update_scryfall()
            self.mtggoldfish_align_card_name()
        except Exception as e:
            raise CommandError('syncdb failed:', e)
        if 'rag' in kwargs and kwargs['rag']:
            self.make_rag()
