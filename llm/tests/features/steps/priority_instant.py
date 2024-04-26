from behave import *
import json
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from llm.prompts.upkeep import UpkeepPromptPreset as UPP
from llm.prompts.priority_instant import PriorityInstantPromptPreset as PIPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor


@given(u'the AI player receiving priority (instant speed) is GPT from OpenAI')
def step_impl(context):
    context.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=1024)
    #context.llm = ChatOpenAI(model_name='gpt-4', temperature=0, max_tokens=1024)
    context.chat_prompt = PIPP.chat_prompt
    context.tools = PIPP.tools
    assert context.tools
    context.tools_prompt = PIPP.tools_prompt
    context.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
    context.requests = PIPP.requests
    context.agent_executor = CSAgentExecutor(
            llm=context.llm,
            chat_prompt=context.chat_prompt,
            tools_prompt=context.tools_prompt,
            tools=context.tools,
            memory=context.memory,
            requests=context.requests,
            verbose=True,
    )


@given(u'the AI player receives a board state')
def step_impl(context):
    """ board analysis needs:
    {opponent_battlefield}
    {self_battlefield}
    {self_hand}
    {self_graveyard}
    {opponent_graveyard}
    {self_exile}
    {opponent_exile}
    {current_phase}
    {whose_turn}
    """
    raise NotImplementedError(u'STEP: Given the AI player receives a board state')


@when(u'the system asks the AI player for instant speed decisions')
def step_impl(context):
    """ board analysis needs:
    {opponent_battlefield}
    {self_battlefield}
    {self_hand}
    {self_graveyard}
    {opponent_graveyard}
    {self_exile}
    {opponent_exile}
    {current_phase}
    {whose_turn}
    """
    raise NotImplementedError(u'STEP: When the system asks the AI player for instant speed decisions')
