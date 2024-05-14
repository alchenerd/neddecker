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
def consume_line(game, todo, i, placeholder) -> bool:
    try:
        todo.remove(todo[i])
    except:
        return False
    return True

#
# go first rules
#
ASK_GO_FIRST_STRING = 'Would you like to go first?';

def ask_random_player_to_go_first(game, todo, i, placeholder) -> bool:
    if 'decide_who_goes_first' in todo[i]:
        todo.remove(todo[i])
        todo.append(['question', random.choice(game.players), ASK_GO_FIRST_STRING, 'Yes', 'No'])
        return True # game or todo was changed
    return False # game or todo was not changed

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK = [
    (
        'When the game wants to determine who goes first',
        lambda game, todo, i, placeholder: 'decide_who_goes_first' in str(todo[i]),
    ),
    (
        'Then the game decides a random player to ask',
        ask_random_player_to_go_first,
    )
]

def set_player_to_go_first(game, todo, i, placeholder) -> bool:
    line = todo[i]
    who, question, answer = line[1:]
    if question != ASK_GO_FIRST_STRING:
        return False # somehow there is a coincidence
    [ this_player ] = [ i for i, p in enumerate(game.players) if p.player_name == who.player_name ]
    next_player = (i + 1) % len(game.players)
    yn = str(answer).lower().startswith('y')
    todo.append(['set_starting_player', game.players[this_player if yn else next_player]])
    todo.remove(line)
    return True # game or todo was changed

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER = [
    (
        'When the chosen player answers whether they go first',
        lambda game, todo, i, placeholder: 'answer_question' in str(todo[i]) and ASK_GO_FIRST_STRING in str(todo[i]),
    ),
    (
        'Then the game sets the appropriate player to go first',
        set_player_to_go_first,
    )
]


#
# companion rules
#
def has_companion(game, todo, i, placeholder):
    _, player_id = todo[i]
    player = game.players[player_id]
    sideboard = player.sideboard
    for card in sideboard:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            oracle_text = card.get('faces', {}).get('front', {}).get('oracle_text', None)
        if oracle_text.startswith('Companion'):
            return True
    return False

def companion_remove_or_increment(game, todo, i, placeholder):
    *others, player_id = todo[i]
    max_players = len(game.players)
    try:
        if player_id + 1 < max_players:
            todo.append([*others, player_id + 1])
        todo.remove(todo[i])
        return True
    except:
        return False

def append_mulligan_if_empty(game, todo, i, placeholder):
    if not todo:
        todo.append(['start_mulligan'])
        return True
    return False

SYSTEM_RULE_REVEAL_COMPANION_CHECK = [
    (
        'When a player could reveal a companion',
        lambda game, todo, i, placeholder: 'ask_reveal_companion' in str(todo[i]) if i < len(todo) else False,
    ),
    (
        'But the player has no companion in their sideboard',
        lambda game, todo, i, placeholder: not has_companion(game, todo, i, placeholder),
    ),
    (
        'Then the game removes the todo item or increment the player ID',
        companion_remove_or_increment,
    ),
    (
        'And start mulligan if nobody is pending',
        append_mulligan_if_empty,
    ),
]

ASK_REVEAL_COMPANION_STRING = 'Which companion would you like to reveal in order to have access to later in the game?';

def ask_player_to_reveal_companion(game, todo, i, placeholder) -> bool:
    if 'ask_reveal_companion' in todo[i]:
        *_, player_id = todo[i]
        player = game.players[player_id]
        todo.remove(todo[i])
        companions = [card['name'] + f" ({card['in_game_id']})" for card in player.sideboard if ('Companion' in str(card) and not 'Companion' in card['name'])]
        todo.append(['question', player, ASK_REVEAL_COMPANION_STRING, *companions, "Don't reveal"])
        return True # game or todo was changed
    return False # game or todo was not changed

SYSTEM_RULE_REVEAL_COMPANION_ASK = [
    (
        'When a player could reveal a companion',
        lambda game, todo, i, placeholder: 'ask_reveal_companion' in str(todo[i]) if i < len(todo) else False,
    ),
    (
        'And the player has a companion in their sideboard',
        has_companion,
    ),
    (
        'Then the game asks the player to reveal a companion',
        ask_player_to_reveal_companion,
    ),
]

def append_reveal_companion_next_step(game, todo, i, placeholder) -> bool:
    _, who, question, answer = todo[i]
    players = game.players
    player_id = players.index(who)
    max_players = len(game.players)
    assert isinstance(player_id, int)
    if player_id + 1 < max_players:
        placeholder.append(['ask_reveal_companion', player_id + 1])
    else:
        placeholder.append(['start_mulligan'])
    return True

def annotate_as_companion(game, todo, i, placeholder) -> bool:
    if 'answer_question' not in todo[i] or ASK_REVEAL_COMPANION_STRING not in todo[i]:
        return False
    *_, answer = todo[i]
    try:
        todo.remove(todo[i]) # consume
    except:
        return False
    expr = r'\b[a-zA-Z](\d+)\#(\d+)\b'
    result = re.search(expr, answer)
    if result is None:
        return False
    in_game_id = result.group(0)
    assert isinstance(in_game_id, str)
    todo.append(['set_annotation', in_game_id, 'is_companion', True])
    return True

SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER = [
    (
        'When a player announces to reveal a companion',
        lambda game, todo, i, placeholder: 'answer_question' in str(todo[i]) and ASK_REVEAL_COMPANION_STRING in str(todo[i]),
    ),
    (
        'Then the game appends the next step to placeholder',
        append_reveal_companion_next_step,
    ),
    (
        'And the game annotates the card as companion',
        annotate_as_companion,
    ),
]

#
# mulligan rules
#
def create_mulligan_states(game, todo, i, placeholder) -> bool:
    players = game.players
    has_keep_hand = False
    to_bottom = 0
    for player in players:
        todo.append(['mulligan_state', player, has_keep_hand, to_bottom])
    todo.append(['mulligan_at', 0])
    return True

SYSTEM_RULE_MULLIGAN_CHECK = [
    (
        'When the game starts the mulligan phase',
        lambda game, todo, i, placeholder: 'start_mulligan' in str(todo[i]),
    ),
    (
        'Then the game consumes it because I have not implement this yet',
        consume_line,
    ),
]


# EVERYTHING
SYSTEM_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_CHECK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_CHECK)),
]
