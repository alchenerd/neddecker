from random import shuffle
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
        self.hitpoints = 20

    def set_player_name(self, name):
        self.player_name = name

    def set_player_type(self, _type):
        self.player_type = _type
        if self.player_type == 'ai':
            self.ai = Ned()

    def shuffle(self):
        shuffle(self.library)

class Game:
    def __init__(self, max_players=2):
        self.max_players = max_players
        self.card_map = {} # {id: cardname}
        self.players = []
        self.stack = []

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
        for card, count in main.items():
            for i in range(1, count + 1):
                player.library.append(rev_map[card] + '#' + str(i))
        for card, count in side.items():
            for i in range(1, count + 1):
                player.sideboard.append(rev_map[card] + '#' + str(i))

    def start(self):
        shuffle(self.players)
        for player in self.players:
            shuffle(player.library)

    def cids_to_cards(self, ids):
        cards = []
        for _id in ids:
            t_id = _id.split('#')[0]
            name = self.card_map[t_id]
            cards.append({
                'id': _id,
                'name': name,
            })
        return cards

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
