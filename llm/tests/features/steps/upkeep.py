from behave import *
import json
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from llm.prompts.upkeep import UpkeepPromptPreset as UPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor

# Cards
def mountain(n):
    return {
        "in_game_id": "n1#{0}".format(n+1),
        "name": "Mountain", "mana_cost": None,
        "type_line": "Basic Land - Mountain",
        "oracle_text": "({T}: Add {R}.)",
        "power": None, "toughness": None,
    }

def forest(n):
    return {
        "in_game_id": "n2#{0}".format(n+1),
        "name": "Forest", "mana_cost": None,
        "type_line": "Basic Land - Forest",
        "oracle_text": "({T}: Add {G}.)",
        "power": None, "toughness": None,
    }

def grizzly_bears(n):
    """A permanent chosen at random that has no upkeep trigger."""
    return {
        "in_game_id": "n3#{0}".format(n+1),
        "name": "Grizzly Bears", "mana_cost": None,
        "type_line": "Creature - Bear",
        "oracle_text": None,
        "power": "2", "toughness": "2",
    }

def vensers_journal(n):
    """A permanent chosen at random that has an upkeep trigger."""
    return {
        "in_game_id": "n4#{0}".format(n+1),
        "name": "Venser's Journal", "mana_cost": "{5}",
        "type_line": "Artifact",
        "oracle_text": "You have no maximum hand size.\nAt the beginning of your upkeep, you gain 1 life for each card in your hand.",
        "power": None, "toughness": None,
    }

def archangel_avacin(n):
    """A permanent chosen at random that has an delayed upkeep trigger."""
    return {
        "in_game_id": "n5#{0}".format(n+1),
        "name": "Archangel Avacyn // Avacyn, the Purifier", "mana_cost": "{3}{W}{W}",
        "type_line": "Legendary Creature - Angel",
        "sides": {
            "front": {
                "name": "Archangel Avacyn",
                "oracle_text": "Flash\nFlying, vigilance\nWhen Archangel Avacyn enters the battlefield, creatures you control gain indestructible until end of turn.\nWhen a non-Angel creature you control dies, transform Archangel Avacyn at the beginning of the next upkeep.",
                "power": "4", "toughness": "4",
            },
            "back": {
                "name": "Avacyn, the Purifier",
                "oracle_text": "Flying\nWhen this creature transforms into Avacyn, the Purifier, it deals 3 damage to each other creature and each opponent.",
                "power": "6", "toughness": "5",
            },
        },
    }

# Steps
@given(u'the AI player for upkeep step is GPT from OpenAI')
def step_impl(context):
    context.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=1024)
    #context.llm = ChatOpenAI(model_name='gpt-4', temperature=0, max_tokens=1024)
    context.chat_prompt = UPP.chat_prompt
    context.tools = UPP.tools
    assert context.tools
    context.tools_prompt = UPP.tools_prompt
    context.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
    context.requests = UPP.requests
    context.agent_executor = CSAgentExecutor(
            llm=context.llm,
            chat_prompt=context.chat_prompt,
            tools_prompt=context.tools_prompt,
            tools=context.tools,
            memory=context.memory,
            requests=context.requests,
            verbose=True,
    )

@given(u'the AI player has no permanent that has an upkeep trigger')
def step_impl(context):
    context.battlefield = [ mountain(0), forest(0), grizzly_bears(0) ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []

@given(u'the AI player has one permanent that has an upkeep trigger because of permanent')
def step_impl(context):
    context.battlefield = [ mountain(0), forest(0), grizzly_bears(0), vensers_journal(0) ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []

@given(u'the AI player has one permanent that has an upkeep trigger because of delayed trigger')
def step_impl(context):
    context.battlefield = [ mountain(0), forest(0), grizzly_bears(0), archangel_avacin(0) ]
    context.ned_delayed_triggers = [
        {
          "targetId": "n5#1",
          "targetCardName": "Archangel Avacyn",
          "affectingWho": "ned",
          "triggerWhen": "At the beginning of this upkeep",
          "triggerContent": "Transform Archangel Avacin",
        },
    ]
    context.user_delayed_triggers = []

@given(u'the AI player has two permanents that has an upkeep trigger')
def step_impl(context):
    context.battlefield = [ mountain(0), forest(0), grizzly_bears(0), vensers_journal(0), archangel_avacin(0) ]
    context.ned_delayed_triggers = [
        {
          "targetId": "n5#1",
          "targetCardName": "Archangel Avacyn",
          "affectingWho": "ned",
          "triggerWhen": "At the beginning of this upkeep",
          "triggerContent": "Transform Archangel Avacin",
        },
    ]
    context.user_delayed_triggers = []


@when(u'the system asks the AI player for upkeep decisions')
def step_impl(context):
    with payload.g_actions_lock:
        payload.g_actions = []

    assert context.battlefield is not None
    assert context.ned_delayed_triggers is not None
    assert context.user_delayed_triggers is not None
    board_analysis = UPP.board_analysis.format( \
            battlefield=json.dumps(context.battlefield, indent=4), \
            ned_delayed_triggers=json.dumps(context.ned_delayed_triggers, indent=4), \
            user_delayed_triggers=json.dumps(context.user_delayed_triggers, indent=4) \
    )
    _input = UPP._input
    context.response = context.agent_executor.invoke({
        'data': board_analysis,
        'input': _input,
    })


@then(u'the AI player creates one upkeep trigger')
def step_impl(context):
    assert len(payload.g_actions) == 1


@then(u'the AI player creates two upkeep triggers')
def step_impl(context):
    assert len(payload.g_actions) == 2
