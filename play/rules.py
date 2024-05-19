from dataclasses import dataclass, field
from typing import List, OrderedDict, Callable, Any, Union
from collections import OrderedDict as CollectionsOrderedDict
import random
import re
from .game import Game

@dataclass
class Rule:
    gherkin: List[str] = field(default_factory=list)
    implementations: OrderedDict[str, Callable[[Game, List[Any], Any], Union[bool, List[Any]]]] = \
            field(default_factory=dict)

    def ensure_ordered_dict(value):
        if not isinstance(value, CollectionsOrderedDict):
            raise ValueError('data field must be an OrderedDict')
        return value

    _validator_implementations = ensure_ordered_dict

    def from_implementations(implementations: OrderedDict[str, Callable[..., bool]]) -> '__class__':
        gherkin = [x for x in implementations]
        #print('Gherkin is:', gherkin)
        return Rule(gherkin, implementations)


#
# general todo manipulation
#
def consume_line(game, todo, matched_line) -> List[Any]:
    return [line for line in todo if line != matched_line]


#
# starting player rules
#
ASK_GO_FIRST_STRING = 'Would you like to go first?';

def ask_random_player_to_go_first(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    ret.append(['question', random.choice(game.players), ASK_GO_FIRST_STRING, 'Yes', 'No'])
    return ret

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK = [
    (
        'When the game wants to determine who goes first',
        lambda context: 'decide_who_goes_first' in str(context.line),
    ),
    (
        'And there are no other pending actions',
        lambda context: len(context.todo) == 1,
    ),
    (
        'Then the game consumes the matched todo line',
        consume_line,
    ),
    (
        'And the game decides a random player to ask',
        ask_random_player_to_go_first,
    ),
]

def set_player_as_starting(game, todo, matched_line) -> List[Any]:
    who, question, answer = matched_line[1:]
    players = game.players
    [this_player] = [i for i, p in enumerate(players) if p.player_name == who.player_name]
    next_player = (this_player + 1) % len(players)
    yn = str(answer).lower().startswith('y')
    ret = [line for line in todo]
    ret.append(['set_starting_player', game.players[this_player if yn else next_player]])
    return ret

SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER = [
    (
        'When the chosen player answers whether they go first',
        lambda context: 'answer_question' in str(context.line) and ASK_GO_FIRST_STRING in str(context.line),
    ),
    (
        'Then the game consumes the matched todo line',
        consume_line,
    ),
    (
        'And the game sets the appropriate player to go first',
        set_player_as_starting,
    ),
]


#
# companion rules
#
def has_companion(context) -> bool:
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

def companion_reveal_increment_player_id(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    *others, player_id = matched_line
    max_players = len(game.players)
    ret = consume_line(game, todo, matched_line)
    ret.append([*others, player_id + 1])
    return ret

def start_mulligan(game, todo, matched_line) -> List[Any]:
    return [['start_mulligan']]

SYSTEM_RULE_REVEAL_COMPANION_CHECK = [
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' in str(context.line),
    ),
    (
        'And the player index has not overflown',
        lambda context: context.line[1] < len(context._match.game.players),
    ),
    (
        'But the player has no companion in their sideboard',
        lambda context: not has_companion(context),
    ),
    (
        'Then the game increments the player ID in the matched line',
        companion_reveal_increment_player_id,
    ),
]

SYSTEM_RULE_REVEAL_COMPANION_OVERFLOW = [
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' in str(context.line),
    ),
    (
        'But the player ID has overflowed',
        lambda context: context.line[1] >= len(context._match.game.players),
    ),
    (
        'Then the game consumes the matched todo line',
        consume_line,
    ),
    (
        'Then the game starts to mulligan',
        start_mulligan,
    ),
]

ASK_REVEAL_COMPANION_STRING = 'Which companion would you like to reveal in order to have access to later in the game?';

def ask_player_to_reveal_companion(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    *_, player_id = matched_line
    player = game.players[player_id]
    companions = [card['name'] + f" ({card['in_game_id']})" for card in player.sideboard if ('Companion' in str(card) and not 'Companion' in card['name'])]
    ret.append(['question', player, ASK_REVEAL_COMPANION_STRING, *companions, "Don't reveal"])
    return ret

SYSTEM_RULE_REVEAL_COMPANION_ASK = [
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' in str(context.line),
    ),
    (
        'And the player index has not overflown',
        lambda context: context.line[1] < len(context._match.game.players),
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

def append_reveal_companion_next_step(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    _, who, question, answer = matched_line
    players = game.players
    player_id = players.index(who)
    max_players = len(players)
    assert isinstance(player_id, int)
    ret.append(['ask_reveal_companion', player_id + 1])
    return ret

def annotate_as_companion(game, todo, matched_line) -> bool:
    ret = [line for line in todo]
    *_, answer = matched_line
    # search in answer for a card's in_game_id e.g. n3#1
    expr = r'\b[a-zA-Z](\d+)\#(\d+)\b'
    result = re.search(expr, answer)
    if result is None:
        return ret
    in_game_id = result.group(0)
    assert isinstance(in_game_id, str)
    ret.append(['set_annotation', in_game_id, 'is_companion', True])
    return ret

SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER = [
    (
        'When a player announces to reveal a companion',
        lambda context: 'answer_question' in str(context.line) and ASK_REVEAL_COMPANION_STRING in str(context.line),
    ),
    (
        'Then the game appends the next step',
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
def shuffle_all(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    for player in game.players:
        ret.append(['shuffle', player])
    return ret

def draw_seven_all(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    for player in game.players:
        ret.append(['draw', player, 7])
    return ret

def create_mulligan_states(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    players = game.players
    has_keep_hand = False
    to_bottom = 0
    for player in players:
        ret.append(['mulligan_state', player, has_keep_hand, to_bottom])
    ret.append(['mulligan_at', 0])
    return ret

SYSTEM_RULE_MULLIGAN_CHECK = [
    (
        'When the game starts the mulligan phase',
        lambda context: 'start_mulligan' in str(context.line),
    ),
    (
        'Then the game creates the needed mulligan states',
        create_mulligan_states,
    ),
    (
        'And the game shuffles all libraries',
        shuffle_all,
    ),
    (
        'And the game deals seven cards to all players',
        draw_seven_all,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def current_player_could_mulligan(context) -> bool:
    # expecting context.line = ['mulligan_at', player_id]
    if context.line[0] != 'mulligan_at':
        return False
    if any(not 'mulligan' in line[0] for line in context.todo):
        # all lines must contain 'mulligan'
        return False
    players = context.game.players
    return context.line[1] < len(players)

def ask_player_mulligan(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    if 'mulligan_at' not in matched_line:
        return ret
    players = game.players
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in todo if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == matched_line[1]][0]
    player = interested_line[1]
    to_bottom = interested_line[3]
    ret.append(['ask_mulligan', player, to_bottom])
    return ret

SYSTEM_RULE_MULLIGAN_ASK = [
    (
        'When a player could take a mulligan',
        current_player_could_mulligan,
    ),
    (
        "And the game haven't ask the player",
        lambda context: not any('ask_mulligan' in line for line in context.todo)
    ),
    (
        'Then the game asks the player for mulligan choices',
        ask_player_mulligan,
    ),
]

def current_player_has_kept_hand(context) -> bool:
    # expecting context.line = ['mulligan_at', player_id]
    if context.line[0] != 'mulligan_at':
        return False
    if any(not 'mulligan' in line[0] for line in context.todo):
        # all lines must contain 'mulligan'
        return False
    players = context.game.players
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in context.todo if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == context.line[1]]
    if not interested_line:
        return False
    interested_line = interested_line[0]
    has_keep_hand = interested_line[2]
    return has_keep_hand

def increment_mulligan_at(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting line = ['mulligan_at', who_id]
    mulligan_at = [line for line in ret if line[0] == 'mulligan_at'][0]
    mulligan_at[1] += 1
    return ret

SYSTEM_RULE_MULLIGAN_SKIP = [
    (
        'When a player could take a mulligan',
        current_player_could_mulligan,
    ),
    (
        'And the current player has already kept their hand',
        current_player_has_kept_hand,
    ),
    (
        'Then the game increments mulligan_at',
        increment_mulligan_at,
    ),
]

def current_player_wants_to_mulligan(context) -> bool:
    # expecting line = [ 'mulligan', who_name ]
    if context.line[0] != 'mulligan':
        return False
    who_name = context.line[1]
    who_id = [i for i, p in enumerate(context.game.players) if p.player_name == who_name][0]
    mulligan_at = [line for line in context.todo if line[0] == 'mulligan_at'][0]
    return who_id == mulligan_at[1]

def increment_to_bottom(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting matched line = ['mulligan', who_name]
    who_name = matched_line[1]
    who = [player for player in game.players if player.player_name == who_name][0]
    # expecting interested = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested = [line for line in ret if 'mulligan_state' in line and line[1] == who][0]
    interested[3] += 1
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_MULLIGAN_ANSWER = [
    (
        'When a player answers to take a mulligan',
        current_player_wants_to_mulligan,
    ),
    (
        "Then the game increments the player's to_bottom",
        increment_to_bottom,
    ),
    (
        'And the game increments mulligan_at',
        increment_mulligan_at,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def current_player_wants_to_keep(context) -> bool:
    # expecting line = [ 'keep_hand', who_name, to_bottom: list[Card] ]
    if context.line[0] != 'keep_hand':
        return False
    who_name = context.line[1]
    who_id = [i for i, p in enumerate(context.game.players) if p.player_name == who_name][0]
    mulligan_at = [line for line in context.todo if line[0] == 'mulligan_at'][0]
    return who_id == mulligan_at[1]

def bottom_mulligan_player_cards(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting matched_line = ['keep_hand', who_name, to_bottom: list[Card]]
    who_name = matched_line[1]
    who = [player for player in game.players if player.player_name == who_name][0]
    to_bottom = matched_line[2]
    ret.append(['bottom_cards', who, to_bottom])
    return ret

def set_player_has_keep(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    who_name = matched_line[1]
    # search for 'mulligan_state'
    # expecting ['mulligan_state', player, has_keep_hand, to_bottom]
    interested = [line for line in ret if line[0] == 'mulligan_state' and line[1].player_name == who_name][0]
    interested[2] = True
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_KEEP_ANSWER = [
    (
        'When a player answers to keep their hand',
        current_player_wants_to_keep,
    ),
    (
        'Then the game puts the cards to the bottom of the library',
        bottom_mulligan_player_cards,
    ),
    (
        'And the game sets the player as has_keep',
        set_player_has_keep,
    ),
    (
        'And the game increments mulligan_at',
        increment_mulligan_at,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def empty_all_mulligan_player_hand(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting [ 'mulligan_state', player, has_keep_hand, to_bottom ]
    mulliganing_players = [line[1] for line in todo if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['bottom_cards', player, [card for card in player.hand]])
    return ret

def shuffle_all_mulligan_player_library(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting ['mulligan_state', player, has_keep_hand, to_bottom]
    mulliganing_players = [line[1] for line in todo if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['shuffle', player])
    return ret

def deal_seven_to_all_mulligan_player(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expecting [ 'mulligan_state', player, has_keep_hand, to_bottom ]
    mulliganing_players = [line[1] for line in todo if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['draw', player, 7])
    return ret

def reset_mulligan_at(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    line = [line for line in ret if line == matched_line][0]
    line[1] = 0
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_CONTINUE = [
    (
        'When mulligan_at exceeds the maximum player count',
        lambda context: 'mulligan_at' in context.line and context.line[1] >= len(context.game.players),
    ),
    (
        'And there exists one or more players who chose to take a mulligan',
        lambda context: any('mulligan_state' in line and not line[2] for line in context.todo),
    ),
    (
        "Then the game empties all mulliganing player's hand",
        empty_all_mulligan_player_hand,
    ),
    (
        "And the game shuffles all mulliganing player's library",
        shuffle_all_mulligan_player_library,
    ),
    (
        'And the game deals seven cards to all mulliganing players',
        deal_seven_to_all_mulligan_player,
    ),
    (
        'And the game resets the mulligan_at counter',
        reset_mulligan_at,
    ),
]

def consume_all_mulligan_items(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo if 'mulligan' not in line[0]]
    return ret

def push_start_game(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    ret.append(['start_game'])
    return ret

def mark_start_of_game_in_todo(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    ret.append(['start_of_game'])
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_FINISH = [
    (
        'When mulligan_at exceeds the maximum player count',
        lambda context: 'mulligan_at' in context.line and context.line[1] >= len(context.game.players),
    ),
    (
        'And all players have kept their hand',
        lambda context: all(line[2] for line in [ line for line in context.todo if 'mulligan_state' in line ])
    ),
    (
        'And there are no other things ongoing in the todo list',
        lambda context: all('mulligan' in line[0] for line in context.todo)
    ),
    (
        'Then the game marks the start of game in todo',
        mark_start_of_game_in_todo,
    ),
    (
        'And the game starts',
        push_start_game,
    ),
    (
        'And the game consumes all mulligan-related items',
        consume_all_mulligan_items,
    ),
]

def create_start_of_game_action_state(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    ret.append(['check_start_of_game_action', 0])
    return ret

SYSTEM_RULE_START_OF_GAME_CHECK = [
    (
        'When the game is in the start of game phase',
        lambda context: 'start_of_game' in context.line and len(context.todo) == 1,
    ),
    (
        'Then the game creates check_start_of_game_action',
        create_start_of_game_action_state,
    ),
    (
        'And the game consumes the matched todo line',
        consume_line,
    ),
]

def append_scan_hand(game, todo, matched_line) -> List[Any]:
    ret = [line for line in todo]
    # expect matched_line = ['check_start_of_game_action']
    who_id = matched_line[1]
    assert isinstance(who_id, int)
    ret.append(['scanning', who_id, 'hand']) # tell the engine that we are scanning
    ret.append(['scan', who_id, 'hand']) # tell the engine to scan the player's hand
    return ret

SYSTEM_RULE_START_OF_GAME_SCAN_HAND = [
    (
        'When the game checks for the current players for start of game action',
        lambda context: 'check_start_of_game_action' in context.line,
    ),
    (
        'And the game is not scanning anything',
        lambda context: not any('scanning' in line[0] for line in context.todo),
    ),
    (
        "Then the game scans the current player's hand",
        append_scan_hand,
    ),
]

# Make rules
DETERMINE_FIRST_PLAYER_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_DETERMINE_FIRST_PLAYER_HANDLE_ANSWER)),
]

REVEAL_COMPANION_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_CHECK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_OVERFLOW)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER)),
]

MULLIGAN_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_CHECK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_SKIP)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_HANDLE_MULLIGAN_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_HANDLE_KEEP_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_CONTINUE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_FINISH)),
]

START_OF_GAME_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_CHECK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_SCAN_HAND)),
]

# EVERYTHING
SYSTEM_RULES = [
    *DETERMINE_FIRST_PLAYER_RULES,
    *REVEAL_COMPANION_RULES,
    *MULLIGAN_RULES,
    *START_OF_GAME_RULES,
]
