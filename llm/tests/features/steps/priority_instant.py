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
from llm.prompts.priority_instant import PriorityInstantPromptPreset as PIPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor


# opponent's cards
def orcish_bowmasters(n):
    return {
        "in_game_id": "u1#{0}".format(n+1),
        "name": "Orcish Bowmasters", "mana_cost": "{1}{B}",
        "type_line": "Creature - Orc Archer",
        "oracle_text": "flash\nwhen orcish bowmasters enters the battlefield and whenever an opponent draws a card except the first one they draw in each of their draw steps, orcish bowmasters deals 1 damage to any target. then amass orcs 1.",
        "power": "1", "toughness": "1",
    }
def gilded_goose(n):
    return {
        "in_game_id": "u2#{0}".format(n+1),
        "name": "Gilded Goose", "mana_cost": "{G}",
        "type_line": "Creature - Bird",
        "oracle_text": "Flying\nWhen Gilded Goose enters the battlefield, create a Food token. (It’s an artifact with “{2}, {T}, Sacrifice this artifact: You gain 3 life.”)\n{1}{G}, {T}: Create a Food token.\n{T}, Sacrifice a Food: Add one mana of any color.",
        "power": "0", "toughness": "2",
    }
def zulaport_cutthroat(n):
    return {
        "in_game_id": "u3#{0}".format(n+1),
        "name": "Zulaport Cutthroat", "mana_cost": "{1}{B}",
        "type_line": "Creature - Human Rogue Ally",
        "oracle_text": "Whenever Zulaport Cutthroat or another creature you control dies, each opponent loses 1 life and you gain 1 life.",
        "power": "1", "toughness": "1",
    }
def verdant_catacombs(n):
    return {
        "in_game_id": "u4#{0}".format(n+1),
        "name": "Verdant Catacombs", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "{T}, Pay 1 life, Sacrifice Verdant Catacombs: Search your library for a Swamp or Forest card, put it onto the battlefield, then shuffle.",
        "power": None, "toughness": None,
    }
def blooming_marsh(n):
    return {
        "in_game_id": "u5#{0}".format(n+1),
        "name": "Blooming Marsh", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "Blooming Marsh enters the battlefield tapped unless you control two or fewer other lands.\n{T}: Add {B} or {G}.",
        "power": None, "toughness": None,
    }


# ned's cards
def dragons_rage_channeler(n):
    return {
        "in_game_id": "n1#{0}".format(n+1),
        "name": "Dragon's Rage Channeler", "mana_cost": "{R}",
        "type_line": "Creature - Human Shaman",
        "oracle_text": "Whenever you cast a noncreature spell, surveil 1. (Look at the top card of your library. You may put that card into your graveyard.)\nDelirium — As long as there are four or more card types among cards in your graveyard, Dragon’s Rage Channeler gets +2/+2, has flying, and attacks each combat if able.",
        "power": "1", "toughness": "1",
    }
def spirebluff_canal(n):
    return {
        "in_game_id": "n2#{0}".format(n+1),
        "name": "Spirebluff Canal", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "Spirebluff Canal enters the battlefield tapped unless you control two or fewer other lands.\n{T}: Add {U} or {R}.",
        "power": None, "toughness": None,
    }
def polluted_delta(n):
    return {
        "in_game_id": "n3#{0}".format(n+1),
        "name": "Polluted Delta", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "{T}, Pay 1 life, Sacrifice Polluted Delta: Search your library for an Island or Swamp card, put it onto the battlefield, then shuffle.",
        "power": None, "toughness": None,
    }
def ragavan_nimble_pilferer(n):
    return {
        "in_game_id": "n4#{0}".format(n+1),
        "name": "Ragavan, Nimble Pilferer", "mana_cost": "{R}",
        "type_line": "Legendary Creature - Monkey Pirate",
        "oracle_text": "Whenever Ragavan, Nimble Pilferer deals combat damage to a player, create a Treasure token and exile the top card of that player’s library. Until end of turn, you may cast that card.\nDash {1}{R} (You may cast this spell for its dash cost. If you do, it gains haste, and it’s returned from the battlefield to its owner’s hand at the beginning of the next end step.)",
        "power": "2", "toughness": "1",
    }
def subtlety(n):
    return {
        "in_game_id": "n5#{0}".format(n+1),
        "name": "Subtlety", "mana_cost": "{2}{U}{U}",
        "type_line": "Creature - Elemental Incarnation",
        "oracle_text": "Flash\nFlying\nWhen Subtlety enters the battlefield, choose up to one target creature spell or planeswalker spell. Its owner puts it on the top or bottom of their library.\nEvoke—Exile a blue card from your hand.",
        "power": "3", "toughness": "3",
    }
def murktide_regent(n):
    return {
        "in_game_id": "n6#{0}".format(n+1),
        "name": "Murktide Regent", "mana_cost": "{5}{U}{U}",
        "type_line": "Creature - Dragon",
        "oracle_text": "Delve (Each card you exile from your graveyard while casting this spell pays for {1}.)\nFlying\nMurktide Regent enters the battlefield with a +1/+1 counter on it for each instant and sorcery card exiled with it.\nWhenever an instant or sorcery card leaves your graveyard, put a +1/+1 counter on Murktide Regent.",
        "power": "3", "toughness": "3",
    }
def lightning_bolt(n):
    return {
        "in_game_id": "n7#{0}".format(n+1),
        "name": "Lightning Bolt", "mana_cost": "{R}",
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "power": None, "toughness": None,
    }


# steps
@given(u'the AI player receiving priority (instant speed) is GPT from OpenAI')
def step_impl(context):
    context.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=1024)
    #context.llm = ChatOpenAI(model_name='gpt-4', temperature=0, max_tokens=1024)
    context.chat_prompt = PIPP.chat_prompt
    context.tools = PIPP.tools
    assert context.tools
    context.tools_prompt = PIPP.tools_prompt
    context.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
    context.requests = PIPP.requests
    context.agent_executor = CSAgentExecutor(
            llm=context.llm,
            chat_prompt=context.chat_prompt,
            tools_prompt=context.tools_prompt,
            tools=context.tools,
            memory=context.memory,
            requests=context.requests,
            verbose=True,
    )


@given(u'the AI player receives a board state')
def step_impl(context):
    """ board analysis needs:
    {opponent_battlefield}
    {self_battlefield}
    {self_hand}
    {self_graveyard}
    {opponent_graveyard}
    {self_exile}
    {opponent_exile}
    {current_phase}
    {whose_turn}
    """
    context.opponent_battlefield = [
        *[ orcish_bowmasters(n) for n in range(1) ],
        *[ gilded_goose(n) for n in range(1) ],
        *[ zulaport_cutthroat(n) for n in range(1) ],
        *[ verdant_catacombs(n) for n in range(1) ],
        *[ blooming_marsh(n) for n in range(1) ],
    ]
    context.self_battlefield = [
        *[ dragons_rage_channeler(n) for n in range(1) ],
        *[ spirebluff_canal(n) for n in range(1) ],
        *[ polluted_delta(n) for n in range(1) ],
    ]
    context.self_hand = [
        *[ ragavan_nimble_pilferer(n) for n in range(1) ],
        *[ subtlety(n) for n in range(1) ],
        *[ murktide_regent(n) for n in range(1) ],
        *[ lightning_bolt(n) for n in range(1) ],
    ]
    context.self_graveyard = []
    context.opponent_graveyard = []
    context.self_exile = []
    context.opponent_exile = []
    context.current_phase = "upkeep step"
    context.whose_turn = "opponent"


@when(u'the system asks the AI player for instant speed decisions')
def step_impl(context):
    assert context.opponent_battlefield is not None
    assert context.self_battlefield is not None
    assert context.self_hand is not None
    assert context.self_graveyard is not None
    assert context.opponent_graveyard is not None
    assert context.self_exile is not None
    assert context.opponent_exile is not None
    assert context.current_phase is not None
    assert context.whose_turn is not None
    with payload.g_actions_lock:
        payload.g_actions = []
    board_analysis = PIPP.board_analysis.format( \
            opponent_battlefield=json.dumps(context.opponent_battlefield, indent=4), \
            self_battlefield=json.dumps(context.self_battlefield, indent=4), \
            self_hand=json.dumps(context.self_hand, indent=4), \
            self_graveyard=json.dumps(context.self_graveyard, indent=4), \
            opponent_graveyard=json.dumps(context.opponent_graveyard, indent=4), \
            self_exile=json.dumps(context.self_exile, indent=4), \
            opponent_exile=json.dumps(context.opponent_exile, indent=4), \
            current_phase=context.current_phase, \
            whose_turn=context.whose_turn, \
    )
    _input = PIPP._input
    context.response = context.agent_executor.invoke({
        'data': board_analysis,
        'input': _input,
    })
