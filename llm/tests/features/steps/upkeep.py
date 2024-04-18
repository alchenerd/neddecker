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
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor

@given(u'the AI player for upkeep step is GPT from OpenAI')
def step_impl(context):
    context.llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=1024)
    #context.llm = ChatOpenAI(model_name='gpt-4', temperature=0, max_tokens=1024)
    context.chat_prompt = UPP.chat_prompt
    context.tools = UPP.tools
    assert context.tools
    context.tools_prompt = UPP.tools_prompt
    context.memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', return_messages=True)
    context.requests = UPP.requests
    context.agent_executor = CSAgentExecutor(
            llm=context.llm,
            chat_prompt=context.chat_prompt,
            tools_prompt=context.tools_prompt,
            tools=context.tools,
            memory=context.memory,
            requests=context.requests,
            verbose=True,
    )


@given(u'the AI player has no permanent that has an upkeep trigger')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the AI player has no permanent that has an upkeep trigger')


@when(u'the system asks the AI player for upkeep decisions')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the system asks the AI player for upkeep decisions')


@given(u'the AI player has one permanent that has an upkeep trigger')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the AI player has one permanent that has an upkeep trigger')


@then(u'the AI player creates one upkeep trigger')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player creates one upkeep trigger')


@given(u'the AI player has two permanents that has an upkeep trigger')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the AI player has two permanents that has an upkeep trigger')


@then(u'the AI player creates two upkeep triggers')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player creates two upkeep triggers')
