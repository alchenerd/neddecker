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
from .actions import CreateTrigger

class PassUpkeep(BaseTool):
    name = "pass_upkeep"
    description = """Pass the upkeep step. If no action is needed according to the TODO list, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        return "Passed the upkeep step! Please announce to your opponent (Human) as Ned Decker (AI) what Ned's upkeep triggers were put onto the stack (refer to card names and abilities if any). Speak as if you are Ned Decker who's making his plays while announcing in the game. Use only Ned's tone. No quotation marks.\n"

upkeep_actions = [ CreateTrigger(), PassUpkeep() ]
