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
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the start of game step.'),
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
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the start of game step.'),
        SystemMessagePromptTemplate.from_template('{data}'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    #awefefwa = """
    requests = [
        "Please answer each question below as Ned Decker (AI):\n"
        "Q1. What is the companion to choose, if any?\n"
        "\n"
        "Q2. What cards to begin the game with which on the battlefield, if any?\n"
        "(Note: put at most one Gemstone Caverns if exist because it's a Legandary Land)\n"
        "Q2a. (If there's Gemstone Caverns, answer this too) Are there more then one Gemstone Caveerns? Note that Gemstone Caverns is a Legendary land, so the redundant copies are useless.\n"
        "Q2a. (If there's Gemstone Caverns, answer this too) What card in hand is the worst? How bad was it? You may exile it for Gemstone Caverns' requirement.\n"
        "\n"
        "Q3. What cards to reveal from the opening hand, if any?\n"
        "\n"
        "Q4. Please summarize Q1 to Q3 by listing Ned's TODO list. "
            "This list is for the \"start of game\" phase, therefore "
            "NO untap, NO upkeep, NO draw, NO play a land.\n"
            "eligible actions:\n"
            "\n"
            "- Nothing to do: No card require action at the start of the game.\n"
            "- Choose companion: Choose which Legendary Creature as the companion? (name and ID)\n"
            "- Reveal from opening hand: Reveal what cards (name and unique ID) from your opening hand?\n"
            "- Begin the game with the card on the battlefield"
                " - Put what cards (name and unique ID) onto the battlefield?\n"
            "- Set a luck counter: Was Gemstone Caverns in the opening hand (and what ID)?\n"
            "- Exile a card from hand: Was Gemstone Caverns in the opening hand (and what name and ID to exile)?\n"
            "Format: each TODO list item is one of the above; accompanied with name and ID; different IDs calls for different TODO list items; separate different IDs into different TODO list items.\n"
        "\n"
        "Begin from Q1 and answer all questions!\n"
    ]
    #"""

    awefefwa = """
    requests = [
        "Please answer each question below as Ned Decker (AI):\n"
        "Q1. List one possible Legandary Creature from the sideboard that meets the \"Choose Companion\" criteria. "
            "(there could be none) "
            "(answer this with columns: ID, name, where, is_companion, type line, the first word of the oracle text)\n"
        "Q1-validation (must answer). Where exactly is the word \"Companion\" in Q1's answer? "
            "If word was not found then Ned Decker cannot choose it as a companion.\n"
            "Answer this validation question with \"Yes/No, therefore...\"\n"
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
        "Q2. List EVERY card in Ned Decker's hand that has the exact phrase \"begin the game with it on the battlefield\" "
            "(answer this with columns: ID, name, where (the card MUST be in HAND NOW), is_begin_game_on_battlefield, oracle text)\n"
        "Q2-validation. Where exactly is the phrase \"you may begin the game with it on the battlefield.\" in Q2's answer? "
            "(Answer this validation question with \"In the oracle text of Q2's answer, "
            "the phrase 'you may begin the game...' is present/missing, therefore (...)\"\n"
            "If the phrase was not found then Ned Decker cannot put it onto the battlefield; "
            "otherwise, Ned Decker may proceed to Q2a.)"
        "Q2a. For each candidate, is the candidate currently in hand or in the sideboard? "
            "(if the card was in sideboard, then the card CANNOT be put onto the battlefield, therefore you MUST say "
            "\"ILLEGAL: CARDNAME should NEVER be put onto the battlefield!!!\" "
            "using the card's name to mark your mistake)\n"
        "Q2b. For each candidate, write down the oracle text, but you MUST start from the word \"REVEAL\""
            " or from the phrase \"ON THE BATTLEFIELD\" in the oracle text. "
            "(if \"REVEAL\" was in the oracle text, then "
            "Ned Decker CANNOT put the card onto the battlefield; "
            "similarly, if \"ON THE BATTLEFIELD\" was NOT in the oracle text, then "
            "Ned Decker also CANNOT put the card onto the battlefield; "
            "you MUST say \"ILLEGAL: CARDNAME should NEVER be put onto the battlefield!!!\" using this card's name "
            "to mark your mistake)\n"
        "Q2c. Can Ned Decker put them onto the battlefield legally in game now? "
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
        "Q3. List EVERY card that has the exact phrase \"reveal from your opening hand\" "
            "(answer this with columns: ID, name, where (the card MUST in HAND NOW), is_reveal_from_opening_hand, oracle text)\n"
        "Q3-validation. Where exactly is the phrase \"You may reveal this card from your opening hand.\" in Q3's answer?"
            "(Answer this validation question with \"In the oracle text of Q3's answer, the phrase "
            "'you may reveal ... from your opening hand' is present/missing, therefore (...)\"\n"
            "If the phrase was not found then Ned Decker cannot reveal the card; "
            "otherwise, Ned Decker may proceed to Q3a.)\n"
        "Q3a. For each candidate, write down the oracle text, but you MUST start from the word \"REVEAL\""
            " or from the phrase \"ON THE BATTLEFIELD\" in the oracle text. "
            "(if \"ON THE BATTLEFIELD\" was in the oracle text, then "
            "Ned Decker CANNOT reveal the card; "
            "similarly, if \"REVEAL\" was NOT in the oracle text, then "
            "Ned Decker also CANNOT reveal the card; "
            "you MUST say \"ILLEGAL: CARDNAME should NEVER be revealed!!!\" using this card's name "
            "to mark your mistake)\n"
        "Q3b. For each candidate, is the revealed card from hand or from sideboard? (only from hand is legal)\n"
        "Q3c. Can Ned Decker reveal those cards for their effects legally in game now? "
            "Would Ned Decker want to reveal those cards for their effects?\n"
        "\n"
        "Q4. Please summarize Q1 to Q3 by listing Ned's TODO list. "
            "Remember to omit all ILLEGAL actions that Ned Decker CANNOT do. "
            "This list is for the \"start of game\" phase, therefore "
            "NO untap, NO upkeep, NO draw, NO play a land.\n"
            "Instead, all possible actions are provided below FYI "
            "(all TODO list items MUST be one of these; "
            "duplicate may happen for cards with same name but different ID):\n"
                "\n"
                "1. Choose Companion - Choose which Legendary Creature as the companion?\n"
                "2. Reveal from opening hand - Reveal what cards (name and unique ID) from your opening hand?\n"
                "3. Begin the game with the card on the battlefield"
                    " - Put what cards (name and unique ID) onto the battlefield?\n"
                "4. Set a luck counter - Was Gemstone Caverns in the opening hand (and what ID)?\n"
                "5. Exile a card from hand - Was Gemstone Caverns in the opening hand (and what ID)?\n"
        "\n"
        "Begin from Q1 and answer all questions!\n"
    ]
    """

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

    efawoeijfa = """
    requests = [
        "At the start of game phase, you may:\n"
        "- choose_companion\n"
        "- reveal_from_hand\n"
        "- move_to_battlefield_from_hand\n"
        "- set_luck_counter (for Gemstone Caverns)\n"
        "- exile_from_hand (for Gemstone Caverns)\n"
        "Are there Gemstone Caverns?\n"
        "If yes then after putting Gemstone Caverns onto the battlefield, "
        "call set_luck_counter and then exile_from_hand in the TODO list\n"
        "Think of the worse card in hand in the early game, how bad was it in the early game?\n"
        "You may exile that card for Gemstone Caverns' requirement.\n"
        "Make a TODO list at the start of game phase based on those cards, provide IDs and names.\n"
        "Remember we're at the start of game phase, so no untap, no upleep, no draw a card, no play a land.\n"
    ]
    """

    board_analysis = (
        "All companions in Ned Decker's sideboard:\n"
        "<companion format=JSON>\n{companion}\n</companion>\n"
        "All cards to reveal at the start of the game:\n"
        "<to_reveal format=JSON>\n{to_reveal}\n</to_reveal>\n"
        "All cards to begin the game on the battlefield with:\n"
        "<to_battlefield format=JSON>\n{to_battlefield}\n</to_battlefield>\n"
        "All cards in Ned Decker's hand:\n"
        "<hand format=JSON>\n{hand}\n</hand>\n"
    )

    _input = (
        "Ned Decker (AI) will take actions for each mentioned card (unique IDs takes multiple same actions) according to the TODO list, and he MUST pass_start_of_game as his last action."
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
