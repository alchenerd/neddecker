import json
from copy import copy
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
from llm.prompts.start_of_game import StartOfGamePromptPreset as SOGPP
from llm.prompts.untap import UntapPromptPreset as UnPP
from llm.prompts.upkeep import UpkeepPromptPreset as UpPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor
import payload

from dotenv import load_dotenv
load_dotenv()

class Ned():
    def __init__(self):
        self.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.2, max_tokens=2048)
        #self.llm = ChatOpenAI(model_name='gpt-4-1106-preview', temperature=0.2, max_tokens=2048)
        self.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
        self.agent_executor = None

    def clear_memory(self):
        self.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)

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
                match json_data['phase']:
                    case 'start of game phase':
                        return self.ask_ned_decker(topic='start_of_game', data=json_data)
                    case 'upkeep step':
                        return self.ask_ned_decker(topic='upkeep', data=json_data)
                    case _:
                        return f'Beep boop Ned passes priority ({json_data["whose_turn"]}\'s {json_data["phase"]})', { 'type': 'pass_priority', 'who': 'ned', 'actions': [] }
            case 'require_player_action':
                match json_data['phase']:
                    case 'untap step':
                        return self.ask_ned_decker(topic='untap', data=json_data)
                    case _:
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

    def process_card(self, bulky_card):
        """Create a processed card by extracting crucial information for LLM to read.
        """
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
        if 'counters' in bulky_card:
            card['counters'] = bulky_card['counters']
        if 'annotations' in bulky_card:
            card['annotations'] = bulky_card['annotations']
        if 'ai_annotations' in bulky_card:
            card['tags'] = bulky_card['ai_annotations']
        return card

    def ask_ned_decker(self, topic, data):
        self.clear_memory()
        with payload.g_payload_lock:
            payload.g_payload = {}
        with payload.g_actions_lock:
            payload.g_actions = []
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

                hand = list(map(self.process_card, data.get('hand', [])))

                to_bottom_count = data.get('to_bottom')
                land_count = MPP.count_lands(hand)
                land_warning_string = MPP.land_warning_string(land_count)
                hand_analysis = MPP.hand_analysis.format(
                        hand=json.dumps(hand, indent=4),
                        land_count=land_count,
                        land_warning_string=land_warning_string,
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
            case 'start_of_game':
                agent_executor = CSAgentExecutor(
                        llm=self.llm,
                        chat_prompt=SOGPP.chat_prompt,
                        tools_prompt=SOGPP.tools_prompt,
                        tools=SOGPP.tools,
                        memory=self.memory,
                        requests=SOGPP.requests,
                        verbose=True,
                )
                players = data.get('board_state', {}).get('players', [])
                [ ned ] = list(filter(lambda p: p['player_name'] == 'ned', players))
                assert ned
                hand = list(map(self.process_card, ned.get('hand', [])))
                sideboard = list(map(self.process_card, ned.get('sideboard', [])))
                companions = []
                to_reveal = []
                to_battlefield = []
                for card in sideboard:
                    print(card)
                    oracle_text = card.get('oracle_text') or card.get('faces').get('front').get('oracle_text')
                    assert oracle_text
                    if 'Companion' in oracle_text:
                        companions.append(card)
                    if 'opening hand' in oracle_text:
                        to_reveal.append(card)
                    if 'begin the game' in oracle_text:
                        to_battlefield.append(card)
                hand = [ { **card, 'where': 'hand' } for card in hand ]
                board_analysis = SOGPP.board_analysis.format( \
                        companions=json.dumps(companions, indent=4), \
                        to_reveal=json.dumps(to_reveal, indent=4), \
                        to_battlefield=json.dumps(to_battlefield, indent=4) \
                )
                if 'Error' not in to_battlefield and any('Gemstone Caverns' in card['name'] for card in to_battlefield):
                    board_analysis += SOGPP.more_board_analysis.format(hand=json.dumps(hand), indent=4)
                _input = SOGPP._input

                response = agent_executor.invoke({
                    'data': board_analysis,
                    'input': _input,
                })
                print (response.get('output'))
                print (payload.g_actions)
                ret_payload = {
                    'type': 'pass_priority',
                    'who': 'ned',
                    'actions': copy(payload.g_actions)
                }
                return response.get('output'), ret_payload
            case 'untap':
                players = data.get('board_state', {}).get('players', [])
                [ ned ] = list(filter(lambda p: p['player_name'] == 'ned', players))
                [ user ] = list(filter(lambda p: p['player_name'] == 'user', players))
                assert ned and user

                battlefield = list(map(self.process_card, ned.get('battlefield', [])))
                ned_delayed_triggers = ned.get('delayed_triggers', [])
                user_delayed_triggers = user.get('delayed_triggers', [])
                triggered_when_untapped = list(filter(
                        lambda x: 'becomes untapped' in x.get('oracle_text', '') or \
                                'Whenever you untap' in x.get('oracle_text', ''), battlefield
                        ))

                requests = None
                board_analysis = None
                tools = None
                if triggered_when_untapped:
                    requests = UnPP.requests + UnPP.bonus_requests
                    board_analysis = UnPP.board_analysis + UnPP.bonus_board_analysis
                    board_analysis = board_analysis.format(
                            battlefield=json.dumps(battlefield, indent=4), \
                            ned_delayed_triggers=json.dumps(ned_delayed_triggers, indent=4), \
                            user_delayed_triggers=json.dumps(user_delayed_triggers, indent=4), \
                            triggered_when_untapped=json.dumps(triggered_when_untapped, indent=4)
                            )
                    tools = UnPP.untap_actions + UnPP.untap_bonus_actions
                else:
                    requests = UnPP.requests
                    board_analysis = UnPP.board_analysis.format( \
                            battlefield=json.dumps(battlefield, indent=4), \
                            ned_delayed_triggers=json.dumps(ned_delayed_triggers, indent=4), \
                            user_delayed_triggers=json.dumps(user_delayed_triggers, indent=4), \
                    )
                    tools = UnPP.untap_actions

                _input = UnPP._input

                agent_executor = CSAgentExecutor(
                        llm=self.llm,
                        chat_prompt=UnPP.chat_prompt,
                        tools_prompt=UnPP.tools_prompt,
                        tools=tools,
                        memory=self.memory,
                        requests=requests,
                        verbose=True,
                )

                response = agent_executor.invoke({
                    'data': board_analysis,
                    'input': _input,
                })
                print (response.get('output'))
                print (payload.g_actions)
                # translate "prevent untap" to "untap all others"
                untap_actions = []
                if any(action['type'] == 'prevent_untap_all' for action in payload.g_actions):
                    pass
                else:
                    prevented_cards = [ action['targetId'] for action in payload.g_actions if action['type'] == 'prevent_untap' ]
                    for card in battlefield:
                        if card['in_game_id'] in prevented_cards:
                            pass
                        else:
                            new_action = {
                                'type': 'set_annotation',
                                'targetId': card['in_game_id'],
                                'annotationKey': 'isTapped',
                                'annotationValue': False,
                            }
                            untap_actions.append(new_action)
                other_actions = [ action for action in payload.g_actions if 'untap' not in action['type'] ]
                untap_actions.extend(other_actions)
                ret_payload = {
                    'type': 'pass_non_priority_action',
                    'who': 'ned',
                    'actions': untap_actions,
                }
                return response.get('output'), ret_payload
            case "upkeep":
                players = data.get('board_state', {}).get('players', [])
                [ ned ] = list(filter(lambda p: p['player_name'] == 'ned', players))
                [ user ] = list(filter(lambda p: p['player_name'] == 'user', players))
                assert ned and user

                battlefield = list(map(self.process_card, ned.get('battlefield', [])))
                ned_delayed_triggers = ned.get('delayed_triggers', [])
                user_delayed_triggers = user.get('delayed_triggers', [])

                requests = UpPP.requests
                board_analysis = UpPP.board_analysis
                board_analysis = board_analysis.format(
                        battlefield=json.dumps(battlefield, indent=4), \
                        ned_delayed_triggers=json.dumps(ned_delayed_triggers, indent=4), \
                        user_delayed_triggers=json.dumps(user_delayed_triggers, indent=4), \
                        )
                tools = UpPP.tools

                _input = UpPP._input

                agent_executor = CSAgentExecutor(
                        llm=self.llm,
                        chat_prompt=UpPP.chat_prompt,
                        tools_prompt=UpPP.tools_prompt,
                        tools=tools,
                        memory=self.memory,
                        requests=requests,
                        verbose=True,
                )

                response = agent_executor.invoke({
                    'data': board_analysis,
                    'input': _input,
                })
                print (response.get('output'))
                print (payload.g_actions)

                ret_speech = response.get('output')
                ret_actions = copy(payload.g_actions)

                # aside from upkeep triggers, Ned will recieve priority as well (instant speed)
                priority_response = self.ask_ned_decker(topic="receive_priority_instant", data=data)
                ret_speech += " "
                ret_speech += priority_response[0]
                ret_actions.extend(copy(payload.g_actions))

                ret_payload = {
                    'type': 'pass_priority',
                    'who': 'ned',
                    'actions': copy(payload.g_actions),
                }
                return ret_speech, ret_payload
            case "receive_priority_instant":
                dummy_action = {
                    "type": "create_trigger",
                    "targetId": "n1#1",
                    "triggerContent": "Ned's special instant-speed decisions!\n"
                }
                return "Test string: pretend these are cool instant-speed decisions!\n", [ dummy_action, ]
            case "receive_priority_sorcery":
                dummy_action = {
                    "type": "create_trigger",
                    "targetId": "n1#1",
                    "triggerContent": "Ned's special sorcery-speed decisions!\n"
                }
                return "Test string: pretend these are cool sorcery-speed decisions!\n", [ dummy_action, ]
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
