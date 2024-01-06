from random import shuffle
import json
from .ned import Ned
from .iterables import MtgTurnsAndPhases as MTGTNPS

class Player:
    def __init__(self):
        self.player_name = '' # 'ned' or 'user'
        self.player_type = '' # 'human' or 'ai'
        self.sideboard = [] # {id, name}
        self.library = [] # {id, name}
        self.battlefield = [] # {id, name, tapped, flipped, counters, annotations}
        self.hand = [] # {id, name, typeline, mana}
        self.graveyard = [] # {id, name}
        self.exile = [] # {id, name}
        self.hp = 20
        self.infect = 0

    def set_player_name(self, name):
        self.player_name = name

    def set_player_type(self, _type):
        self.player_type = _type
        if self.player_type == 'ai':
            self.ai = Ned()

    def shuffle(self):
        shuffle(self.library)

    def untap(self):
        for card in self.battlefield:
            if card.get('tapped', None) == True:
                card['tapped'] = False

    def first_draw(self, turn_count):
        if (turn_count > 1):
            self.draw()

    def draw(self):
        try:
            self.hand.append(self.library.pop(0))
        except IndexError:
            return -1
        return 0

    def cleanup(self):
        for card in self.battlefield:
            if card.get('annotations', {}).get('damage', None):
                card['annotations']['damage'] = 0

    def move_card(self, item, _from, to):
        assert(item[id][0] == self.player_name[0])
        src_zone = _from
        dst_zone = to
        for zone in (src_zone, dst_zone):
            if isinstance(zone, str):
                zone = self.getattr(zone)
        assert(isinstance(src_zone, list))
        assert(isinstance(dst_zone, list))
        src_zone.remove(item)
        dst_zone.append(item)

    def clear(self):
        self.hp = 20
        self.infect = 0
        for zone in (self.hand, self.battlefield, self.graveyard, self.exile):
            for card in zone:
                self.move_card(card, _from=zone, to='library')

    def get_board_state(self):
        board_state = {}
        board_state['player_name'] = self.player_name
        board_state['library'] = self.library
        board_state['battlefield'] = self.battlefield
        board_state['hand'] = self.hand
        board_state['graveyard'] = self.graveyard
        board_state['exile'] = self.exile
        board_state['hp'] = self.hp
        board_state['infect'] = self.infect
        return board_state

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
        self.turn_count = 1
        self.whose_turn = ''
        self.phase = 0
        self.whose_priority = ''
        self.player_has_priority = False
        self.turn_phase_tracker = None

    def add_player(self, data):
        player = Player()
        player.set_player_name(data['player_name']) # 'ned' or 'user'
        player.set_player_type(data['player_type']) # 'ai' or 'human'
        main, side = data['main'], data['side']
        all_cards = main | side
        self.import_card_map(all_cards, player.player_name)
        self.load_cards(player, main, side)
        self.players.append(player)

    def shuffle_players(self):
        shuffle(self.players)
        self.turn_phase_tracker = iter(MTGTNPS([p.player_name for p in self.players]))

    def import_card_map(self, cards, name):
        player_id = name[0] # 'n' for ned and 'u' for user
        cardnames = list(cards.keys())
        cardnames.sort()
        for i, cardname in enumerate(cardnames):
            card_id = f'{player_id}{i+1}'
            self.card_map[card_id] = cardname

    def load_cards(self, player, main, side):
        rev_map = { value: key for key, value in self.card_map.items() }
        visited = {}
        for name in main.keys():
            visited[name] = 1
        for name in side.keys():
            visited[name] = 1
        for name, count in main.items():
            for i in range(count):
                card = dict()
                _id = rev_map[name] + '#' + str(visited[name])
                visited[name] += 1
                card['id'] = _id
                card['name'] = name
                player.library.append(card)
        for name, count in side.items():
            for i in range(count):
                card = dict()
                _id = rev_map[name] + '#' + str(visited[name])
                visited[name] += 1
                card['id'] = _id
                card['name'] = name
                player.sideboard.append(card)

    def start(self):
        self.next_step()

    def next_step(self):
        self.turn_count, self.whose_turn, (self.phase, self.player_has_priority) = next(self.turn_phase_tracker)
        self.apply_turn_based_actions()

    def apply_turn_based_actions(self):
        player = self.whose_turn
        player = [p for p in self.players if p.player_name == player][0]
        match self.phase:
            case 'untap step':
                player.untap()
            case 'draw step':
                player.first_draw(self.turn_count)
            case 'cleanup step':
                player.cleanup()

    def apply(self, action):
        pass

    def get_payload(self):
        payload = {}
        if self.player_has_priority:
            payload = {
                'type': 'receive_priority',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': self.whose_priority,
                'board_state': self.get_board_state(),
            }
        else:
            payload = {
                'type': 'log',
                'message': f"Turn {self.turn_count}: {self.whose_turn}'s turn\n{self.phase}",
            }
        return payload

    def move_to_owner(self, item, _from, to):
        owner = [p for p in self.players if p.player_name[0] == item['id'][0]][-1]
        assert(owner)
        src_zone = _from
        dst_zone = to
        for zone in (src_zone, dst_zone):
            if zone == 'stack':
                zone = self.stack
            elif isinstance(zone, str):
                zone = owner.getattr(zone)
        assert(isinstance(src_zone, list))
        assert(isinstance(dst_zone, list))
        src_zone.remove(item)
        dst_zone.append(item)

    def clear(self):
        for card in self.stack:
            self.move_to_owner(card, _from=self.stack, to='library')
        for player in self.players:
            player.clear()
        self.players.append(self.players.pop(0))
        self.turn_phase_tracker = iter(MTGTNPS([p.player_name for p in self.players]))
        # will be overwritten but set just in case
        self.turn_count = 0
        self.whose_turn = self.players[0].player_name
        self.phase = 0
        self.whose_priority = self.players[0].player_name
        self.priority_waitlist = []
        self.has_ended = False

    def get_board_state(self):
        board_state = {}
        board_state['stack'] = self.stack
        board_state['players'] = [p.get_board_state() for p in self.players]
        return board_state

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