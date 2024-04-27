from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.tools.render import render_text_description

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../')
sys.path.insert(0, rootdir)
from llm.tools.untap import untap_actions, untap_bonus_actions
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
    untap_actions = untap_actions
    untap_bonus_actions = untap_bonus_actions

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
        "Q1. Assess all cards on the battlefield; for each card you control on the battlefield, would you untap as normal, or keep it tapped because the oracle text says so? "
            "(When answering this question, use format of Ned Decker's monologue; "
            "the monologue is announcing all the game actions that Ned Decker will do; "
            "e.g. \"I will untap card_name (card_id)...\" or \"card_name (card_id) stays untap because...\")\n"
        "Q2. Do any permanents you control say \"doesn't untap\" or \"may choose to not untap\"? "
            "(answer with names and card IDs) "
            "(if there are no permanents that would be prevented, then you may skip to the final verdict.)\n"
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
        "TODO ({[count/\"all\"/\"no\"]} permanents to prevent from untapping):"
        "\n"
        "in the TODO list, each list item could be one of below:\n"
        "\n"
        "- \"There is nothing to do\"\n"
        ", OR\n"
        "- \"I will prevent ALL permanents from untapping\"\n"
        ", OR\n"
        "- \"I will prevent card_id card_name from untapping (NOT ALL!)\" (each id will be in a new line)\n"
        "\n"
        ")\n"
    ]

    bonus_requests = [
        "Looks like there are permanants you control that would be triggered when untapped. "
        "Please continue to answer as Ned Decker:\n"
        "\n"
        "Q1. Please provide a table of permanents you control that would be triggered when untapped. "
            "(columns = card id, card name, does it untap, what does it do when untapped)\n"
        "Q2. If there would be more than one triggers, think about what order do you want them to happen in game. "
            "You may skip this if there is only one trigger. "
            "(answer as Ned Decker with his analysis; what trigger happens first, what happens next, ...)"
        "Q3. The MTG stack follows LIFO (Last In, First Out); So, as Ned decker, reverse that order and "
            "talk about the order of triggers that you will put onto the stack.\n"
        "Q4. Please recite the previous TODO list, and then append all the create trigger actions to the TODO list, "
            "following the order of answer for Q3.\n"
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

    bonus_board_analysis = (
        "\n"
        "Permanents you (Ned Decker, AI) control are as follows:\n"
        "<triggered_when_untapped format=JSON>\n"
        "{triggered_when_untapped}\n"
        "</triggered_when_untapped>\n"
        "\n"
    )

    _input = (
        "Currently, NONE in the TODO list was done (all items are pending your action). Ned Decker (AI) will follow the TODO list. After all items in the TODO list are done, Ned Decker will pass the untap phase. However, if there is nothing to do in the TODO list, Ned Decker will pass the untap phase immediately."
    )

    improvement_prompt = (
        ""
    )

if __name__ == '__main__':
    print(UntapPromptPreset.chat_prompt)
    print(UntapPromptPreset.tools)
    print(UntapPromptPreset.tools_prompt)
    print(UntapPromptPreset.requests)
    print(UntapPromptPreset.bonus_requests)
    print(UntapPromptPreset.board_analysis)
    print(UntapPromptPreset.bonus_board_analysis)
    print(UntapPromptPreset._input)
    print(UntapPromptPreset.improvement_prompt)
