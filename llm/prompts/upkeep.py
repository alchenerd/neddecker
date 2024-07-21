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
        "Q1. Whose turn and what step/phase are you in? The answer is guaranteed to be in the context. "
            "(if its not your turn, then ignore those that say \"your upkeep\" and look for \"each upkeep\" instead.)\n"
        "Q2. What do you see on your battlefield? "
            "For each permanent, think out loud if the permanent mentions \"at the beginning of upkeep\".\n"
        "Q3. Please summarize all the above and recap what upkeep triggers are to be created if there's any. "
            "Answer this question by listing the card_id, name, and oracle_text_about_upkeep.\n"
        "Q4. Upkeep Trigger Filter - for each summarized card, is the reason of the trigger "
            "\"at the beginning of ... upkeep\"? If not, omit that card."
        "Q5. Final Verdict - "
            "with the information above, please create a TODO list about creating the required upkeep triggers, if any; "
            "if there are upkeep triggers to create, for each TODO list item, "
            "state the name, ID, and the trigger content within a JSON object, "
            "otherwise if there are no upkeep triggers to create, say \"There is nothing to do.\"\n",
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
        "<stack format=JSON top-of-stack=first-item>\n"
        "{stack}\n"
        "</stack>\n"
        "\n"
        "You are now checking for/taking turn-based actions at {whose_turn}'s {current_phase}.\n"
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
