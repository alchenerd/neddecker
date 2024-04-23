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

    requests = [
        "Please answer these questions for submitting triggers for the upkeep step as Ned Decker "
            "(answers should be short and terse):\n"
        "Q1. What do you see on your battlefield? "
            "For each permanent, think out loud if this permanent needs attention during this upkeep; "
            "if the permanent requires attention for this upkeep, state the oracle text that referenes this.\n"
        "Q2. Summarize the above - what permanents require your attention during this upkeep step, if any?\n"
        "Q3. What delayed triggers were referenced this upkeep step, if any?\n"
        "Q4. Please summarize all the above and recap what upkeep triggers are to be created.\n"
        "Q5. Final Verdict - "
            "with the information above, please create a TODO list about creating the required upkeep triggers, if any; "
            "if there are upkeep triggers to create, for each TODO list item, "
            "state the name, ID, and the trigger content within a JSON object, "
            "otherwise, say \"There is nothing to do.\"\n",
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
        "Currently, NONE of the TODO list was done (all items are pending your action). Ned Decker (AI) will follow the TODO list by calling appropriate functions. After all items in the TODO list are done, Ned Decker will pass the upkeep phase using `pass_upkeep`. However, if there is nothing to do in the TODO list, Ned Decker will pass the upkeep phase immediately."
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
