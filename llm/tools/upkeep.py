from typing import Required, Type, Dict, Any
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload

class TriggerInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\"")
    card_name: Required[str] = Field(description="The name of the target card")
    trigger_content: Required[str] = Field(description= \
            "The excerpt of the card's oracle text that describes the trigger that will be put onto the stack;" \
            " e.g. trigger_content will be \"You may pay {2}...\" " \
            "for a card that says \"Whenever ~ untaps, you may pay {2}...\""
    )

class create_trigger(BaseTool):
    name = "create_trigger"
    description = """Create a trigger on the stack according to a card."""
    args_schema: Type[BaseModel] = TriggerInput
    def _run(self, in_game_id, card_name, trigger_content):
        new_action = {
            "type": "create_trigger",
            "targetId": in_game_id,
            "triggerContent": trigger_content,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return "Card {name} ({_id}) trigger is put onto the stack! You may create more triggers using `create_trigger` or pass the upkeep step using `pass_upkeep`.\n".format(name=card_name, _id=in_game_id)

class pass_upkeep(BaseTool):
    name = "pass_upkeep"
    description = """Pass the upkeep step. If no action is needed according to the TODO list, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        return "Passed the upkeep step! Please announce to your opponent (Human) as Ned Decker (AI) what Ned's upkeep triggers were put onto the stack (refer to card names and abilities if any). Speak as if you are Ned Decker who's making his plays while announcing in the game. Use only Ned's tone. No quotation marks.\n"

upkeep_actions = [ create_trigger(), pass_upkeep() ]
