from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain.agents import create_openai_tools_agent
from langchain.agents.agent import AgentExecutor
from langchain.chains import LLMChain
from langchain.prompts.chat import MessagesPlaceholder
from langchain.pydantic_v1 import ValidationError

import os
import sys
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
llmrootdir = os.path.dirname(currentdir + '/../')
rootdir = os.path.dirname(currentdir + '/../../')
sys.path.insert(0, rootdir)
import payload

def handle_error(error):
    print('Trying to handle my custom error')
    if isinstance(error, ValueError):
        return str(error)
    if isinstance(error, ValidationError):
        return str(error)
    raise error

class ChainOfThoughtAgentExecutor():
    """Agent Executor that aims to retrieve Chain of thought history.
    May include tools that help the AI to better make decisions.
    """
    def __init__(self, llm, prompt, memory, requests=[], verbose=True):
        self.llm = llm
        self.prompt = prompt
        self.memory = memory
        self.verbose = verbose
        self.requests = requests
        self.chain = LLMChain(
                llm=self.llm,
                prompt=self.prompt,
                memory=self.memory,
                verbose=verbose,
        )

    def request(self, data=None):
        for request in self.requests:
            resp = self.chain.invoke({'input': request, 'data': data})
            print(resp['text'])
        return resp['text']

    def invoke(self, _input):
        resp = self.chain.invoke(_input)
        print(resp['text'])
        return resp['text']

class SubmitAgentExecutor():
    """Agent Executor that have the AI call submit tool(s) based on memory.
    Require at least one tool for submission.
    """
    def __init__(self, llm, prompt, tools, memory, requests, verbose=True, handle_parsing_errors=True):
        self.llm = llm
        self.prompt = prompt + MessagesPlaceholder("agent_scratchpad")
        self.tools = tools
        self.memory = memory
        self.verbose = verbose
        self.requests = requests
        self.agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.chain = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                prompt=self.prompt,
                memory=self.memory,
                verbose=self.verbose,
                handle_parsing_errors=handle_parsing_errors,
        )

    def request(self, data=None):
        for request in self.requests:
            resp = self.chain.invoke({'input': request, 'data': data})
            print(resp['output'])
        return resp['output']

    def invoke(self, _input):
        return self.chain.invoke(_input)

class ChatAndThenSubmitAgentExecutor():
    """Agent Executor that have the AI chat and then submit.
    Require at least one tool for submission.
    """
    def __init__(self, llm, chat_prompt, tools_prompt, tools, memory, requests=[], verbose=True, handle_parsing_errors=True):
        self.memory = memory
        if chat_prompt:
            self.chatter = ChainOfThoughtAgentExecutor(
                    llm=llm,
                    prompt=chat_prompt,
                    memory=self.memory,
                    requests=requests,
                    verbose=verbose,
            )
        if tools:
            self.submitter = SubmitAgentExecutor(
                    llm=llm,
                    prompt=tools_prompt,
                    tools=tools,
                    memory=self.memory,
                    requests=requests,
                    verbose=verbose,
                    handle_parsing_errors=handle_error,
            )

    def invoke(self, _input):
        if self.chatter and self.submitter:
            self.chatter.request(_input.get('data', None))
            return self.submitter.invoke(_input)
        return ""
