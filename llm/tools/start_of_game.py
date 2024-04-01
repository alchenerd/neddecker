import json
import threading
from typing import Required, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from pprint import pprint

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

class DelayedTriggerInput(BaseModel):
    in_game_id: Required[str] = Field(description="ID of a card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    trigger_what: Required[str] = Field(description=(
        "What to do when the trigger is triggered; "
        "this needs to be an excerpt of the card's oracle text. "
        "(The excerpt must be minimal and describe the desired only trigger.)"
    ))

class choose_companion(BaseTool):
    name = "choose_companion"
    description = """Submit the chosen companion; required input is the chosen companion's ID. If there was no companion in the sideboard, then skip this."""
    args_schema: Type[BaseModel] = CardIdInput
    def _run(self, in_game_id, card_name):
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
            "You may later in the game pay three mana and put it into your hand as a sorcery. "
            "For now, it stays in your sideboard.\n"
            "Pass the start of game phase or "
            "continue to take start of game actions for other cards "
            "until Ned Decker (AI) wants to pass the start of game phase."
        )

class reveal_from_hand(BaseTool):
    name = "reveal_from_hand"
    description = """Submit a delayed trigger that will happen at the first upkeep of the game. Do not use this to choose a companion; use choose_companion instead. Do not use this to move a card from hand to battlefield; use move_to_battlefield_from_hand instead."""
    args_schema: Type[BaseModel] = DelayedTriggerInput
    def _run(self, in_game_id, card_name, trigger_what):
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
    description = """Submit to move a card from hand to battlefield. Only call this when a card in hand says that you may begin the game with it on the battlefield."""
    args_schema: Type[BaseModel] = CardIdInput
    def _run(self, in_game_id, card_name):
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

class pass_start_of_game(BaseTool):
    name = "pass_start_of_game"
    description = """Submit to pass the start of game phase. No parameter needed from input."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}

    def _run(self):
        pprint(payload.g_actions)
        return "Submitted to pass the start of game phase! As Ned Decker, announce to opponent (Human) what actions were made. Be short and terse. No quotation marks, and no metadata."

start_of_game_actions = [
    choose_companion(),
    reveal_from_hand(),
    move_to_battlefield_from_hand(),
    pass_start_of_game(),
]
