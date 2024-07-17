import requests
import json
import re
from typing import List, Dict, Any, Optional, Literal
from collections import OrderedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field, validator, ValidationError
from langchain.output_parsers.openai_tools import JsonOutputKeyToolsParser
from langchain_core.output_parsers.openai_tools import PydanticToolsParser
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain.output_parsers import RetryOutputParser
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_chroma import Chroma
from django.db.models import CharField, Value, F
from dotenv import load_dotenv
load_dotenv()
from .rules import Rule
from .models import GameRule, GherkinRule, GherkinImpl, get_card_orm_by_name

# Comprehensive Rules
CR_ABILITY_TYPE_DESCRIPTION = """113.3. There are four general categories of abilities:

113.3a Spell abilities are abilities that are followed as instructions while an instant or sorcery spell is resolving. Any text on an instant or sorcery spell is a spell ability unless it’s an activated ability, a triggered ability, or a static ability that fits the criteria described in rule 113.6.

113.3b Activated abilities have a cost and an effect. They are written as “[Cost]: [Effect.] [Activation instructions (if any).]” A player may activate such an ability whenever they have priority. Doing so puts it on the stack, where it remains until it’s countered, it resolves, or it otherwise leaves the stack. See rule 602, “Activating Activated Abilities.”

113.3c Triggered abilities have a trigger condition and an effect. They are written as “[Trigger condition], [effect],” and include (and usually begin with) the word “when,” “whenever,” or “at.” Whenever the trigger event occurs, the ability is put on the stack the next time a player would receive priority and stays there until it’s countered, it resolves, or it otherwise leaves the stack. See rule 603, “Handling Triggered Abilities.”

113.3d Static abilities are written as statements. They’re simply true. Static abilities create continuous effects which are active while the permanent with the ability is on the battlefield and has the ability, or while the object with the ability is in the appropriate zone. See rule 604, “Handling Static Abilities.”"""

class AbilityResponse(BaseModel):
    """Parsed list of abilities rules text."""
    abilities: List[str] = Field(description="a list of interpreted abilities derived from the rules text")

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
    yes_or_no: Literal['y', 'n'] = Field('response to a yes-or-no question; answer \"y\"for yes or \"n\" for no')

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


class DelayedTriggerWhenWhatResponse(BaseModel):
    """Describes the 'when' and 'what' of a delayed triggered ability."""
    trigger_when: str = Field(description="when will the delayed triggered ability be triggered in game")
    trigger_what: str = Field(description="the content of the trigger when the delayed ability is triggered")


class WriteRegexResponse(BaseModel):
    """Submits a regex response."""
    regex_expression: str = Field(description="the regex expression that can match the ability from the card text")
    matches_example: str = Field(description="a mock rules text that the regex expression would match")

class MultiWriteRegexResponse(BaseModel):
    """Submits one or more regex responses."""
    regex_list: List[WriteRegexResponse] = Field(description="one or more expressions that can match the ability (and its variants, if any) from the card text")

class GameRulesWriter:
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0, max_tokens=4096)
    seen = {}

    def __init__(self):
        self.keyword_actions = self.get_keyword_actions()
        self.keyword_abilities = self.get_keyword_abilities()
        self.db = Chroma(persist_directory='./rag', embedding_function=OpenAIEmbeddings())
        self.kw_to_cr_map = {}

    def write_simple_rules(self, card_name, splitted_text):
        print(splitted_text)
        card_representation = "Card name: {card_name}\n\n<oracle>\n{oracle_text}\n</oracle>"
        instruction = "Given the above oracle text from a Magic: the Gathering card, write its implementation logic in gherkin syntax"
        rules = '\n'.join((
                "Gherkin Writing Rules:\n",
                "1. \"Given\" statements will check static game data, \"When\" statements will check actions, and \"Then\" statements will describe the effect",
                "2. All gherkins MUST have a scenario title that uses this format: \"[<Static/Activated/Triggered/Spell/Mana> Ability] - <Related Rule Text>\"; E.G.: `Scenario: [Mana Ability] - Add {{R}}. Spend this mana only to cast creature spells.`",
                "3. Respond only using the gherkin format that is easy to parse",
                "4. Do not use any punctuation at the end of each gherkin statement",
                "5. If you are writing for a triggered ability or an activated ability, DO NOT write gherkin as-is; instead, say something like \'create an <XYZ> ability on the stack that says \"<ability content>\"\'; this way we can allow player to respond to the ability",
                "6. Triggered ability will have `Then` clause `Then create a triggered ability on the stack that says...`",
                "7. Delayed triggered ability will have `Then` clause `Then create a delayed triggered ability on the stack that says...`, where the content is the rule text of the created triggered ability",
                "8. Activated ability will have `Then` clause `Then create an activated ability on the stack that says...`",
                "9. If you wrote a \"created ability on the stack\" ability, you will need to also write a gherkin rule for resolving that ability on the stack, using scenario title with type `Resolve Ability`; E.G.: `Scenario: [Resolve Ability] - Resolve \"Target player gains 3 life.\"`"
                "10. Baseline Scenario: The baseline gherkin scenario for a card is as follows\n``` gherkin\nGiven <card_name> is in a zone where a player can interact with\nWhen <player_type> interacts with <card_name>\nThen <what_happens_next, usually replace the event ['interact', card] with one of ['cast', card], ['activate', card], ['play_land', card]>; replace everything inside <> with whatever appropriate\""
        ))
        possible_presets = '\n'.join((
                "Possible Abilities You May Encounter:\n",
                "1. static ability that allows/disallows the player play the card",
                    "(...When player receives priority ... Then player may cast...)",
                "2. static ability that modifies the characteristics of a card or permanent",
                    "(...When the game checks State-Based Actions ... Then ~ has...)",
                "3. triggered ability that creates a triggered ability on top of the stack when condition is met",
                    "(...When [condition] ... Then create a triggered ability that says...)",
                "4. delayed triggered ability that creates an effect that could be triggered in the future",
                    "(...When [condition] ... Then create a delayed triggered ability that says...)",
                "5. mana ability that adds mana to a player's mana pool and doesn't use the stack nor targets anything",
                    "(...Then add [mana description, add restrictions if needed] to player's mana pool) // does not use the stack",
        ))

        prompt = ChatPromptTemplate.from_messages([
            ('user', '\n\n'.join((card_representation, instruction, rules, possible_presets)))
        ])
        chain = prompt | self.llm | StrOutputParser()
        ret = []
        for text in splitted_text:
            response = chain.invoke({'card_name': card_name, 'oracle_text': text})
            print(f'{response=}')
            reserved = ('scenario', 'given', 'when', 'then', 'and', 'but')
            gherkin = [line for line in response.split('\n') if any(line.lower().startswith(x) for x in reserved)]
            ret.append('\n'.join(gherkin))
        return ret

    def write_rules(self, card: Dict[str, Any]) -> List[Rule]:
        card_orm = get_card_orm_by_name(card.get('name'))
        try:
            gherkin_query_set = GherkinRule.objects.get(card=card_orm)
        except GherkinRule.DoesNotExist:
            rules_texts = self.split_rules_text(card)
            rule_gherkin = self.write_simple_rules(card.get('name', 'undefined'), rules_texts)
            GherkinRule.objects.create(card=card_orm, gherkin='\n\n'.join(rule_gherkin))
            return rule_gherkin
        return gherkin_query_set.gherkin.split('\n\n')

        """
        print('[Rules Texts]:', rules_texts)
        abilities = self.interpret_abilities(rules_texts)
        print('[Abilities]:', abilities)
        rules = []
        for ability in abilities:
            # check if our database has this ability
            rule_query_set = GameRule.objects.annotate(value=Value(ability, output_field=CharField())
                                                       ).filter(value__regex=F('ability_regex_expression'))
            if rule_query_set.exists():
                rule_query_set = rule_query_set.order_by('gherkin_order')
                first_rule = rule_query_set.first()
                rule = {'ability': ability, 'ability_type': first_rule.ability_type, 'gherkins': [], 'lambdas': []}
                for obj in rule_query_set:
                    rule['gherkins'].append(obj.gherkin)
                    rule['lambdas'].append(obj.lambda_code)
                if ability not in self.seen:
                    self.seen[ability] = rule
                rules.append(rule)
                continue
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
            #play_gherkin = self.double_check_gherkin(card=card, ability=ability, gherkin=play_gherkin, ability_type=ability_type, gherkin_type='play')
            print('\n[Play Gherkin]:')
            print(play_gherkin)
            print()
            # resolve gherkin
            resolve_gherkin = self.write_gherkin(ability, detected_keywords, ability_type, 'resolve')
            #resolve_gherkin = self.double_check_gherkin(card=card, ability=ability, gherkin=resolve_gherkin, ability_type=ability_type, gherkin_type='resolve')
            print('\n[Resolve Gherkin]:')
            print(resolve_gherkin)
            print()
            i = 0
            rule = {'ability': ability, 'ability_type': ability_type, 'gherkins': [], 'lambdas': []}
            for gherkin in (play_gherkin, resolve_gherkin):
                if not gherkin:
                    continue
                for line in gherkin.split('\n'):
                    rule['gherkins'].append(line)
                    rule['lambdas'].append('lambda context: None')
                    GameRule.objects.create(ability_regex_expression=ability, ability_type=('mana' if is_mana_ability else ability_type), gherkin=line, gherkin_order=i, lambda_code='lambda context: None')
                    i += 1
            self.seen[ability] = rule
            rules.append(rule)
        return rules
        """

    def is_mana_ability(self, ability: str) -> bool:
        return 'add {' in ability.lower() and 'target' not in ability.lower()

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

    def get_oracle_text(self, card: Dict[str, Any]) -> str:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            faces = card['faces']
            oracle_text = '\n'.join(faces[face]['oracle_text'] for face in faces)
        name = card['name']
        front_name = card.get('faces', {}).get('front', card['name'])
        # In case of no back side, we need a name that WotC will never ever print on a card.
        # WotC will never tell players to shread themselves, right?
        # ...right?
        back_name = card.get('faces', {}).get('back', 'Form of the Chaos Confetti')
        return oracle_text.replace('{', '{{').replace('}', '}}')
        oracle_text = str(oracle_text) \
                .replace(name, '~') \
                .replace(front_name, '~') \
                .replace(back_name, '~') \
                .replace('your', "controller's") \
                .replace('you', 'controller') \
                .lower()
        return oracle_text

    def group_listed_text(self, rules_texts: List[str]) -> List[str]:
        """ Some rules text on the card represents a table or a list.
        They and the previous word chunk will be merged into one single ability text. """
        ret = []
        buffer = []
        for line in rules_texts:
            if '|' in line:
                buffer.append(line)
            elif '•' in line:
                buffer.append(line)
            elif buffer:
                ret[-1] = ret[-1] + '\n'.join(buffer)
                buffer = []
            else:
                ret.append(line)
        return ret

    def split_rules_text(self, card: Dict[str, Any]) -> List[str]:
        oracle_text = self.get_oracle_text(card)
        splitted = oracle_text.split('\n')
        grouped = self.group_listed_text(splitted)
        # from this point oracle_text becomes rules_text that one element maps to one or more abilities
        return grouped

    def write_regex(self, info: str, example: str) -> List[str]:
        """ Write a regex expression using the information given. """
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are a skilled, competent regex writing expert. You will be given rules about a specific Magic: the Gathering ability. Write the regex expression that will match the described ability from card texts."),
            ('user', '{info}'),
            ('user', 'Regex expressions for one-word or one-phrase abilities should be wrapped with word boundaries.'),
            ('user', "Also, keep in mind that there won't be any square brackets in actual card texts (except for the special-case abiliity 'Cleave'.)"),
            ('user', "Example target card text: {example}"),
        ])
        model = self.llm.bind_tools([MultiWriteRegexResponse])
        parser = JsonOutputKeyToolsParser(key_name="MultiWriteRegexResponse", first_tool_only=True)
        chain = prompt | model | parser
        reply = chain.invoke({'info': info, 'example': example})
        print('LLM replies:', reply)
        try:
            regex_list = reply['regex_list']
            ret = [regex['regex_expression'] for regex in regex_list]
        except:
            ret = None
        return ret or ['',]

    def interpret_abilities(self, rules_texts: List[str], additional_information=None) -> List[str]:
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering card's card text."),
            ('system', CR_ABILITY_TYPE_DESCRIPTION),
        ])
        if additional_information:
            prompt.append(('system', '{additional_information}'))
        prompt.append(('user', "Given the rules text \"{rules_text}\", interpret the rules text into one or more abilities."))
        model = self.llm.bind_tools([AbilityResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityResponse", first_tool_only=True)
        chain = prompt | model | parser
        ret = []
        for rules_text in rules_texts:
            parameters = {'rules_text': rules_text}
            if additional_information:
                parameters['additional_information'] = additional_information
            abilities = chain.invoke(parameters)['abilities']
            ret.extend(abilities)
        return ret

    def get_ability_type(self, ability: str, detected_keywords: List[str]) -> Literal['spell', 'activated', 'triggered', 'static']:
        # 1. an ability with a colon is an activated ability
        if ':' in ability:
            return 'activated'

        # 2. an ability with 'when', 'whenever', 'at' is a triggered ability
        triggered_expression = r'\b(when|whenever|at)\b'
        re_reply = re.match(triggered_expression, ability.lower())
        if re_reply:
            return 'triggered'

        # 3. LLM fallback
        prompt = ChatPromptTemplate.from_messages([
            ('system', "You are given a Magic: the Gathering ability rules text. You will classify the ability into one of a set of mutually exclusive categories."),
            ('system', CR_ABILITY_TYPE_DESCRIPTION),
        ])

        keyword_knowledge = [('system', self.kw_to_cr_map[kw]) for kw in detected_keywords]
        print(keyword_knowledge)
        if keyword_knowledge:
            prompt.extend(keyword_knowledge)

        prompt.append(('system', "Keep in mind that an ability that is continuously true when it's in a zone would be count as a static ability."))
        prompt.append(('user', "Given the rules text {ability}, catergorize what kind of ability it is. If you are unsure, choose the best one among them."))

        print('[Before invoke]:', prompt, ability)

        model = self.llm.bind_tools([AbilityTypeResponse])
        parser = JsonOutputKeyToolsParser(key_name="AbilityTypeResponse", first_tool_only=True)
        chain = prompt | model | parser

        return chain.invoke({'ability': ability})['abilitity_type']

    def write_lambda(self, gherkin_rule, gherkin_line, gherkin_type) -> str:
        basic_game_knowledge = (
                "You may access the game state via `context.game`\n"
                "`context.game` is a class `Game` defined as below:\n"
                "``` python\n"
                "class Game:\n"
                "    def __init__(self):\n"
                "       self.has_ended = False\n"
                "       self.players: List[Player] = []\n"
                "       self.stack: List[Card] = []\n"
                "       self.pending_triggers: List[Card] = []\n"
                "       self.turn_count = 1\n"
                "       self.whose_turn = '' # player.player_name: str\n"
                "       self.phase = ''\n"
                "       self.whose_priority = '' # player.player_name: str\n"
                "       self.static_effects = []\n"
                "```\n"
                "Player is also a class:\n"
                "``` python\n"
                "class Player:\n"
                "    def __init__(self):\n"
                "        self.player_name: str = '' # 'ned' or 'user'\n"
                "        self.player_type: str = '' # 'human' or 'ai'\n"
                "        self.sideboard: List[Card] = []\n"
                "        self.library: List[Card] = []\n"
                "        self.battlefield: List[Card] = []\n"
                "        self.hand: List[Card] = []\n"
                "        self.graveyard: List[Card] = []\n"
                "        self.exile: List[Card] = []\n"
                "        self.command: List[Card] = [] # command zone\n"
                "        self.ante: List[Card] = []\n"
                "        self.mana_pool = {'W': 0, 'U': 0, 'B': 0, 'R': 0, 'G': 0, 'C': 0}\n"
                "        self.hp = 20\n"
                "        self.counters = {} # counters on the player\n"
                "        self.annotations = {} # annotations on the player\n"
                "        self.delayed_triggers: List[Card] = []\n"
                "        self.land_played = 0 # land played this turn\n"
                "```\n"
                "Each `card` is a nested dict() that has this default value:\n"
                "``` python\n"
                "card = {\n"
                "    'name': 'Some Card Name',\n"
                "    'cmc': 0.0, # float data type\n"
                "    'colors': \"['W','U','B','R','G']\" # also C for colorless,\n"
                "    'mana_cost': '{4}{G}{G}',\n"
                "    'type_line': 'Creature - Dinosaur',\n"
                "    'oracle_text': 'Trample',\n"
                "    'power': '6', # str data type\n"
                "    'toughness': '6', # str data type\n"
                "    'produced_mana': \"['W','U','B','R','G']\" # also C for colorless,\n"
                "    'loyalty': '6', # for planeswalkers\n"
                "    'defense': '6', # for battles\n"
                "    'in_game_id': 'n12#3', # 'n' for ned and 'u' for user, number before '#' is serial and number after '#' is copy count\n"
                "    'counters': {'+1/+1': 0},\n"
                "    'annotations': {'isTapped': False, 'isFlipped': False, 'isPhasedOut': False, 'isFaceDown': False},\n"
                "    'faces': {\n"
                "        'front': {},\n"
                "        'back': {},\n"
                "    },\n"
                "}\n"
                "```\n"
        )
        assert type(basic_game_knowledge) == str
        basic_game_knowledge = basic_game_knowledge.replace('{', '{{').replace('}', '}}')
        match gherkin_type:
            case 'given':
                request = "Given the full gherkin rule {gherkin_rule} and the current line {gherkin_line}, write a lambda function `lambda context: ...` that returns `bool`. This lambda would mainly check `context.game`."
            case 'when':
                request = "Given the full gherkin rule {gherkin_rule} and the current line {gherkin_line}, write a lambda function `lambda context: ...` that returns `bool`. This lambda would mainly check `context.matched_event`, which is `List[Union[str, card, Player]]`. For instance, a matched event could be `['resolve', card]` or `['tap', card]` or `['deal_damage', Player, 3]`."
            case 'then':
                request = (
                    "Given the full gherkin rule {gherkin_rule} and the current line {gherkin_line}, write a lambda function `lambda context: ...` that returns a modified frozen list `context.events`, which is `List[List[Union[str, card, Player]]]`. Here are some example list elements that you can put into the `context.events` list:\n"
                    "``` python\n"
                    "['ask', Player, question: str, answer_key: str] # after the player answers, the answer will be accessible in the future at `card['annotations'][answer_key]`."
                    "['create_copy', card]\n"
                    "['create_token', {{...}}]\n"
                    "['create_trigger, controller: Player, trigger_content: str']\n"
                    "['create_delayed_trigger, controller: Player, trigger_content: str']\n"
                    "['move', card, from: str, to: str]\n"
                    "['set_counter', card, counter_type: str, counter_amount: str]\n"
                    "['set_annotation', card, annotation_key: str, annotation_value: str]\n"
                    "['set_player_counter', Player, counter_type: str, counter_amount: str]\n"
                    "['set_player_annotation', Player, annotation_key: str, annotation_value: str]\n"
                    "['prevent_untap', card]\n"
                    "['set_mana', Player, mana_color: str, mana_restrictions: Optional[str]]\n"
                    "['set_hp', Player, amount: int]\n"
                    "```\n"
                )
        prompt = ChatPromptTemplate.from_messages(
            [
                ('user', basic_game_knowledge),
                ('user', request),
            ]
        )
        model = self.llm
        parser = StrOutputParser()
        chain = prompt | model | parser
        response = chain.invoke({'gherkin_rule': gherkin_rule, 'gherkin_line': gherkin_line})
        response = response.split('lambda context:')[-1]
        response = 'lambda context:' + response
        response = response.split('```')[0]
        return response or "lambda x: exec('raise NotImplementedError())'"

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
        template_gherkin['activated']['play'] = "Given ~ is [on the battlefield|in owner's hand|any zone that this ability could be activated\nAnd [owner|opponent|any player] could [cast a sorcery|cast an instant|activate mana ability] (default is cast an instant)\nWhen [owner|opponent|any player] gets priority\nAnd [owner|opponent|any player] chooses [choices specified by the ability, such as mode, alternative cost, additional cost, value of X, if any]\nAnd [owner|opponent|any player] distributes [distribution actions specified by the ability, if any]\nAnd [owner|opponent|any player] targets [targets specified by the ability, if any; each different target type uses a statement]\nAnd [owner|opponent|any player] determines the cost [total cost if you can determine it]\nAnd [owner|opponent|any player] pays the cost [total cost of you can determine it]\nThen ~ is activated\nAnd put an activated ability that says [the rules text that describes the effect the ability has] on the top of the stack"
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

    def get_start_of_game_delayed_trigger_ability(self, card):
        assert 'oracle_text' in card
        prompt = ChatPromptTemplate.from_messages([
            ('user', card['oracle_text'].replace('{', '{{').replace('}', '}}')),
            ('user', 'This card is a Magic: the Gathering card that has a delayed triggered ability at the start of the game. Please answer only using the excerpt of the rules text on this card: 1. When will this ability be triggered? 2. When triggered, a triggered ability will be created; what rules text describes the triggered ability?'),
        ])
        model = self.llm.bind_tools([DelayedTriggerWhenWhatResponse], tool_choice='DelayedTriggerWhenWhatResponse')
        parser = JsonOutputKeyToolsParser(key_name='DelayedTriggerWhenWhatResponse', first_tool_only=True)
        chain = prompt | model | parser
        response = chain.invoke({})
        return response['trigger_when'], response['trigger_what']

    def create_gherkin_rules_from_gherkin(self, rules: List[str]) -> List[Rule]:
        print('create_gherkin_rules_from_gherkin')
        created_rules = []
        for rule in rules:
            rule_lines = []
            for line in rule.split('\n'):
                if any(line.lower().startswith(x) for x in ('given', 'when', 'then', 'and', 'but')):
                    implementation = GherkinImpl.objects.get(gherkin_line=line)
                    rule_lines.append((line, implementation.lambda_code))
            created_rule = Rule.from_implementations(OrderedDict(rule_lines))
            created_rules.append(created_rule)
        print(created_rules)
        return created_rules
