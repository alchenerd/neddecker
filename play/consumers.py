import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import datetime

class PlayConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(
                'user',
                self.channel_name
        )
        self.accept()
        self.send(text_data=json.dumps({'log': 'hello world from consumer'}))

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
                'user',
                self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        type_ = text_data_json['type']

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
