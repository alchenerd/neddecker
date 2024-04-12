from behave import *
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
import json

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../../../')
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from llm.prompts.start_of_game import StartOfGamePromptPreset as SGPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor

from dotenv import load_dotenv
load_dotenv()

def leyline_of_the_void(n):
    return {
        "in_game_id": "n4#{0}".format(n+1),
        "name": "Leyline of the Void", "mana_cost": "{2}{B}{B}",
        "type_line": "Enchantment",
        "oracle_text": "If Leyline of the Void is in your opening hand, you may begin the game with it on the battlefield.\nIf a card would be put into an opponent’s graveyard from anywhere, exile it instead.",
        "power": None, "toughness": None,
    }

def veil_of_summer(n):
    return {
        "in_game_id": "n13#{0}".format(n+1),
        "name": "Veil of Summer", "mana_cost": "{G}",
        "type_line": "Instant",
        "oracle_text": "Draw a card if an opponent has cast a blue or black spell this turn. Spells you control can’t be countered this turn. You and permanents you control gain hexproof from blue and from black until end of turn. (You and they can’t be the targets of blue or black spells or abilities your opponents control.)",
        "power": None, "toughness": None,
    }

def cursed_totem(n):
    return {
        "in_game_id": "n14#{0}".format(n+1),
        "name": "Cursed Totem", "mana_cost": "{2}",
        "type_line": "Artifact",
        "oracle_text": "Activated abilities of creatures can’t be activated.",
        "power": None, "toughness": None,
    }

def evil_presence(n):
    return {
        "in_game_id": "n15#{0}".format(n+1),
        "name": "Evil Presence", "mana_cost": "{B}",
        "type_line": "Enchantment - Aura",
        "oracle_text": "Enchant land\nEnchanted land is a Swamp.",
        "power": None, "toughness": None,
    }

def fatal_push(n):
    return {
        "in_game_id": "n16#{0}".format(n+1),
        "name": "Fatal Push", "mana_cost": "{B}",
        "type_line": "Instant",
        "oracle_text": "Destroy target creature if it has mana value 2 or less.\nRevolt - Destroy that creature if it has mana value 4 or less instead if a permanent you controlled left the battlefield this turn.",
        "power": None, "toughness": None,
    }

def chancellor_of_the_dross(n):
    return {
        "in_game_id": "n17#{0}".format(n+1),
        "name": "Chancellor of the Dross", "mana_cost": "{4}{B}{B}{B}",
        "type_line": "Creature - Phyrexian Vampire",
        "oracle_text": "You may reveal this card from your opening hand. If you do, at the beginning of the first upkeep, each opponent loses 3 life, then you gain life equal to the life lost this way.\nFlying, lifelink",
        "power": "6", "toughness": "6",
    }

def sleeper_agent(n):
    return {
        "in_game_id": "n19#{0}".format(n+1),
        "name": "Sleeper Agent", "mana_cost": "{B}",
        "type_line": "Creature - Phyrexian Minion",
        "oracle_text": "When Sleeper Agent enters the battlefield, target opponent gains control of it.\nAt the beginning of your upkeep, Sleeper Agent deals 2 damage to you.",
        "power": "3", "toughness": "3",
    }

def marsh_flats(n):
    return {
        "in_game_id": "n20#{0}".format(n+1),
        "name": "Marsh Flats", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "{T}, Pay 1 life, Sacrifice Marsh Flats: Search your library for a Plains or Swamp card, put it onto the battlefield, then shuffle.",
        "power": None, "toughness": None,
    }

def swamp(n):
    return {
        "in_game_id": "n21#{0}".format(n+1),
        "name": "Swamp", "mana_cost": None,
        "type_line": "Basic Land - Swamp",
        "oracle_text": "({T}: Add {B}.)",
        "power": None, "toughness": None,
    }

def gemstone_caverns(n):
    return {
        "in_game_id": "n32#{0}".format(n+1),
        "name": "Gemstone Caverns", "mana_cost": None,
        "type_line": "Legendary Land",
        "oracle_text": "If Gemstone Caverns is in your opening hand and you’re not the starting player, you may begin the game with Gemstone Caverns on the battlefield with a luck counter on it. If you do, exile a card from your hand.\n{T}: Add {C}. If Gemstone Caverns has a luck counter on it, instead add one mana of any color.",
        "power": None, "toughness": None,
    }

def steam_vents(n):
    return {
        "in_game_id": "n35#{0}".format(n+1),
        "name": "Steam Vents", "mana_cost": None,
        "type_line": "Land - Island Mountain",
        "oracle_text": "({T}: Add {U} or {R}.)\nAs Steam Vents enters the battlefield, you may pay 2 life. If you don’t, it enters the battlefield tapped.",
        "power": None, "toughness": None,
    }

def damping_sphere(n):
    return {
        "in_game_id": "n1#{0}".format(n+1),
        "name": "Damping Sphere", "mana_cost": "{2}",
        "type_line": "Artifact",
        "oracle_text": "If a land is tapped for two or more mana, it produces {C} instead of any other type and amount.\nEach spell a player casts costs {1} more to cast for each other spell that player has cast this turn.",
        "power": None, "toughness": None,
    }

def flusterstorm(n):
    return {
        "in_game_id": "n2#{0}".format(n+1),
        "name": "Flusterstorm", "mana_cost": "{U}",
        "type_line": "Instant",
        "oracle_text": "Counter target instant or sorcery spell unless its controller pays {1}.\nStorm (When you cast this spell, copy it for each spell cast before it this turn. You may choose new targets for the copies.)",
        "power": None, "toughness": None,
    }

def jegantha_the_wellspring(n):
    return {
        "in_game_id": "n3#{0}".format(n+1),
        "name": "Jegantha, the Wellspring", "mana_cost": "{4}{R/G}",
        "type_line": "Legendary Creature - Elemental Elk",
        "oracle_text": "Companion — No card in your starting deck has more than one of the same mana symbol in its mana cost. (If this card is your chosen companion, you may put it into your hand from outside the game for {3} as a sorcery.)\n{T}: Add {W}{U}{B}{R}{G}. This mana can’t be spent to pay generic mana costs.",
        "power": "5", "toughness": "5",
    }

def pick_your_poison(n):
    return {
        "in_game_id": "n5#{0}".format(n+1),
        "name": "Pick Your Poison", "mana_cost": "{G}",
        "type_line": "Sorcery",
        "oracle_text": "Choose one -\n- Each opponent sacrifices an artifact.\n- Each opponent sacrifices an enchantment.\n- Each opponent sacrifices a creature with flying.",
        "power": None, "toughness": None,
    }

def pick_your_poison(n):
    return {
        "in_game_id": "n5#{0}".format(n+1),
        "name": "Pick Your Poison", "mana_cost": "{G}",
        "type_line": "Sorcery",
        "oracle_text": "Choose one -\n- Each opponent sacrifices an artifact.\n- Each opponent sacrifices an enchantment.\n- Each opponent sacrifices a creature with flying.",
        "power": None, "toughness": None,
    }

def wear_tear(n):
    return {
        "in_game_id": "n6#{0}".format(n+1),
        "name": "Wear // Tear", "mana_cost": "{1}{R} // {W}",
        "type_line": "Instant // Instant",
        "oracle_text": "Destroy target artifact.\nFuse (You may cast one or both halves of this card from your hand.) // Destroy target enchantment.\nFuse (You may cast one or both halves of this card from your hand.)",
        "power": None, "toughness": None,
    }

def leyline_of_the_guildpact(n):
    return {
        "in_game_id": "n7#{0}".format(n+1),
        "name": "Leyline of the Guildpact", "mana_cost": "{G/W}{G/U}{B/G}{R/G}",
        "type_line": "Enchantment",
        "oracle_text": "If Leyline of the Guildpact is in your opening hand, you may begin the game with it on the battlefield.\nEach nonland permanent you control is all colors.\nLands you control are every basic land type in addition to their other types.",
        "power": None, "toughness": None,
    }

def lightning_bolt(n):
    return {
        "in_game_id": "n8#{0}".format(n+1),
        "name": "Lightning Bolt", "mana_cost": "{R}",
        "type_line": "Instant",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "power": None, "toughness": None,
    }

def scion_of_draco(n):
    return {
        "in_game_id": "n9#{0}".format(n+1),
        "name": "Scion of Draco", "mana_cost": "{12}",
        "type_line": "Artifact Creature — Dragon",
        "oracle_text": "Domain — This spell costs {2} less to cast for each basic land type among lands you control.\nFlying\nEach creature you control has vigilance if it’s white, hexproof if it’s blue, lifelink if it’s black, first strike if it’s red, and trample if it’s green.",
        "power": "4", "toughness": "4",
    }

def tribal_flames(n):
    return {
        "in_game_id": "n10#{0}".format(n+1),
        "name": "Tribal Flames", "mana_cost": "{1}{R}",
        "type_line": "Sorcery",
        "oracle_text": "Domain — Tribal Flames deals X damage to any target, where X is the number of basic land types among lands you control.",
        "power": None, "toughness": None,
    }

def arid_mesa(n):
    return {
        "in_game_id": "n11#{0}".format(n+1),
        "name": "Arid Mesa", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "{T}, Pay 1 life, Sacrifice Arid Mesa: Search your library for a Mountain or Plains card, put it onto the battlefield, then shuffle.",
        "power": None, "toughness": None,
    }

def windswept_heath(n):
    return {
        "in_game_id": "n12#{0}".format(n+1),
        "name": "Windswept Heath", "mana_cost": None,
        "type_line": "Land",
        "oracle_text": "{T}, Pay 1 life, Sacrifice Arid Mesa: Search your library for a Forest or Plains card, put it onto the battlefield, then shuffle.",
        "power": None, "toughness": None,
    }

@given('the AI player for start of game is GPT from OpenAI')
def step_impl(context):
    context.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=1024)
    #context.llm = ChatOpenAI(model_name='gpt-4', temperature=0, max_tokens=1024)
    context.chat_prompt = SGPP.chat_prompt
    context.tools = SGPP.tools
    assert context.tools
    context.tools_prompt = SGPP.tools_prompt
    context.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
    context.requests = SGPP.requests
    context.agent_executor = CSAgentExecutor(
            llm=context.llm,
            chat_prompt=context.chat_prompt,
            tools_prompt=context.tools_prompt,
            tools=context.tools,
            memory=context.memory,
            requests=context.requests,
            verbose=True,
    )

@given('the AI player has one companion card in sideboard')
def step_impl(context):
    """ Sets the sideboard with one containing a companion. Also sets the hand as a keepable one.
    Sideboard (Domain Zoo): [ 4 Damping Sphere, 2 Flusterstorm, 1 Jegantha, the Wellspring, 4 Leyline of the Void, 3 Pick Your Poison, 1 Wear // Tear ]
    Hand (Domain Zoo): [ Leyline of the Guildpact, Lightning Bolt, Scion of Draco, Tribal Flames, Arid Mesa, Windswept Heath, Windswept Heath ]
    """
    context.sideboard = []
    context.sideboard.extend(damping_sphere(n) for n in range(4))
    context.sideboard.extend(flusterstorm(n) for n in range(2))
    context.sideboard.extend(jegantha_the_wellspring(n) for n in range(1))
    context.sideboard.extend(leyline_of_the_void(n) for n in range(4))
    context.sideboard.extend(pick_your_poison(n) for n in range(3))
    context.sideboard.extend(wear_tear(n) for n in range(1))
    #print(len(context.sideboard))


    context.hand = []
    context.hand.extend([ leyline_of_the_guildpact(n) for n in range(1) ])
    context.hand.extend([ lightning_bolt(n) for n in range(1) ])
    context.hand.extend([ scion_of_draco(n) for n in range(1) ])
    context.hand.extend([ tribal_flames(n) for n in range(1) ])
    context.hand.extend([ arid_mesa(n) for n in range(1) ])
    context.hand.extend([ windswept_heath(n) for n in range(2) ])

    #print(len(context.hand))

@when('the system asks the AI player for start of game decisions')
def step_impl(context):
    if not hasattr(context, 'hand') or not hasattr(context, 'sideboard'):
        return
    with payload.g_actions_lock:
        payload.g_actions = []
    companions = [ card for card in context.sideboard if 'Companion' in card['oracle_text']]
    to_reveal = [ card for card in context.hand if 'from your opening hand' in card['oracle_text']]
    to_battlefield = [ card for card in context.hand if 'begin the game' in card['oracle_text']]
    hand = [ { **card, 'where': 'hand'} for card in context.hand ]
    board_analysis = SGPP.board_analysis.format( \
            hand=json.dumps(hand, indent=4), \
            companions=json.dumps(companions, indent=4), \
            to_reveal=json.dumps(to_reveal, indent=4), \
            to_battlefield=json.dumps(to_battlefield, indent=4) \
    )
    _input = SGPP._input
    context.response = context.agent_executor.invoke({
        'data': board_analysis,
        'input': _input,
    })

@then('the AI Player marks the card as companion')
def step_impl(context):
    try:
        assert any((a.get('annotationKey', '') == 'isCompanion' and a.get('targetId', '').startswith('n3')) for a in payload.g_actions)
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@given('the AI player has one Chancellor of the Dross in hand')
def step_impl(context):
    """ Sets the hand with one Chancellor of Dross.
    Sideboard (Black Burn): [ 3 Veil of Summer, 3 Cursed Totem, 3 Evil Presence, 3 Leyline of the Void, 3 Fatal Push ]
    Hand (Black Burn): [ Chancellor of the dross, Okiba Reckoner Raid, Sleeper Agent, Sleeper Agent, Marsh Flats, Marsh Flats, Swamp ]
    """
    context.sideboard = []
    context.sideboard.extend([ veil_of_summer(n) for n in range(3) ])
    context.sideboard.extend([ cursed_totem(n) for n in range(3) ])
    context.sideboard.extend([ evil_presence(n) for n in range(3) ])
    context.sideboard.extend([ leyline_of_the_void(n) for n in range(3) ])
    context.sideboard.extend([ fatal_push(n) for n in range(3) ])
    assert len(context.sideboard) == 15

    # Hand (Black Burn): [ Chancellor of the dross, Okiba Reckoner Raid, Sleeper Agent, Sleeper Agent, Marsh Flats, Marsh Flats, Swamp ]

    def okiba_reckoner_raid(n):
        return {
            "in_game_id": "n18#{0}".format(n+1),
            "name": "Okiba Reckoner Raid // Nezumi Road Captain", "mana_cost": "{B}",
            "type_line": "Enchantment - Saga // Enchantment Creature - Rat Rogue",
            "oracle_text": "(As this Saga enters and after your draw step, add a lore counter.)\nI, II - Each opponent loses 1 life and you gain 1 life.\nIII - Exile this Saga, then return it to the battlefield transformed under your control. // Menace\nVehicles you control have menace. (They can’t be blocked except by two or more creatures.)",
            "power": "None // 2", "toughness": "None // 2",
        }

    context.hand = []
    context.hand.extend([ chancellor_of_the_dross(n) for n in range(1) ])
    context.hand.extend([ okiba_reckoner_raid(n) for n in range(1) ])
    context.hand.extend([ sleeper_agent(n) for n in range(2) ])
    context.hand.extend([ marsh_flats(n) for n in range(2) ])
    context.hand.extend([ swamp(n) for n in range(1) ])
    assert len(context.hand) == 7

@then('the AI player registers a delayed trigger for Chancellor of the Dross')
def step_impl(context):
    try:
        assert len(payload.g_actions) == 1
        assert payload.g_actions[0].get('type', '') == 'create_delayed_trigger'
        assert payload.g_actions[0].get('targetCardName', '') == 'Chancellor of the Dross'
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@given(u'the AI player has three Chancellor of the Dross in hand')
def step_impl(context):
    """ Sets the hand with three Chancellor of Dross.
    Sideboard (Black Burn): [ 3 Veil of Summer, 3 Cursed Totem, 3 Evil Presence, 3 Leyline of the Void, 3 Fatal Push ]
    Hand (Black Burn): [ Chancellor of the dross, Chancellor of the dross, Chancellor of the dross, Sleeper Agent, Marsh Flats, Marsh Flats, Swamp ]
    """
    context.sideboard = []
    context.sideboard.extend([ veil_of_summer(n) for n in range(3) ])
    context.sideboard.extend([ cursed_totem(n) for n in range(3) ])
    context.sideboard.extend([ evil_presence(n) for n in range(3) ])
    context.sideboard.extend([ leyline_of_the_void(n) for n in range(3) ])
    context.sideboard.extend([ fatal_push(n) for n in range(3) ])
    assert len(context.sideboard) == 15

    context.hand = []
    context.hand.extend([ chancellor_of_the_dross(n) for n in range(3) ])
    context.hand.extend([ sleeper_agent(n) for n in range(1) ])
    context.hand.extend([ marsh_flats(n) for n in range(2) ])
    context.hand.extend([ swamp(n) for n in range(1) ])
    assert len(context.hand) == 7

@then(u'the AI player registers three different delayed trigger for each of the Chancellor of the Dross')
def step_impl(context):
    try:
        assert len(payload.g_actions) == 3
        for i in range(3):
            assert payload.g_actions[i].get('type', '') == 'create_delayed_trigger'
            assert payload.g_actions[i].get('targetCardName', '') == 'Chancellor of the Dross'
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@given(u'the AI player has one Gemstone Caverns in hand')
def step_impl(context):
    """ Sets the hand with one Gemstone Caverns.
    Sideboard (Temur Rhinos): [ 2 Blood Moon, 1 Boseiju, Who Endures, 3 Endurance, 3 Force of Vigor, 1 Magus of the Moon, 4 Mystical Dispute, 1 Tishana's Tidebinder ]
    Hand (Temur Rhinos): [ Shardless Agent, Dead // Gone, Fire // Ice, Gemstone Caverns, Ketria Triome, Misty Rainforest, Steam Vents ]
    """
    def blood_moon(n):
        return {
            "in_game_id": "n22#{0}".format(n+1),
            "name": "Blood Moon", "mana_cost": "{2}{R}",
            "type_line": "Enchantment",
            "oracle_text": "Nonbasic lands are Mountains.",
            "power": None, "toughness": None,
        }
    def boseiju_who_endures(n):
        return {
            "in_game_id": "n23#{0}".format(n+1),
            "name": "Boseiju Who Endures", "mana_cost": None,
            "type_line": "Legendary Land",
            "oracle_text": "{T}: Add {G}.\nChannel - {1}{G}, Discard Boseiju, Who Endures: Destroy target artifact, enchantment, or nonbasic land an opponent controls. That player may search their library for a land card with a basic land type, put it onto the battlefield, then shuffle. This ability costs {1} less to activate for each legendary creature you control.",
            "power": None, "toughness": None,
        }
    def endurance(n):
        return {
            "in_game_id": "n24#{0}".format(n+1),
            "name": "Endurance", "mana_cost": "{1}{G}{G}",
            "type_line": "Creature - Elemental Incarnation",
            "oracle_text": "Flash\nReach\nWhen Endurance enters the battlefield, up to one target player puts all the cards from their graveyard on the bottom of their library in a random order.\nEvoke-Exile a green card from your hand.",
            "power": "3", "toughness": "4",
        }
    def force_of_vigor(n):
        return {
            "in_game_id": "n25#{0}".format(n+1),
            "name": "Force of Vigor", "mana_cost": "{2}{G}{G}",
            "type_line": "Instant",
            "oracle_text": "If it’s not your turn, you may exile a green card from your hand rather than pay this spell’s mana cost.\nDestroy up to two target artifacts and/or enchantments.",
            "power": None, "toughness": None,
        }
    def magus_of_the_moon(n):
        return {
            "in_game_id": "n26#{0}".format(n+1),
            "name": "Magus of the Moon", "mana_cost": "{2}{R}",
            "type_line": "Creature - Human Wizard",
            "oracle_text": "Nonbasic lands are Mountains.",
            "power": "2", "toughness": "2",
        }
    def mystical_dispute(n):
        return {
            "in_game_id": "n27#{0}".format(n+1),
            "name": "Mystical Dispute", "mana_cost": "{2}{U}",
            "type_line": "Instant",
            "oracle_text": "This spell costs {2} less to cast if it targets a blue spell.\nCounter target spell unless its controller pays {3}.",
            "power": None, "toughness": None,
        }
    def tishanas_tidebinder(n):
        return {
            "in_game_id": "n28#{0}".format(n+1),
            "name": "Tishana's Tidebinder", "mana_cost": "{2}{U}",
            "type_line": "Creature - Merfolk Wizard",
            "oracle_text": "Flash\nWhen Tishana’s Tidebinder enters the battlefield, counter up to one target activated or triggered ability. If an ability of an artifact, creature, or planeswalker is countered this way, that permanent loses all abilities for as long as Tishana’s Tidebinder remains on the battlefield. (Mana abilities can’t be targeted.)",
            "power": "3", "toughness": "2",
        }

    context.sideboard = []
    context.sideboard.extend([ blood_moon(n) for n in range(2) ])
    context.sideboard.extend([ boseiju_who_endures(n) for n in range(1) ])
    context.sideboard.extend([ endurance(n) for n in range(3) ])
    context.sideboard.extend([ force_of_vigor(n) for n in range(3) ])
    context.sideboard.extend([ magus_of_the_moon(n) for n in range(1) ])
    context.sideboard.extend([ mystical_dispute(n) for n in range(4) ])
    context.sideboard.extend([ tishanas_tidebinder(n) for n in range(1) ])
    assert len(context.sideboard) == 15

    def shardless_agent(n):
        return {
            "in_game_id": "n29#{0}".format(n+1),
            "name": "Shardless Agent", "mana_cost": "{1}{G}{U}",
            "type_line": "Artifact Creature - Human Rogue",
            "oracle_text": "Cascade (When you cast this spell, exile cards from the top of your library until you exile a nonland card that costs less. You may cast it without paying its mana cost. Put the exiled cards on the bottom of your library in a random order.)",
            "power": "2", "toughness": "2",
        }
    def dead_gone(n):
        return {
            "in_game_id": "n30#{0}".format(n+1),
            "name": "Dead // Gone", "mana_cost": "{R} // {2}{R}",
            "type_line": "Instant // Instant",
            "oracle_text": "Dead deals 2 damage to target creature. // Return target creature you don’t control to its owner’s hand.",
            "power": None, "toughness": None,
        }
    def fire_ice(n):
        return {
            "in_game_id": "n31#{0}".format(n+1),
            "name": "Fire // Ice", "mana_cost": "{1}{R} // {1}{U}",
            "type_line": "Instant // Instant",
            "oracle_text": "Fire deals 2 damage divided as you choose among one or two targets. // Tap target permanent.\nDraw a card.",
            "power": None, "toughness": None,
        }
    context.hand = []
    def ketria_triome(n):
        return {
            "in_game_id": "n33#{0}".format(n+1),
            "name": "Ketria Triome", "mana_cost": None,
            "type_line": "Land - Forest Island Mountain",
            "oracle_text": "({T}: Add {G}, {U}, or {R}.)\nKetria Triome enters the battlefield tapped.\nCycling {3} ({3}, Discard this card: Draw a card.)",
            "power": None, "toughness": None,
        }
    def misty_rainforest(n):
        return {
            "in_game_id": "n34#{0}".format(n+1),
            "name": "Misty Rainforest", "mana_cost": None,
            "type_line": "Land",
            "oracle_text": "{T}, Pay 1 life, Sacrifice Misty Rainforest: Search your library for a Forest or Island card, put it onto the battlefield, then shuffle.",
            "power": None, "toughness": None,
        }
    context.hand.extend([ shardless_agent(n) for n in range(1) ])
    context.hand.extend([ dead_gone(n) for n in range(1) ])
    context.hand.extend([ fire_ice(n) for n in range(1) ])
    context.hand.extend([ gemstone_caverns(n) for n in range(1) ])
    context.hand.extend([ ketria_triome(n) for n in range(1) ])
    context.hand.extend([ misty_rainforest(n) for n in range(1) ])
    context.hand.extend([ steam_vents(n) for n in range(1) ])
    assert len(context.hand) == 7

@then(u'the AI player puts one Gemstone Caverns on the battlefield')
def step_impl(context):
    try:
        assert not any(a['type'] == 'set_annotation' for a in payload.g_actions)
        assert any((a['type'] == 'move' and a['targetId'].startswith('n32') )for a in payload.g_actions)
        assert any((a['type'] == 'set_counter' and a['targetId'].startswith('n32') and 'luck' in a['counterType'].lower() and a['counterAmount'] == 1 )for a in payload.g_actions)
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@then(u'the AI player exiles a card from hand')
def step_impl(context):
    try:
        assert any((a['type'] == 'move' and 'hand' in a['from'] and 'exile' in a['to'])for a in payload.g_actions)
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@given(u'the AI player has three Gemstone Caverns in hand')
def step_impl(context):
    """ Sets the hand with three Gemstone Caverns.
    Sideboard (Lightning Hunt): [ 4 Bojuka Bog, 4 Detection Tower, 2 Seismic Assult, 4 Countryside Crusher, 1 Laboratory Maniac ]
    Hand (Lightning Hunt): [3 Gemstone Caverns, 1 Treasure Hunt, 1 Reliquary Tower, 1 Steam Vents, 1 Lightning Storm ]
    """

    def bojuka_bog(n):
        return {
            "in_game_id": "n36#{0}".format(n+1),
            "name": "Bojuka Bog", "mana_cost": None,
            "type_line": "Land",
            "oracle_text": "Bojuka Bog enters the battlefield tapped.\nWhen Bojuka Bog enters the battlefield, exile target player’s graveyard.\n{T}: Add {B}.",
            "power": None, "toughness": None,
        }
    def detection_tower(n):
        return {
            "in_game_id": "n37#{0}".format(n+1),
            "name": "Detection Tower", "mana_cost": None,
            "type_line": "Land",
            "oracle_text": "{T}: Add {C}.\n{1}, {T}: Until end of turn, your opponents and creatures your opponents control with hexproof can be the targets of spells and abilities you control as though they didn’t have hexproof.",
            "power": None, "toughness": None,
        }
    def seismic_assault(n):
        return {
            "in_game_id": "n38#{0}".format(n+1),
            "name": "Seismic Assault", "mana_cost": "{R}{R}{R}",
            "type_line": "Enchantment",
            "oracle_text": "Discard a land card: Seismic Assault deals 2 damage to any target.",
            "power": None, "toughness": None,
        }
    def countryside_crusher(n):
        return {
            "in_game_id": "n39#{0}".format(n+1),
            "name": "Countryside Crusher", "mana_cost": "{1}{R}{R}",
            "type_line": "Creature - Giant Warrior",
            "oracle_text": "At the beginning of your upkeep, reveal the top card of your library. If it’s a land card, put it into your graveyard and repeat this process.\nWhenever a land card is put into your graveyard from anywhere, put a +1/+1 counter on Countryside Crusher.",
            "power": "3", "toughness": "3",
        }
    def laboratory_maniac(n):
        return {
            "in_game_id": "n40#{0}".format(n+1),
            "name": "Laboratory Maniac", "mana_cost": "{2}{U}",
            "type_line": "Creature - Human Wizard",
            "oracle_text": "If you would draw a card while your library has no cards in it, you win the game instead.",
            "power": "2", "toughness": "2",
        }

    context.sideboard = []
    context.sideboard.extend([ bojuka_bog(n) for n in range(4) ])
    context.sideboard.extend([ detection_tower(n) for n in range(4) ])
    context.sideboard.extend([ seismic_assault(n) for n in range(2) ])
    context.sideboard.extend([ countryside_crusher(n) for n in range(4) ])
    context.sideboard.extend([ laboratory_maniac(n) for n in range(1) ])
    assert len(context.sideboard) == 15

    def treasure_hunt(n):
        return {
            "in_game_id": "n41#{0}".format(n+1),
            "name": "Treasure Hunt", "mana_cost": "{1}{U}",
            "type_line": "Sorcery",
            "oracle_text": "Reveal cards from the top of your library until you reveal a nonland card, then put all cards revealed this way into your hand.",
            "power": None, "toughness": None,
        }
    def reliquary_tower(n):
        return {
            "in_game_id": "n42#{0}".format(n+1),
            "name": "Reliquary Tower", "mana_cost": None,
            "type_line": "Land",
            "oracle_text": "You have no maximum hand size.\n{T}: Add {C}.",
            "power": None, "toughness": None,
        }
    def lightning_storm(n):
        return {
            "in_game_id": "n43#{0}".format(n+1),
            "name": "Lightning Storm", "mana_cost": "{1}{R}{R}",
            "type_line": "Instant",
            "oracle_text": "Lightning Storm deals X damage to any target, where X is 3 plus the number of charge counters on Lightning Storm.\nDiscard a land card: Put two charge counters on Lightning Storm. You may choose a new target for it. Any player may activate this ability but only if Lightning Storm is on the stack.",
            "power": None, "toughness": None,
        }

    context.hand = []
    context.hand.extend([ gemstone_caverns(n) for n in range(3) ])
    context.hand.extend([ treasure_hunt(n) for n in range(1) ])
    context.hand.extend([ reliquary_tower(n) for n in range(1) ])
    context.hand.extend([ steam_vents(n) for n in range(1) ])
    context.hand.extend([ lightning_storm(n) for n in range(1) ])
    assert len(context.hand) == 7

@given(u'the AI player has one Leyline of the Guildpact in hand')
def step_impl(context):
    """ Sets the sideboard with one containing a companion. Also sets the hand as a keepable one.
    Sideboard (Domain Zoo): [ 4 Damping Sphere, 2 Flusterstorm, 1 Jegantha, the Wellspring, 4 Leyline of the Void, 3 Pick Your Poison, 1 Wear // Tear ]
    Hand (Domain Zoo): [ Leyline of the Guildpact, Lightning Bolt, Scion of Draco, Tribal Flames, Arid Mesa, Windswept Heath, Windswept Heath ]
    """
    context.sideboard = []
    context.sideboard.extend(damping_sphere(n) for n in range(4))
    context.sideboard.extend(flusterstorm(n) for n in range(2))
    context.sideboard.extend(jegantha_the_wellspring(n) for n in range(1))
    context.sideboard.extend(leyline_of_the_void(n) for n in range(4))
    context.sideboard.extend(pick_your_poison(n) for n in range(3))
    context.sideboard.extend(wear_tear(n) for n in range(1))
    assert len(context.sideboard) == 15

    context.hand = []
    context.hand.extend([ leyline_of_the_guildpact(n) for n in range(1) ])
    context.hand.extend([ lightning_bolt(n) for n in range(1) ])
    context.hand.extend([ scion_of_draco(n) for n in range(1) ])
    context.hand.extend([ tribal_flames(n) for n in range(1) ])
    context.hand.extend([ arid_mesa(n) for n in range(1) ])
    context.hand.extend([ windswept_heath(n) for n in range(2) ])
    assert len(context.hand) == 7

@given(u'the AI player has three Leyline of the Guildpact in hand')
def step_impl(context):
    """ Sets the sideboard with one containing a companion. Also sets the hand as a keepable one.
    Sideboard (Domain Zoo): [ 4 Damping Sphere, 2 Flusterstorm, 1 Jegantha, the Wellspring, 4 Leyline of the Void, 3 Pick Your Poison, 1 Wear // Tear ]
    Hand (Domain Zoo): [ 3 Leyline of the Guildpact, Lightning Bolt, Scion of Draco, Windswept Heath, Windswept Heath ]
    """
    context.sideboard = []
    context.sideboard.extend(damping_sphere(n) for n in range(4))
    context.sideboard.extend(flusterstorm(n) for n in range(2))
    context.sideboard.extend(jegantha_the_wellspring(n) for n in range(1))
    context.sideboard.extend(leyline_of_the_void(n) for n in range(4))
    context.sideboard.extend(pick_your_poison(n) for n in range(3))
    context.sideboard.extend(wear_tear(n) for n in range(1))
    assert len(context.sideboard) == 15

    context.hand = []
    context.hand.extend([ leyline_of_the_guildpact(n) for n in range(3) ])
    context.hand.extend([ lightning_bolt(n) for n in range(1) ])
    context.hand.extend([ scion_of_draco(n) for n in range(1) ])
    context.hand.extend([ windswept_heath(n) for n in range(2) ])
    assert len(context.hand) == 7

@then(u'the AI player puts one or more Leyline of the Guildpact on the battlefield')
def step_impl(context):
    try:
        assert any(a.get('type', '') == 'move' and a.get('targetId', '').startswith('n7') for a in payload.g_actions)
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e

@given(u'the AI has nothing to do at the start of the game')
def step_impl(context):
    """ Sets the sideboard and hand with nothing to do at the start of the game.
    Sideboard (8 cast): [ 4 Metallic Rebuke, 2 Spell Pierce, 2 Dismember, 2 Damping Sphere, 1 Pithing Needle, 2 Seal of Cleansing, 1 Relic of Progenitus, 1 Welding Jar ]
    Hand (8 cast): [ 1 Darksteel Citadel, 1 Urza's Saga, 1 Springleaf Drum, 1 Ornithopter, 1 Cranial Plating, 1 Haywire Mite, 1 Nettlecyst ]
    """
    def metallic_rebuke(n):
        return {
            "in_game_id": "n44#{0}".format(n+1),
            "name": "Metallic Rebuke", "mana_cost": "{2}{U}",
            "type_line": "Instant",
            "oracle_text": "Improvise (Your artifacts can help cast this spell. Each artifact you tap after you’re done activating mana abilities pays for {1}.)\nCounter target spell unless its controller pays {3}.",
            "power": None, "toughness": None,
        }
    def spell_pierce(n):
        return {
            "in_game_id": "n45#{0}".format(n+1),
            "name": "Spell Pierce", "mana_cost": "{U}",
            "type_line": "Instant",
            "oracle_text": "Counter target noncreature spell unless its controller pays {2}.",
            "power": None, "toughness": None,
        }
    def dismember(n):
        return {
            "in_game_id": "n46#{0}".format(n+1),
            "name": "Dismember", "mana_cost": "{1}{B/P}{B/P}",
            "type_line": "Instant",
            "oracle_text": "({B/P} can be paid with either {B} or 2 life.)\nTarget creature gets -5/-5 until end of turn.",
            "power": None, "toughness": None,
        }
    def damping_sphere(n):
        return {
            "in_game_id": "n47#{0}".format(n+1),
            "name": "Damping Sphere", "mana_cost": "{2}",
            "type_line": "Artifact",
            "oracle_text": "If a land is tapped for two or more mana, it produces {C} instead of any other type and amount.\nEach spell a player casts costs {1} more to cast for each other spell that player has cast this turn.",
            "power": None, "toughness": None,
        }
    def pithing_needle(n):
        return {
            "in_game_id": "n48#{0}".format(n+1),
            "name": "Pithing Needle", "mana_cost": "{1}",
            "type_line": "Artifact",
            "oracle_text": "As Pithing Needle enters the battlefield, choose a card name.\nActivated abilities of sources with the chosen name can’t be activated unless they’re mana abilities.",
            "power": None, "toughness": None,
        }
    def seal_of_cleansing(n):
        return {
            "in_game_id": "n49#{0}".format(n+1),
            "name": "Seal of Cleansing", "mana_cost": "{1}{W}",
            "type_line": "Enchantment",
            "oracle_text": "Sacrifice Seal of Cleansing: Destroy target artifact or enchantment.",
            "power": None, "toughness": None,
        }
    def relic_of_progenitus(n):
        return {
            "in_game_id": "n50#{0}".format(n+1),
            "name": "Relic of Progenitus", "mana_cost": "{1}",
            "type_line": "Artifact",
            "oracle_text": "{T}: Target player exiles a card from their graveyard.\n{1}, Exile Relic of Progenitus: Exile all graveyards. Draw a card.",
            "power": None, "toughness": None,
        }
    def welding_jar(n):
        return {
            "in_game_id": "n51#{0}".format(n+1),
            "name": "Welding Jar", "mana_cost": "{0}",
            "type_line": "Artifact",
            "oracle_text": "Sacrifice Welding Jar: Regenerate target artifact.",
            "power": None, "toughness": None,
        }
    context.sideboard = []
    context.sideboard.extend([ metallic_rebuke(n) for n in range(4) ])
    context.sideboard.extend([ spell_pierce(n) for n in range(2) ])
    context.sideboard.extend([ dismember(n) for n in range(2) ])
    context.sideboard.extend([ damping_sphere(n) for n in range(2) ])
    context.sideboard.extend([ pithing_needle(n) for n in range(1) ])
    context.sideboard.extend([ seal_of_cleansing(n) for n in range(2) ])
    context.sideboard.extend([ relic_of_progenitus(n) for n in range(1) ])
    context.sideboard.extend([ welding_jar(n) for n in range(1) ])
    assert len(context.sideboard) == 15

    def darksteel_citadel(n):
        return {
            "in_game_id": "n52#{0}".format(n+1),
            "name": "Darksteel Citadel", "mana_cost": None,
            "type_line": "Artifact Land",
            "oracle_text": "Indestructible\n{T}: Add {C}.",
            "power": None, "toughness": None,
        }
    def urzas_saga(n):
        return {
            "in_game_id": "n53#{0}".format(n+1),
            "name": "Urza's Saga", "mana_cost": None,
            "type_line": "Enchantment Land - Urza's Saga",
            "oracle_text": "(As this Saga enters and after your draw step, add a lore counter. Sacrifice after III.)\nI - Urza’s Saga gains “{T}: Add {C}.”\nII - Urza’s Saga gains “{2}, {T}: Create a 0/0 colorless Construct artifact creature token with ‘This creature gets +1/+1 for each artifact you control.’”\nIII - Search your library for an artifact card with mana cost {0} or {1}, put it onto the battlefield, then shuffle.",
            "power": None, "toughness": None,
        }
    def springleaf_drum(n):
        return {
            "in_game_id": "n54#{0}".format(n+1),
            "name": "Springleaf Drum", "mana_cost": "{1}",
            "type_line": "Artifact",
            "oracle_text": "{T}, Tap an untapped creature you control: Add one mana of any color.",
            "power": None, "toughness": None,
        }
    def ornithopter(n):
        return {
            "in_game_id": "n55#{0}".format(n+1),
            "name": "Ornithopter", "mana_cost": "{0}",
            "type_line": "Artifact Creature - Thopter",
            "oracle_text": "Flying",
            "power": "0", "toughness": "2",
        }
    def cranial_plating(n):
        return {
            "in_game_id": "n56#{0}".format(n+1),
            "name": "Cranial Plating", "mana_cost": "{2}",
            "type_line": "Artifact - Equipment",
            "oracle_text": "Equipped creature gets +1/+0 for each artifact you control.\n{B}{B}: Attach Cranial Plating to target creature you control.\nEquip {1}",
            "power": None, "toughness": None,
        }
    def haywire_mite(n):
        return {
            "in_game_id": "n57#{0}".format(n+1),
            "name": "Haywire Mite", "mana_cost": "{1}",
            "type_line": "Artifact Creature - Insect",
            "oracle_text": "When Haywire Mite dies, you gain 2 life.\n{G}, Sacrifice Haywire Mite: Exile target noncreature artifact or noncreature enchantment.",
            "power": "1", "toughness": "1",
        }
    def nettlecyst(n):
        return {
            "in_game_id": "n58#{0}".format(n+1),
            "name": "Nettlecyst", "mana_cost": "{3}",
            "type_line": "Artifact - Equipment",
            "oracle_text": "Living weapon (When this Equipment enters the battlefield, create a 0/0 black Phyrexian Germ creature token, then attach this to it.)\nEquipped creature gets +1/+1 for each artifact and/or enchantment you control.\nEquip {2}",
            "power": None, "toughness": None,
        }
    context.hand = []
    context.hand.extend([ darksteel_citadel(n) for n in range(1) ])
    context.hand.extend([ urzas_saga(n) for n in range(1) ])
    context.hand.extend([ springleaf_drum(n) for n in range(1) ])
    context.hand.extend([ ornithopter(n) for n in range(1) ])
    context.hand.extend([ cranial_plating(n) for n in range(1) ])
    context.hand.extend([ haywire_mite(n) for n in range(1) ])
    context.hand.extend([ nettlecyst(n) for n in range(1) ])
    assert len(context.hand) == 7

@then(u'the AI player does nothing')
def step_impl(context):
    try:
        assert isinstance(payload.g_actions, list) and len(payload.g_actions) == 0
    except AssertionError as e:
        improvement = context.agent_executor.chatter.invoke({
            'data': '',
            'input': "Ned Decker has made one or more illegal action(s). What wrong actions did Ned Decker make? What was asked to guide Ned Decker to make mistake(s)?",
        })
        raise Exception('[improvement]: ' + improvement) from e
