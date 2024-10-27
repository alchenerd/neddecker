import json
import threading
from typing import Required, Type, Dict, Any
from pydantic import BaseModel, Field, root_validator
from langchain.tools import BaseTool
from pprint import pprint
import re

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../../../')
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload

class CardIdInput(BaseModel):
    in_game_id: str = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: str = Field(description="The name of the target card")

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'^Companion', values.get('oracle_text')):
            raise ValueError('This card is not a companaion!')
        return values
"""

class BeginOnBattlefieldCardInput(BaseModel):
    in_game_id: str = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: str = Field(description="The name of the target card")
    oracle_text: str = Field(description="The oracle text of the target card", pattern=r'begin the game.*on the battlefield')

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'begin the game.*on the battlefield', values.get('oracle_text')):
            raise ValueError('This card cannot be put onto the battlefield at the start of the game!')
        return values
"""

class RevealDelayedTriggerInput(BaseModel):
    in_game_id: str = Field(description="ID of a card; e.g. \"n1#1\"")
    card_name: str = Field(description="The name of the target card")
    trigger_what: str = Field(description=(
        "What to do when the trigger is triggered; "
        "this needs to be an excerpt of the card's oracle text. "
        "(The excerpt must be minimal and describe the desired only trigger.)"
    ))
    oracle_text: str = Field(description="The oracle text of the target card", pattern=r'reveal.*opening hand')

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'reveal.*opening hand', values.get('oracle_text')):
            raise ValueError('This card cannot be revealed for effects at the start of the game!')
        return values
"""

class SetLuckCounterInput(BaseModel):
    in_game_id: str = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: str = Field(description="The name of the target card")

class reveal_from_opening_hand(BaseTool):
    name: str = "reveal_from_opening_hand"
    description: str = """Submit a delayed trigger that will happen at the first upkeep of the game. Do not use this to choose a companion; use choose_companion instead. Do not use this to move a card from hand to battlefield; use move_to_battlefield_from_hand instead."""
    args_schema: Type[BaseModel] = RevealDelayedTriggerInput
    def _run(self, in_game_id, card_name, trigger_what, oracle_text):
        new_action = {
            "type": "create_delayed_trigger",
            "targetId": in_game_id,
            "targetCardName": card_name,
            "triggerWhen": "At the beginning of the first upkeep",
            "triggerWhat": trigger_what,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return (
            "Delayed trigger {name} ({_id}): \"{what}\" submitted!\n".format(name=card_name, _id=in_game_id, what=trigger_what) +
            "Continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase.\n"
        )

class move_to_battlefield_from_hand(BaseTool):
    name: str = "move_to_battlefield_from_hand"
    description: str = """Submit to move a card from hand to battlefield. Only call this when a card in hand says that owner may begin the game with it on the battlefield."""
    args_schema: Type[BaseModel] = BeginOnBattlefieldCardInput
    def _run(self, in_game_id, card_name, oracle_text):
        new_action = {
            "type": "move",
            "targetId": in_game_id,
            "from": "{ned}.hand",
            "to": "{ned}.battlefield",
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)

        return_string = (
            "Card {name} ({_id}) moved to battledfield!\n".format(name=card_name, _id=in_game_id) +
            "Continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase.\n"
        )
        if card_name == 'Gemstone Caverns':
            return_string += (
                "Looks like you have put a Gemstone Caverns onto the battlefield!\n"
                "Remember to set a luck counter on it!\n"
            )
        return return_string

class set_luck_counter(BaseTool):
    name: str = "set_luck_counter"
    description: str = """Set a luck counter on Gemstone Caverns."""
    args_schema: Type[BaseModel] = SetLuckCounterInput
    def _run(self, in_game_id, card_name,):
        new_action = {
            "type": "set_counter",
            "targetId": in_game_id,
            "counterType": "luck",
            "counterAmount": 1,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return (
            "One luck counter is set on card {name} ({_id})!\n".format(name=card_name, _id=in_game_id) +
            "Remember to exile a card from hand because of Gemstone Caverns!\n"
            "Continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase.\n"
        )

class exile_from_hand(BaseTool):
    name: str = "exile_from_hand"
    description: str = """Move a card from hand to exile."""
    args_schema: Type[BaseModel] = CardIdInput
    def _run(self, in_game_id, card_name):
        new_action = {
            "type": "move",
            "targetId": in_game_id,
            "from": "{ned}.hand",
            "to": "{ned}.exile",
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return (
            "Card {name} ({_id}) is exiled!\n".format(name=card_name, _id=in_game_id) +
            "Continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase.\n"
        )

class pass_start_of_game(BaseTool):
    name: str = "pass_start_of_game"
    description: str = """Pass the start of game phase. No input parameter needed."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}

    def _run(self):
        pprint(payload.g_actions)
        return "Submitted to pass the start of game phase!\nPlease announce to opponent (Human) what actions were made as Ned Decker (AI). If no actions were made, say that you're passing the phase. Announce from Ned Decker's POV. Be short and terse. No quotation marks, and no metadata. You must only write down what Ned Decker would say.\n"

start_of_game_actions = [
    reveal_from_opening_hand(),
    move_to_battlefield_from_hand(),
    set_luck_counter(),
    exile_from_hand(),
    pass_start_of_game(),
]
