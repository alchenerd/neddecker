from typing import Required, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from .actions import CreateTrigger

class CardIdInput(BaseModel):
    in_game_id: str = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: str = Field(description="The name of the target card")

class PreventUntapOne(BaseTool):
    name: str = "prevent_untap_one"
    description: str = """This will prevent one target permanent you control from untapping. Use this to keep the permanent tapped. You may only use this if and only if the card instructs you to do so. Prevent cards from untapping separately (call this N times for N cards to prevent from untapping!)"""
    args_schema: Type[BaseModel] = CardIdInput
    def _run(self, in_game_id, card_name):
        new_action = {
            "type": "prevent_untap",
            "targetId": in_game_id,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return "Card {name} ({_id}) will stay tapped if it were tapped! Please continue with the next item of the TODO list and continue to prevent cards from untapping.\n".format(name=card_name, _id=in_game_id)

class PreventUntapAll(BaseTool):
    name: str = "prevent_untap_all"
    description: str = """This will prevent all permanents you control from untapping. Use this to prevent all cards from untapping. Only use this if a trigger (NOT CARD!) says that you will skip the untap step."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        new_action = {
            "type": "prevent_untap_all",
            "who": "ned",
            "targetId": None,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return "All tapped permanents you control will stay tapped! Please pass the untap step next.\n"

class PassUntap(BaseTool):
    name: str = "pass_untap"
    description: str = """Pass the untap step. If no action is needed according to the TODO list, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        return "Passed the untap step! If you have prevented nothing from untapping, say \"Untap.\" Otherwise, if you have prevented anything from untapping, announce to your opponent (Human) what cards stay tapped as Ned Decker.\n"

untap_actions = [ PreventUntapOne(), PreventUntapAll(), PassUntap() ]
untap_bonus_actions = [ CreateTrigger() ]
