from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../')
rootdir = os.path.dirname(currentdir + '/../../')
sys.path.insert(0, rootdir)
from llm.tools.mulligan import submit_mulligan_decision
from llm.tools.start_of_game import start_of_game_actions
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import PONDER_GUIDE, TOOLS_GUIDE

class StartOfGamePromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(PONDER_GUIDE),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently in the start of game step.'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    tools = [ *start_of_game_actions ]

    tools_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(TOOLS_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently in the start of game step.'),
        SystemMessagePromptTemplate.from_template('{data}'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    requests = [
        "Please answer each question below as Ned Decker (AI):\n"
        "Q1. List one possible Legandary Creature from the sideboard that meets the \"Choose Companion\" criteria. "
            "(there could be none) "
            "(answer this with columns: ID, name, where, type line, the first word of the oracle text)\n"
        "Q1-validation (must answer). Where exactly is the word \"Companion\" in Q1's answer? "
            "If mistaken then Ned Decker cannot choose it as a companion.\n"
        "Q1a. If one or more cards were listed, for each candidate, "
            "write down the first two words of the type line and the exact phrase \"Legendary Creature\"; "
            "are they the exact same phrase? "
        "Q1b. Continue from Q1a, write down the first word of the oracle text and the exact word \"Companion\"; "
            "are they the exact same word?"
        "Q1c. Continue from Q1b, provide the candidate's deck-building restriction from the oracle text. "
            "(If the answer was no to Q1a, or Q1b, or Q1c, "
            "then Ned Decker cannot choose any of the candidates as companion; "
            "otherwise, Ned should choose the candidate as companion.)\n"
        "\n"
        "Q2. List EVERY card in Ned Decker's hand that have the exact phrase \"begin the game with it on the battlefield\" "
            "(answer this with columns: ID, name, where, oracle text)\n"
        "Q2-validation. Where exactly is the phrase \"you may begin the game with it on the battlefield.\" in Q2's answer? "
            "If mistaken then Ned Decker cannot put it onto the battlefield; state this mistake explicitly.\n"
        "Q2a. For each candidate, is the candidate currently in hand or in the sideboard? "
            "(only put from hand is legal, and if the card was in sideboard "
            "then that card cannot be put onto the battlefield and move on to the next candidate)\n"
        "Q2b. For each candidate, does the card's oracle text lean more towards reveal instead of move to battlefield? "
            "(if towards reveal, then the card is for Q3 instead, and "
            "Ned Decker cannot put the card onto the battlefield)\n"
        "Q2c. Can Ned Decker put them onto the battlefield legally in gane now? "
            "Would Ned Decker want to put them onto the battlefield?\n"
        "Q2d. Is one of the put cards Gemstone Caverns?\n"
            "(If there's Gemstone Caverns, Ned Decker MUST set a luck counter on Gemstone Caverns "
            "after putting it onto the battlefield.)\n"
        "Q2e. If there's Gemstone Caverns, what card in hand is the most useless and will be exiled?\n"
        "Q2f. You will lose the exiled card for the rest of the game; how bad in the early game was that card? "
            "You may pick another card if you want to.\n"
            "(If there's Gemstone Caverns, Ned Decker MUST exile a card from hand "
            "after setting a luck counter on the Gemstone Caverns.)\n"
        "\n"
        "Q3. List EVERY card in Ned Decker's hand that has the exact phrase \"reveal from your opening hand\" "
            "(answer this with columns: ID, name, where, oracle text)\n"
        "Q3-validation. Where exactly is the phrase \"You may reveal this card from your opening hand.\" in Q3's answer?"
            "If mistaken then Ned Decker cannot reveal the card; state this mistake explicitly.\n"
        "Q3a. For each candidate, is the revealed card from hand or from sideboard? (only from hand is legal)\n"
        "Q3b. Can Ned Decker reveal those cards for their effects legally in game now? "
            "Would Ned Decker want to reveal those cards for their effects?\n"
        "\n"
        "Q4. Please summarize Q1 to Q3 by listing Ned's TODO list. "
            "This list is for the \"start of game\" phase - "
            "no untap, no upkeep, no draw, no play land - we are currently way before that!\n"
        "\n"
        "<eligible_actions>\n"
            "1. Choose Companion - Choose a companion card from the player's sideboard "
                "(Choose Companion Criteria: card is a Legendary Creature, and has the exact keyword \"Companion\" at the beginning of its oracle text.)\n"
            "2. Reveal from opening hand - Reveal one or more cards that has an effect when revealed from the opening hand "
                "(Reveal from opening hand criteria: card is in hand and mentions \"reveal this card from your opening hand\" in the oracle text.)\n"
            "3. Begin the game with the card on the battlefield - Put one or more cards from hand to battlefield "
                "(Begin the game with the card on the battlefield criteria: card is in hand and mentions \"begin the game with ~ on the battlefield\" in the oracle text.)\n"
            "4. Set counter at the start of the game - Put an amount of counters of one type onto a card that is on the battlefield. "
                "(Set counter criteria: card was put onto the battlefield, and mentions \"with a luck counter\" in the oracle text.)\n"
            "5. Exile from hand at the start of the game - Exile a card from hand. "
                "(Exile from hand criteria: When Gemstone Caverns states to exile a card from hand.)\n"
        "</eligible_actions>\n"
        "\n"
        "Begin!\n"
    ]

    weawefaf = """
    requests = [
        "- List your sideboard (expected fields: ID, name, oracle_text, and is_companion?)\n"
        "- In your sideboard, is there a companion?\n"
        "- List your hand (expected fields: ID, name, oracle_text, is_reveal_opening_hand?, starts_on_battlefield?)\n"
        "- In your hand, are there any cards that you can begin the game with them on the battlefield?\n"
        "- For the rest of your hand, are there cards that you can reveal to gain their effect?\n"
        "- Recap: Companion? Put to battlefield? Reveal from opening hand? List them all.\n"
            "(Recap Special Case: After putting \"Gemstone Caverns\" onto the battlefield, "
            "you will have to set a luck counter on it and exile a useless card from hand.)\n"
    ]
    """

    board_analysis = (
        "Ned Decker's sideboard is:\n<sideboard>\n{sideboard}\n</sideboard>\n\n"
        "Ned Decker's hand is:\n<hand>\n{hand}\n</hand>\n\n"
    )

    _input = (
        "Ned Decker (AI) should take all actions in the TODO list, and then he should pass the start of game phase."
    )

    improvement_prompt = (
        ""
    )

if __name__ == '__main__':
    print(StartOfGamePromptPreset.chat_prompt)
    print(StartOfGamePromptPreset.tools)
    print(StartOfGamePromptPreset.submit)
    print(StartOfGamePromptPreset.tools_prompt)
    print(StartOfGamePromptPreset.requests)
    print(StartOfGamePromptPreset._input)
    print(StartOfGamePromptPreset.improvement_prompt)
