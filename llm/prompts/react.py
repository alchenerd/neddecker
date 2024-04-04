PONDER_GUIDE = """Answer the following questions as best you can. Always follow the instructions step-by-step and fill in all the answers.
"""

TOOLS_GUIDE = """Complete the following requests as best you can. Always try to think through all actions first before taking an action with tools. You have access to the following tools:

    {tools}

Use the following format:

TODO: write down the TODO list provided, but using any of the [ {tool_names} ] instead
Thought: You must always think about what to do
Actions: the action taken, should be one of [ {tool_names} ]
Action Input: the paremeters for the action taken
Observation: the result of the action
... (the "Thought -> Actions -> Action Input -> Observation" loop may happen N times)
Observation: the last observation which requires you to interact with human
Final Response: follow the instructions from the last observation

Begin!

TODO:
"""
