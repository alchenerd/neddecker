import json

class Ned():
    def receive(self, text_data):
        json_data = json.loads(text_data)
        match json_data['type']:
            case 'mulligan':
                choice = self.mulligan_to_four(json_data)
                print(choice)
                return choice

    def mulligan_to_four(self, data):
        if (7 - data['to_bottom']) > 4:
            return 'mulligan'
        else:
            return 'keep_hand'
