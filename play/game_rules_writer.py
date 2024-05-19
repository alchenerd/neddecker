from typing import List, Dict, Any, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()
from .rules import Rule


class AbilityResponse(BaseModel):
    """Parsed list of abilities."""
    abilities: list[str] = Field(description="separated list of abilities, with each ability having a single effect")

class AbilityTypeResponse(BaseModel):
    """Types of abilities."""
    abilitity_type: Literal['spell', 'static', 'activated', 'triggered'] = Field(description="type of a Magic: the Gathering ability")

class GherkinResponse(BaseModel):
    """Custom gherkin rule that describes an ability."""
    given: list[str] = Field(description="list of statements that checks the static game to determine whether When and Then statements fire; content starts with 'Given', 'And', or 'But'")
    when: list[str] = Field(description="list of statements that checks a todo list: List[any] of the game engine; content starts with 'When', 'And', or 'But'")
    then: list[str] = Field(description="list of statements that modifies the todo list representing an effect; content starts with 'Then', 'And', or 'But'")


class GameRulesWriter:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=4096)

    def write_rules(self, card: Dict[str, Any]) -> List[Rule]:
        abilities = self.get_abilities(card)
        print(abilities)
        for ability in abilities:
            ability_type = self.classify_ability(ability)
            print(repr(ability), 'is a', ability_type, 'ability')
            #gherkin = self.write_gherkin(ability)
            #print(gherkin)

    def get_abilities(self, card: Dict[str, Any]) -> List[str]:
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

    def classify_ability(self, ability: str) -> Literal['static', 'activated', 'triggered', 'delayed_triggered', 'mana']:
        CR_ABILITY_TYPE_DESCRIPTION = """113.3. There are four general categories of abilities:

113.3a Spell abilities are abilities that are followed as instructions while an instant or sorcery spell is resolving. Any text on an instant or sorcery spell is a spell ability unless it’s an activated ability, a triggered ability, or a static ability that fits the criteria described in rule 113.6.

113.3b Activated abilities have a cost and an effect. They are written as “[Cost]: [Effect.] [Activation instructions (if any).]” A player may activate such an ability whenever they have priority. Doing so puts it on the stack, where it remains until it’s countered, it resolves, or it otherwise leaves the stack. See rule 602, “Activating Activated Abilities.”

113.3c Triggered abilities have a trigger condition and an effect. They are written as “[Trigger condition], [effect],” and include (and usually begin with) the word “when,” “whenever,” or “at.” Whenever the trigger event occurs, the ability is put on the stack the next time a player would receive priority and stays there until it’s countered, it resolves, or it otherwise leaves the stack. See rule 603, “Handling Triggered Abilities.”

113.3d Static abilities are written as statements. They’re simply true. Static abilities create continuous effects which are active while the permanent with the ability is on the battlefield and has the ability, or while the object with the ability is in the appropriate zone. See rule 604, “Handling Static Abilities.”"""
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering ability rules text. You will classify the ability into one of a set of mutually exclusive categories."),
            ('system', CR_ABILITY_TYPE_DESCRIPTION),
            ('user', "Given the rules text {ability}, catergorize what kind of ability it is. If you are unsure, choose the better one of the choices."),
        ])
        model = self.llm.bind_tools([AbilityTypeResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityTypeResponse", first_tool_only=True)
        chain = prompt | model | parser
        return chain.invoke({'ability': ability})['abilitity_type']

    def write_gherkin(self, ability: str) -> List[str]:
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering ability rules text. You will write rules in the gherkin format that represents the ability."),
            ('user', "Given the rules text {ability}:\n\nWrite a gherkin rule with following restrictions:\n'Given' statements are checks on a static game object like zone of card or phase of the game; 'When' statements are checks on a `todo` list which is a List[Any] that holds all pending game actions that will happen at the next instant; 'Then' statements are modifications on `todo` that represents the effect of the ability.\n\nFor example, if an ability reads \"this doesn't untap.\", then the gherkin rule would be something like:\n\n``` gherkin\nGiven this is on the battlefield\nWhen \"this untaps\" if present in `todo`\nThen remove this infromation from `todo`\n```\n\n Here is the ability text in case you forgot: {ability}"),
        ])
        model = self.llm.bind_tools([GherkinResponse])
        parser = JsonOutputKeyToolsParser(key_name="GherkinResponse", first_tool_only=True)
        chain = prompt | model | parser
        response = chain.invoke({'ability': ability})
        return [str(gherkin_line) for gherkin_line in response.values()]
