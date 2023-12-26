from random import shuffle
import json
from .models import Card, Face
from .ned import Ned

class Player:
    def __init__(self):
        self.player_name = ''
        self.player_type = ''
        self.sideboard = []
        self.library = []
        self.battlefield = []
        self.hand = []
        self.graveyard = []
        self.exile = []
        self.seen_opponent_cards = {
                'this_game': [],
                'this_match': [],
        }
        self.hitpoints = 20

    def set_player_name(self, name):
        self.player_name = name

    def set_player_type(self, _type):
        self.player_type = _type
        if self.player_type == 'ai':
            self.ai = Ned()

    def shuffle(self):
        shuffle(self.library)

    def toJSON(self):
        return json.dumps(self, default=lambda x: x.__dict__, sort_keys=True)

    def __str__(self):
        return self.player_name

    def __repr__(self):
        return self.player_name

class Game:
    def __init__(self, max_players=2):
        self.has_ended = False
        self.max_players = max_players
        self.card_map = {} # {id: cardname}
        self.players = []
        self.stack = []
        self.turn_count = 0
        self.whose_turn = 0
        self.phase = 0
        self.whose_priority = 0

    def add_player(self, data):
        player = Player()
        player.set_player_name(data['player_name']) # 'ned' or 'user'
        player.set_player_type(data['player_type']) # 'ai' or 'human'
        main, side = data['main'], data['side']
        all_cards = main | side
        self.import_card_map(all_cards, player.player_name)
        self.load_cards(player, main, side)
        self.players.append(player)

    def import_card_map(self, cards, name):
        player_id = name[0] # 'n' for ned and 'u' for user
        cardnames = list(cards.keys())
        cardnames.sort()
        for i, cardname in enumerate(cardnames):
            card_id = f'{player_id}{i+1}'
            self.card_map[card_id] = cardname

    def load_cards(self, player, main, side):
        rev_map = { value: key for key, value in self.card_map.items() }
        for name, count in main.items():
            card = {}
            for i in range(1, count + 1):
                _id = rev_map[name] + '#' + str(i)
                card['id'] = _id
                card['name'] = name
                player.library.append(card)
        for name, count in side.items():
            card = {}
            for i in range(1, count + 1):
                _id = rev_map[name] + '#' + str(i)
                card['id'] = _id
                card['name'] = name
                player.sideboard.append(card)

    def start(self):
        self.has_ended = False
        shuffle(self.players)
        for player in self.players:
            shuffle(player.library)

    def toJSON(self):
        return json.dumps(self, default=lambda x: x.__dict__, sort_keys=True)

class Match:
    def __init__(self, **kwargs):
        self.mtg_format = kwargs['mtg_format']
        max_players = 2
        match(self.mtg_format):
            case 'modern':
                max_players = 2
        self.max_games = kwargs['games']
        self.games_played = 0
        self.scores = [ 0, 0 ]
        self.game = Game(max_players)
