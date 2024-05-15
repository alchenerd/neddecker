from dataclasses import dataclass, field
from typing import List, OrderedDict, Callable, Any
from collections import OrderedDict as CollectionsOrderedDict
import random
import re
from .game import Game

@dataclass
class Rule:
    gherkin: List[str] = field(default_factory=list)
    implementations: OrderedDict[str, Callable[[Game, List[Any]], bool]] = field(default_factory=dict)

    def from_implementations(implementations: OrderedDict[str, Callable[..., bool]]) -> '__class__':
        gherkin = [ x for x in implementations ]
        #print('Gherkin is:', gherkin)
        return Rule(gherkin, implementations)

#
# general
#
def consume_line(context) -> bool:
    print('items', context.items)
    print('line', context.line)
    context.items.remove(context.line)
    return True

#
# go first rules
#
ASK_GO_FIRST_STRING = 'Would you like to go first?';

def ask_random_player_to_go_first(context) -> bool:
    context.items.append(['question', random.choice(context.game.players), ASK_GO_FIRST_STRING, 'Yes', 'No'])
    return True

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK = [
    (
        'When the game wants to determine who goes first',
        lambda context: 'decide_who_goes_first' in str(context.line),
    ),
    (
        'Then the game decides a random player to ask',
        ask_random_player_to_go_first,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def set_player_to_go_first(context) -> bool:
    who, question, answer = context.line[1:]
    if question != ASK_GO_FIRST_STRING:
        return False # somehow there is a coincidence
    players = context.game.players
    [ this_player ] = [ i for i, p in enumerate(players) if p.player_name == who.player_name ]
    next_player = (this_player + 1) % len(players)
    yn = str(answer).lower().startswith('y')
    context.items.append(['set_starting_player', context.game.players[this_player if yn else next_player]])
    return True # game or todo was changed

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER = [
    (
        'When the chosen player answers whether they go first',
        lambda context: 'answer_question' in str(context.line) and ASK_GO_FIRST_STRING in str(context.line),
    ),
    (
        'Then the game sets the appropriate player to go first',
        set_player_to_go_first,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]


#
# companion rules
#
def has_companion(context):
    if 'ask_reveal_companion' not in context.line:
        return False
    *_, player_id = context.line
    player = context.game.players[player_id]
    sideboard = player.sideboard
    for card in sideboard:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            oracle_text = card.get('faces', {}).get('front', {}).get('oracle_text', None)
        if oracle_text.startswith('Companion'):
            return True
    return False

def companion_remove_or_increment(context):
    *others, player_id = context.line
    max_players = len(context.game.players)
    if player_id + 1 < max_players:
        context.items.append([*others, player_id + 1])
    else:
        consume_line(context)
    return True

def append_mulligan_if_empty(context):
    if not context.todo:
        context.line.append(['start_mulligan'])
        return True
    return False

SYSTEM_RULE_REVEAL_COMPANION_CHECK = [
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' in str(context.line),
    ),
    (
        'But the player has no companion in their sideboard',
        lambda context: not has_companion(context),
    ),
    (
        'Then the game removes the matched todo line or increment the player ID',
        companion_remove_or_increment,
    ),
    (
        'And start the mulligan phase if nobody is pending',
        append_mulligan_if_empty,
    ),
]

ASK_REVEAL_COMPANION_STRING = 'Which companion would you like to reveal in order to have access to later in the game?';

def ask_player_to_reveal_companion(context) -> bool:
    *_, player_id = context.line
    player = context.game.players[player_id]
    companions = [ card['name'] + f" ({card['in_game_id']})" for card in player.sideboard if ('Companion' in str(card) and not 'Companion' in card['name']) ]
    context.items.append(['question', player, ASK_REVEAL_COMPANION_STRING, *companions, "Don't reveal"])
    return True

SYSTEM_RULE_REVEAL_COMPANION_ASK = [
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' in str(context.line),
    ),
    (
        'And the player has a companion in their sideboard',
        has_companion,
    ),
    (
        'Then the game asks the player to reveal a companion',
        ask_player_to_reveal_companion,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def append_reveal_companion_next_step(context) -> bool:
    _, who, question, answer = context.line
    players = context.game.players
    player_id = players.index(who)
    max_players = len(players)
    assert isinstance(player_id, int)
    if player_id + 1 < max_players:
        context.items.append(['ask_reveal_companion', player_id + 1])
    else:
        context.items.append(['start_mulligan'])
    return True

def annotate_as_companion(context) -> bool:
    *_, answer = context.line
    expr = r'\b[a-zA-Z](\d+)\#(\d+)\b'
    result = re.search(expr, answer)
    if result is None:
        return False
    in_game_id = result.group(0)
    assert isinstance(in_game_id, str)
    context.items.append(['set_annotation', in_game_id, 'is_companion', True])
    return True

SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER = [
    (
        'When a player announces to reveal a companion',
        lambda context: 'answer_question' in str(context.line) and ASK_REVEAL_COMPANION_STRING in str(context.line),
    ),
    (
        'Then the game appends the next step to placeholder',
        append_reveal_companion_next_step,
    ),
    (
        'And the game annotates the card as companion',
        annotate_as_companion,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

#
# mulligan rules
#
def shuffle_all(context) -> bool:
    for player in context.game.players:
        context.items.append(['shuffle', player])
    return True

def deal_seven_all(context) -> bool:
    for player in context.game.players:
        context.items.append(['draw', player, 7])
    return True

def create_mulligan_states(context) -> bool:
    players = context.game.players
    has_keep_hand = False
    to_bottom = 0
    for player in players:
        context.items.append(['mulligan_state', player, has_keep_hand, to_bottom])
    context.items.append(['mulligan_at', 0])
    return True

SYSTEM_RULE_MULLIGAN_CHECK = [
    (
        'When the game starts the mulligan phase',
        lambda context: 'start_mulligan' in str(context.line),
    ),
    (
        'Then the game shuffles all libraries',
        shuffle_all,
    ),
    (
        'And the game deals seven cards to all players',
        deal_seven_all,
    ),
    (
        'And the game creates the needed mulligan states',
        create_mulligan_states,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def current_player_could_mulligan(context):
    # expecting context.line = ['mulligan_at', player_id]
    if context.line != 'mulligan_at':
        return False
    players = context.game.players
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in context.todo if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == context.line[1]][0]
    has_keep_hand = interested_line[2]
    assert isinstance(has_keep_hand, bool)
    return not has_keep_hand

def ask_player_mulligan(context):
    players = context.game.players
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in context.todo if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == context.line[1]][0]
    player = interested_line[1]
    context.items.append('ask_mulligan', player, interested_line[3])
    return True

SYSTEM_RULE_MULLIGAN_ASK = [
    (
        'When a player could take a mulligan',
        current_player_could_mulligan,
    ),
    (
        'Then the game asks the player for mulligan choices',
        ask_player_mulligan,
    ),
]

def current_player_wants_to_mulligan(context):
    return False
SYSTEM_RULE_MULLIGAN_HANDLE_MULLIGAN_ANSWER = [
    (
        'When a player answers to take a mulligan',
        current_player_wants_to_mulligan,
    ),
    (
        'Then the game asks the player for mulligan choices',
        ask_player_mulligan,
    ),
]
# TODO: finish the mulligan logic

# EVERYTHING
SYSTEM_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_CHECK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_CHECK)),
]
