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
        "1a. Classify Ned Decker's hand as one of "
        "["
            "\"mana screw\" (too few mana sources, e.g. one land or less), "
            "\"balanced\", "
            "\"mana flood\" (too many mana sources, e.g. five lands or more) "
        "] "
        "(don't say anything else).\n"
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
        "3c. Compile a hand after sending those cards to the bottom of the library (with only name and ID).\n"
        "3d. After bottoming the unwanted cards, is the rest of the hand good enough for keeping?\n"
        "(If there are too many unplayable cards and can't bottom them, consider taking a mulligan.)\n"
        "\n"
        "(IMPORTANT: From now on, analysis should be exclusively based on the compiled hand created in 3c.)\n"
        "4. Please summarize the hand's early game plays for each of [ turn 1, turn 2, turn 3 ]:\n"
        "(\n"
            "\treply with Ned Decker's inner monologues, "
                "where Ned Decker thinks about the following each turn (include step count):\n"
                "\n"
                "\t1. \"I check my battlefield and I see there are {count_lands_on_battlefield} lands "
                    "on the battlefield, and they are ... \""
                    "(describe the lands on the battlefield, or \"None\" if there are no lands on the battlefield)\n"
                "\t2. \"I will tap each land on the battlefield and gain one mana for each tapped land = "
                    "{mana_pool_list_on_battlefield}\"\n"
                "\t3. \"I check my remaining hand and I see that I have {count_lands_in_hand} lands that "
                    "I can play one of which this turn, and they are ... "
                    "(describe the remaining lands in the hand or \"None\" if there are none in hand)\"\n"
                "\t4a. (if there are lands in remaining hand) \"I can play one of them. I will choose ...\"\n"
                "\t4b. (if no land to play in hand) "
                    "\"Oh, I would miss my land drop this turn. This hand is a MANA SCREW!\"\n"
                "\t5. \"I will [play {land_name_in_4}/miss land drop]. "
                    "Now on the battlefield there are {describe_lands_on_the_battlefield}\"\n"
                "\t6. \"My remaining hand is {remaining_hand (you MUST include lands in hand)}.\"\n"
                "\t7. (if played land is NOT tapped) "
                    "\"I can tap {played_land_name} to add {mana_pool_list_played_land}\"\n"
                "\t8. \"This turn, I would have {count_mana_on_battlefield + count_mana_played_land} mana available: \" "
                    "(write down the total mana pool in a python list[str], example given: "
                    "\"[ \"{W}\", \"{U}\", \"{B}\", \"{R}\", \"{G}\", \"{C}\" ]\")\n"
                "\t9. \"My remaining hand is {remaining_hand (you MUST include lands in hand)}.\"\n"
                "\t10. \"My non-land permanents on the battlefield is {battlefield_non_land_permanents}.\"\n"
                "\t11. \"Checking for next action or next spell cast: I could {do_what}.\"\n"
                "\t12a. (if casting a spell) "
                    "\"I want to cast {spell_name} and the mana cost is {mana_cost}.\"\n"
                "\t12b. (else if any of [ activate_from_hand, activate_on_battlefield ]) "
                    "\"I want to {action_type with card_name} and the mana cost is {mana_cost}.\"\n"
                "\t13. (if mana_pool >= mana_cost) \"With {mana_pool}, I can afford {target_mana_cost}, "
                    "so I can cast {spell_name} for {spell effect}.\"\n"
                "\t... (if cannot afford mana_cost, then return to 11 and come up with another cheaper action, "
                    "or go to 15 if there's nothing else to do)\n"
                "\t14a. (if casting a spell) \"I will cast {spell_name_in_12a}.\"\n"
                "\t14b. (else if taking another action) \"I will {action_from_12b}.\"\n"
                "\t14c. (else if neither 14a nor 14b was chosen this turn and "
                    "you have wasted a full turn doing nothing) "
                    "\"I have done nothing; which indicates possible MANA FLOOD.\"\n"
                "\t15. \"The remaining mana is {mana_pool - mana_cost}.\"\n"
                    "\t\t(REMEMBER: [\"{X}\"] - [\"{0}\"] = [\"{X}\"], "
                    "thus the mana pool REMAINS THE SAME if the mana_cost was {0} mana)\n"
                "\t16. \"My remaining unplayed hand is "
                    "{remaining_hand (you MUST include lands in hand; "
                    "you MUST answer using fields = [id, name, mana_cost(NEW)])}.\"\n"
                "\t17. \"With {remaining_mana_pool}, I can ["
                        "take {affordable_actions}/"
                        "cast {affordable_spells}/"
                        "not do anything else"
                    "].\"\n"
                "\t... (continue to 18 if you can not do anything else; "
                    "otherwise repeat from 11; this loop may happen N times)\n"
                "\t18. \"I will end turn {current_turn_count} out of 3. "
                    "I will move on to {next_turn_count} out of 3.\"\n"
                "\t19. \"My remaining unplayed hand is {remaining_hand (you MUST include lands in hand)}.\"\n"
                "\t... (rinse and repeat; move to the next turn and start over from step 1; "
                    "go through ALL the steps from step 1 to step 19 "
                    "for ALL of [ turn 1, turn 2, turn 3 ])\n"
                "\n"
        ")\n"
        "\n"
        "5a. Has Ned Decker missed any land drop for the turn and lost tempo (Yes/No, and explain why)?\n"
        "5b. Has Ned Decker passed a turn without casting a spell and lost tempo (Yes/No, and explain why)?\n"
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
