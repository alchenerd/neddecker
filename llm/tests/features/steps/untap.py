from behave import *
from langchain_openai import ChatOpenAI
from langchain.chains.conversation.memory import ConversationBufferMemory
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../../../')
rootdir = os.path.dirname(currentdir + '/../../../../')
sys.path.insert(0, rootdir)
import payload
from llm.prompts.untap import UntapPromptPreset as UPP
from llm.agents.agent import ChatAndThenSubmitAgentExecutor as CSAgentExecutor

@given(u'the AI player for untap step is GPT from OpenAI')
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


@given(u'there is no card to prevent from untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there is no card to prevent from untapping')


@when(u'the system asks the AI player for prevent untap decisions')
def step_impl(context):
    raise NotImplementedError(u'STEP: When the system asks the AI player for prevent untap decisions')


@given(u'there is one card that doesn\'t untap because of oracle text')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there is one card that doesn\'t untap because of oracle text')


@then(u'the AI player chooses to prevent the card\'s untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent the card\'s untapping')


@given(u'there are three cards that don\'t untap because of oracle text')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there are three cards that don\'t untap because of oracle text')


@then(u'the AI player chooses to prevent those cards\' untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent those cards\' untapping')


@given(u'the AI player is set to skip the untap step')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given the AI player is set to skip the untap step')


@then(u'the AI player chooses to prevent all controlled cards\' untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent all controlled cards\' untapping')


@given(u'there is one card that was annotated as doesn\'t untap')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there is one card that was annotated as doesn\'t untap')


@given(u'there are three cards that were annotated as doesn\'t untap')
def step_impl(context):
    raise NotImplementedError(u'STEP: Given there are three cards that were annotated as doesn\'t untap')


@then(u'the AI player chooses to prevent the three card\'s untapping')
def step_impl(context):
    raise NotImplementedError(u'STEP: Then the AI player chooses to prevent the three card\'s untapping')
