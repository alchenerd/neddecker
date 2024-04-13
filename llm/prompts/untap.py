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
        "If Ned passes the untap phase without doing anything, by default all permanents on his battlefield will be untapped. Most permanents will be untapped except for some special cases.\n"
        "The task is simple: identify what permanent(s) would stay tapped because of its text, or any of the delayed effects from either player.\n"
        "\n"
        "\n"
        "Please answer as Ned Decker:\n"
        "\n"
        "Q1. Assess all cards on the battlefield; for each card you control on the battlefield, would you tap or untap? "
            "(When answering this question, use format of Ned Decker's monologue; "
            "the monologue is announcing all the game actions that Ned Decker will do; "
            "e.g. \"I will untap card_name (card_id)...\" or \"card_name (card_id) stays untap because...\")\n"
        "Q2. Do any permanents you control say \"doesn't untap\" or \"may choose to not untap\"? "
            "(answer with names and card IDs) "
            "(if none then you may pass without doing anything)\n"
        "\n"
        "Q3. Would you skip the untap step because of a delayed trigger? "
            "(if yes, then Ned Decker will prevent all permanents from untapping) "
            "(hint: Ned Decker is opponent's opponent)\n"
        "\n"
        "Q4. Will all permanents you control be prevented from untapping due to skipping the untap step?\n"
        "\n"
        "Q5. If not all permanents will be prevented from untapping, then list each permanent that you will prevent from untapping (use name and card ID; each id will be in a new line).\n"
        "\n"
        "(only answer the final verdict question AFTER ALL questions above are answered)\n"
        "Final Verdict: Please create a TODO list about what permanents to prevent from untapping. If all should be prevented from untapping, then list \"all.\"\n"
        "(for the Final Verict question, the expected format is:\n"
        "\n"
        "Final Verdict:\n"
        "\n"
        "TODO ({[count/\"all\"]} permanents to prevent from untapping):"
        "\n"
        "- there is nothing to do\n"
        "or\n"
        "- write down this exact sentence: \"I will prevent ALL permanents from untapping\"\n"
        "or\n"
        "- write down this exact sentence: \"I will prevent card_id card_name from untapping (NOT ALL!)\" (each id will be in a new line)\n"
        ")\n"
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
        "Currently, NONE in the TODO list was done (all are pending action). Ned Decker (AI) will follow the TODO list. After all items in the TODO list are done, Ned Decker will pass the untap phase. However, if there is nothing to do in the TODO list, Ned Decker will pass the untap phase immediately."
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
