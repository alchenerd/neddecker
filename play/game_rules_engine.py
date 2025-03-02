import json
import random
import pdb
from typing import Dict, List, Any, Optional, Callable
from langgraph.graph import END, StateGraph
from dataclasses import dataclass, field
from functools import wraps
from .game import Match, Game, Player
from .rules import Rule, SYSTEM_RULES
from .game_rules_writer import GameRulesWriter as Naya
from .models import GherkinRule, GherkinImpl, get_card_orm_by_name

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
        self.seen = {}

    def _repl(self, data:str) -> None:
        #try:
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
                """
                print('\n[* end of cycle report *]')
                print('\n'.join(map(str, self.events)))
                _ = input('[* end of cycle press any key to continue *]')
                """
            #print(self.abort, self.halt)
        """
        except Exception as e:
            self.consumer.send_log(f'Something went wrong: {str(e)}')
            breakpoint()
        """

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
                case 'pass_non_priority_action': # user passes non-priority
                    self.handle_pass_non_priority()
                case 'update_gherkin': # user submits a new gherkin rule set for a card
                    self.handle_update_gherkin()
        self.input = None # consume

        # return early if there is no game
        if not hasattr(self, 'game') or not self.game:
            return

        def card_is_visible(name) -> bool:
            """Returns if a card with the same name is in a visible zone from the perspective of the game engine."""
            for card in self.game.stack:
                if card.get('name') == name:
                    return True
            for player in self.game.players:
                for zone_name in ('hand', 'battlefield', 'graveyard', 'exile', 'command'):
                    zone = getattr(player, zone_name)
                    for card in zone:
                        if card.get('name') == name:
                            return True
                    if player.library:
                        if player.library[0].get(name) == name:
                            return True
            return False

        # load rules based on the game state
        self.rules = []
        self.seen = {name: rules for name, rules in self.seen.items() if card_is_visible(name)}
        rules_to_check = []
        rules_to_check.extend(SYSTEM_RULES)
        # FIXME: Don't load card rules yet for they are dangerous
        # for rules in self.seen.values():
            # rules_to_check.extend(rules)
        for rule in rules_to_check:
            given_statements = []
            for statement in rule.gherkin:
                if any(statement.startswith(x) for x in ('When', 'Then')):
                    break
                given_statements.append(statement)
            if all(rule.implementations[s](self) for s in given_statements):
                self.rules.append(rule)
                #print('\n'.join(rule.gherkin), '\nis loaded.')
        assert self.rules

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
            try:
                self.generate_changes_by_rules()
            except IndexError:
                pdb.set_trace()
            if not self.changes: # all rules are checked
                print('all rules are checked')
                self.loop_counter += 1
                if self.loop_counter > 7:
                    breakpoint()
                return
            else:
                self.loop_counter = 0

    def apply_changes_to_events(self):
        #print('apply_changes_to_events')
        #print(self.changes)
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
            #print('to_apply:', to_apply)
            for event, effect in to_apply:
                #print('applying', effect, 'to', event)
                self.matched_event = event
                try:
                    self.events = effect(self)
                except Exception as e:
                    effect = eval(self.naya.rewrite_lambda(self, rule, statement, exception=e))
                    self.events = effect(self)
        self.changes = []

    def generate_changes_by_rules(self):
        #print(f'generate_changes_by_rules: {len(self.rules)}')
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
                    """
                    print(statement)
                    print(self.matched_event)
                    print(self.events)
                    #"""
                    match start:
                        case 'Given' | 'When':
                            try:
                                if not f(self):
                                    break
                            except Exception as e:
                                f = eval(self.naya.rewrite_lambda(self, rule, statement, exception=e))
                                if not f(self):
                                    break
                        case 'Then':
                            #print('appending ', f)
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
            #print(args)
            f = getattr(self, args[0], None)
            if f and callable(f):
                print("[game action '{}' has fired]".format(args[0]))
                f(*args[1:])
            else:
                remainder.append(args)
        while remainder:
            self.events.append(remainder.pop())
        # halt if pending
        is_pending = any('pending' in e[0] for e in self.events)
        if is_pending:
            self.halt = True

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
            self.game.start()
            payload = game.get_payload(is_update=True)
            self.consumer.send(text_data=json.dumps(payload)) # update game state
            self.events.append([self.game.phase])
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

    def handle_interaction(self):
        print(self.input)
        who = [p for p in self.game.players if p.player_name == self.input['who']][0]
        card = self.game.find_card_by_id(self.input['targetId'])
        self.consumer.send_log(f"{who} interacts with {card.get('name', 'null')} ({card.get('in_game_id')})")
        rules = card.get('rules')
        if not rules:
            self.consumer.send_log(f"Scanning {card['name']}")
            rules = self.naya.write_rules(card=card)
            card['rules'] = rules
            self.update_frontend_gherkin(card)
        rules = self.naya.create_gherkin_rules_from_gherkin(rules)
        for rule in rules:
            for line in rule.gherkin:
                assert type(card) == dict
                if 'lambdas' not in card:
                    card['lambdas'] = {}
                card['lambdas'][line] = GherkinImpl.objects.get(gherkin_line=line).lambda_code
        self.update_game_state()
        self.seen[card.get('name')] = rules
        # self.events.append(['interact', who, card]) # FIXME: Don't put the interaction into events for now

    def update_frontend_gherkin(self, card):
        payload = {
            'type': 'update_gherkin',
            'card_name': card.get('name'),
            'gherkin': card.get('rules'),
        }
        self.consumer.send(text_data=json.dumps(payload)) # update game state

    def set_starting_player_decider(self, *args):
        player, *_ = args
        self.game.starting_player_decider = player
        self.consumer.send_log(f'{player.player_name} decides who goes first.')

    def set_starting_player(self, *args):
        player = None
        if args:
            player, *_ = args
        else:
            player = self.game.starting_player_decider
        players = self._match.game.players
        idx = players.index(player)
        assert isinstance(idx, int)
        self._match.game.register_first_player(idx)
        self.events.append(['starting_player_is_set'])
        self.consumer.send_log(f'{player.player_name} goes first.')
        self.update_game_state()

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

    def handle_pass_priority(self):
        print(self.input)
        who_str = self.input['who']
        actions = self.input['actions']
        grouping = self.input.get('grouping', [])
        self.game.record_actions(actions, grouping)
        while self.game.actions:
            action = self.game.actions.pop(0)
            self.game.apply_action(action)
        # recount pass priority if stack changes
        if hash(str(self.game.stack)) != self.game.last_known_stack_hash:
            self.events = [e for e in self.events if 'pass_priority' != e[0]]
        who = [p for p in self.game.players if p.player_name == who_str][0]
        assert who and isinstance(who, Player)
        self.events.append(['pass_priority', who])

    def handle_pass_non_priority(self):
        print(self.input)
        who_str = self.input['who']
        actions = self.input['actions']
        grouping = self.input.get('grouping', [])
        self.game.record_actions(actions, grouping)
        while self.game.actions:
            action = self.game.actions.pop(0)
            self.game.apply_action(action)
        who = [p for p in self.game.players if p.player_name == who_str][0]
        assert who and isinstance(who, Player)
        self.events.append(['pass_non_priority', who])

    def handle_update_gherkin(self):
        card_name = self.input.get('card_name')
        gherkin = self.input.get('gherkin')
        if card_name and gherkin:
            card_orm = get_card_orm_by_name(card_name)
            rule, created = GherkinRule.objects.get_or_create(card=card_orm, defaults={'card': card_orm, 'gherkin': gherkin})
            rule.gherkin = gherkin
            rule.save()
        cards = self.game.find_cards_by_name(card_name)
        for card in cards:
            card['rules'] = gherkin.split('\n\n')
            card['lambdas'] = {line: GherkinImpl.objects.get(gherkin_line=line).lambda_code for line in gherkin.split('\n') if any(line.lower().startswith(x) for x in ('given', 'when', 'then', 'but', 'and'))}
        self.update_game_state()

    def set_as_companion(self, *args):
        in_game_id, *_ = args
        self.set_annotation(in_game_id, 'is_companion', True)

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
        try:
            for _ in range(amount):
                player.draw()
        except IndexError:
            player.has_drawn_from_empty_library = True
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
            card = [ card for card in player.hand if card['in_game_id'] == card_id ][0]
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
            self.update_game_state()
        self.seen[card.get('name')] = card.get('rules')
        self.events.append(['scan_done'])
        #self.events.append(['_manual_halt']) # FIXME: this is here for debug reasons

    def scan_start_of_game_in_hand(self, *args):
        """search in the player's hand for one or more start of game card"""
        who_id, *_ = args
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        zone = player.hand
        CR_103_6_OPENING_HAND = """103.6a If a card allows a player to begin the game with that card on the battlefield, the player taking this action puts that card onto the battlefield.

103.6b If a card allows a player to reveal it from their opening hand, the player taking this action does so. The card remains revealed until the first turn begins. Each card may be revealed this way only once.""".replace('{', '{{').replace('}', '}}')
        interactable_cards = []
        for card in zone:
            if 'interactable' in card:
                if card['interactable']:
                    interactable_cards.append(card)
                continue
            oracle_text = card.get('oracle_text', None) or card['faces']['front']['oracle_text']
            yn = self.naya.ask_yes_no(context=CR_103_6_OPENING_HAND, question=f"Given a card that says: \n\n\"{oracle_text}\"\n\n answer with YesNoResponse: Is the card described in rule 103.6? Answer \'y\' if the card should be revealed from the opening hand or begin on the battlefield at the beginning of the game before the first turn; otherwise, answer \'n\' if the card cannot be played until the first turn.")
            if 'y' in yn:
                card['interactable'] = True
                interactable_cards.append(card)
            else:
                card['interactable'] = False
        self.events = [e for e in self.events if e[0] != 'scanning']
        self.events.append(['interactable', interactable_cards])
        self.events.append(['scan_done'])

    def give_priority(self, *args):
        who_id, interactable, *_ = args
        if interactable is None:
            interactable = self.suggest_interactable_objects(who_id)
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        self.game.last_known_stack_hash = hash(str(self.game.stack))
        payload = self.game.get_payload()
        payload['interactable'] = interactable
        self.events = [e for e in self.events if 'interactable' not in e[0]]
        self.consumer.send_log(f'{player.player_name} gets priority, {interactable=}')
        self.events.append(['pending_pass_priority', who_id, interactable])
        self.send_to_player(player=player, text_data=json.dumps(payload))
        self.halt = True

    def give_pseudo_priority(self, *args):
        who_id, interactable, *_ = args
        if interactable is None:
            interactable = self.suggest_interactable_objects(who_id)
        assert who_id is None or isinstance(who_id, int) and who_id < len(self._match.game.players)
        player = self._match.game.players[who_id] if who_id is not None else None
        self.game.last_known_stack_hash = hash(str(self.game.stack))
        payload = self.game.get_payload(is_non_priority_interaction=True)
        payload['interactable'] = interactable
        self.events = [e for e in self.events if 'interactable' not in e[0]]
        self.consumer.send_log(f"require {player.player_name}'s actions, {interactable=}")
        self.events.append(['pending_pass_non_priority', who_id, interactable])
        self.send_to_player(player=player, text_data=json.dumps(payload))
        self.halt = True

    def suggest_interactable_objects(self, player_id):
        # FIXME: implelent calculate interactable after state-based actions are checked (need static effects)
        ret = []
        game = self.game
        players = game.players
        player = players[player_id]
        is_self_turn = game.whose_turn == player.player_name
        can_cast_sorcery = is_self_turn and 'main' in game.phase and not game.stack
        land_per_turn = 1 + len([e for e in game.static_effects if 'additional land' in str(e).lower()])
        land_played = player.land_played

        # scan hand
        for card in player.hand:
            type_line = card.get('type_line') or card.get('faces').get('front').get('type_line')
            if 'instant' in type_line.lower() or 'flash' in card.get('oracle_text', '').lower():
                ret.append(card)
            elif can_cast_sorcery and 'land' not in type_line.lower():
                ret.append(card)
            elif is_self_turn and 'land' in type_line.lower() and can_cast_sorcery and land_per_turn > land_played:
                ret.append(card)

        # scan static effects
        effects = game.static_effects
        may_play = [e[2] for e in effects if len(e) == 3 and e[0].startswith('may_') and e[1] == player]
        prohibited = set(e[2] for e in effects if len(e) == 3 and e[0].startswith('may_not') and e[1] == player)
        interactable = [x for x in may_play if x not in prohibited]
        interactable = list(set(interactable))
        ret.extend(interactable)
        return ret

    def take_start_of_game_action(self, *args):
        # consume the taking action marker
        self.events = [e for e in self.events if 'taking_start_of_game_action' != e[0]]
        # expecting ['take_start_of_game_action', who, card]
        who, card, *_ = args
        assert isinstance(who, Player)
        assert isinstance(card, dict)
        oracle_text = card.get('oracle_text', None) or card['faces']['front']['oracle_text']
        assert oracle_text and isinstance(oracle_text, str)
        if 'from your opening hand' in oracle_text:
            self.reveal(who, card)
            ability = [ab for ab in oracle_text.split('\n') if 'from your opening hand' in ab][0]
            assert ability and isinstance(ability, str)
            when, what = self.naya.get_start_of_game_delayed_trigger_ability(card)
            self.create_delayed_triggered_ability(who, card, ability, when, what, 'triggered once')
        elif 'begin the game' in oracle_text:
            if 'Gemstone Caverns' == card['name']:
                self.set_counter(card, 'luck', 1)
            _from = f'{who.player_name}.hand'
            to = f'{who.player_name}.battlefield'
            self.move(card, _from, to)
        else:
            # mark the matched card as un-interactable
            interactable_event = [e for e in self.events if e[0] == 'interactable']
            if not interactable_event:
                return
            interactable_event = interactable_event[0]
            for interactable_card in interactable_event[1]:
                if interactable_card['in_game_id'] == card['in_game_id']:
                    interactable_card['interactable'] = False
            interactable_event[1] = [card for card in interactable_event[1] if card['interactable']]
        self.events = [e for e in self.events if e[0] == 'check_start_of_game_action']

    def reveal(self, *args):
        who, card, *_ = args
        assert isinstance(who, Player)
        assert 'name' in card and 'in_game_id' in card
        self.consumer.send_log(f"{who.player_name} reveals {card['name']} ({card['in_game_id']})")

    def create_delayed_triggered_ability(self, *args):
        who, card, ability, when, what, expire_when, *_ = args
        action = {
            'type': 'create_delayed_trigger',
            'targetId': card['in_game_id'],
            'targetCardName': card['name'],
            'affectingWho': who,
            'triggerWhen': when,
            'triggerContent': what,
            'expireWhen': expire_when,
        }
        self.consumer.send_log(f"Create a delayed triggered ability: {ability}")
        self.game.apply_action(action)
        self.update_game_state()

    def move(self, *args):
        card, _from, to, *_ = args
        assert isinstance(card, dict)
        assert isinstance(_from, str) and isinstance(to, str)
        action = {
            'type': 'move',
            'targetId': card['in_game_id'],
            'from': _from,
            'to': to,
        }
        self.consumer.send_log(f"Move {card['name']} from {_from} to {to}")
        self.game.apply_action(action)
        self.update_game_state()

    def set_counter(self, *args):
        card, counter_type, amount, *_ = args
        assert isinstance(card, dict)
        assert isinstance(counter_type, str)
        assert isinstance(amount, int)
        amount = amount if amount >= 0 else 0
        action = {
            'type': 'set_counter',
            'targetId': card['in_game_id'],
            'counterType': counter_type,
            'counterAmount': amount,
        }
        self.consumer.send_log(f"Set counter ({amount} {counter_type}) on {card['name']}")
        self.game.apply_action(action)
        self.update_game_state()
        
    def handle_phasing(self, *args):
        self.consumer.send_log(f"Beginning phase - Untap step - TBA: handle phasing")
        who = [p for p in self.game.players if p.player_name == self.game.whose_turn][0]
        battlefield = who.battlefield
        for permanent in battlefield:
            if 'is_phased_out' in permanent['annotations']:
                permanent['is_phased_out'] = not permanent['is_phased_out']
                continue
            if 'phasing' in permanent.get('abilities', []) and not permanent.get('is_phased_out', False):
                permanent['is_phased_out'] = True
        self.events = [['handle_phasing_done']]

    def handle_day_night(self, *args):
        self.consumer.send_log(f"Beginning phase - Untap step - TBA: handle day/night")
        game = self.game
        if not getattr(game, 'is_day', None):
            self.events = [['handle_day_night_done']]
            return
        is_day = game.is_day
        if is_day and game.active_player_spell_count_previous_turn == 0:
            self.events.append(['it becomes night'])
        if not is_day and game.active_player_spell_count_previous_turn >= 2:
            self.events.append(['it becomes day'])
        self.events.append(['handle_day_night_done'])

    def handle_untap_step(self, *args):
        self.consumer.send_log(f"Beginning phase - Untap step - TBA: untap all")
        who = [p for p in self.game.players if p.player_name == self.game.whose_turn][0]
        battlefield = who.battlefield
        for permanent in battlefield:
            self.events.append(['untap', permanent])
        self.events.append(['handle_untap_step_done'])

    def ask_check_legend_rule(self, *args):
        player, question, card_name, *_ = args
        self.consumer.send_log(f"Asking {player} to keep 1 of {card_name} because of the Legend Rule")
        eligible_cards = [card for card in player.battlefield if card['name'] == card_name and 'legendary' in card['type_line'].lower()]
        self.question(player, question, eligible_cards)

    def check_sba(self, *args):
        print('Check State Based Action')
        to_check = [
            'sba_check_zero_or_less_life', # CR 704.5a
            'sba_check_draw_from_empty_library', # CR 704.5b
            'sba_check_ten_or_more_poison_counters', # CR 704.5c
            'sba_check_non_battlefield_tokens', # CR 704.5d
            'sba_check_misplaced_copies', # CR 704.5e
            'sba_check_creature_zero_or_less_toughness', # CR 704.5f
            'sba_check_lethal_damage', # CR 704.5g
            'sba_check_deathtouch_damage', # CR 704.5h
            'sba_check_planeswalker_loyalty', # CR 704.5i
            'sba_check_legend_rule', # CR 704.5j
            #'sba_check_world_rule', # no world cards in modern # CR 704.5k
            'sba_check_aura_attachment', # CR 704.5m
            'sba_check_equipment_or_fortification_attachment', # CR 704.5n
            'sba_check_battle_or_creature_attachment', # CR 704.5p
            'sba_check_plus_one_minus_one_counters', # CR 704.5q
            #'sba_check_counter_upper_bound', # rasputin, dreamweaver is not in modern # CR 704.5r
            'sba_check_saga', # CR 704.5s
            'sba_check_dungeon', # CR 704.5t
            #'sba_check_space_sculptor', # space beleren is not in modern # CR 704.5u
            'sba_check_battle_zero_or_less_defense', # CR 704.5v
            'sba_check_battle_designation', # CR 704.5w
            'sba_check_siege_no_self_protector', # CR 704.5x
            'sba_check_permanent_no_multiple_roles', # CR 704.5y
        ]
        for e in self.events:
            was_checked = e[0].replace('done', 'sba')
            if was_checked in to_check:
                to_check.remove(was_checked)
        if to_check:
            self.events.append([to_check[0],])
        elif any('sba_changed' in str(e) for e in self.events):
            self.game.stack.extend(self.game.pending_triggers)
            self.events = [e for e in self.events if 'sba' not in str(e)]
            self.events.append(['check_sba_done'] if stack else ['check_sba'])
        else:
            self.events = [e for e in self.events if 'sba' not in str(e)]
            self.events.append(['check_sba_done',])

    def untap(self, *args):
        permanent, *_ = args
        permanent['annotations']['isTapped'] = False

    def resolve(self, *args):
        # FIXME: implement top of stack resolving
        game_object, *_ = args
        print(game_object)

    def draw_step_tba(self, *args):
        game = self.game
        players = game.players
        active_player_name = game.whose_turn
        active_player = [p for p in players if p.player_name == active_player_name][0]
        self.events.append(['draw', active_player, 1])
        self.events.append(['draw_step_tba_ongoing',])

    def precombat_main_phase_tba_saga(self, *args):
        game = self.game
        players = game.players
        active_player_name = game.whose_turn
        active_player = [p for p in players if p.player_name == active_player_name][0]
        for card in active_player.battlefield:
            if 'saga' in card.get('type_line', '').lower():
                lore = card.get('counters', {}).get('lore', 0)
                self.events.append(['set_counter', card, 'lore', lore + 1])
        self.consumer.send_log('Add one lore counter to each saga active player controls')

    def ask_player_to_declare_attackers_tba(self, *args):
        game = self.game
        players = game.players
        active_player_name = game.whose_turn
        active_player = [p for p in players if p.player_name == active_player_name]
        if not active_player:
            raise ValueError("Can't find active player")
        active_player = active_player[0]
        can_attack = [card for card in active_player.battlefield if 'creature' in card.get('type_line', '').lower()]
        can_attack = [card for card in can_attack if ['cant_attack', card.get('in_game_id') not in game.static_effects]]
        if can_attack:
            raise NotImplementedError("You played a creature? Haven't coded that part yet")
        else: # no creatures that can attack
            self.events.append(['skip_declare_blocker_and_combat_damage_steps'])

    def skip_declare_blocker_and_combat_damage_steps(self, *args):
        effects = self.game.static_effects
        effects.append(['skip_step', 'declare blockers step'])
        effects.append(['skip_step', 'combat damage step'])

    def discard_to_hand_size_tba(self, *args):
        # TODO: implement this
        raise NotImplementedError()

    def update_game_state(self):
        payload = self.game.get_payload(is_update=True)
        pending_event = [e for e in self.events if e[0].startswith('pending') and e[0].endswith('priority')]
        if pending_event:
            interactable = pending_event[0][-1] # get the first matched item and get the last element of the event
            interactable = [self.game.find_card_by_id(card.get('in_game_id')) for card in interactable]
            payload.setdefault('interactable', interactable) # which is interactable cards
        self.consumer.send(text_data=json.dumps(payload)) # update game state

    def next_phase(self, *args):
        phase = self.game.phase
        while not self.game.phase.endswith('phase') or self.game.phase == phase:
            self.next_step()
        self.events = [[self.game.phase,],]

    def next_step(self, *args):
        self.game.next_step()
        self.update_game_state()
        self.events = [[self.game.phase,],]

    def halt(self, *args):
        self.halt = True

    # """ This is for temporarily halting the GRE.
    def _manual_halt(self, *args):
        self.halt = True
    # """
