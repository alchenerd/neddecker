import json
from typing import Tuple
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.agents import load_tools, initialize_agent, AgentType
from langchain_core.output_parsers.string import StrOutputParser
from .models import Card, Face
from .serializers import CardSerializer, FaceSerializer
from dotenv import load_dotenv

load_dotenv()

class Ned():
    def __init__(self):
        self.llm = ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.8, max_tokens=1024)
        self.output_parser = StrOutputParser()

    def receive(self, text_data):
        print(text_data)
        json_data = json.loads(text_data)
        thoughts, choice = self.ask_ned_decker(self.generate_payload(json_data))
        return thoughts, choice

    def get_card_by_name(self, name) -> Card:
        return Card.objects.filter(name=name).order_by().first()

    def get_faces_by_name(self, name) -> Tuple[Face, Face]:
        if ' // ' not in name:
            return None, None
        f, b = name.split(' // ')
        front, back = None, None
        try:
            front = Face.objects.filter(name=f).order_by().first()
            back = Face.objects.filter(name=b).order_by().first()
        except:
            pass
        return front, back

    def hand_to_data(self, hand):
        ret = []
        for card in hand:
            name = card['name']
            card_orm = self.get_card_by_name(name)
            front_orm, back_orm = self.get_faces_by_name(name)
            info = dict()
            info['id'] = card['id']
            info['card'] = str(card_orm)
            if front_orm:
                info['front'] = str(front_orm)
            if back_orm:
                info['back'] = str(back_orm)
            ret.append(info)
        return ret

    def generate_payload(self, json_data):
        _WHOAMI = """Assistant's name: Ned Decker\nAssistant's summary: Ned Decker is a competitive Magic: the Gathering player; Ned Decker is very skilled: he can anticipate his opponent's play; Ned Decker always play to win."""
        context = ''
        data = ''
        request = ''
        match json_data['type']:
            case 'mulligan':
                context = f"Ned Decker is playing a game of Magic: the Gathering against his opponent.\nThe current phase is mulligan phase."
                to_bottom = json_data['to_bottom']
                hand_information = self.hand_to_data(json_data['hand'])
                data = f"Ned Decker has seven cards in his hand; if Ned Decker takes this hand, he will need to put {to_bottom} cards from his hand to the bottom of his library.\nNed Decker's hand = {hand_information}."
                request = f"REQUEST: Please briefly judge if this hand is keepable. If the hand is keepable, what would your first three turns look like? Additionally, if the hand is keepable, list {to_bottom} cards that you will put to the bottom of your library (skip the list if zero card is required). If the hand is not keepable, what were lacking in this hand? Remember to reply as Ned Decker."
        return '\n'.join((_WHOAMI, context, data, request))

    def ask_ned_decker(self, payload):
        print(str(payload))
        prompt = ChatPromptTemplate.from_messages([SystemMessage(content=payload)])
        chain = prompt | self.llm
        response = chain.invoke({})
        thoughts = response.content
        print(response.__dict__)
        return 'Ned: ' + thoughts, {'type': 'keep_hand', 'who': 'ned', 'bottom': []}

    def mulligan_to_four(self, data):
        to_bottom = data['to_bottom']
        if (7 - to_bottom) > 4:
            return {'type': 'mulligan', 'who': 'ned'}
        else:
            return {'type': 'keep_hand', 'who': 'ned', 'bottom': data['hand'][-to_bottom:]}
