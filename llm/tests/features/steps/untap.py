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
        "type_line": "Artifact Creature — Insect",
        "oracle_text": "Flying\nBrass Gnat doesn’t untap during your untap step.\nAt the beginning of your upkeep, you may pay {1}. If you do, untap Brass Gnat.",
        "power": "1", "toughness": "1",
        "annotations": {
            "isTapped": True,
        }
    }

def tapped_and_frozen_goblin_guide(n):
    return {
        "in_game_id": "n1#{0}".format(n+1),
        "name": "Goblin Guide", "mana_cost": "{R}",
        "type_line": "Creature — Goblin Scout",
        "oracle_text": "Haste\nWhenever Goblin Guide attacks, defending player reveals the top card of their library. If it’s a land card, that player puts it into their hand.",
        "power": "2", "toughness": "2",
        "annotations": {
            "isTapped": True,
            "affectedByCreepingChill": "Tap target creature. It doesn’t untap during its controller’s next untap step.",
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
    try:
        assert len(payload.g_actions) == 1
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e


@given(u'there are three cards that don\'t untap because of oracle text')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], *[ tapped_brass_gnat(n) for n in range(3) ], ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []


@given(u'the AI player is set to skip the untap step because of self')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], ]
    context.ned_delayed_triggers = [ { "targetId": "n3#1", "targetCardName": "Savor the Moment", "triggerWhen": "On the extra turn (this turn)", "triggerWhat": "Casted last turn: \"Take an extra turn after this one.\nSkip the untap step of that turn.\"" } ]
    context.user_delayed_triggers = []


@given(u'the AI player is set to skip the untap step because of opponent')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = [ { "targetId": "u1#1", "targetCardName": "Brine Elemental", "triggerWhen": "opponent's next untap step", "triggerWhat": "When Brine Elemental is turned face up, each opponent skips their next untap step." } ]


@then(u'the AI player chooses to prevent all controlled cards\' untapping')
def step_impl(context):
    try:
        assert len(payload.g_actions) == 1 and payload.g_actions[0]['type'] == 'prevent_untap_all'
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e


@given(u'there is one card that was annotated as doesn\'t untap')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], tapped_and_frozen_goblin_guide(2), ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []


@given(u'there are three cards that were annotated as doesn\'t untap')
def step_impl(context):
    context.battlefield = [ *[ tapped_goblin_guide(n) for n in range(2) ], *[ tapped_and_frozen_goblin_guide(n) for n in range(2, 5) ], ]
    context.ned_delayed_triggers = []
    context.user_delayed_triggers = []


@then(u'the AI player chooses to prevent the three card\'s untapping')
def step_impl(context):
    try:
        assert len(payload.g_actions) == 3
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e
