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
llmrootdir = os.path.dirname(currentdir + '/../../../')
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from llm.prompts.untap import UntapPromptPreset as UPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor

@given(u'the AI player for untap step is GPT from OpenAI')
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

def tapped_goblin_guide(n):
    return {
        "in_game_id": "n1#{0}".format(n+1),
        "name": "Goblin Guide", "mana_cost": "{R}",
        "type_line": "Creature — Goblin Scout",
        "oracle_text": "Haste\nWhenever Goblin Guide attacks, defending player reveals the top card of their library. If it’s a land card, that player puts it into their hand.",
        "power": "2", "toughness": "2",
        "annotations": {
            "isTapped": True,
        }
    }

def tapped_brass_gnat(n):
    return {
        "in_game_id": "n2#{0}".format(n+1),
        "name": "Brass Gnat", "mana_cost": "{1}",
        "type_line": "Artifact Creature — Insect ",
        "oracle_text": "Flying\nBrass Gnat doesn’t untap during your untap step.\nAt the beginning of your upkeep, you may pay {1}. If you do, untap Brass Gnat.",
        "power": "1", "toughness": "1",
        "annotations": {
            "isTapped": True,
        }
    }


@given(u'there is no card to prevent from untapping')
def step_impl(context):
    context.battlefield = [ tapped_goblin_guide(n) for n in range(2) ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []


@when(u'the system asks the AI player for prevent untap decisions')
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

@given(u'there is one card that doesn\'t untap because of oracle text')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], tapped_brass_gnat(1), ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []


@then(u'the AI player chooses to prevent the card\'s untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent the card\'s untapping')


@given(u'there are three cards that don\'t untap because of oracle text')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there are three cards that don\'t untap because of oracle text')


@then(u'the AI player chooses to prevent those cards\' untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent those cards\' untapping')


@given(u'the AI player is set to skip the untap step')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the AI player is set to skip the untap step')


@then(u'the AI player chooses to prevent all controlled cards\' untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent all controlled cards\' untapping')


@given(u'there is one card that was annotated as doesn\'t untap')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there is one card that was annotated as doesn\'t untap')


@given(u'there are three cards that were annotated as doesn\'t untap')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there are three cards that were annotated as doesn\'t untap')


@then(u'the AI player chooses to prevent the three card\'s untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent the three card\'s untapping')
