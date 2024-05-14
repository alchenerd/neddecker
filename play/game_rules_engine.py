from typing import Dict, List, Any, Optional, Callable
from langgraph.graph import END, StateGraph
import json
import random
from dataclasses import dataclass, field
from functools import wraps
from .game import Match, Game, Player
from .rules import Rule, SYSTEM_RULES

STATE_BASED_ACTIONS = {
    "life_check": "check player life totals (win/loss)",
    "library_check": "check for empty libraries (win/loss)",
    "poison_check": "check for poison counters (win/loss)",
    "creature_toughness_check": "check creature toughness (destruction)",
    "creature_damage_check": "check creature damage (destruction)",
    "deathtouch_check": "check for deathtouch damage (destruction)",
    "planeswalker_loyalty_check": "check planeswalker loyalty (destruction)",
    "legend_rule": "check for legendary permanents duplicates",
    "world_rule": "check for world permanents duplicates",
    "aura_attachment_check": "check aura attachment validity",
    "equipment_attachment_check": "check equipment attachment validity",
    "fortification_attachment_check": "check fortification attachment validity",
    "counter_removal": "remove excess +1/+1 counters",
    "limited_counter_removal": "remove excess counters based on ability",
    "saga_completion_check": "check for saga completion (sacrifice)",
    "venture_completion_check": "check for completed venture (remove marker)",
    "space_sculptor_check": "assign sector designation for creatures",
    "battle_defense_check": "check battle defense (destruction)",
    "battle_protector_check": "assign protector for battle",
    "siege_protector_check": "assign protector for siege",
    "role_timestamp_check": "remove duplicate roles based on timestamp",
}


TURN_BASED_ACTIONS = {
        # old: new
        'untap_step': 'phase_in',
        'phase_in': 'day_night',
        'day_night': 'untap',
        'draw_step': 'draw 1',
        'precombat_main_phase': 'saga_add_counter',
        'declare_attackers_step': 'declare_attacker'
}


class GameRulesEngine:
    def __init__(self, consumer):
        self.consumer = consumer
        self._match = None
        self.input = None
        self.todo = []
        self.placeholder = []
        self.rules = []
        self.rules.extend(SYSTEM_RULES)
        self.graph = None
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
            print(self.todo)
            if not self.todo:
                break
        #print(self.abort, self.halt)

    def _read(self) -> None:
        if self.input:
            match(self.input['type']):
                case 'register_match': # initiated by user
                    self.register_match()
                    return
                case 'register_player': # initiated by user
                    self.register_player()
                    game = self._match.game
                    if len(game.players) < game.max_players:
                        return
                case 'answer': # user's response to 'question'
                    self.handle_answer()
                case 'mulligan': # user takes a mulligan
                    self.handle_mulligan()
                case 'keep_hand': # user keeps their hand
                    self.handle_keep_hand()
                case 'play': # user plays an object with multiple possible actions
                    self.handle_select()
                case 'cast': # user casts a spell
                    self.handle_cast()
                case 'activate': # user activates an ability
                    self.handle_activation()
                case 'special_action': # user takes a special action
                    self.handle_special_action()
                case 'abort': # user makes the previous action illegal and we rollback
                    self.handle_abort()
                case 'pay_cost': # user responds to 'ask_cost'
                    self.handle_pay_cost()
                case 'pass_priority': # user passes priority
                    self.handle_pass_priority()
                case 'resolve_stack': # user resolves the stack
                    self.handle_resolve_stack()
        self.input = None # consume

    def _evaluate(self):
        if self.abort:
            return
        require_checking = True
        while require_checking:
            require_checking = self.apply_rules()

    def _execute(self):
        if self.abort:
            return
        while self.todo:
            args = self.todo.pop()
            print(args)
            f = getattr(self, args[0], None)
            if f and callable(f):
                print("[game action '{}' has fired]".format(args[0]))
                f(*args[1:])
            else:
                self.placeholder.append(args)
        while self.placeholder:
            self.todo.append(self.placeholder.pop())

    def apply_rules(self):
        changed = False
        for rule in self.rules:
            for i in range(len(self.todo)):
                for statement in rule.gherkin:
                    print(statement)
                    tracking = 'Given'
                    start = statement.split(' ')[0]
                    if start == tracking or start == 'And' or start == 'But':
                        start = tracking
                    else:
                        tracking = start
                    f = rule.implementations.get(statement, lambda game, todo, i, placeholder: False)
                    assert callable(f)
                    match start:
                        case 'Given' | 'When':
                            if not f(self._match.game, self.todo, i, self.placeholder):
                                break
                        case 'Then':
                            if f(self._match.game, self.todo, i, self.placeholder): # state changed
                                changed = True
                if changed:
                    return True # requires another round
        return False # all done

    def register_match(self):
        self._match = Match(
            mtg_format=self.input['format'],
            games=self.input['games'],
            consumer=self.consumer,
        )
        self.graph = StateGraph((self._match.game, self.todo))
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
            payload = game.get_payload(is_update=True)
            self.consumer.send(text_data=json.dumps(payload)) # update game state
            self.todo.append(['decide_who_goes_first'])
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
        self.todo.append(['answer_question', who, question, answer])

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
        self.placeholder.append(['ask_reveal_companion', 0])
        print(self.placeholder)
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


    def get_turn_based_actions(self, game):
        match game.phase:
            case 'untap step':
                self.todo.append("permanents the active player controls phase in")
                self.todo.append("check day or night")
                self.todo.append("permanents the active player controls untap")
            case 'draw step':
                self.todo.append("the active player draws a card")
            case 'precombat main phase':
                self.todo.append("add a lore counter on each saga the active player controls")
            case 'declare attackers step':
                self.todo.append("the active player declares attackers")
            case 'declare blockers step':
                self.todo.append("defending player declares blockers")
                self.todo.append("active player announces damage assignment order among blocking creatures")
                self.todo.append("defending player announces damage assignment order among attacking creatures")
                self.todo.append("active player announces how attacking creatures assign combat damage")
                self.todo.append("defending player announces how blocking creatures assign combat damage")
                self.todo.append("deal combat damage")
            case 'cleanup step':
                self.todo.append("active player discards down to hand size")
                self.todo.append("remove all damage on permanents and end \"until end of turn\" or \"this turn\" effects")


    def get_state_based_actions(self, game):
        for k, v in STATE_BASED_ACTIONS.items:
            self.todo.insert(v)
        return self.repl(game)
