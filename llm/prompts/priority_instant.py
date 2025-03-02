from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../')
sys.path.insert(0, rootdir)
from llm.tools.priority_instant import priority_instant_actions
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import PONDER_GUIDE, TOOLS_GUIDE

class PriorityInstantPromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(PONDER_GUIDE),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) has received priority (instant speed.)'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    tools = [ *priority_instant_actions ]

    tools_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(TOOLS_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) has received priority (instant speed.)'),
        SystemMessagePromptTemplate.from_template('{data}'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    requests = [
        "Q1. Whose turn is it and what phase/step of the game currently? The answer is guaranteed to be present in the above context.\n"
        "Q2. At this stage, you are given the priority; what can you legally do in game right now?\n"
        "Q3. Observe the board and your hand and decide what you want to do at this moment. Keep in mind that you cannot take any sorcery speed actions right now.\n"
        "Q4. Double-check: is now the right time to act, or could you wait until later in the game?\n"
        "Final Verdict - Make a TODO list of what you want to do in this priority. Keep in mind that you may only cast non-flash, non-instant spells when it's your turn and the stack is empty. End the list with \"Pass the priority.\"",
    ]

    # factor in the lost in the middle problem, the information ordering will be in descending order:
    # - opponent battlefield
    # - self battlefield
    # - self hand
    # - self graveyard
    # - opponent graveyard
    # - self exile
    # - opponent exile
    # - the current phase
    # - whose turn
    board_analysis = (
        "\n"
        "<opponent_battlefield format=JSON>\n"
        "{opponent_battlefield}\n"
        "</opponent_battlefield>\n"
        "\n"
        "\n"
        "<self_battlefield format=JSON>\n"
        "{self_battlefield}\n"
        "</self_battlefield>\n"
        "\n"
        "\n"
        "<self_hand format=JSON>\n"
        "{self_hand}\n"
        "</self_hand>\n"
        "\n"
        "\n"
        "<self_graveyard format=JSON>\n"
        "{self_graveyard}\n"
        "</self_graveyard>\n"
        "\n"
        "\n"
        "<opponent_graveyard format=JSON>\n"
        "{opponent_graveyard}\n"
        "</opponent_graveyard>\n"
        "\n"
        "\n"
        "<self_exile format=JSON>\n"
        "{self_exile}\n"
        "</self_exile>\n"
        "\n"
        "\n"
        "<opponent_exile format=JSON>\n"
        "{opponent_exile}\n"
        "</opponent_exile>\n"
        "\n"
        "\n"
        "Stack:\n"
        "The stack is currently empty.\n"
        "\n"
        "You are given priority at {whose_turn}'s {current_phase}.\n"
    )

    _input = (
        "Currently, NONE of the TODO list was done (all items are pending your action). Ned Decker (AI) will follow the TODO list by calling appropriate functions. After all items in the TODO list are done, Ned Decker will pass the priority using `pass_priority`. However, if there is nothing to do in the TODO list, Ned Decker will pass the priority immediately."
    )

    improvement_prompt = (
        ""
    )

if __name__ == '__main__':
    pass
