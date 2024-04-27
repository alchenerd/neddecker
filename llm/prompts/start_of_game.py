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
        "Q1. What cards to begin the game with which on the battlefield, if any?\n"
        "(Note: put at most one Gemstone Caverns if exist because it's a Legandary Land)\n"
        "Q1a. (If there's Gemstone Caverns, answer this too) Are there more then one Gemstone Caveerns? Note that Gemstone Caverns is a Legendary land, so the redundant copies are useless.\n"
        "Q1b. (If there's Gemstone Caverns, answer this too) What card in hand is the worst? How bad was it? You may exile it for Gemstone Caverns' requirement.\n"
        "\n"
        "Q2. What cards to reveal from the opening hand, if any?\n"
        "\n"
        "Q3. Please summarize Q1 and Q2 by listing Ned's TODO list. "
            "This list is for the \"start of game\" phase, therefore "
            "NO untap, NO upkeep, NO draw, NO play a land.\n"
            "eligible actions:\n"
            "\n"
            "- Nothing to do: No card require action at the start of the game.\n"
            "- Reveal from opening hand: Reveal what cards (name and unique ID) from your opening hand?\n"
            "- Begin the game with the card on the battlefield"
                " - Put what cards (name and unique ID) onto the battlefield?\n"
            "- Set a luck counter: Was Gemstone Caverns in the opening hand (and what ID)?\n"
            "- Exile a card from hand: Was Gemstone Caverns in the opening hand (and what name and ID to exile)?\n"
            "Format: each TODO list item is one of the above; accompanied with name and ID; different IDs calls for different TODO list items; separate different IDs into different TODO list items.\n"
        "\n"
        "Begin from Q1 and answer all questions!\n"
    ]

    board_analysis = (
        "All cards to reveal at the start of the game:\n"
        "<to_reveal format=JSON>\n{to_reveal}\n</to_reveal>\n"
        "All cards to begin the game on the battlefield with:\n"
        "<to_battlefield format=JSON>\n{to_battlefield}\n</to_battlefield>\n"
    )

    more_board_analysis = (
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
    print(StartOfGamePromptPreset.tools_prompt)
    print(StartOfGamePromptPreset.requests)
    print(StartOfGamePromptPreset._input)
    print(StartOfGamePromptPreset.improvement_prompt)
