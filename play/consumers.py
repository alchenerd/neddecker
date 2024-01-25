import json
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
            case 'mulligan':
                self.mulligan(data)
            case 'keep_hand':
                self.player_keep_hand(data)
            case 'pass_priority':
                self.handle_pass_priority(data)
            case 'pass_non_priority_action':
                self.handle_non_priority_action(data)

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
            game.shuffle_players()
            payload = {
                    'type': 'game_start',
                    'game': _match.games_played + 1,
                    'of': _match.max_games,
                    'who_goes_first': str(game.players[0]),
            }
            self.send(text_data=json.dumps(payload))
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
        players = self.mtg_match.game.players
        [i] = [i for i, p in enumerate(players) if p.player_name == data['who']]
        player = players[i]
        for card in reversed(data['bottom']):
            player.hand.remove(card)
            player.library.append(card)
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
        #print(data)
        whose_priority = self.mtg_match.game.whose_priority
        if whose_priority != self.mtg_match.game.priority_waitlist[0]:
            # not sender's priority
            return
        self.mtg_match.game.priority_waitlist.pop(0)
        actions = data.get('actions', [])
        for action in actions:
            self.mtg_match.game.apply(action)
        if len(self.mtg_match.game.priority_waitlist) > 0:
            # other players can respond
            self.mtg_match.game.whose_priority = self.mtg_match.game.priority_waitlist[0]
            whose_priority = self.mtg_match.game.whose_priority
            player = [p for p in self.mtg_match.game.players if p.player_name == whose_priority][0]
            payload = self.mtg_match.game.get_payload()
            self.send_to_player(player, json.dumps(payload))
        else:
            # may resolve top of stack or move to next step
            if len(self.mtg_match.game.stack) == 0:
                self.advance()
            else:
                # TODO have controller resolve stack
                pass

    def handle_non_priority_action(self, data={}):
        print(f'passed non-priority action {self.mtg_match.game.phase}!')
        actions = data.get('actions', [])
        for action in actions:
            self.mtg_match.game.apply(action)
        self.advance()

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
        assert(isinstance(player, Player))
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
