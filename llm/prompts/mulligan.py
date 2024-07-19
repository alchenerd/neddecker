from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../')
rootdir = os.path.dirname(currentdir + '/../../')
sys.path.insert(0, rootdir)
from llm.tools.mulligan import submit_mulligan_decision
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import PONDER_GUIDE, TOOLS_GUIDE

class MulliganPromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(PONDER_GUIDE),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently in the mulligan step.'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    tools = [ submit_mulligan_decision() ]

    tools_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(TOOLS_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    requests = [
        "1. How many mana sources are there in Ned Decker's hand? (only integer)\n"
        "1a. Classify Ned Decker's hand as one of the following: "
        "["
            "\"mana screw\" (too few mana sources, e.g. one land or less), "
            "\"balanced\", "
            "\"mana flood\" (too many mana sources, e.g. five lands or more) "
        "] "
        "1b. State the colors that Ned Decker's lands in hand can produce (use {W}{U}{B}{R}{G}, no duplicates).\n"
        "1c. State the colors that Ned Decker's spells in hand require (use {W}{U}{B}{R}{G}, no duplicates).\n"
        "(If lands cannot provide enough mana or enough color, consider taking a mulligan.)\n"
        "(If there are too many lands and not enough spells, consider taking a mulligan.)\n"
        "\n"
        "2. Are there 2 spells or more that costs more than 3 CMC (Yes/No)?\n"
        "2a. If yes, at what turn can Ned Decker use those spells (only integer)?\n"
        "\n"
        "3. How many cards would be put to the bottom of Ned Decker's library (only integer)?\n"
        "3a. How many cards would be in Ned Decker's hand after bottoming (only integer)?\n"
        "3b. What unwanted, worst card(s) would Ned Decker send to the bottom of the library (give name and ID)?\n"
        "3c. Compile a hand after sending those cards to the bottom of the library (reply with an n-item list, each item contains name and ID).\n"
        "3d. After bottoming the unwanted cards, is the rest of the hand good enough for keeping?\n"
        "(If there are too many unplayable cards and can't bottom them, consider taking a mulligan.)\n"
        "\n"
        "(IMPORTANT: From now on, analysis should be exclusively based on the compiled hand created in 3c.)\n"
        "4. Please analyze the possible plays for turn 1, turn 2, and turn 3 that the compiled hand allows. \n"
        "(reply with a 3-item list, each item stating (a) what land to play for turn, (b) what cards to play for turn, and (c) what the hand looks like at the end of turn; the same card will appear in the plays at mose once.)\n"
        "\n"
        "5a. Has Ned Decker missed any land drop for the turn and lost tempo in the first three turns? (Yes/No, and explain why)\n"
        "5b. Has Ned Decker passed a turn without casting a spell and lost tempo in the first three turns? (Yes/No, and explain why)\n"
        "5c. Did Ned Decker make board pressure or meaningfully interact in the first three turns?\n"
        "(If the early game feels slow and without tempo, strongly consider taking a mulligan.)\n"
        "5d. A Burn deck could deal 21 damage to Ned Decker within four turns; "
        "could Ned Decker race the opponent or survive the first three turns?\n"
        "5e. If the opponent removes some of the early game plays, could Ned Decker keep up without topdecking?\n"
        "5f. Was color an issue or would be an issue (Yes/No only)?\n"
        "(If the early game was not resilient enough, consider taking a mulligan.)\n"
        "\n"
        "6. Analyze why Ned Decker should keep or mulligan (only 1 reason, be super short & terse).\n"
        "6b. How many cards would Ned Decker get to keep if he chooses mulligan? \n"
        "6c. Is it worth it to have one less card in hand to see the next seven cards? \n"
        "(If should mulligan but mulligan is not worth having one less card, "
            "then Ned Decker should reluctantly keep instead.)\n"
        "\n"
        "7. Final Verdict: keep or mulligan (answer starts with \"Because...\")?\n",
        "\n",
        "Answer in a way that the user can infer what was the question that you are answering. Also, take the hand if you have to bottom too many cards!"
    ]

    def count_lands(hand):
        assert hand and hand[0].get('type_line', None)
        return sum([ 1 if 'land' in card['type_line'].lower() else 0 for card in hand ])

    def land_warning_string(land_count):
        if land_count < 2:
            return "There are too few lands in your hand and would cause mana screw; CONSIDER TAKING A MULLIGAN!!! "
        elif land_count > 4:
            return "There are too many lands in your hand and would cause mana flood; CONSIDER TAKING A MULLIGAN!!! "
        else:
            return ""

    hand_analysis = (
        "Ned Decker's hand is:\n\n<hand format=JSON>\n{hand}\n</hand>\n\n...\n\n"
        "There are {land_count} land(s) in your hand. "
        "{land_warning_string} "
        "You will bottom {to_bottom_count} card(s) and will have {keep_card_count} cards in hand if you keep.\n"
    )

    _input = "AI will choose to mulligan or to keep the {keep_card_count}-card(s) hand and bottom {to_bottom_count} card(s). Please submit your choice; if you chose to keep, remember to specify what card(s) to bottom using only ID(s)."

    improvement_prompt = (
        "The previous Chain of Thought was intended to make AI Ned Decker to {expected_action} this hand. "
        "However, you chose to {chosen_action}. "
        "The most important question is (answer to best of your knowledge and explain step-by-step): "
        "What guidances in the deduction step made you think that you should {chosen_action}? "
        "And these are some less-important questions: "
        "What {expected_action}-able aspects about this hand did the deduction step miss? "
        "What should be asked instead to make AI Ned Decker {expected_action} this hand?"
    )

if __name__ == '__main__':
    print(MulliganPromptPreset.chat_prompt)
    print(MulliganPromptPreset.tools)
    print(MulliganPromptPreset.tools_prompt)
    print(MulliganPromptPreset.requests)
    print(MulliganPromptPreset.count_lands)
    print(MulliganPromptPreset.land_warning_string)
    print(MulliganPromptPreset.hand_analysis)
    print(MulliganPromptPreset._input)
    print(MulliganPromptPreset.improvement_prompt)
