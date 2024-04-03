from behave import *
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory

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

@given('AI has one companion card in sideboard')
def step_impl(context):
    """ Sets the sideboard with one containing a companion. Also sets the hand as a keepable one.
    Sideboard (Domain Zoo): [ 4 Damping Sphere, 2 Flusterstorm, 1 Jegantha, the Wellspring, 4 Leyline of the Void, 3 Pick Your Poison, 1 Wear // Tear ]
    Hand (Domain Zoo): [ Leyline of the Guildpact, Lightning Bolt, Scion of Draco, Tribal Flames, Arid Mesa, Windswept Heath, Windswept Heath ]
    """
    context.sideboard = []
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

    context.sideboard.extend(damping_sphere(n) for n in range(4))
    context.sideboard.extend(flusterstorm(n) for n in range(2))
    context.sideboard.extend(jegantha_the_wellspring(n) for n in range(1))
    context.sideboard.extend(leyline_of_the_void(n) for n in range(4))
    context.sideboard.extend(pick_your_poison(n) for n in range(3))
    context.sideboard.extend(wear_tear(n) for n in range(1))
    #print(len(context.sideboard))

    # Hand (Domain Zoo): [Leyline of the Guildpact, Lightning Bolt, Scion of Draco, Tribal Flames, Arid Mesa, Windswept Heath, Windswept Heath ]
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

    context.hand = []
    context.hand.append(leyline_of_the_guildpact(1))
    context.hand.append(lightning_bolt(1))
    context.hand.append(scion_of_draco(1))
    context.hand.append(tribal_flames(1))
    context.hand.append(arid_mesa(1))
    context.hand.extend([windswept_heath(n) for n in range(2)])

    #print(len(context.hand))

@when('the system asks the AI player for start of game decisions')
def step_impl(context):
    if not hasattr(context, 'hand') or not hasattr(context, 'sideboard'):
        return
    with payload.g_actions_lock:
        payload.g_actions = []
    board_analysis = SGPP.board_analysis.format(hand=context.hand, sideboard=context.sideboard)
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
            "oracle_text": "Fire deals 2 damage divided as you choose among one or two targets. // Tap target permanent.\nDraw a card." ,
            "power": None, "toughness": None,
        }
    context.hand = []
    def gemstone_caverns(n):
        return {
            "in_game_id": "n32#{0}".format(n+1),
            "name": "Gemstone Caverns", "mana_cost": None,
            "type_line": "Legendary Land",
            "oracle_text": "If Gemstone Caverns is in your opening hand and you’re not the starting player, you may begin the game with Gemstone Caverns on the battlefield with a luck counter on it. If you do, exile a card from your hand.\n{T}: Add {C}. If Gemstone Caverns has a luck counter on it, instead add one mana of any color." ,
            "power": None, "toughness": None,
        }
    def ketria_triome(n):
        return {
            "in_game_id": "n33#{0}".format(n+1),
            "name": "Ketria Triome", "mana_cost": None,
            "type_line": "Land - Forest Island Mountain",
            "oracle_text": "({T}: Add {G}, {U}, or {R}.)\nKetria Triome enters the battlefield tapped.\nCycling {3} ({3}, Discard this card: Draw a card.)" ,
            "power": None, "toughness": None,
        }
    def misty_rainforest(n):
        return {
            "in_game_id": "n34#{0}".format(n+1),
            "name": "Misty Rainforest", "mana_cost": None,
            "type_line": "Land",
            "oracle_text": "{T}, Pay 1 life, Sacrifice Misty Rainforest: Search your library for a Forest or Island card, put it onto the battlefield, then shuffle." ,
            "power": None, "toughness": None,
        }
    def steam_vents(n):
        return {
            "in_game_id": "n35#{0}".format(n+1),
            "name": "Steam  Vents", "mana_cost": None,
            "type_line": "Land - Island Mountain",
            "oracle_text": "({T}: Add {U} or {R}.)\nAs Steam Vents enters the battlefield, you may pay 2 life. If you don’t, it enters the battlefield tapped." ,
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
    pass

@given(u'the AI player has one Leyline of the Guildpact in hand')
def step_impl(context):
    pass

@given(u'the AI player has three Leyline of the Guildpact in hand')
def step_impl(context):
    pass

@then(u'the AI player puts one or more Leyline of the Guildpact on the battlefield')
def step_impl(context):
    pass
