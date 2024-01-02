from random import shuffle
import json
from .ned import Ned
from .iterables import MtgTurnsAndPhases as MTGTNPS

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
        self.turn_count = 1
        self.whose_turn = None
        self.phase = 0
        self.whose_priority = None
        self.priority_waitlist = []
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

    def phase_to_str(self, i):
        return Game.PHASES_AND_STEPS[i]

    def next_step(self):
        if len(self.priority_waitlist) > 0:
            return self.priority_waitlist.pop(0), True
        player_has_priority = False
        self.turn_count, _, self.whose_turn, (self.phase, player_has_priority) = next(self.turn_phase_tracker)
        if player_has_priority:
            i = 0
            while (self.players[i].player_name != self.whose_turn):
                i += 1
            self.priority_waitlist = []
            while i < len(self.players):
                self.priority_waitlist.append(self.players[i].player_name)
            for player in self.players:
                if player.player_name == self.whose_turn:
                    break
                else:
                    self.priority_waitlist.append(player.player_name)
            return self.priority_waitlist[0], True
        else:
            return self.whose_turn, False

    def get_priority_payload(self):
        return {}

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
