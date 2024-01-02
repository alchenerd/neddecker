import json
from typing import Tuple, Optional, Type, Sequence
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import HumanMessagePromptTemplate, PromptTemplate
from langchain.schema.messages import SystemMessage, HumanMessage, AIMessage
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.tools import BaseTool
from langchain.tools.render import format_tool_to_openai_function

from langchain.memory import ConversationBufferMemory
from langchain.pydantic_v1 import BaseModel, Field
from langchain_community.chat_models import ChatOpenAI
from .models import Card, Face
from .serializers import CardSerializer, FaceSerializer
from dotenv import load_dotenv

load_dotenv()

# This is a sin but I don't know any other solution
g_payload = {} # What Ned answers to the consumer backend, this will be load as JSON

class MtgCard(BaseModel):
    _id: str = Field(description='The ID of the card')
    name: str = Field(description='The name of the card')

class MulliganInput(BaseModel):
    choice: str = Field(description='"take mulligan" or "keep hand"')
    to_bottom: Optional[Sequence[MtgCard]] = Field(description='An array of cards that will be send to the bottom of library')

class SubmitMulliganDescision(BaseTool):
    name = 'submit_mulligan_descision'
    description = 'After thinking, use this tool to submit "take mulligan" or "keep hand"; if "keep hand" was chosen, Ned Decker has to submit cards to put from his hand to the bottom of his library (e.g. [{"id": "n1#2", "name": "some card name"}, {"id": "n6#4", "name": "another card name"}]); if Ned Decker chose to keep a seven-card hand, the submitted value for "to_bottom" should be "[]".'
    args_schema: Type[BaseModel] = MulliganInput
    def _run(self, choice: str, to_bottom: Optional[str] = '') -> str:
        choice = choice.lower()
        assert(choice in ('take mulligan', 'keep hand'))
        what_to_bottom = [{'id': card['_id'], 'name': card['name']} for card in to_bottom]
        global g_payload
        match choice:
            case 'take mulligan':
                g_payload = {
                    'type': 'mulligan',
                    'who': 'ned',
                }
                return 'Submitted! Ned Decker takes another mulligan. As Ned Decker, say a sentence to complain about bad luck.'
            case 'keep hand':
                g_payload = {
                    'type': 'keep_hand',
                    'who': 'ned',
                    'bottom': what_to_bottom,
                }
                return 'Kept the hand! As Ned Decker, say a sentence to the opponent as the game starts.'
    def _arun(self, choice: str, to_bottom: Optional[str] = '') -> str:
        raise NotImplementedError('No async submission for now! Please select another.')

class Ned():
    def __init__(self):
        self.llm = ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.8, max_tokens=1024)
        #self.llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0.8, max_tokens=1024)

    def receive(self, text_data):
        print(text_data)
        json_data = json.loads(text_data)
        match json_data['type']:
            case 'log':
                print(json_data['message'])
                return 'Ned received: ' + json_data['message'], json_data
            case 'mulligan':
                return 'Beep boop I mull to 4', self.mulligan_to_four(json_data)
                payload, user_request = self.generate_contexts(json_data)
                tools = [SubmitMulliganDescision()]
                thoughts, choice = self.ask_ned_decker(payload, user_request, tools=tools)
                return thoughts, choice
            case _:
                return '...What?', {'type': 'log', 'message': 'Error'}

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
        cards = []
        lands = []
        for card in hand:
            name = card['name']
            card_orm = self.get_card_by_name(name)
            front_orm, back_orm = self.get_faces_by_name(name)
            info = dict()
            info['id'] = card['id']
            info['card'] = json.loads(str(card_orm))
            if front_orm:
                info['front'] = json.loads(str(front_orm))
            if back_orm:
                info['back'] = json.loads(str(back_orm))
            cards.append(info)
            type_line = ''.join((x.type_line for x in (card_orm, front_orm, back_orm) if x and x.type_line)).lower()
            if 'land' in type_line:
                land = dict()
                land['id'] = card['id']
                land['name'] = card_orm.name
                land['produced_mana'] = card_orm.produced_mana
                lands.append(land)
        return cards, lands

    def generate_contexts(self, json_data):
        _WHOAMI = """Assistant's name: Ned Decker\nAssistant's summary: Ned Decker is a competitive Magic: the Gathering player; Ned Decker is very skilled; Ned Decker always play to win."""
        context = ''
        data = ''
        request = ''
        match json_data['type']:
            case 'mulligan':
                context = f"Ned Decker is playing a game of Magic: the Gathering against his opponent.\nThe current phase is mulligan phase."
                to_bottom = json_data['to_bottom']
                hand, lands = self.hand_to_data(json_data['hand'])
                data = f"Ned Decker has seven cards in his hand; if Ned Decker takes this hand, he will need to put {to_bottom} cards from his hand to the bottom of his library.\nNed Decker's hand = {hand}\nLands in Ned Decker's hand = {lands}"
                user_requests = [
                        "With one sentence, briefly estimate how this deck tries to win.",
                        "Count the lands and spells in Ned Decker's hand (if there's little to no land, or little to no impactful spell, then it's probably better to take a mulligan).",
                        "Outline the most impactful plays that Ned Decker can make with this hand for the first three turns, specifying which land to play from this hand and which spells to cast from this hand, then observe if mana screw or mana flood happened.",
                        "Choose 'keep hand' or 'take mulligan'.",
                        f"Sort Ned Decker's hand = {json_data['hand']} from most useful in the early game to most useless in the early game, with the last card being the most useless in the early game; be extremely brief when explaining why.",
                        f"List {to_bottom} cards from this hand that Ned Decker should put to the bottom of his library; the answer of the sorting task might help; skip this task if Ned Decker should mulligan.",
                ]
                return '\n'.join((_WHOAMI, context, data)), user_requests

    def ask_ned_decker(self, payload, user_requests, tools):
        print(str(payload))
        print(str(user_requests))
        llm_with_tools = self.llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=payload),
            MessagesPlaceholder(variable_name="history", optional=True),
            HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='{input}')),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        history = []
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
                "history": lambda x: x["history"],
            }
            | prompt
            | self.llm
            | OpenAIFunctionsAgentOutputParser()
        )
        agent_executor = AgentExecutor(agent=agent, tools=[], verbose=True)
        for request in user_requests:
            print(request)
            history.append(HumanMessage(content=request))
            response = agent_executor.invoke({'input': request, 'history': history})
            history.append(AIMessage(content=response['output']))
        # Reconfigure agent runnable sequence with tools baked in
        agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
                "history": lambda x: x["history"],
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        final = "Call the function 'submit_mulligan_descision' to submit Ned Decker's choice."
        history.append(HumanMessage(content=final))
        response = agent_executor.invoke({'input': final, 'history': history})
        history.append(AIMessage(content=response['output']))
        thoughts = response['output']
        print(history)
        global g_payload
        print(g_payload)
        return thoughts, g_payload

    def mulligan_to_four(self, data):
        to_bottom = data['to_bottom']
        if (7 - to_bottom) > 4:
            return {'type': 'mulligan', 'who': 'ned'}
        else:
            return {'type': 'keep_hand', 'who': 'ned', 'bottom': data['hand'][-to_bottom:]}
