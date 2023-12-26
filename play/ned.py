import json

class Ned():
    def receive(self, text_data):
        json_data = json.loads(text_data)
        match json_data['type']:
            case 'mulligan':
                choice = self.mulligan_to_four(json_data)
                return choice

    def mulligan_to_four(self, data):
        to_bottom = data['to_bottom']
        if (7 - to_bottom) > 4:
            return {'type': 'mulligan', 'who': 'ned'}
        else:
            return {'type': 'keep_hand', 'who': 'ned', 'bottom': data['hand'][-to_bottom:]}
