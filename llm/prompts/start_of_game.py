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
from llm.tools.start_of_game import start_of_game_actions
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import REACT_GUIDE

class StartOfGamePromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
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
    ])

    requests = [
        "At the start of the game, a player may (in listed order):\n"
        "<eligible actions>\n"
            "1. Choose Companion - Choose a companion card in the player's sideboard "
                "(Choose Companion Criteria: Is a Legendary Creature, and has the exact keyword \"Companion\" at the beginning of its oracle text.)\n"
            "2. Reveal from Hand - Reveal one or more cards that has an effect when revealed from the opening hand "
                "(Reveal from Hand Criteria: Mentions \"reveal this card from your opening hand\" in the oracle text.)\n"
            "3. Put onto Battlefield - Put one or more cards from hand to battlefield "
                "(Put onto Battlefield Criteria: Mentions \"begin the game with ~ on the battlefield\" in the oracle text.)\n"
        "</eligible actions>\n"
        "Answer as Ned Decker (AI):\n"
        "Q1. List all Legandary Creatures in the sideboard that meets the \"Choose Companion\" criteria.\n"
        "Q2. List all cards in hand that meets the \"Reveal from Hand\" criteria. (Answer with card IDs and names.)\n"
        "Q2a. Would Ned Decker want to reveal those cards for their effects?\n"
        "Q3. List all cards in hand that meets the \"Put onto Battlefield\" criteria. (Answer with card IDs and names.)\n"
        "Q3a. Would Ned Decker want to put them onto the battlefield?\n"
        "Q4. Summarize Q1 to Q3 by listing Ned's TODO list of start-of-game actions.\n"
    ]

    board_analysis = (
        "Ned Decker's hand is:\n<hand>\n{hand}\n</hand>\n\n"
        "Ned Decker's sideboard is:\n<sideboard>\n{sideboard}\n</sideboard>\n\n"
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
