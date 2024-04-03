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
from llm.prompts.react import REACT_GUIDE, PONDER_GUIDE

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
        SystemMessagePromptTemplate.from_template(REACT_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently in the start of game step.'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    requests = [
        "At the start of the game, a player may (in listed order):\n"
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
        "Please answer as Ned Decker (AI):\n"
        "Q1. List one possible Legandary Creature from the sideboard that meets the \"Choose Companion\" criteria. "
            "(There could be none. Expected columns: "
            "ID, name, type line, and the first word of the oracle text.)\n"
        "Q1a. If one or more cards were listed, for each candidate, "
            "write down the first two words of the type line and the exact phrase \"Legendary Creature\"; are they the exact same phrase? "
        "Q1b. Continue from Q1a, write down the first word of the oracle text and the exact word \"Companion\"; are they the exact same word?"
        "Q1c. Continue from Q1b, provide the candidate's deck-building restriction from the oracle text. "
        "(If the answer was no to Q1a, or Q1b, or Q1c, then Ned Decker cannot choose any of the candidates as companion. "
        "Otherwise, Ned should choose the candidate as companion.)\n"
        "\n"
        "Q2. List all cards that meets the \"Begin the game with the card on the battlefield\" criteria: "
            "oracle text must have the exact phrase \"begin the game\" "
            "(expected columns: unique card IDs, names, and oracle texts.)\n"
        "Q2a. For each candidate, is the put card from hand or from sideboard?\n"
        "Q2b. For each candidate, provide oracle texts that makes it legal in game to put the cards onto the battlefield before the first turn.\n"
        "Q2c. For each candidate, does the card's oracle text lean more towards reveal instead of move to battlefield? (if reveal then use Q3 instead)\n"
        "Q2d. Would Ned Decker want to put them onto the battlefield?\n"
        "Q2e. Is the put card from hand or from sideboard? (only from hand is legal)\n"
        "Q2f. Is one of the put card Gemstone Caverns?\n"
        "(If the answer was yes to Q2f, Ned Decker MUST set a luck counter on Gemstone Cavern after putting it onto the battlefield.)\n"
        "Q2g. If the answer was yes to Q2f, what card in hand is the most useless and will be exiled?\n"
        "(If the answer was yes to Q2f, Ned Decker MUST exile a card from hand after setting a luck counter on the Gemstone Caverns.)\n"
        "\n"
        "Q3. List all cards that meets the \"Reveal from opening hand\" criteria: "
            "oracle text must have the exact phrase \"opening hand\" "
            "(expected columns: unique card IDs, names, and oracle texts.)\n"
        "Q3a. Is the revealed card from hand or from sideboard? (only from hand is legal)\n"
        "Q3b. For each candidate, provide oracle text that makes it legal in game to reveal the cards from opening hand for effects.\n"
        "Q3c. Would Ned Decker want to reveal those cards for their effects?\n"
        "\n"
        "Q4. Please summarize Q1 to Q3 by listing Ned's TODO list. "
        "(\"Put onto the battlefield\", \"set counter\", and \"exile from hand\" must be listed separately. "
        "Remember to choose a companion if one was found, reveal cards if needed, and put cards to the battlefield if appropriate.)\n"
    ]

    _ = """
    requests = [
        "Please perform these tasks as Ned Decker:\n"
        "- List your sideboard (expected fields: ID, name, oracle_text, and is_companion?)\n"
        "- In your sideboard, is there a companion?\n"
        "- List your hand (expected fields: ID, name, oracle_text, is_reveal_opening_hand?, starts_on_battlefield?)\n"
        "- In your hand, are there any cards that you can begin the game with them on the battlefield?\n"
        "- For the rest of your hand, are there cards that you can reveal to gain their effect?\n"
        "- Recap: Companion? Put to battlefield? Reveal from opening hand? List them all.\n"
        "(Recap note: For special case \"Gemstone Caverns\", "
        "you will have to also list to set a luck counter and exile a card from hand.)\n"
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
