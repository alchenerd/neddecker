import json
from random import randint
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .game import Match, Game, Player
import datetime

class PlayConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
                'user',
                self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                'user',
                self.channel_name
        )

    def receive(self, text_data):
        data = json.loads(text_data)
        self.multiplexer_handle(data)

    def multiplexer_handle(self, data):
        msg_type = data['type']
        match(msg_type):
            case 'register_match':
                self.register_match(data)
            case 'register_player':
                self.register_player(data)
            case 'who_goes_first':
                self.register_who_first(data)
            case 'ask_reveal_companion':
                self.register_companion(data)
            case 'mulligan':
                self.mulligan(data)
            case 'keep_hand':
                self.player_keep_hand(data)
            case 'pass_priority':
                self.handle_pass_priority(data)
            case 'pass_non_priority_action':
                self.handle_non_priority_action(data)
            case 'resolve_stack':
                self.handle_resolve_stack(data)

    def register_match(self, data):
        if hasattr(self, 'mtg_match'):
            payload = {
                    'type': 'error',
                    'message': 'Cannot initialize match: match in progress.',
            }
            self.send(text_data=json.dumps(payload))
            return
        self.mtg_match = Match(
                mtg_format=data['format'],
                games=data['games'],
        )
        payload = {
                'type': 'match_initialized',
                'message': f'{self.mtg_match.max_games} game(s) of {self.mtg_match.mtg_format} initialized.',
        }
        self.send(text_data=json.dumps(payload))

    def register_player(self, data):
        self.mtg_match.game.add_player(data)
        _match = self.mtg_match
        game = _match.game
        added = game.players[-1]
        payload = {
                'type': 'player_registered',
                'message': f'Player {added.player_name} registered.',
                'count': len(game.players),
                'of': game.max_players,
        }
        self.send(text_data=json.dumps(payload))
        if len(game.players) == game.max_players:
            game.clear()
            payload = {
                    'type': 'game_start',
                    'game': _match.games_played + 1,
                    'of': _match.max_games,
            }
            self.send(text_data=json.dumps(payload)) # announce start of game
            self.decide_who_goes_first()

    def decide_who_goes_first(self):
        players = self.mtg_match.game.players
        who_decides = randint(0, len(players) - 1)
        payload = {
            'type': 'who_goes_first',
            'message': 'You decide if you will go first or not.',
        }
        player = players[who_decides]
        self.send_to_player(player=player, text_data=json.dumps(payload))

    def register_who_first(self, data):
        who_first = data['who']
        assert who_first
        players = self.mtg_match.game.players
        [index] = [ i for i, player in enumerate(players) if player.player_name == who_first ]
        assert type(index) == int
        self.mtg_match.game.register_first_player(index)
        pending = self.handle_companion()
        if not pending:
            self.start_mulligan()
        else:
            self.mtg_match.game.pending_companion = pending

    def handle_companion(self):
        pending = 0
        players = self.mtg_match.game.players
        for player in players:
            print(player.player_name)
            for card in player.sideboard:
                print(card['name'])
                if 'Companion' in repr(card):
                    self.ask_reveal_companion(player)
                    pending += 1
        return pending

    def ask_reveal_companion(self, player):
        payload = {
            'type': 'ask_reveal_companion',
            'message': 'You may reveal at most one companion.',
            'sideboard': player.sideboard,
        }
        self.send_to_player(player=player, text_data=json.dumps(payload))

    def register_companion(self, data):
        _id = data['targetId']
        if not _id:
            return
        self.mtg_match.game.set_companion(_id)
        self.mtg_match.game.pending_companion -= 1
        if not self.mtg_match.game.pending_companion:
            delattr(self.mtg_match.game, 'pending_companion')
            self.start_mulligan()

    def next_mulligan_player(self, i):
        players = self.mtg_match.game.players
        i = (i + 1) % len(players)
        count = len(players) + 1
        while hasattr(players[i], 'mulligan_done'):
            i = (i + 1) % len(players)
            count -= 1
            if count <= 0:
                return None
        return players[i]

    def start_mulligan(self):
        players = self.mtg_match.game.players
        for player in players:
            player.to_bottom = 0
            while player.hand:
                player.library.append(player.hand.pop())
            for _ in range(7):
                player.hand.append(player.library.pop(0))
        self.mulligan_helper(players[0], 0)

    def mulligan(self, data):
        players = self.mtg_match.game.players
        next_player = players[0]
        if data:
            [(i, p)] = [(i, p) for i, p in enumerate(players) if p.player_name == data['who']]
            self.send(json.dumps({
                    'type': 'log',
                    'message': f'{p.player_name} mulligans to {7 - p.to_bottom}'
            }))
            next_player = self.next_mulligan_player(i)
        [i] = [(i, p) for i, p in enumerate(players) if p.player_name == next_player.player_name]
        self.mulligan_helper(next_player, i)

    def mulligan_helper(self, player, i):
        while player.hand:
            player.library.append(player.hand.pop())
        if player.to_bottom >= 7:
            player.mulligan_done = True
            return self.check_all_mulligan_done(i)
        player.shuffle()
        for _ in range(7):
            player.hand.append(player.library.pop(0))
        payload = {
                'type': 'mulligan',
                'hand': player.hand,
                'to_bottom': player.to_bottom,
        }
        player.to_bottom += 1
        self.send_to_player(player=player, text_data=json.dumps(payload))

    def player_keep_hand(self, data):
        # print(data)
        players = self.mtg_match.game.players
        [i] = [i for i, p in enumerate(players) if p.player_name == data['who']]
        player = players[i]
        for card_id in reversed(data['bottom']):
            card_to_bottom, *_ = filter(lambda c: c['in_game_id'] == card_id, player.hand)
            player.hand.remove(card_to_bottom)
            player.library.append(card_to_bottom)
        player.mulligan_done = True
        self.send(json.dumps({
                'type': 'log',
                'message': f'{player.player_name} keeps their hand of {7 - player.to_bottom + 1}'
        }))
        self.check_all_mulligan_done(i)

    def check_all_mulligan_done(self, i):
        players = self.mtg_match.game.players
        if all([ hasattr(player, 'mulligan_done') for player in players ]):
            for player in players:
                delattr(player, 'to_bottom')
                delattr(player, 'mulligan_done')
            payload = {
                    'type': 'log',
                    'message': 'All players have kept their hand',
            }
            self.send(json.dumps(payload))
            self.start_first_turn()
        else:
            next_player = self.next_mulligan_player(i)
            self.mulligan_helper(next_player, i)

    def start_first_turn(self):
        self.mtg_match.game.start()
        player = self.mtg_match.game.whose_priority
        player = [p for p in self.mtg_match.game.players if p.player_name == player][0]
        payload = self.mtg_match.game.get_payload()
        self.send_to_player(player, json.dumps(payload))
        if self.mtg_match.game.require_player_action:
            return
        if self.mtg_match.game.player_has_priority:
            return
        else:
            self.advance()

    # Called when a player passes priority
    def handle_pass_priority(self, data={}):
        whose_priority = self.mtg_match.game.whose_priority
        print(f'{whose_priority} passed priority action {self.mtg_match.game.phase}!')

        if (self.mtg_match.game.priority_waitlist):
            if whose_priority != self.mtg_match.game.priority_waitlist[0]:
                # not sender's priority
                return
            self.mtg_match.game.priority_waitlist.pop(0)

        # apply the board state to the game we're keeping track of
        board_state = data.get('gameData', {}).get('board_state', {})
        #print(board_state)
        if board_state:
            self.mtg_match.game.apply_board_state(board_state)
        else:
            # TODO: save actions to database for replayability
            actions = data.get('actions', [])
            print(actions)
            for action in actions:
                #print(action);
                self.mtg_match.game.apply_action(action)

        if len(self.mtg_match.game.priority_waitlist) > 0:
            # if the stack has grown, then refill the priority queue starting with the caster
            if (self.mtg_match.game.stack_has_grown):
                self.mtg_match.game.stack_has_grown = False
                self.mtg_match.game.refill_priority_waitlist(next_player=whose_priority)
                # assume that the caster has passed priority
                self.mtg_match.game.priority_waitlist.pop(0)
            # then, other players may respond
            self.mtg_match.game.whose_priority = self.mtg_match.game.priority_waitlist[0]
            whose_priority = self.mtg_match.game.whose_priority
            player = [p for p in self.mtg_match.game.players if p.player_name == whose_priority][0]
            payload = self.mtg_match.game.get_payload()
            self.send_to_player(player, json.dumps(payload))
        else:
            # may resolve top of stack or move to the next step
            if len(self.mtg_match.game.stack) == 0:
                self.advance()
            else:
                self.resolve_stack()

    def handle_non_priority_action(self, data={}):
        print(f'passed non-priority action {self.mtg_match.game.phase}!')
        #print(data)
        board_state = data.get('gameData', {}).get('board_state', {})
        #print(board_state)
        if board_state:
            self.mtg_match.game.apply_board_state(board_state)
        else:
            actions = data.get('actions', [])
            for action in actions:
                self.mtg_match.game.apply_action(action)
        self.advance()

    def handle_resolve_stack(self, data={}):
        print('The top of the stack has resolved!')
        board_state = data.get('gameData', {}).get('board_state', {})
        #print(board_state)
        self.mtg_match.game.apply_board_state(board_state)
        actions = data.get('actions', [])
        for action in actions:
            self.mtg_match.game.apply_action(action)
        self.mtg_match.game.is_resolving = False
        # refill priority waitlist; active player receives priority
        self.mtg_match.game.refill_priority_waitlist(next_player=self.mtg_match.game.whose_turn)
        self.mtg_match.game.whose_priority = self.mtg_match.game.priority_waitlist[0]
        whose_priority = self.mtg_match.game.whose_priority
        player = [p for p in self.mtg_match.game.players if p.player_name == whose_priority][0]
        payload = self.mtg_match.game.get_payload()
        #print(payload['type'])
        self.send_to_player(player, json.dumps(payload))

    # Called when all players agree to let the top of the stack to resolve
    def resolve_stack(self, data={}):
        assert len(self.mtg_match.game.stack) > 0
        topmost = self.mtg_match.game.stack[-1]
        assert topmost.get('annotations', {}).get('controller', '')
        resolver = [p for p in self.mtg_match.game.players if p.player_name == topmost['annotations']['controller']][0]
        self.mtg_match.game.is_resolving = True
        self.mtg_match.game.whose_priority = resolver.player_name
        payload = self.mtg_match.game.get_payload()
        self.send_to_player(resolver, json.dumps(payload))

    # Called when all players agree to move to the next step
    def advance(self, data={}):
        self.mtg_match.game.next_step()
        player = self.mtg_match.game.whose_priority
        player = [p for p in self.mtg_match.game.players if p.player_name == player][0]
        payload = self.mtg_match.game.get_payload()
        self.send_to_player(player, json.dumps(payload))
        if self.mtg_match.game.require_player_action:
            return
        if self.mtg_match.game.player_has_priority:
            return
        else:
            self.advance()

    def send_log(self, to_log):
        self.send(json.dumps({
                'type': 'log',
                'message': f'{str(to_log)}',
        }))

    def send_to_player(self, player, text_data):
        assert isinstance(player, Player)
        match player.player_type:
            case 'ai':
                thoughts, choice = player.ai.receive(text_data=text_data)
                self.send_log(thoughts)
                self.multiplexer_handle(choice)
            case 'human':
                self.send(text_data=text_data)

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.deck_name = self.scope['url_route']['kwargs']['deck_name']
        async_to_sync(self.channel_layer.group_add)(
                self.deck_name,
                self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                self.deck_name,
                self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        async_to_sync(self.channel_layer.group_send)(
             self.deck_name,
             {
                 'type': 'chat_message',
                 'message': message
             }
         )

    def chat_message(self, event):
        message = event['message']
        datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.send(text_data=json.dumps({
            'message': f'{datetime_str}:{message}'
        }))
