from typing import Required, Type, Dict, Any
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from .actions import Move, SetCounter, SetAnnotation, CreateTrigger, SetMana, SetHp, PassPriority


priority_instant_actions = [Move(), SetCounter(), SetAnnotation(), CreateTrigger(), SetMana(), SetHp(), PassPriority() ]
