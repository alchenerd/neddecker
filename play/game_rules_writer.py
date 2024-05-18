from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from .rules import Rule


class AbilityResponse(BaseModel):
    """Response about abilities."""
    abilities: List[str] = Field(description="separated list of abilities, with each ability having a single effect")


class GameRulesWriter:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=4096)

    def get_abilities(self, card: Dict[str, Any]) -> List[Rule]:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            faces = card['faces']
            oracle_text = '---'.join(faces[face]['oracle_text'] for face in faces)
        rules_text = str(oracle_text).replace(card['name'], 'this')
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering card's card text."),
            ('user', "Given the rules text {rules_text}:\n\nHow many abilities are there in the rules text?"),
        ])
        model = self.llm.bind_tools([AbilityResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityResponse", first_tool_only=True)
        chain = prompt | model | parser
        return chain.invoke({'rules_text': rules_text})['abilities']
