import json
from typing import Optional, Sequence, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../../../')
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload

class MulliganInput(BaseModel):
    choice: str = Field(description="\"mulligan\" or \"keep\" (without quotation marks)")
    to_bottom: Optional[Sequence[str]] = Field(
            description='An array of card IDs that will be sent to the bottom of the library'
    )

class submit_mulligan_decision(BaseTool):
    name: str = 'submit_mulligan_descision'
    description: str = """Use this tool to submit "mulligan" or "keep"; if "keep" was chosen, Ned Decker has to submit cards to put from his hand to the bottom of his library (e.g. ["n1#1", "n1#2", "n2#1"]); if Ned Decker chose to keep a seven-card hand, the submitted value for "to_bottom" should be "[]"."""
    args_schema: Type[BaseModel] = MulliganInput

    def _run(self, choice: str, **kwargs) -> str:
        choice = choice.lower()
        assert choice in ('mulligan', 'keep')
        match choice:
            case 'mulligan':
                with payload.g_payload_lock:
                    payload.g_payload['type'] = 'mulligan'
                    payload.g_payload['who'] = 'ned'
                return "Ned Decker takes a mulligan! As Ned Decker, complain to your opponent about bad luck with a short sentence said by Ned Decker, but remember to keep all infomation of your cards a top secret! Don't say anything else; no quotes and no metadata. Just the sentence only."
            case 'keep':
                with payload.g_payload_lock:
                    payload.g_payload['type'] = 'keep_hand'
                    payload.g_payload['who'] = 'ned'
                    payload.g_payload['bottom'] = kwargs.get('to_bottom', [])
                return "Submitted to keep this hand! As Ned Decker, please hint your opponent how awesome is your hand with a short sentence said by Ned Decker, but remember to keep all infomation of your cards a top secret! Don't say anything else; no quotes and no metadata. Just the sentence only."
