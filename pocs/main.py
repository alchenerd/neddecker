import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import goldfish
import dotenv

# Objective:
# - Create an AI assistant called Ned Decker
# - Provide Ned Decker with function calls = [
#       'select_random_deck',
#       'get_current_deck',
#       'get_decklist']
# - Have Ned Decker chat about his deck with user
# TODO: Let Ned play an MTG game with user

JSON_DIR = 'json/'
GPT_MODEL = 'gpt-3.5-turbo'

class Assistant():
    def __init__(self):
        self.load_api_key()
        self.load_model()
        self.history = []
        self.load_whoami()
        self.load_system_message()
        self.load_every_function_description()
        self.goldfish = goldfish.Goldfish()
        [self.current_deck] = self.goldfish.random_meta_deck().values()

    def load_api_key(self):
        dotenv.load_dotenv()

    def load_model(self):
        self.model = GPT_MODEL

    def load_json(self, fname: str) -> dict:
        with open(fname, 'r') as f:
            data = f.read()
            return json.loads(data)

    def load_whoami(self, fname='whoami.json'):
        self.whoami = self.load_json(JSON_DIR + fname)
        self.history.append(self.whoami)

    def load_system_message(self, fname='system_message.json'):
        self.system_message = self.load_json(JSON_DIR + fname)
        self.history.append(self.system_message)

    def load_every_function_description(self, in_files: list[str]=[]):
        path = JSON_DIR + 'function_description/'
        files = [f for f in os.listdir(path) if os.path.isfile(path + f)] + in_files
        self.function_descriptions = [self.load_json(path + f) for f in files if f != 'template.json']

    def process_function_call(self, call):
        data = ''
        fname = call['name']
        if fname == 'select_random_deck':
            [self.current_deck] = self.goldfish.random_meta_deck().values()
            data = json.dumps(self.current_deck)
        elif fname == 'get_current_deck':
            data = json.dumps(self.current_deck)
        elif fname == 'get_decklist':
            decklist_path = self.goldfish.fetch_decklist(self.current_deck['link'])
            with open('neds_decks/' + decklist_path, 'r') as f:
                data = f.read()
        else:
            data = 'Ned Decker can bend reality to his will; assistant will make up some random content and be very creative!'
        result = {'role': 'function', 'name': fname, 'content': data}
        self.history.append(result)

if __name__ == '__main__':
    ned = Assistant()
    chatting = True
    user_content = input('User: ')
    ned.history.append({"role": "user", "content": user_content})
    while chatting:
        response = client.chat.completions.create(model=ned.model, messages=ned.history, functions=ned.function_descriptions, temperature=0.8, max_tokens=512)
        assistant_message = response['choices'][0]['message']
        ned.history.append(assistant_message)
        content = assistant_message['content']
        if content:
            print(f'Ned: {content}')
        else:
            ned.process_function_call(assistant_message['function_call'])
            continue
        print()
        user_content = input('User: ')
        print()
        ned.history.append({"role": "user", "content": user_content})
