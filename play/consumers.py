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
            game.start()
            payload = {
                    'type': 'game_start',
                    'game': _match.games_played + 1,
                    'of': _match.max_games,
                    'who_goes_first': str(game.players[0]),
            }
            self.send(text_data=json.dumps(payload))
            self.mulligan()

    def next_mulligan_player(self, i):
        players = self.mtg_match.game.players
        i = (i + 1) % len(players)
        count = len(players) + 1
        while hasattr(players[i], 'mulligan_done'):
            i = (i + 1) % len(players)
            count -= 1
            if count <= 0:
                raise ValueError('Expected at least on player needs mulligan but no')
        return players[i]

    def mulligan(self, data=None):
        players = self.mtg_match.game.players
        next_player = players[0]
        if data:
            [i] = [i for i, p in enumerate(players) if p.player_name == data['who']]
            next_player = self.next_mulligan_player(i)
        self.mulligan_helper(next_player)

    def mulligan_helper(self, player):
        if not hasattr(player, 'to_bottom'):
            player.to_bottom = 0
        if player.to_bottom >= 7:
            while player.hand:
                player.library.append(player.hand.pop())
            player.mulligan_done = True
            return
        if player.to_bottom > 0:
            self.send(json.dumps({
                    'type': 'log',
                    'message': f'{player.player_name} mulligans to {7 - player.to_bottom}'
            }))
        while player.hand:
            player.library.append(player.hand.pop())
        player.shuffle()
        for _ in range(7):
            player.hand.append(player.library.pop(0))
        game = self.mtg_match.game
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
            self.mulligan_helper(next_player)

    def start_first_turn(self):
        pass

    def send_to_player(self, player, text_data):
        match player.player_type:
            case 'ai':
                self.multiplexer_handle(player.ai.receive(text_data=text_data))
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
