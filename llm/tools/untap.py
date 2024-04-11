from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload

class prevent_one_untap(BaseTool):
    name = "prevent_one_untap"
    description = """This will prevent one permanent you control from untapping. Use this to keep the permanent tapped. You may only use this if and only if the card instructs you to do so."""
    def _run(self, _id):
        pass

class prevent_all_untap(BaseTool):
    name = "prevent_all_untap"
    description = """This will prevent all permanents you control from untapping. You can only use this if you are affected by delayed triggers and can't untap."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        pass

class pass_untap(BaseTool):
    name = "pass_untap"
    description = """Pass the untap step. If no action is needed, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        pass

untap_actions = [ prevent_one_untap(), prevent_all_untap(), pass_untap() ]
