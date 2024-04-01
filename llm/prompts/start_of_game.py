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
        "At the start of the game, a player may:\n"
        "<actions>\n"
        "1. Set a companion card in the player's sideboard as a companion; "
            "then the player can pay three mana "
            "to put the companion card "
            "from the player's sideboard "
            "to the player's hand later in the game as a sorcery.\n"
            "(A companion is usually a Legendary Creature that has a companion deckbuilding restriction.)\n"
            "(To be eligible for action 1, a card must have the keyword \"Companion\" in its oracle text.)\n"
        "2. Reveal one or more cards that do something at the start of the game if the card says so; "
            "then the player may register a delayed trigger to resolve the effects. "
            "(To be eligible for action 2, a card must have \"reveal\" and \"opening hand\" in its oracle text.)\n"
        "3. Put one or more cards from the player's hand to the player's battlefield if the card says so; "
            "then the player may move the card from hand to battlefield. "
            "(To be eligible for action 3, a card must have \"...begin the game with ... on the battlefield\" in its oracle text.)\n"
        "</actions>\n"
        "Answer as Ned Decker (AI):\n"
        "Q1. List all Legandary Creatures that are in Ned Decker's sideboard and has oracle text starting with \"Companion\".\n"
        "Q1a. If there is one or more, which would Ned Decker choose as his companion?\n"
        "Q2. List all cards in Ned Decker's hand that does something when revealed from the opening hand (has exactly \"reveal\" in the oracle text). Give related oracle text excerpt and names.\n"
        "Q2a. For each card listed, would Ned Decker want to reveal that card for its effect?\n"
        "Q3. List all cards in Ned Decker's hand that in its oracle text state that Ned may begin the game with it on the battlefield. Give names.\n"
        "Q3a. For each card listed, would Ned Decker want to put it to the battlefield?\n"
        "Q3b. For each card about to put onto the battlefield, give exact excerpts from its oracle text that allows Ned to put it on the battlefield; is the allowed card really the card itself, or is the allowed card other things instead?\n"
        "Q4. List all start-of game actions Ned Decker will take.\n"
    ]

    board_analysis = (
        "Ned Decker's hand is:\n<hand>\n{hand}\n</hand>\n\n"
        "Ned Decker's sideboard is:\n<sideboard>\n{sideboard}\n</sideboard>\n\n"
    )

    _input = (
        "Ned Decker (AI) may take any number of actions as planned, and then he should pass the start of game phase."
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
