import requests
import json
from typing import List, Dict, Any, Optional, Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator, ValidationError
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import RetryOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()
from .rules import Rule

# Comprehensive Rules
CR_ABILITY_TYPE_DESCRIPTION = """113.3. There are four general categories of abilities:

113.3a Spell abilities are abilities that are followed as instructions while an instant or sorcery spell is resolving. Any text on an instant or sorcery spell is a spell ability unless it’s an activated ability, a triggered ability, or a static ability that fits the criteria described in rule 113.6.

113.3b Activated abilities have a cost and an effect. They are written as “[Cost]: [Effect.] [Activation instructions (if any).]” A player may activate such an ability whenever they have priority. Doing so puts it on the stack, where it remains until it’s countered, it resolves, or it otherwise leaves the stack. See rule 602, “Activating Activated Abilities.”

113.3c Triggered abilities have a trigger condition and an effect. They are written as “[Trigger condition], [effect],” and include (and usually begin with) the word “when,” “whenever,” or “at.” Whenever the trigger event occurs, the ability is put on the stack the next time a player would receive priority and stays there until it’s countered, it resolves, or it otherwise leaves the stack. See rule 603, “Handling Triggered Abilities.”

113.3d Static abilities are written as statements. They’re simply true. Static abilities create continuous effects which are active while the permanent with the ability is on the battlefield and has the ability, or while the object with the ability is in the appropriate zone. See rule 604, “Handling Static Abilities.”"""

class AbilityResponse(BaseModel):
    """Parsed list of abilities rules text."""
    abilities: List[str] = Field(description="a list of abilities quoting the original rules text; separator is usually '.' or new line")

class AbilityTypeResponse(BaseModel):
    """Types of abilities."""
    abilitity_type: Literal['spell', 'activated', 'triggered', 'static'] = Field(description="type of a Magic: the Gathering ability")

class GherkinResponse(BaseModel):
    """Custom gherkin rule that describes an ability."""
    game_state_check: List[str] = Field(description="list of statements that checks the static game object to determine whether When and Then statements fire; your input must start with 'Given', 'And', or 'But'")
    game_event_check: List[str] = Field(description="list of statements that checks a todo list: List[any] of the game engine; your input must start with 'When', 'And', or 'But'")
    ability_effect_statement: List[str] = Field(description="list of statements that modifies the todo list representing an effect; your input must start with 'Then', 'And', or 'But'")

    """
    @validator('given')
    def must_start_with_given_keyword(cls, v):
        for line in v:
            if not any(line.lower().startswith(x) for x in ('given', 'and', 'but')):
                raise ValueError('Must start with \"Given\", \"And\" or \"But\"')

    @validator('when')
    def must_start_with_when_keyword(cls, v):
        for line in v:
            if not any(line.lower().startswith(x) for x in ('when', 'and', 'but')):
                raise ValueError('Must start with \"When\", \"And\" or \"But\"')

    @validator('then')
    def must_start_with_then_keyword(cls, v):
        for line in v:
            if not any(line.lower().startswith(x) for x in ('then', 'and', 'but')):
                raise ValueError('Must start with \"Then\", \"And\" or \"But\"')
    """

class YesNoResponse(BaseModel):
    """Answer a yes or no question."""
    yes_or_no: Literal['y', 'n'] = Field('yes or no; \"y\"for yes and \"n\" for no')

    @validator('yes_or_no')
    def must_use_y_or_n(cls, v):
        if not v in ('y', 'n'):
            raise ValueError('Must use either \'y\' or \'n\'')


class RevisedGherkinResponse(BaseModel):
    """Revised custom gherkin rule that describes an ability."""
    game_state_check: List[str] = Field(description="list of statements that checks the static game object to determine whether When and Then statements fire; your input must start with 'Given', 'And', or 'But'")
    game_event_check: List[str] = Field(description="list of statements that checks a todo list: List[any] of the game engine; your input must start with 'When', 'And', or 'But'")
    ability_effect_statement: List[str] = Field(description="list of statements that modifies the todo list representing an effect; your input must start with 'Then', 'And', or 'But'")
    explanation: Optional[str] = Field('explain your changes you\'ve made to the gherkin rule')


class GameRulesWriter:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=4096)
    seen = {}

    def __init__(self):
        self.keyword_actions = self.get_keyword_actions()
        self.keyword_abilities = self.get_keyword_abilities()
        self.db = Chroma(persist_directory='./rag', embedding_function=OpenAIEmbeddings())
        self.kw_to_cr_map = {}

    def write_rules(self, card: Dict[str, Any]) -> List[Rule]:
        abilities = self.get_abilities(card)
        print('[Abilities]:', abilities)
        rules = []
        for ability in abilities:
            if ability in self.seen:
                rules.append(self.seen[ability])
                continue
            #known_keywords = self.keyword_actions + self.keyword_abilities
            known_keywords = self.keyword_abilities
            detected_keywords = [kw for kw in known_keywords if kw.lower() in ability.lower()]
            print('[Detected keywords]:', detected_keywords)
            for kw in detected_keywords:
                if kw not in self.kw_to_cr_map:
                    self.kw_to_cr_map[kw] = self.get_comprehensive_rules_by_keyword_ability(kw)
            # mana ability
            is_mana_ability = self.is_mana_ability(ability=ability)
            print(repr(ability), 'is' if is_mana_ability else 'is not', 'a mana ability')
            # ability type
            ability_type = self.get_ability_type(ability=ability, detected_keywords=detected_keywords)
            print(repr(ability), 'is', \
                    'an' if any(ability_type.lower().startswith(x) for x in 'aeiou') else 'a', \
                    ability_type, 'ability')
            # play gherkin
            play_gherkin = self.write_gherkin(ability, detected_keywords, ability_type, 'play')
            play_gherkin = self.double_check_gherkin(card=card, ability=ability, gherkin=play_gherkin, ability_type=ability_type, gherkin_type='play')
            print('\n[Play Gherkin]:')
            print(play_gherkin)
            print()
            # resolve gherkin
            resolve_gherkin = self.write_gherkin(ability, detected_keywords, ability_type, 'resolve')
            resolve_gherkin = self.double_check_gherkin(card=card, ability=ability, gherkin=resolve_gherkin, ability_type=ability_type, gherkin_type='resolve')
            print('\n[Resolve Gherkin]:')
            print(resolve_gherkin)
            print()
        return rules

    def is_mana_ability(self, ability: str) -> bool:
        return 'add {' in ability.lower()

    def double_check_gherkin( \
            self, \
            card: Dict[str, Any], \
            ability: str, \
            gherkin: Optional[str], \
            ability_type: Literal['spell', 'activated', 'triggered', 'static'], \
            gherkin_type: Literal['play', 'resolve'], \
     ) -> Optional[str]:
        """Ask LLM again to check the gherkin rule; returns the best gherkin string."""
        if gherkin is None:
            return None
        prompt = ChatPromptTemplate.from_messages([
            ('system', 'You are a gherkin rules checker: you will be given a card, an ability that is a part of the card, the type of the ability (spell ability, activated ability, triggered ability, and static ability), the type of the rule (play rule, which is the rule that cares from proposing to play to the ability to be consider played, and resolve rule, which is the rule that care about the effect when the ability resolves), and the resultant gherkin rule. The rule is written in gherkin format, with the following rules:\n1. \"Given\" rules check the game state, especially the location of the game object and the timing in game such as phases and steps\n2. \"When\" rules check the event todo list, which records actions and effects that will happen in game in the next instant\n3. \"Then\" rules describe the effect of the ability; for most \"play\" rules, the end result is creating an ability object on the top of the stack rather than action, event, or effect - those will be handled in \"resolve\" rule\'s \"Then\" rules, where spell ability, activated ability, and triggered ability are processed when the ability object resolves\n\n4. In the written gherkin rule, tilde (\'~\') means \"thie game object\"\n\n5. In the written gherkin rule, the actor is usually \"controller\", \"owner\", \"opponent\", but never \"you\"\n\nYour role as the gherkin rules checker is to inspect all data given to you and determine if the gherkin rule describes the ability correctly.'),
            ('user', 'Card:\n{card}\n\nExtracted Ability:\n{ability}\n\nClassified Ability Type:\n{ability_type}\n\nWriting Gherkin Rules for:\n{gherkin_type}\n\nResultant Gherkin Rule:\n{gherkin}\n\n---\n\nGiven data above, answer yes(y) or no(n): Does this gherkin rule correctly describe the ability written on the card?'),
        ])
        model = self.llm.bind_tools([YesNoResponse])
        parser = JsonOutputKeyToolsParser(key_name='YesNoResponse', first_tool_only=True)
        chain = prompt | model | parser
        yn = chain.invoke({'card': card, 'ability': ability, 'ability_type': ability_type, 'gherkin_type': gherkin_type, 'gherkin': gherkin})
        print(yn)
        print('Double check:', 'LGTM' if yn.get('yes_or_no', 'n') == 'y' else 'Bad Rule')
        if yn.get('yes_or_no', 'n') == 'y':
            return gherkin
        # Revise the gherkin rule
        prompt = ChatPromptTemplate.from_messages([
            ('user', '{gherkin}\n\nThis gherkin rule was deemed incorrect.\n\nPlease revise the gherkin rule so that it better describes the ability on a card:\n\nCard:\n{card}\n\n{ability_type} Ability:\n{ability}\n\nPlease fix the fiven gherkin rule and state why.'),
        ])
        model = self.llm.bind_tools([RevisedGherkinResponse], tool_choice="RevisedGherkinResponse")
        parser = JsonOutputKeyToolsParser(key_name='RevisedGherkinResponse', first_tool_only=True)
        chain = prompt | model | parser
        response = chain.invoke({'gherkin': gherkin, 'card': card, 'ability': ability, 'ability_type': ability_type.title()})
        ret = []
        print(response)
        for key, item in response.items():
            if key in ('game_state_check', 'game_event_check', 'ability_effect_statement'):
                ret.extend(item)
        return '\n'.join(ret)

    def get_comprehensive_rules_by_keyword_ability(self, query) -> str:
        assert isinstance(query, str)
        raw_document = None
        with open('wotc/comprehensive_rules.txt') as f:
            raw_document = f.read()
        if not raw_document:
            raise FileNotFoundError()
        header = None
        filtered = []
        for line in raw_document.split('\n'):
            #print(line)
            if not header and f'. {query}' in line:
                title_line = line
                print(title_line)
                header = title_line.split(' ')[0][:-1]
                print(header)
            if header:
                if line.startswith(header):
                    filtered.append(line)
        print(filtered)
        ret = '\n'.join(filtered)
        ret = ret.replace('{', '{{').replace('}', '}}')
        return ret

    def get_keyword_actions(self) -> List[str]:
        response = requests.get('https://api.scryfall.com/catalog/keyword-actions')
        data = json.loads(response.content.decode('utf-8')).get('data')
        return data

    def get_keyword_abilities(self) -> List[str]:
        response = requests.get('https://api.scryfall.com/catalog/keyword-abilities')
        data = json.loads(response.content.decode('utf-8')).get('data')
        return data

    def get_abilities(self, card: Dict[str, Any]) -> List[str]:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            faces = card['faces']
            oracle_text = '---'.join(faces[face]['oracle_text'] for face in faces)
        rules_text = str(oracle_text)\
                .replace(card['name'], '~')\
                .replace('your', "controller's")\
                .replace('you', 'controller')
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering card's card text."),
            ('system', CR_ABILITY_TYPE_DESCRIPTION),
            ('user', "Given the rules text {rules_text}:\n\nHow many abilities are there in the rules text? Answer with the rules text."),
        ])
        model = self.llm.bind_tools([AbilityResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityResponse", first_tool_only=True)
        chain = prompt | model | parser
        return chain.invoke({'rules_text': rules_text})['abilities']

    def get_ability_type(self, ability: str, detected_keywords: List[str]) -> Literal['spell', 'activated', 'triggered', 'static']:
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering ability rules text. You will classify the ability into one of a set of mutually exclusive categories."),
            ('system', CR_ABILITY_TYPE_DESCRIPTION),
        ])
        keyword_knowledge = [('system', self.kw_to_cr_map[kw]) for kw in detected_keywords]
        print(keyword_knowledge)
        if keyword_knowledge:
            prompt.extend(keyword_knowledge)
        prompt.append(('system', "Keep in mind that an ability that allows the player to cast with an alternative cost is a static ability that functions when the spell is on the stack."))
        prompt.append(('user', "Given the rules text {ability}, catergorize what kind of ability it is. If you are unsure, choose the best one among them."))
        print('[Before invoke]:', prompt, ability)
        model = self.llm.bind_tools([AbilityTypeResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityTypeResponse", first_tool_only=True)
        chain = prompt | model | parser
        return chain.invoke({'ability': ability})['abilitity_type']

    def write_gherkin(self, ability: str, detected_keywords: List[str], ability_type: Literal['spell', 'activated', 'triggered', 'static'], gherkin_type: Literal['play', 'resolve']) -> List[str]:
        if ability_type == 'static' and gherkin_type == 'resolve':
            return None
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering rules text of an ability. You will write its rules in gherkin format that properly represent the ability."),
        ])
        # append relevant keyword knowledge
        keyword_knowledge = [('system', self.kw_to_cr_map[kw]) for kw in detected_keywords]
        if keyword_knowledge:
            prompt.extend(keyword_knowledge)
        # append writing rules
        prompt.append(('user', 'Writing Rule for the Actors Referred by the Ability: In the gherkin rule you write, refer to the players \"owner\", \"controller\", \"opponent\" so that the game enging can pinpoint who is who.'))
        prompt.append(('user', 'Writing Rule for referring to \"this object\": Use tilde (~) to represent the current object/this object/the object that has this ability.'))
        prompt.append(('user', "Note that activated ability and triggered ability will create a game object on the top of the stack that has the ability's effect's relevant rules text. Make sure the \"Then\" statements create the ability object instead of taking those game actions."))
        # append request
        prompt.append(('user', "Given the rules text {ability}:\n\nWrite a gherkin rule with following restrictions:\n'Given' statements are checks on a static game object like what zone the card is in (e.g. library, hand, battlefield, graveyard, exile, command), and/or the timing in game (e.g. phase, step, priority, could cast an instant, could cast a sorcery); 'When' statements are checks on an event list which is a List[Any] that holds all pending game events that will happen next; 'Then' statements are modifications on `todo` that represents the effect of the ability.\n\nFor example, if an ability reads \"this permanent doesn't untap.\", then the gherkin rule would be something like:\n\n``` gherkin\nGiven this is on the battlefield\nWhen \"this untaps\" if present in `todo`\nThen remove this infromation from `todo`\n```\n\n Here is the ability text in case you forgot: {ability}"))
        # generate gherkin template map
        template_gherkin = {x: {} for x in ('spell', 'activated', 'triggered', 'static')}
        template_gherkin['spell']['play'] = "Given ~ is in owner's [hand|graveyard|exile]\nAnd owner could [cast a sorcery|cast an instant|activate mana ability]\nWhen owner gets priority\nAnd owner chooses [choices specified by the ability, such as mode, alternative cost, additional cost, value of X, if any]\nAnd owner distributes [distribution actions specified by the ability, if any]\nAnd owner targets [targets specified by the ability, if any; each different target type uses a statement]\nAnd owner determines the cost [total cost if you can determine it]\nAnd owner pays the cost [total cost of you can determine it]\nThen ~ is cast"
        template_gherkin['spell']['resolve'] = "Given ~ is the topmost object of the stack\nAnd ~ is not countered\nWhen ~ resolves\nThen [ability effect; each atomic game action uses a statement]"
        template_gherkin['activated']['play'] = "Given ~ is [on the battlefield|in owner's hand|any zone that this ability could be activated\nAnd [owner|opponent|any player] could [cast a sorcery|cast an instant|activate mana ability]\nWhen [owner|opponent|any player] gets priority\nAnd [owner|opponent|any player] chooses [choices specified by the ability, such as mode, alternative cost, additional cost, value of X, if any]\nAnd [owner|opponent|any player] distributes [distribution actions specified by the ability, if any]\nAnd [owner|opponent|any player] targets [targets specified by the ability, if any; each different target type uses a statement]\nAnd [owner|opponent|any player] determines the cost [total cost if you can determine it]\nAnd [owner|opponent|any player] pays the cost [total cost of you can determine it]\nThen ~ is activated\nAnd put an activated ability that says [the rules text that describes the effect the ability has] on the top of the stack"
        template_gherkin['activated']['resolve'] = "Given an activated ability that says [the rules text that describes the effect the ability has] is the topmost object of the stack\nAnd the ability that says [the rules text that describes the effect the ability has] is not countered\nWhen the activated ability that says [the rules text that describes the effect the ability has] resolves\nThen [ability effect; each atomic game action uses a Then statement; actions that happen at the same time are grouped using the And keyword; sequential actions are separated using the Then keyword]"
        template_gherkin['triggered']['play'] = "Given ~ is [on the battlefield|in owner's hand|any zone that this ability could be triggered\nWhen [the requirements of the triggered ability; each atomic check uses a When statement]\nThen ~ is triggered\nAnd put a triggered ability that says [the rules text that describes the effect the ability has] on top of the stack"
        template_gherkin['triggered']['resolve'] = "Given a triggered ability that says [the rules text that describes the effect the ability has] is the topmost object of the stack\nAnd the triggered ability that says [the rules text that describes the effect the ability has] is not countered\nWhen the triggered ability that says [the rules text that describes the effect the ability has] resolves\nThen [ability effect; each atomic game action uses a statement; actions that happen at the same time are grouped using the And keyword; sequential actions are separated using the Then keyword]"
        template_gherkin['static']['play'] = "Given [the zone check that the static ability would work]\nThen [ability effect; each atomic game effect uses a statement; actions that happen at the same time are grouped using the And keyword; sequential actions are separated using the Then keyword]"
        prompt.append(('system', 'Here is an automatically generated gherkin rule template that you can make changes from for your information:\n\n{}'.format(template_gherkin[ability_type][gherkin_type])))

        model = self.llm.bind_tools([GherkinResponse])
        parser = JsonOutputKeyToolsParser(key_name='GherkinResponse')
        #parser = PydanticOutputParser(pydantic_object=GherkinResponse)
        #retry_parser = RetryOutputParser.from_llm(parser=parser, llm=self.llm)
        chain = prompt | model | parser
        #main_chain = RunnableParallel(completion=chain, prompt_value=prompt) | \
        #        RunnableLambda(lambda x: retry_parser.parse_with_prompt(**x))
        responses = chain.invoke({'ability': ability})
        print(responses)
        ret = []
        for response in responses:
            for item in response.values():
                ret.extend(item)
        return '\n'.join(ret)

    def ask_yes_no(self, context, question):
        prompt = ChatPromptTemplate.from_messages([
            ('user', context),
            ('user', '{question}'),
        ])
        model = self.llm.bind_tools([YesNoResponse], tool_choice='YesNoResponse')
        parser = JsonOutputKeyToolsParser(key_name='YesNoResponse', first_tool_only=True)
        chain = prompt | model | parser
        yn = chain.invoke({'question': question.replace('{', '{{').replace('}', '}}')})
        print(question)
        print(yn)
        return yn.get('yes_or_no', 'n') if yn else 'n'
