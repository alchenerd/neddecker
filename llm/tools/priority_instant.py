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

class pass_priority(BaseTool):
    name = "pass_priority"
    description = """Pass the priority to your opponent. If no action is needed according to the TODO list, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        return "Passed the priority! " \
            "Please announce to your Magic: the Gathering opponent as Ned Decker (AI) " \
            "what were done during this priority window. Say something like the output of this python fstring: " \
            "f\"{announce_your_game_actions} I will pass the priority.\" However, " \
            "you will paraphrase this string using the tone of Ned Decker, whose personality was given previously." \

priority_instant_actions = [ pass_priority() ]
