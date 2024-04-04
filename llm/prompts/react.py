PONDER_GUIDE = """Answer the following questions as best you can. ALWAYS follow the instructions step-by-step and fill in all the answers. STRICTLY adhere to the card oracle texts provided. MUST assume CARD is NULL if you haven't seen it before.
"""

TOOLS_GUIDE = """Complete the following requests as best you can. Always try to think through all actions first before taking an action with tools. You have access to the following tools:

    {tools}

STRICTLY use the following format:

TODO: translate the TODO list into [ {tool_names} ]; skip item if no action is needed
Thought: You must always think about what to do
Action: the action taken, should be one of [ {tool_names} ]
Action Input: the paremeters for the action taken
Observation: the result of the action
... (the "Thought -> Actions -> Action Input -> Observation" loop may happen zero to N times)
Thought: all done!
Action: the action to finish this phase
Observation: the last observation which requires you to interact with human
(follow the instructions from the last observation as your final response)

Begin!

TODO: (but I'm using any of [ {tool_names} ], and skipping those needed no action)
"""
