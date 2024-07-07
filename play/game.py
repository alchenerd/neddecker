import json
import re
from random import shuffle
from string import Formatter
from copy import copy
from typing import Optional, List, Dict, Union, Literal, Any
from langchain_core.pydantic_v1 import Field
from .models import get_card_by_name_as_dict, get_faces_by_name_as_dict
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
        self.command = []
        self.ante = []
        self.mana_pool = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}
        self.hp = 20
        self.counters = {}
        self.annotations = {}
        self.delayed_triggers = []
        self.land_played = 0

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

    def draw(self):
        self.hand.append(self.library.pop(0))

    def cleanup(self):
        for card in self.battlefield:
            if card.get('annotations', {}).get('damage', None):
                card['annotations']['damage'] = 0

    def move_card(self, item, _from, to):
        assert item[id][0] == self.player_name[0]
        src_zone = _from
        dst_zone = to
        for zone in (src_zone, dst_zone):
            if isinstance(zone, str):
                zone = self.getattr(zone)
        assert isinstance(src_zone, list)
        assert isinstance(dst_zone, list)
        src_zone.remove(item)
        dst_zone.append(item)

    def clear(self):
        self.hp = 20
        self.land_played = 0
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
        board_state['sideboard'] = self.sideboard
        board_state['mana_pool'] = self.mana_pool
        board_state['counters'] = self.counters
        board_state['annotations'] = self.annotations
        board_state['delayed_triggers'] = self.delayed_triggers
        return board_state

    def apply_board_state(self, updated):
        assert self.player_name == updated.get('player_name', 'ned')
        assert 'delayed_triggers' in updated.keys()
        for k, v in updated.items():
            #print('updating k = ' + k)
            #print('updating v = ' + str(v))
            setattr(self, k, v)

    def __str__(self):
        return self.player_name

    def __repr__(self):
        return self.player_name


class Game:
    def __init__(self, max_players=2, consumer=None):
        self.consumer = consumer
        self.has_ended = False
        self.end_reason = ''
        self.winner = None
        self.loser = None
        self.max_players = max_players
        self.card_map = {} # {id: cardname}
        self.players = []
        self.starting_player_decider = None
        self.starting_player = None
        self.stack = []
        self.last_known_stack_hash = None
        self.pending_triggers = []
        self.turn_count = 1
        self.whose_turn = ''
        self.phase = ''
        self.whose_priority = ''
        self.is_resolving = False
        self.player_has_priority = False
        self.require_player_action = False
        self.stack_has_grown = False
        self.turn_phase_tracker = None
        self.priority_waitlist = []
        self.static_effects = []

    def add_player(self, data):
        player = Player()
        player.set_player_name(data['player_name']) # 'ned' or 'user'
        player.set_player_type(data['player_type']) # 'ai' or 'human'
        main, side = data['main'], data['side']
        all_cards = main | side
        self.import_card_map(all_cards, player.player_name)
        self.load_cards(player, main, side)
        self.players.append(player)
        if player.player_name not in self.__dict__:
            setattr(self, player.player_name, player)

    def register_first_player(self, index):
        if isinstance(index, int) and index:
            self.players = self.players[index:] + self.players[:index]
        self.turn_phase_tracker = iter(MTGTNPS([p.player_name for p in self.players]))
        self.starting_player = self.players[0]

    def import_card_map(self, cards, name):
        player_id = name[0] # 'n' for ned and 'u' for user
        cardnames = list(cards.keys())
        cardnames.sort()
        for i, cardname in enumerate(cardnames):
            card_id = f'{player_id}{i+1}'
            self.card_map[card_id] = cardname

    def get_ai_annotations(self, card):
        """Get a tag set that helps data preprocessing for the AI player."""
        ai_annotations = []
        oracle_text = card.get('oracle_text', '').lower() or \
                card.get('faces', {}).get('front', {}).get('oracle_text', '').lower()

        # general tags
        # has triggered ability?
        if re.search('when', oracle_text):
            ai_annotations.append('has_trigger')

        # start of game specific tags: check scryfall `q=otag:start-of-game f:modern`
        # is companion?
        if 'companion' in oracle_text:
            ai_annotations.append('is_companion')
        # can reveal at start of game?
        if 'opening hand' in oracle_text:
            ai_annotations.append('should_reveal_at_start_of_game')
        # can begin the game with the card on the battlefield?
        if 'begin the game with' in oracle_text:
            ai_annotations.append('should_move_to_battlefield_at_start_of_game')

        # untap tags
        # triggered when day/night changes?
        if re.search('becomes[^,]+(day|night)', oracle_text):
            ai_annotations.append('day_night_matters')
        # triggered when untap?
        if any(substring in oracle_text for substring in ['becomes untapped', 'whenever you untap']):
            ai_annotations.append('untap_matters')

        # upkeep tags
        # at the beginning of .+ upkeep?
        if re.search('at the beginning of .+ upkeep', oracle_text):
            ai_annotations.append('beginning_upkeep')

        # draw tags
        # triggered when draw?
        if re.search('when.+draw', oracle_text) or re.search('drawn.+this turn', oracle_text):
            ai_annotations.append('draw_matters')
        # draw replacement?
        if re.search('draw.+instead', oracle_text):
            ai_annotations.append('draw_replacement')

        # main phase tags
        # at the beginning of the main phase?
        if re.search('beginning[^.]+main phase', oracle_text):
            if re.search('precombat main', oracle_text):
                ai_annotations.append('beginning_precombat_main')
            elif re.search('postcombat main', oracle_text):
                ai_annotations.append('beginning_postcombat_main')
            else:
                ai_annotations('beginning_main')

        # combat tags
        # at the beginning of combat?
        if re.search('beginning[^,]+combat on your turn', oracle_text) or \
                re.search('beginning[^,]+(each|next|that|of) combat', oracle_text):
            ai_annotations.append('beginning_combat')
        # triggered when attacking?
        if re.search('when[^,]+attack', oracle_text):
            ai_annotations.append('attacking_matters')
        # triggered when blocked?
        if re.search('when[^,]+block', oracle_text):
            ai_annotations.append('blocking_matters')
        # triggered when dealing combat damage?
        if re.search('when[^,]+deals? combat damage', oracle_text):
            ai_annotations.append('dealing_combat_damage_matters')
        # triggered when dealt combat damage?
        if re.search('when[^,]+dealt combat damage', oracle_text):
            ai_annotations.append('dealt_combat_damage_matters')
        # damage replacement?
        if re.search('damage[^,]+instead', oracle_text):
            ai_annotations.append('damage_replacement')

        # cleanup tags
        # lose mana replacement?
        if re.search('lose mana[^,]+instead', oracle_text):
            ai_annotations.append('lose_mana_replacement')

        return ai_annotations

    def load_cards(self, player, main, side):
        rev_map = { value: key for key, value in self.card_map.items() }
        visited = {}
        for name in (main | side).keys():
            visited[name] = 1
        for name, count in main.items():
            for i in range(count):
                card = dict()
                _id = rev_map[name] + '#' + str(visited[name])
                visited[name] += 1
                card['in_game_id'] = _id
                card['name'] = name
                card |= get_card_by_name_as_dict(card['name'])
                front, back = get_faces_by_name_as_dict(card['name'])
                if front and back:
                    card['faces'] = dict()
                    card['faces'] |= {'front': front, 'back': back}
                card['counters'] = dict()
                card['annotations'] = dict()
                card['rules'] = None
                card['ai_annotations'] = self.get_ai_annotations(card)
                player.library.append(card)
        for name, count in side.items():
            for i in range(count):
                card = dict()
                _id = rev_map[name] + '#' + str(visited[name])
                visited[name] += 1
                card['in_game_id'] = _id
                card['name'] = name
                card |= get_card_by_name_as_dict(card['name'])
                front, back = get_faces_by_name_as_dict(card['name'])
                if front and back:
                    card['faces'] = dict()
                    card['faces'] |= {'front': front, 'back': back}
                card['counters'] = dict()
                card['annotations'] = dict()
                card['rules'] = None
                card['ai_annotations'] = self.get_ai_annotations(card)
                player.sideboard.append(card)

    def set_companion(self, _id):
        sideboards = [ player.sideboard for player in self.players ]
        for sideboard in sideboards:
            for card in sideboard:
                if card['in_game_id'] == _id:
                    card['annotations']['isCompanion'] = True
                    return

    def get_visible_cards(self):
        cards = []
        cards.extend(self.stack)
        for player in self.players:
            cards.extend(player.hand)
            cards.extend(player.battlefield)
            cards.extend(player.graveyard)
            cards.extend(player.exile)
            cards.extend(player.command)
        return cards

    def start(self):
        self.next_step()

    def next_step(self):
        old_turn_count = self.turn_count
        self.turn_count, self.whose_turn, (self.phase, self.player_has_priority, self.require_player_action) = next(self.turn_phase_tracker)
        self.whose_priority = self.whose_turn
        self.refill_priority_waitlist(next_player=self.whose_priority)
        if self.turn_count != old_turn_count:
            player = getattr(self, self.whose_turn, None)
            if player:
                player.land_played = 0

    def refill_priority_waitlist(self, next_player=None):
        if next_player is None:
            next_player = self.whose_turn
        self.priority_waitlist = [p.player_name for p in self.players]
        while True:
            if self.priority_waitlist[0] != next_player:
                self.priority_waitlist.append(self.priority_waitlist.pop(0))
            else:
                break
        assert len(self.priority_waitlist) == len(self.players)
        assert self.priority_waitlist[0] == next_player

    def record_actions(self, actions, grouping):
        grouped = list()
        current = dict()
        for index, action in enumerate(actions):
            search = [ group for group in grouping if (index >= group[1] and index <= group[2] )]
            if not search:
                current['tag'] = None
                if 'group' not in current:
                    current['group'] = list()
                current['group'].append(action)
                grouped.append(current)
                current = dict()
            else:
                group_attributes = search[0]
                current['tag'] = group_attributes[0]
                if 'group' not in current:
                    current['group'] = list()
                current['group'].append(action)
                if index == group_attributes[2]:
                    grouped.append(current)
                    current = dict()
        print('Grouped actions: ' + str(grouped))
        self.actions = grouped

    def apply_action(self, action):
        if 'group' in action:
            action = action.get('group')
        if isinstance(action, list):
            action = action[0]
        print("Applying an action!")
        print(action)
        target_id = action.get('targetId', None)
        who = action.get('who', None)
        if not who and target_id:
            who = target_id[0] # n for ned or u for user
        if who:
            [ player ] = [ p for p in self.players if p.player_name.startswith(who) ] # not correct but convenient

        zones = [ getattr(p, z) for z in ('library', 'hand', 'battlefield', 'graveyard', 'sideboard') for p in self.players ]
        zones.append(self.stack)

        found_card = None
        found_zone = None
        if target_id and '#' in target_id:
            for zone in zones:
                for card in zone:
                    if card['in_game_id'] == target_id:
                        found_card = card
                        found_zone = zone
                        break
                if found_card:
                    break
            assert found_card

        match action.get('type'):
            case 'create_token' | 'create_copy':
                token = {**action.get('card', {})}
                splitted = action.get('destination').split('.')
                destination = splitted[-1]
                recipient = '.'.join(splitted[:-1])
                if 'stack' in action.get('to'):
                    found_card['annotations']['controller'] = self.whose_priority
                    self.stack.append(token)
                else:
                    if 'ned' in recipient:
                        recipient = [ p for p in self.players if 'ned' in p.player_name ][0]
                    elif 'user' in recipient:
                        recipient = [ p for p in self.players if 'user' in p.player_name ][0]
                    else:
                        [digit] = [ c for c in recipient if c.isdigit() ]
                        assert digit is not []
                        digit = int(digit[0])
                        recipient = self.players[digit]
                    getattr(recipient, destination).append(token)
                return
            case 'create_trigger':
                stack = self.stack
                relevants = [card for card in stack if card['in_game_id'].endswith(found_card['in_game_id'])]
                used_ids = [ int(card['in_game_id'].split('@')[0]) for card in relevants if '@' in card['in_game_id']]
                seen = set(used_ids)
                enum = set(range(1, len(seen) + 2)) # edge and factor in seen could be (1, 2, 3)
                next_serial_number = 1 if not seen else min(enum - seen)
                controller = player.player_name
                pseudo_card = copy(found_card)
                pseudo_card['in_game_id'] = 'trigger' + str(next_serial_number) + '@' + found_card['in_game_id']
                pseudo_card['triggerContent'] = action['triggerContent']
                pseudo_card['annotations']['controller'] = action['controller']
                self.stack.append(pseudo_card)
                return
            case 'create_delayed_trigger':
                action |= {'affectingWho': action.get('affectingWho').player_name}
                player.delayed_triggers.append(copy(action))
                return
            case 'move':
                # for move, we cannot assume the owner == whose zone
                splitted = action.get('to').split('.')
                destination = splitted[-1]
                recipient = '.'.join(splitted[:-1])
                if 'stack' in action.get('to'):
                    found_card['annotations']['controller'] = self.whose_priority
                    self.stack.append(copy(found_card))
                else:
                    if 'ned' in recipient:
                        recipient = [ p for p in self.players if 'ned' in p.player_name ][0]
                    elif 'user' in recipient:
                        recipient = [ p for p in self.players if 'user' in p.player_name ][0]
                    else:
                        [digit] = [ c for c in recipient if c.isdigit() ]
                        assert digit is not []
                        digit = int(digit[0])
                        recipient = self.players[digit]
                    getattr(recipient, destination).append(copy(found_card))
                found_zone.remove(found_card)
                return
            case 'set_counter':
                found_card['counters'][action['counterType']] = action['counterAmount']
                return
            case 'set_annotation':
                found_card['annotations'][action['annotationKey']] = action['annotationValue']
            case 'set_player_counter':
                player['counters'][action['counterType']] = action['counterAmount']
                return
            case 'set_player_annotation':
                player['annotations'][action['annotationKey']] = action['annotationValue']
                return
            case 'prevent_untap_all':
                for card in player.battlefield:
                    card['annotations']['preventUntap'] = True
                return
            case 'prevent_untap':
                found_card['annotations']['preventUntap'] = True
                return
            case 'set_mana':
                name = action['targetId'] # expected ned or user
                players = self.players
                [ player ] = [ p for p in players if p.player_name == name ]
                assert player
                player.mana_pool = action['manaPool']
                return
            case 'set_hp':
                name = action['targetId'] # expected ned or user
                players = self.players
                [ player ] = [ p for p in players if p.player_name == name ]
                assert player
                player.hp = action['value']
                return
            case 'pass':
                pass
            case _:
                raise Exception('Unknown action type')


    def is_board_sane(self, board):
        seen_ids = set()
        def _check_unique_ids(item):
            nonlocal seen_ids
            if isinstance(item, dict):
                if 'in_game_id' in item:
                    id_val = item['in_game_id']
                    if id_val in seen_ids:
                        print(id_val, 'is bad!')
                        return False
                    seen_ids.add(id_val)
                for value in item.values():
                    if not _check_unique_ids(value):
                        return False
            elif isinstance(item, list):
                for value in item:
                    if not _check_unique_ids(value):
                        return False
            return True
        return _check_unique_ids(board)

    def apply_board_state(self, board_state):
        if not board_state:
            return
        assert self.is_board_sane(board_state), 'There are duplicate Ids in the new board!'
        players = board_state.get('players', [])
        for updated, tracking in zip(players, self.players):
            tracking.apply_board_state(updated)
        stack = board_state.get('stack', [])
        #print(stack)
        if stack is not self.stack:
            if len(stack) > len(self.stack):
                stack_has_grown = True
            self.stack = stack

    def get_payload(self, is_update=False, is_non_priority_interaction=False):
        payload = {}
        if is_update:
            payload = {
                'type': 'update',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': self.whose_priority,
                'board_state': self.get_board_state(),
                'actions': getattr(self, 'actions', []),
            }
        elif self.is_resolving:
            payload = {
                'type': 'resolve_stack',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': self.whose_priority,
                'board_state': self.get_board_state(),
                'is_resolving': self.is_resolving,
                'actions': getattr(self, 'actions', []),
            }
        elif self.player_has_priority:
            payload = {
                'type': 'receive_priority',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': self.whose_priority,
                'board_state': self.get_board_state(),
                'actions': getattr(self, 'actions', []),
            }
        elif self.require_player_action or is_non_priority_interaction:
            payload = {
                'type': 'require_player_action',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': None,
                'board_state': self.get_board_state(),
                'actions': getattr(self, 'actions', []),
            }
        else:
            payload = {
                'type': 'receive_step',
                'turn_count': self.turn_count,
                'whose_turn': self.whose_turn,
                'phase': self.phase,
                'whose_priority': None,
                'board_state': self.get_board_state(),
                'actions': getattr(self, 'actions', []),
            }
        return payload

    def move_to_owner(self, item, _from, to):
        owner = [p for p in self.players if p.player_name[0] == item['id'][0]][-1]
        assert owner
        src_zone = _from
        dst_zone = to
        for zone in (src_zone, dst_zone):
            if zone == 'stack':
                zone = self.stack
            elif isinstance(zone, str):
                zone = owner.getattr(zone)
        assert isinstance(src_zone, list)
        assert isinstance(dst_zone, list)
        src_zone.remove(item)
        dst_zone.append(item)

    def clear(self):
        for card in self.stack:
            self.move_to_owner(card, _from=self.stack, to='library')
        for player in self.players:
            player.clear()
        self.pending_triggeres = []
        self.players.append(self.players.pop(0))
        self.starting_player_chooser = None
        self.starting_player = None
        self.turn_phase_tracker = iter(MTGTNPS([p.player_name for p in self.players]))
        # will be overwritten but set just in case
        self.turn_count = 1
        self.whose_turn = self.players[0].player_name
        self.phase = ''
        self.whose_priority = self.players[0].player_name
        self.priority_waitlist = []
        self.has_ended = False
        self.static_effects = []

    def get_board_state(self):
        board_state = {}
        board_state['stack'] = self.stack
        board_state['players'] = [p.get_board_state() for p in self.players]
        return board_state

    def find_card_by_id(self, id_str: str) -> Dict[str, Any]:
        for player in self.players:
            for zone_str in ('library', 'hand', 'battlefield', 'graveyard', 'exile', 'command', 'ante'):
                zone = getattr(player, zone_str)
                filtered = [card for card in zone if card['in_game_id'] == id_str]
                if filtered:
                    return filtered[0]
        filtered = [card for card in self.stack if card['in_game_id'] == id_str]
        if filtered:
            return filtered[0]
        return None

    def move_pending_triggers(self):
        """Moves pending triggers onto the stack."""
        self.stack.extend(self.pending_triggers)

class Match:
    def __init__(self, **kwargs):
        self.mtg_format = kwargs['mtg_format']
        max_players = 2
        match(self.mtg_format):
            case 'modern':
                max_players = 2
        self.max_games = kwargs['games']
        self.games_played = 0
        self.scores = [0, 0]
        self.consumer = kwargs['consumer']
        self.game = Game(max_players, self.consumer)
        self.games = [self.game,]
