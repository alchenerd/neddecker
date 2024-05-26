from typing import Dict, List, Any, Optional, Callable
from langgraph.graph import END, StateGraph
import json
import random
from dataclasses import dataclass, field
from functools import wraps
from .game import Match, Game, Player
from .rules import Rule, SYSTEM_RULES
from .game_rules_writer import GameRulesWriter as Naya


class GameRulesEngine:
    def __init__(self, consumer):
        self.consumer = consumer
        self._match = None
        self.game = None
        self.input = None
        self.events = []
        self.line = None
        self.changes = []
        self.placeholder = []
        self.rules = []
        self.rules.extend(SYSTEM_RULES)
        self.naya = Naya()
        self.halt = True
        self.abort = False

    def _repl(self, data:str) -> None:
        self.input = json.loads(data)
        self.halt = False
        self.abort = False
        while not self.abort and not self.halt:
            self._read()
            self._evaluate()
            self._execute()
            #print(self.events)
            if not self.events:
                break
        #print(self.abort, self.halt)

    def _read(self) -> None:
        """ Translate input into one or more event. """
        if self.input:
            match(self.input['type']):
                case 'register_match': # initiated by user
                    self.register_match()
                case 'register_player': # initiated by user
                    self.register_player()
                    game = self._match.game
                case 'answer': # user's response to 'question'
                    self.handle_answer()
                case 'reorder': # user's response to 'reorder'
                    self.handle_reorder()
                case 'mulligan': # user takes a mulligan
                    self.handle_mulligan()
                case 'keep_hand': # user keeps their hand
                    self.handle_keep_hand()
                case 'interact': # user interacts with an object
                    self.handle_interaction()
                case 'cast': # user casts a spell
                    self.handle_cast()
                case 'activate': # user activates an ability
                    self.handle_activation()
                case 'special_action': # user takes a special action
                    self.handle_special_action()
                case 'abort': # user makes the previous action illegal and the game rolls back
                    self.handle_abort()
                case 'pay_cost': # user responds to 'ask_cost'
                    self.handle_pay_cost()
                case 'pass_priority': # user passes priority
                    self.handle_pass_priority()
        self.input = None # consume

    def _evaluate(self):
        """ Run through the events and check rules. """
        if self.abort:
            return
        while True:
            try:
                self.apply_changes_to_events()
            except ValueError: # reorder is required
                print('value error')
                return
            self.generate_changes_by_rules()
            if not self.changes: # all rules are checked
                print('all rules are checked')
                return

    def apply_changes_to_events(self):
        print('apply_changes_to_events')
        print(self.changes)
        if not self.changes:
            return
        # expecting self.changes to be a list of (item, callable)
        assert all(callable(change[1]) for change in self.changes)
        for matched_event in self.events:
            #print(self.events)
            if not self.changes: # no changes to make
                break
            relevant_changes = [ x for x in self.changes if x[0] == matched_event ]
            self.changes = [ x for x in self.changes if x[0] != matched_event ]
            if not relevant_changes:
                continue
            to_apply = None
            if isinstance(relevant_changes, list): # this could still be a list of replacement effects (sorted)
                to_apply = relevant_changes[:]
            else:
                to_apply = [ relevant_changes ]
            print('to_apply:', to_apply)
            events = [ line for line in self.events ]
            for event, effect in to_apply:
                print('events', events)
                print('applying', effect, 'to', event)
                events = effect(self.game, events, matched_event)
        self.events = events
        self.changes = []

    def generate_changes_by_rules(self):
        print('generate_changes_by_rules')
        for rule in self.rules:
            for item in self.events:
                self.matched_event = item
                tracking = 'Given'
                for statement in rule.gherkin:
                    start = statement.split(' ')[0]
                    if start == tracking or start == 'And' or start == 'But':
                        start = tracking
                    else:
                        tracking = start
                    f = rule.implementations.get(statement, lambda x: False)
                    assert callable(f)
                    print(statement)
                    print(self.matched_event)
                    print(self.events)
                    match start:
                        case 'Given' | 'When':
                            if not f(self):
                                break
                        case 'Then':
                            print('appending ', f)
                            self.changes.append((item, f))
        self.changes.reverse() # reverse the appending action so the events will be applied in gherkin order
        return bool(self.changes)

    def _execute(self):
        """ Try to apply the events if able; if can't then the item is pushed back when all is done. """
        if self.abort:
            return
        remainder = []
        while self.events:
            args = self.events.pop()
            print(args)
            f = getattr(self, args[0], None)
            if f and callable(f):
                print("[game action '{}' has fired]".format(args[0]))
                f(*args[1:])
            else:
                remainder.append(args)
        while remainder:
            self.events.append(remainder.pop())

    def register_match(self):
        self._match = Match(
            mtg_format=self.input['format'],
            games=self.input['games'],
            consumer=self.consumer,
        )
        payload = {
                'type': 'match_initialized',
                'message': f'{self._match.max_games} game(s) of {self._match.mtg_format} is initialized.',
        }
        self.consumer.send(text_data=json.dumps(payload))
        self.halt = True
        self.abort = True
        print('[match initialized]')

    def register_player(self):
        game = self._match.game
        game.add_player(self.input)
        added = game.players[-1]
        payload = {
                'type': 'player_registered',
                'message': f'Player {added.player_name} is registered.',
                'count': len(game.players),
                'of': game.max_players,
        }
        self.consumer.send(text_data=json.dumps(payload))

        if len(game.players) == game.max_players:
            game.clear()
            payload = {
                    'type': 'game_start',
                    'game': self._match.games_played + 1,
                    'of': self._match.max_games,
            }
            self.consumer.send(text_data=json.dumps(payload)) # announce start of game
            self.game = self._match.game # shorthand
            payload = game.get_payload(is_update=True)
            self.consumer.send(text_data=json.dumps(payload)) # update game state
            self.events.append(['decide_who_goes_first'])
            self.halt = False
            self.abort = False
        else:
            self.halt = True
            self.abort = True
        print(f'[player {added} initialized]')

    def handle_answer(self):
        print(self.input)
        who = self.input['who']
        question = self.input['question']
        answer = self.input['answer']
        players = self._match.game.players
        [ who ] = [ player for player in players if player.player_name == who ]
        assert who and isinstance(who, Player)
        self.events.append(['answer_question', who, question, answer])

    def question(self, *args):
        player, question, *options = args
        payload = {
            'type': 'log',
            'message': f'Asking {player.player_name} a question: {question}',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = {
            'type': 'question',
            'who': player.player_name,
            'question': question,
            'options': options,
        }
        self.send_to_player(player, json.dumps(payload))
        self.halt = True
        self.abort = False

    def reorder(self, *args):
        player, description, to_reorder = args
        payload = {
            'type': 'log',
            'message': f'Asking {player.player_name} to reorder {description}',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = {
            'type': 'reorder',
            'who': player.player_name,
            'description': description,
            'to_reorder': to_reorder,
        }
        self.send_to_player(player, json.dumps(payload))
        self.halt = True
        self.abort = False

    def handle_mulligan(self):
        print(self.input)
        who_name = self.input['who']
        self.events.append(['mulligan', who_name])

    def handle_keep_hand(self):
        print(self.input)
        who_name = self.input['who']
        bottom = self.input['bottom']
        self.events.append(['keep_hand', who_name, bottom])

    def set_starting_player(self, *args):
        player, *_ = args
        players = self._match.game.players
        idx = players.index(player)
        assert isinstance(idx, int)
        self._match.game.register_first_player(idx)
        payload = {
            'type': 'log',
            'message': f'{player.player_name} goes first.'
        }
        self.consumer.send(text_data=json.dumps(payload))
        self.events.append(['ask_reveal_companion', 0])
        self.halt = False
        self.abort = False

    def send_to_player(self, player, text_data):
        assert isinstance(player, Player)
        match player.player_type:
            case 'ai':
                thoughts, choice = player.ai.receive(text_data=text_data)
                self.send_chat(player, thoughts)
                self._repl(json.dumps(choice))
            case 'human':
                self.consumer.send(text_data=text_data)
        self.halt = True
        self.abort = False

    def send_chat(self, speaker, content):
        payload = {
            'type': 'chat',
            'message': content,
        }
        self.consumer.send(text_data=json.dumps(payload))
        self.halt = True
        self.abort = False

    def set_annotation(self, *args):
        in_game_id, k, v, *_ = args
        game = self._match.game
        payload = {
            'targetId': in_game_id,
            'type': 'set_annotation',
            'annotationKey': k,
            'annotationValue': v,
        }
        game.apply_action(payload)
        payload = {
            'type': 'log',
            'message': f'Set annotation on card ({in_game_id}) with key: {k}, value: {v}',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = game.get_payload(is_update=True)
        self.consumer.send(text_data=json.dumps(payload)) # update game state
        self.halt = False
        self.abort = False

    def shuffle(self, *args):
        player, *_ = args
        player.shuffle()
        payload = {
            'type': 'log',
            'message': f'{player} shuffles',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = self.game.get_payload(is_update=True)
        self.consumer.send(text_data=json.dumps(payload)) # update game state
        self.halt = False
        self.abort = False

    def draw(self, *args):
        player, amount, *_ = args
        for _ in range(amount):
            player.draw()
        payload = {
            'type': 'log',
            'message': f'{player} draws {amount} card(s)',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = self.game.get_payload(is_update=True)
        self.consumer.send(text_data=json.dumps(payload)) # update game state
        self.halt = False
        self.abort = False

    def ask_mulligan(self, *args):
        player, to_bottom, *_ = args
        payload = {
            'type': 'mulligan',
            'hand': player.hand,
            'to_bottom': to_bottom
        }
        self.send_to_player(player, json.dumps(payload))
        self.halt = True
        self.abort = False

    def bottom_cards(self, *args):
        player, card_ids_to_bottom, *_ = args
        amount = len(card_ids_to_bottom)
        while card_ids_to_bottom:
            card_id = card_ids_to_bottom.pop()
            card = [ card for card in player.hand if card['in_game_id'] != card_id ][0]
            player.hand.remove(card)
            player.library.append(card)
        payload = {
            'type': 'log',
            'message': f'{player} bottoms {amount} card(s)',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = self.game.get_payload(is_update=True)
        self.consumer.send(text_data=json.dumps(payload)) # update game state
        self.halt = False
        self.abort = False

    def start_game(self, *_):
        self._match.game.start()
        payload = {
            'type': 'log',
            'message': f'mulligan phase has ended; checking for start of game actions',
        }
        self.consumer.send(text_data=json.dumps(payload))
        payload = self.game.get_payload(is_update=True)
        self.consumer.send(text_data=json.dumps(payload)) # update game state
        self.halt = False
        self.abort = False

    def scan(self, *args):
        who_id, zone_str, *_ = args
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        assert zone_str in ('stack', 'battlefield', 'library', 'hand', 'graveyard', 'exile', 'command')
        game = self._match.game
        to_scan = getattr(player, zone_str) if player else getattr(game, zone_str)
        to_scan = [x for x in to_scan if x['rules'] is None]
        for card in to_scan:
            self.consumer.send_log(f"scanning {card['name']}...")
            card['rules'] = self.naya.write_rules(card=card)
        self.events.append(['scan_done'])
        self.events.append(['_manual_halt']) # FIXME: this is here for debug reasons

    def scan_start_of_game_in_hand(self, *args):
        """search in the player's hand for one or more start of game card"""
        who_id, *_ = args
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        zone = player.hand
        CR_103_6_OPENING_HAND = """103.6a If a card allows a player to begin the game with that card on the battlefield, the player taking this action puts that card onto the battlefield.

103.6b If a card allows a player to reveal it from their opening hand, the player taking this action does so. The card remains revealed until the first turn begins. Each card may be revealed this way only once.""".replace('{', '{{').replace('}', '}}')
        interactible_cards = []
        for card in zone:
            oracle_text = card.get('oracle_text', None) or card['faces']['front']['oracle_text']
            yn = self.naya.ask_yes_no(context=CR_103_6_OPENING_HAND, question=f"Given a card that says: \"{oracle_text}\"\n\nAnswer with YesNoResponse: Is the card described in rule 103.6? Answer \'y\' if the card should be revealed from the opening hand or begin on the battlefield since the game starts; answer \'n\' if the card has no such rules text.")
            if 'y' in yn:
                interactible_cards.append(card)
        if interactible_cards:
            self.events.append(['interactable', interactible_cards])
        self.events.append(['scan_done'])

    def give_priority(self, *args):
        who_id, *_ = args
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        payload = self.game.get_payload()
        interactable = [e for e in self.events if e[0] == 'interactable'][0][1]
        payload['interactable'] = interactable
        self.send_to_player(player=player, text_data=json.dumps(payload))
        self.events.append(['_manual_halt']) # FIXME: this is here for debug reasons

    # """ This is for temporarily halting the GRE.
    def _manual_halt(self, *args):
        self.halt = True
    # """
