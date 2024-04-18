from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../')
sys.path.insert(0, rootdir)
from llm.tools.upkeep import upkeep_actions
from llm.prompts.whoami import AI_ROLE
from llm.prompts.react import PONDER_GUIDE, TOOLS_GUIDE

class UpkeepPromptPreset():
    chat_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(PONDER_GUIDE),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('{data}'),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the upkeep phase.'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
    ])

    tools = [ *upkeep_actions ]

    tools_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(TOOLS_GUIDE.format(
            tools=render_text_description(tools),
            tool_names=", ".join([ t.name for t in tools ]),
        )),
        SystemMessagePromptTemplate.from_template(AI_ROLE),
        SystemMessagePromptTemplate.from_template('Ned Decker (AI) is currently at the upkeep phase.'),
        SystemMessagePromptTemplate.from_template('{data}'),
        MessagesPlaceholder("chat_history"),
        HumanMessagePromptTemplate.from_template('{input}'),
        AIMessagePromptTemplate.from_template('{agent_scratchpad}'),
    ])

    requests = []

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
        "Currently, NONE in the TODO list was done (all items are pending your action). Ned Decker (AI) will follow the TODO list. After all items in the TODO list are done, Ned Decker will pass the untap phase. However, if there is nothing to do in the TODO list, Ned Decker will pass the untap phase immediately."
    )

    improvement_prompt = (
        ""
    )

if __name__ == '__main__':
    print(UpkeepPreset.chat_prompt)
    print(UpkeepPreset.tools)
    print(UpkeepPreset.tools_prompt)
    print(UpkeepPreset.requests)
    print(UpkeepPreset.board_analysis)
    print(UpkeepPreset._input)
    print(UpkeepPreset.improvement_prompt)
