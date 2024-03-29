import json
from multiprocessing import Manager
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../')
sys.path.insert(0, llmrootdir)

from llm.prompts.mulligan import MulliganPromptPreset as MPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor
import payload

from dotenv import load_dotenv
load_dotenv()

class Ned():
    def __init__(self):
        #self.llm = ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.8, max_tokens=1024)
        self.llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0.8, max_tokens=1024)
        self.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
        self.agent_executor = None

    def receive(self, text_data):
        #print(text_data)
        json_data = json.loads(text_data)
        match json_data['type']:
            case 'log':
                #print(json_data['message'])
                return 'Ned received: ' + json_data['message'], json_data
            case 'mulligan':
                #return 'Beep boop Ned mulligans to 4', self.mulligan_to_four(json_data)
                # ...or you may let GPT decide
                thoughts, choice = self.ask_ned_decker(topic='mulligan', data=json_data)
                return thoughts, choice
            case 'receive_priority':
                return f'Beep boop Ned passes priority ({json_data["whose_turn"]}\'s {json_data["phase"]})', { 'type': 'pass_priority', 'who': 'ned', 'actions': [] }
            case 'require_player_action':
                return 'Beep boop Ned does nothing on ' + json_data['phase'], { 'type': 'pass_non_priority_action', 'who': 'ned', 'actions': [], }
            case 'receive_step':
                return 'Beep boop Ned does nothing on ' + json_data['phase'], { 'type': 'log', 'message': 'received step ' + json_data['phase'], }
            case 'resolve_stack':
                card_name = json_data['board_state']['stack'][-1]['name']
                game_data, actions = self.move_top_of_stack(json_data)
                return 'Beep boop Ned moves the topmost card of the stack ' + card_name, { 'type': 'resolve_stack', 'who': 'ned', 'gameData': game_data, 'actions': actions, }
            case _:
                print('[ERROR]')
                #print(json_data)
                #print('...What?')
                return '...What?', {'type': 'log', 'message': 'Error:\n' + text_data}

    def ask_ned_decker(self, topic, data):
        match (topic):
            case 'mulligan':
                agent_executor = CSAgentExecutor(
                        llm=self.llm,
                        chat_prompt=MPP.chat_prompt,
                        tools_prompt=MPP.tools_prompt,
                        tools=MPP.tools,
                        memory=self.memory,
                        requests=MPP.requests,
                        verbose=True,
                )
                hand = []
                for bulky_card in data.get('hand'):
                    card = {}
                    card['in_game_id'] = bulky_card['in_game_id']
                    card['name'] = bulky_card['name']
                    card['mana_cost'] = bulky_card.get('mana_cost', '') or None
                    card['type_line'] = bulky_card.get('type_line', '') or None
                    card['oracle_text'] = bulky_card.get('oracle_text', '') or None
                    card['power'] = bulky_card.get('power', '') or None
                    card['toughness'] = bulky_card.get('toughness', '') or None
                    card['produced_mana'] = bulky_card.get('produced_mana', '') or None
                    card['loyalty'] = bulky_card.get('loyalty', '') or None
                    card['defense'] = bulky_card.get('defense', '') or None
                    if 'faces' in bulky_card:
                        card['faces'] = {}
                        card['faces'] |= bulky_card['faces']
                    hand.append(card)

                to_bottom_count = data.get('to_bottom')
                land_count = MPP.count_lands(hand)
                hand_analysis = MPP.hand_analysis.format(
                        hand=hand,
                        land_count=land_count,
                        to_bottom_count=to_bottom_count,
                        keep_card_count=7-to_bottom_count,
                        )
                _input = MPP._input.format(
                        to_bottom_count=to_bottom_count,
                        keep_card_count=7-to_bottom_count,
                        )
                response = agent_executor.invoke({
                    'data': hand_analysis,
                    'input': _input,
                })
                print (response.get('output'))
                print (payload.g_payload)
                return response.get('output'), payload.g_payload
            case _:
                return None, None

    def mulligan_to_four(self, data):
        to_bottom = data['to_bottom']
        if (7 - to_bottom) > 4:
            return {'type': 'mulligan', 'who': 'ned'}
        else:
            return {'type': 'keep_hand', 'who': 'ned', 'bottom': data['hand'][-to_bottom:]}

    def move_top_of_stack(self, data):
        card = data['board_state']['stack'].pop()
        non_permanent = ['instant', 'sorcery']
        target_zone = 'battlefield'
        if any(_type in card['type_line'].lower() for _type in non_permanent):
            target_zone = 'graveyard'
        players = data['board_state']['players']
        idx = 0
        for i, player in enumerate(players):
            if player['player_name'] == 'ned':
                idx = i
                player[target_zone].append(card)

        return data, [{'type': 'move', 'targetId': card['in_game_id'], 'from': 'board_state.stack', 'to': f'board_state.players[{idx}].{target_zone}'}]
