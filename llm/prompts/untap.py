from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../')
sys.path.insert(0, rootdir)
from llm.tools.untap import untap_actions
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import PONDER_GUIDE, TOOLS_GUIDE

class UntapPromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(PONDER_GUIDE),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the untap phase.'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    tools = [ *untap_actions ]

    tools_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(TOOLS_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the untap phase.'),
        SystemMessagePromptTemplate.from_template('{data}'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    requests = [
        "Ned Decker is given the state of his battlefield before the untap phase, as well as lists of both player's delayed triggers. "
        "If Ned passes the untap phase without doing anything, by default all permanents on his battlefield will be untapped. Most cards will be untapped except for some special cases.\n"
        "The task is simple: identify what card(s) would stay tapped because of the card text, or any of the delayed effects on either player.\n"
        "\n"
        "Q1. Did any card say that it doesn't untap or may choose to not untap? "
            "(if none then may pass without doing anything)\n"
        "Q2. If some of the cards should stay untapped, what are their ID and names?\n"
        "Q3. Is any of the player affected by delayed triggers that prevents untapping?\n"
        "Final Verdict: Please make a TODO list about what permanents to prevent from untapping.\n",
    ]

    board_analysis = (
        "\n"
        "<battlefield format=JSON>\n"
        "{battlefield}\n"
        "</battlefield>\n"
        "\n"
        "<ned_delayed_triggers format=JSON>\n"
        "{ned_delayed_triggers}\n"
        "</ned_delayed_triggers>\n"
        "\n"
        "<user_delayed_triggers format=JSON>\n"
        "{user_delayed_triggers}\n"
        "</user_delayed_triggers>\n"
        "\n"
    )

    _input = (
        "Ned Decker (AI) will, if the TODO list instructed, prevent N permanents or all permanants from untapping, and then Ned Decker will pass the untap phase. However, if there is nothing to do, Ned Decker will pass the untap phase immediately."
    )

    improvement_prompt = (
        ""
    )

if __name__ == '__main__':
    print(UntapPromptPreset.chat_prompt)
    print(UntapPromptPreset.tools)
    print(UntapPromptPreset.tools_prompt)
    print(UntapPromptPreset.requests)
    print(UntapPromptPreset._input)
    print(UntapPromptPreset.improvement_prompt)
