import json
import threading
from typing import Required, Type, Dict, Any
from langchain.pydantic_v1 import BaseModel, Field, root_validator
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
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")

class CompanionCardInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    oracle_text: Required[str] = Field(description="The oracle text of the target card", pattern=r'^Companion')

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'^Companion', values.get('oracle_text')):
            raise ValueError('This card is not a companaion!')
        return values
"""

class BeginOnBattlefieldCardInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    oracle_text: Required[str] = Field(description="The oracle text of the target card", pattern=r'begin the game.*on the battlefield')

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'begin the game.*on the battlefield', values.get('oracle_text')):
            raise ValueError('This card cannot be put onto the battlefield at the start of the game!')
        return values
"""

class RevealDelayedTriggerInput(BaseModel):
    in_game_id: Required[str] = Field(description="ID of a card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    trigger_what: Required[str] = Field(description=(
        "What to do when the trigger is triggered; "
        "this needs to be an excerpt of the card's oracle text. "
        "(The excerpt must be minimal and describe the desired only trigger.)"
    ))
    oracle_text: Required[str] = Field(description="The oracle text of the target card", pattern=r'reveal.*opening hand')

"""
    @root_validator
    def validate_query(cls, values: Dict[str, Any]) -> Dict:
        if not re.search(r'reveal.*opening hand', values.get('oracle_text')):
            raise ValueError('This card cannot be revealed for effects at the start of the game!')
        return values
"""

class SetCounterInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    counter_type: Required[str] = Field(description="The type of the counter; e.g. \"stun\", \"+1/+1\"")
    counter_amount: Required[int] = Field(description="The amount of the counter")

class choose_companion(BaseTool):
    name = "choose_companion"
    description = """Submit the chosen companion; required input is the chosen companion's ID. If there was no companion in the sideboard, then skip this."""
    args_schema: Type[BaseModel] = CompanionCardInput
    def _run(self, in_game_id, card_name, oracle_text):
        new_action = {
            "type": "set_annotation",
            "targetId": in_game_id,
            "annotationKey": "isCompanion",
            "annotationValue": True,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return (
            "{name} ({_id}) is set to be companion! ".format(name=card_name, _id=in_game_id) +
            "Ned Decker may later in the game pay three mana and put it into his hand as a sorcery. "
            "For now, it stays in Ned's sideboard.\n"
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class reveal_from_hand(BaseTool):
    name = "reveal_from_hand"
    description = """Submit a delayed trigger that will happen at the first upkeep of the game. Do not use this to choose a companion; use choose_companion instead. Do not use this to move a card from hand to battlefield; use move_to_battlefield_from_hand instead."""
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
            "Delayed trigger {name} ({_id}): \"{what}\" submitted! ".format(name=card_name, _id=in_game_id, what=trigger_what) +
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class move_to_battlefield_from_hand(BaseTool):
    name = "move_to_battlefield_from_hand"
    description = """Submit to move a card from hand to battlefield. Only call this when a card in hand says that owner may begin the game with it on the battlefield."""
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
        return (
            "Card {name} ({_id}) moved to battledfield! ".format(name=card_name, _id=in_game_id) +
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class set_counter(BaseTool):
    name = "set_counter"
    description = """Set a number of counters of one type on a card on the battlefield. Target card must be moved by move_to_battlefield_from_hand."""
    args_schema: Type[BaseModel] = SetCounterInput
    def _run(self, in_game_id, card_name, counter_type, counter_amount):
        new_action = {
            "type": "set_counter",
            "targetId": in_game_id,
            "counterType": counter_type,
            "counterAmount": counter_amount,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return (
            "{count} {_type} counter(s) is set on card {name} ({_id})! ".format(count=counter_amount, _type=counter_type, name=card_name, _id=in_game_id) +
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class exile_from_hand(BaseTool):
    name = "exile_from_hand"
    description = """Move a card from hand to exile."""
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
            "Card {name} ({_id}) is exiled! ".format(name=card_name, _id=in_game_id) +
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class pass_start_of_game(BaseTool):
    name = "pass_start_of_game"
    description = """Submit to pass the start of game phase. No parameter needed."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}

    def _run(self):
        pprint(payload.g_actions)
        return "Submitted to pass the start of game phase! As Ned Decker, announce to opponent (Human) what actions were made. Be short and terse. No quotation marks, and no metadata."

start_of_game_actions = [
    choose_companion(),
    reveal_from_hand(),
    move_to_battlefield_from_hand(),
    set_counter(),
    exile_from_hand(),
    pass_start_of_game(),
]
