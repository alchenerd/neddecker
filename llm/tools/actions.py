from typing import Required, Type
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload


# move card from a to b
class MoveInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\".")
    card_name: Required[str] = Field(description="The name of the target card.")
    from_where: Required[str] = Field(description="Use format [player_name]-[zone_name]; e.g. ned-hand.")
    to_where: Required[str] = Field(description="Use format [player_name]-[zone_name]; e.g. ned-graveyard.")

class Move(BaseTool):
    name = "move"
    description = """Move target card from source zone to destination zone. This is for paying cost only, such as discard or sacrifice. Additionally, you may put a card from your hand to the stack to cast it. Do not use this for any other purpose."""
    args_schema: Type[BaseModel] = MoveInput
    def _run(self, in_game_id, card_name, from_where, to_where):
        new_action = {
            "type": "move",
            "targetId": in_game_id,
            "from": from_where,
            "to": to_where,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return f"{card_name} ({in_game_id}) is moved from {from_where} to {to_where}!"


# set counter on a card
class SetCounterInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\".")
    card_name: Required[str] = Field(description="The name of the target card.")
    counter_type: Required[str] = Field(description="The type of the counter you want to set; e.g. +1/+1.")
    counter_amount: Required[int] = Field(description="The resultant counter amount that will be on the target card. For example, if a card had 1 loyalty counter on it before and you activate a +2 ability, then the resultant counter amount will be 3, because 1 + 2 = 3.")

class SetCounter(BaseTool):
    name = "set_counter"
    description = """Set the amount of a type of counter on target card. This is for paying cost only, such as removing counters by setting a lower value for some counter. Do not use this for any other purpose."""
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
        return f"{card_name} ({in_game_id}) now has {counter_amount} {counter_type} counter(s)!"


# set annotation on a card
class SetAnnotationInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\".")
    card_name: Required[str] = Field(description="The name of the target card.")
    annotation_key: Required[str] = Field(description="The topic of annotation that you want to set on target card; e.g. isTapped.")
    annotation_value: Required[str] = Field(description="Target card's value regarding the annotation key topic; e.g. True.")

class SetAnnotation(BaseTool):
    name = "set_annotation"
    description = """Set a non-counter annotaion on target card. This is for paying cost only, such as tapping a card or untapping a card. Do not use this for any other purpose."""
    args_schema: Type[BaseModel] = SetAnnotationInput
    def _run(self, in_game_id, card_name, annotation_key, annotation_value):
        new_action = {
            "type": "set_annotation",
            "targetId": in_game_id,
            "annotationKey": annotation_key,
            "annotationValue": annotation_value,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return f"{card_name} ({in_game_id}) now is marked with {annotation_key}: {annotation_value}!"


# create trigger because of a card
class CreateTriggerInput(BaseModel):
    in_game_id: Required[str] = Field(description="The ID of the target card; e.g. \"n1#1\".")
    card_name: Required[str] = Field(description="The name of the target card.")
    trigger_content: Required[str] = Field(description="What part of target card's oracle text describes the intended trigger?")

class CreateTrigger(BaseTool):
    name = "create_trigger"
    description = """Create a trigger on top of the stack originated from target card. This is for activating a card. Do not use this for any other purpose."""
    args_schema: Type[BaseModel] = CreateTriggerInput
    def _run(self, in_game_id, card_name, trigger_content):
        new_action = {
            "type": "create_trigger",
            "targetId": in_game_id,
            "triggerContent": trigger_content,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return f"The trigger of {card_name} ({in_game_id}) - {trigger_content} is put onto the stack!"


# set mana
class SetManaInput(BaseModel):
    white: Required[int] = Field(description="State the resultant amount of white mana you will have.")
    blue: Required[int] = Field(description="State the resultant amount of blue mana you will have.")
    black: Required[int] = Field(description="State the resultant amount of black mana you will have.")
    red: Required[int] = Field(description="State the resultant amount of red mana you will have.")
    green: Required[int] = Field(description="State the resultant amount of green mana you will have.")
    colorless: Required[int] = Field(description="State the resultant amount of colorless mana you will have.")

class SetMana(BaseTool):
    name = "set_mana"
    description = """Set your mana pool. This is for paying cost, or activating mana abilities for paying cost later. Do not use this for any other purpose."""
    args_schema: Type[BaseModel] = SetManaInput
    def _run(self, white, blue, black, red, green, colorless):
        mana_pool = {
            "W": white,
            "U": blue,
            "B": black,
            "R": red,
            "G": green,
            "C": colorless,
        }
        new_action = {
            "type": "set_mana",
            "targetId": "ned",
            "manaPool": mana_pool,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return f"You now have: \n- {white} white mana,\n- {blue} blue mana, \n- {black} black mana, \n- {red} red mana, \n- {green} green mana, \n- {colorless} colorless mana!"


# set hp
class SetHpInput(BaseModel):
    amount: Required[int] = Field(description="State the amount of hit point you will have.")

class SetHp(BaseTool):
    name = "set_hp"
    description = """Set your hit point. This is for paying life for casting spells or activate abilities. Do not use this for any other purpose."""
    args_schema: Type[BaseModel] = SetHpInput
    def _run(self, amount):
        new_action = {
            "type": "set_hp",
            "targetId": "ned",
            "value": amount,
        }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return f"You now have {amount} HP!"


# pass priority
class PassPriority(BaseTool):
    name = "pass_priority"
    description = """Pass the priority to your opponent. If no action is needed according to the TODO list, immediately call this only."""
    def _to_args_and_kwargs(self, tool_input):
        return (), {}
    def _run(self):
        new_action = { "type": "pass" }
        with payload.g_actions_lock:
            payload.g_actions.append(new_action)
        return "Passed the priority! " \
            "Please announce to your Magic: the Gathering opponent as Ned Decker (AI) " \
            "what were done during this priority window. Say something like the output of this python fstring: " \
            "f\"{announce_your_game_actions} I will pass the priority.\" However, " \
            "you will paraphrase this string using the tone of Ned Decker, whose personality was given previously."
