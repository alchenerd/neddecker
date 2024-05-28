from dataclasses import dataclass, field
from typing import List, OrderedDict, Callable, Any, Union
from collections import OrderedDict as CollectionsOrderedDict
from deprecated import deprecated
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
            raise ValueError('Data field must be an OrderedDict')
        return value

    _validator_implementations = ensure_ordered_dict

    def from_implementations(implementations: OrderedDict[str, Callable[..., Union[bool, List[Any]]]]) -> '__class__':
        gherkin = [x for x in implementations]
        #print('Gherkin is:', gherkin)
        return Rule(gherkin, implementations)


#
# general event list manipulation
#
def consume_line(context) -> List[Any]:
    return [e for e in context.events if e != context.matched_event]


#
# starting player rules
#
SYSTEM_RULE_CHOOSE_STARTING_PLAYER_DECIDER_RANDOM = [
    (
        'Given the game is in the determine starting player phase',
        lambda context: context.game.phase == 'determine starting player phase'
    ),
    (
        'And there is no starting player decider',
        lambda context: not context.game.starting_player_decider
    ),
    (
        'And this is the first game',
        lambda context: len(context._match.games) == 1
    ),
    (
        'When the game reaches the start of the phase',
        lambda context: len(context.events) == 1 and context.matched_event[0] == context.game.phase
    ),
    (
        'Then choose the starting player decider randomly',
        lambda context: [*context.events, ['set_starting_player_decider', random.choice(context.game.players)]]
    ),
]

# TODO: Implement after a full game can be played
SYSTEM_RULE_CHOOSE_STARTING_PLAYER_DECIDER_PREVIOUS_DRAW = None
SYSTEM_RULE_CHOOSE_STARTING_PLAYER_DECIDER_PREVIOUS_LOST = None

ASK_WHO_GO_FIRST_STRING = 'Who will you choose to take the first turn?';

SYSTEM_RULE_CHOOSE_STARTING_PLAYER_ASK = [
    (
        'Given the game is in the determine starting player phase',
        lambda context: context.game.phase == 'determine starting player phase'
    ),
    (
        'And there is a starting player decider',
        lambda context: bool(context.game.starting_player_decider)
    ),
    (
        'But there is no starting player',
        lambda context: not context.game.starting_player
    ),
    (
        'When the game is at the start of the phase',
        lambda context: len(context.events) == 1 and context.matched_event[0] == context.game.phase
    ),
    (
        'Then ask the starting player decider who goes first',
        lambda context: [
            *context.events,
            [
                'question',
                context.game.starting_player_decider,
                ASK_WHO_GO_FIRST_STRING,
                *(\
                        p.player_name + ' (You)' if p == context.game.starting_player_decider \
                        else p.player_name \
                        for p in context.game.players\
                ),
            ],
        ]
    ),
]

SYSTEM_RULE_CHOOSE_STARTING_PLAYER_HANDLE_ANSWER = [
    (
        'Given the game is in the determine starting player phase',
        lambda context: context.game.phase == 'determine starting player phase'
    ),
    (
        'And there is a starting player decider',
        lambda context: bool(context.game.starting_player_decider)
    ),
    (
        'But there is no starting player',
        lambda context: not context.game.starting_player
    ),
    (
        'When the starting player decider answers who goes first',
        lambda context: \
                'answer_question' == context.matched_event[0] and \
                context.game.starting_player_decider == context.matched_event[1] and \
                ASK_WHO_GO_FIRST_STRING == context.matched_event[2],
    ),
    (
        'Then set the starting player',
        lambda context: [['set_starting_player', *[p for p in context.game.players if \
                p.player_name.lower() in context.matched_event[-1].lower()]]]
    ),
]

# TODO: implement when conspiracy draft is supported
SYSTEM_RULE_CHOOSE_STARTING_PLAYER_HANDLE_POWER_PLAY = None

SYSTEM_RULE_CHOOSE_STARTING_PLAYER_PROCEED = [
    (
        'Given the game is in the determine starting player phase',
        lambda context: context.game.phase == 'determine starting player phase'
    ),
    (
        'And there is a starting player decider',
        lambda context: bool(context.game.starting_player_decider)
    ),
    (
        'And there is a starting player',
        lambda context: bool(context.game.starting_player)
    ),
    (
        'When the game has a starting player',
        lambda context: len(context.events) == 1 and context.matched_event[0] == 'starting_player_is_set'
    ),
    (
        'Then proceed to the next phase',
        lambda context: [['next_phase']]
    ),
]

#
# companion rules
#
def has_companion(context) -> bool:
    if 'ask_reveal_companion' != context.matched_event[0]:
        return False
    *_, player_id = context.matched_event
    player = context.game.players[player_id]
    sideboard = player.sideboard
    for card in sideboard:
        oracle_text = card.get('oracle_text', None)
        if not oracle_text:
            continue # there are no double-faced companion
        if oracle_text.startswith('Companion'):
            return True
    return False

def companion_reveal_increment_player_id(context) -> List[Any]:
    assert 'ask_reveal_companion' == context.matched_event[0]
    *others, player_id = context.matched_event
    return [*[e for e in context.events if e[0] != 'ask_reveal_companion'], [*others, player_id + 1]]

SYSTEM_RULE_REVEAL_COMPANION_KICKSTART = [
    (
        'Given the game is in the reveal companion phase',
        lambda context: context.game.phase == 'reveal companion phase'
    ),
    (
        'When a the game is at the beginning of the phase',
        lambda context: len(context.events) == 1 and context.matched_event[0] == context.game.phase,
    ),
    (
        'Then append an ask_reveal_companion marking',
        lambda context: [*context.events, ['ask_reveal_companion', 0]],
    ),
    (
        'And the game consumes the matched event',
        consume_line,
    ),
]

SYSTEM_RULE_REVEAL_COMPANION_CHECK = [
    (
        'Given the game is in the reveal companion phase',
        lambda context: context.game.phase == 'reveal companion phase'
    ),
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' == context.matched_event[0],
    ),
    (
        'And the player index has not overflown',
        lambda context: context.matched_event[1] < len(context.game.players),
    ),
    (
        'But the player has no companion in their sideboard',
        lambda context: not has_companion(context),
    ),
    (
        'Then the game increments the player index in the matched line',
        companion_reveal_increment_player_id,
    ),
]

SYSTEM_RULE_REVEAL_COMPANION_OVERFLOW = [
    (
        'Given the game is in the reveal companion phase',
        lambda context: context.game.phase == 'reveal companion phase'
    ),
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' == context.matched_event[0],
    ),
    (
        'But the player index has overflowed',
        lambda context: context.matched_event[1] >= len(context._match.game.players),
    ),
    (
        'And the matched event is the only event',
        lambda context: len(context.events) == 1
    ),
    (
        'Then the game proceeds to the next phase',
        lambda context: [['next_phase']]
    ),
]

ASK_REVEAL_COMPANION_STRING = 'Which companion would you like to reveal so you could later in game put into hand from outside of game for the cost of paying {3}?';

def ask_player_to_reveal_companion(context) -> List[Any]:
    *_, player_id = context.matched_event
    player = context.game.players[int(player_id)]
    companions = [card['name'] + f" ({card['in_game_id']})" for card in player.sideboard if ('Companion' in str(card) and not 'Companion' in card['name'])]
    return [*context.events, ['question', player, ASK_REVEAL_COMPANION_STRING, *companions, "Don't reveal"]]

SYSTEM_RULE_REVEAL_COMPANION_ASK = [
    (
        'Given the game is in the reveal companion phase',
        lambda context: context.game.phase == 'reveal companion phase'
    ),
    (
        'When a player could reveal a companion',
        lambda context: 'ask_reveal_companion' == context.matched_event[0],
    ),
    (
        'And the player index has not overflown',
        lambda context: context.matched_event[1] < len(context._match.game.players),
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
        'And the game consumes the matched event',
        consume_line,
    ),
]

def append_reveal_companion_next_step(context) -> List[Any]:
    _, who, question, answer = context.matched_event
    players = context.game.players
    player_id = players.index(who)
    assert isinstance(player_id, int)
    return [*context.events, ['ask_reveal_companion', player_id + 1]]

def annotate_as_companion(context) -> bool:
    *_, answer = context.matched_event
    # search in answer for a card's in_game_id e.g. n3#1
    expr = r'\b[a-zA-Z](\d+)\#(\d+)\b'
    result = re.search(expr, answer)
    if result is None:
        return context.events
    in_game_id = result.group(0)
    assert isinstance(in_game_id, str)
    return [*context.events, ['set_as_companion', in_game_id]]

SYSTEM_RULE_REVEAL_COMPANION_HANDLE_ANSWER = [
    (
        'Given the game is in the reveal companion phase',
        lambda context: context.game.phase == 'reveal companion phase'
    ),
    (
        'When a player announces to reveal a companion',
        lambda context: 'answer_question' == context.matched_event[0] and \
                ASK_REVEAL_COMPANION_STRING in str(context.matched_event),
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
        'And the game consumes the matched event',
        consume_line,
    ),
]


#
# mulligan rules
#
def shuffle_all(context) -> List[Any]:
    additional_events = [['shuffle', player] for player in context.game.players]
    return [*context.events, *additional_events]

def draw_seven_all(context) -> List[Any]:
    additional_events = [['draw', player, 7] for player in context.game.players]
    return [*context.events, *additional_events]

def create_mulligan_states(context) -> List[Any]:
    to_bottom = 0
    has_keep_hand = False
    additional_events = [['mulligan_state', player, has_keep_hand, to_bottom] for player in context.game.players]
    return [*context.events, *additional_events, ['mulligan_at', 0]]

SYSTEM_RULE_MULLIGAN_CHECK = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
    (
        'When the game starts the mulligan phase',
        lambda context: context.matched_event[0] == 'mulligan phase' and len(context.events) == 1,
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
        'And the game consumes the matched events line',
        consume_line,
    ),
]

def current_player_could_mulligan(context) -> bool:
    # expecting context.matched_event = ['mulligan_at', player_id]
    if context.matched_event[0] != 'mulligan_at':
        return False
    if any(not 'mulligan_' in line[0] for line in context.events):
        # all events must be 'mulligan_at' or 'mulligan_state'
        return False
    players = context.game.players
    return context.matched_event[1] < len(players)

def ask_player_mulligan(context) -> List[Any]:
    ret = [line for line in context.events]
    if 'mulligan_at' != context.matched_event[0]:
        return ret
    players = context.game.players
    if context.matched_event[1] >= len(players):
        return ret
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in context.events if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == context.matched_event[1]][0]
    player = interested_line[1]
    to_bottom = interested_line[3]
    ret.append(['ask_mulligan', player, to_bottom])
    return ret

SYSTEM_RULE_MULLIGAN_ASK = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
    (
        'When a player could take a mulligan',
        current_player_could_mulligan,
    ),
    (
        "And the game haven't ask the player",
        lambda context: not any('ask_mulligan' in line for line in context.events)
    ),
    (
        'Then the game asks the player for mulligan choices',
        ask_player_mulligan,
    ),
]

def current_player_has_kept_hand(context) -> bool:
    # expecting context.matched_event = ['mulligan_at', player_id]
    if context.matched_event[0] != 'mulligan_at':
        return False
    if any(not 'mulligan' in line[0] for line in context.events):
        # all events must contain 'mulligan'
        return False
    players = context.game.players
    # expecting interested_line = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested_lines = [l for l in context.events if (l[0] if l else None) == 'mulligan_state']
    interested_line = [l for l in interested_lines if players.index(l[1]) == context.matched_event[1]]
    if not interested_line:
        return False
    interested_line = interested_line[0]
    has_keep_hand = interested_line[2]
    return has_keep_hand

def increment_mulligan_at(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting line = ['mulligan_at', who_id]
    mulligan_at = [line for line in ret if line[0] == 'mulligan_at'][0]
    mulligan_at[1] += 1
    return ret

SYSTEM_RULE_MULLIGAN_SKIP = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
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
    # expecting line = ['mulligan', who_name]
    if context.matched_event[0] != 'mulligan':
        return False
    who_name = context.matched_event[1]
    who_id = [i for i, p in enumerate(context.game.players) if p.player_name == who_name][0]
    mulligan_at = [line for line in context.events if line[0] == 'mulligan_at'][0]
    return who_id == mulligan_at[1]

def increment_to_bottom(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting matched line = ['mulligan', who_name]
    who_name = context.matched_event[1]
    who = [player for player in context.game.players if player.player_name == who_name][0]
    # expecting interested = ['mulligan_state', player, has_keep_hand, to_bottom]
    interested = [line for line in ret if 'mulligan_state' in line and line[1] == who][0]
    interested[3] += 1
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_MULLIGAN_ANSWER = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
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
        'And the game consumes the matched events line',
        consume_line,
    ),
]

def current_player_wants_to_keep(context) -> bool:
    # expecting line = [ 'keep_hand', who_name, to_bottom: list[Card] ]
    if context.matched_event[0] != 'keep_hand':
        return False
    who_name = context.matched_event[1]
    who_id = [i for i, p in enumerate(context.game.players) if p.player_name == who_name][0]
    mulligan_at = [line for line in context.events if line[0] == 'mulligan_at'][0]
    return who_id == mulligan_at[1]

def bottom_mulligan_player_cards(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting matched_event = ['keep_hand', who_name, to_bottom: list[Card]]
    who_name = context.matched_event[1]
    who = [player for player in context.game.players if player.player_name == who_name][0]
    to_bottom = context.matched_event[2]
    ret.append(['bottom_cards', who, to_bottom])
    return ret

def set_player_has_keep(context) -> List[Any]:
    ret = [line for line in context.events]
    who_name = context.matched_event[1]
    # search for 'mulligan_state'
    # expecting ['mulligan_state', player, has_keep_hand, to_bottom]
    interested = [line for line in ret if line[0] == 'mulligan_state' and line[1].player_name == who_name][0]
    interested[2] = True
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_KEEP_ANSWER = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
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
        'And the game consumes the matched events line',
        consume_line,
    ),
]

def empty_all_mulligan_player_hand(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting [ 'mulligan_state', player, has_keep_hand, to_bottom ]
    mulliganing_players = [line[1] for line in context.events if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['bottom_cards', player, [card for card in player.hand]])
    return ret

def shuffle_all_mulligan_player_library(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting ['mulligan_state', player, has_keep_hand, to_bottom]
    mulliganing_players = [line[1] for line in context.events if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['shuffle', player])
    return ret

def deal_seven_to_all_mulligan_player(context) -> List[Any]:
    ret = [line for line in context.events]
    # expecting [ 'mulligan_state', player, has_keep_hand, to_bottom ]
    mulliganing_players = [line[1] for line in context.events if line[0] == 'mulligan_state' and not line[2]]
    for player in mulliganing_players:
        ret.append(['draw', player, 7])
    return ret

def reset_mulligan_at(context) -> List[Any]:
    ret = [line for line in context.events]
    line = [line for line in ret if line == context.matched_event][0]
    line[1] = 0
    return ret

SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_CONTINUE = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
    (
        'When mulligan_at exceeds the maximum player count',
        lambda context: 'mulligan_at' in context.matched_event and context.matched_event[1] >= len(context.game.players),
    ),
    (
        'And there exists one or more players who chose to take a mulligan',
        lambda context: any('mulligan_state' in line and not line[2] for line in context.events),
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

SYSTEM_RULE_MULLIGAN_HANDLE_OVERFLOW_FINISH = [
    (
        'Given the game is in the mulligan phase',
        lambda context: context.game.phase == 'mulligan phase'
    ),
    (
        'When mulligan_at exceeds the maximum player count',
        lambda context: 'mulligan_at' in context.matched_event and context.matched_event[1] >= len(context.game.players),
    ),
    (
        'And all players have kept their hand',
        lambda context: all(line[2] for line in [ line for line in context.events if 'mulligan_state' in line ])
    ),
    (
        'And there are no other things ongoing in the events list',
        lambda context: all('mulligan' in line[0] for line in context.events)
    ),
    (
        'Then the game proceeds to the next phase',
        lambda context: [['next_phase']]
    ),
]

SYSTEM_RULE_START_OF_GAME_CHECK = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When the game is in the start of game phase',
        lambda context: 'take start of game actions phase' == context.matched_event[0] and len(context.events) == 1,
    ),
    (
        'Then the game creates check_start_of_game_action',
        lambda context: [*context.events, ['check_start_of_game_action', 0]]
    ),
    (
        'And the game consumes the matched events line',
        consume_line,
    ),
]

def append_find_start_of_game_card_in_hand(context) -> List[Any]:
    ret = [line for line in context.events]
    # expect matched_event = ['check_start_of_game_action']
    who_id = context.matched_event[1]
    assert isinstance(who_id, int)
    ret.append(['scanning', who_id, 'hand']) # tell the engine that we are scanning
    ret.append(['scan_start_of_game_in_hand', who_id]) # tell the engine to scan the player's hand
    return ret

SYSTEM_RULE_START_OF_GAME_SCAN_HAND = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When the game checks for the current players for start of game action',
        lambda context: 'check_start_of_game_action' in context.matched_event,
    ),
    (
        'And the game is not scanning anything',
        lambda context: not any('scan' in line[0] for line in context.events),
    ),
    (
        "Then the game scans the current player's hand",
        append_find_start_of_game_card_in_hand,
    ),
]

SYSTEM_RULE_START_OF_GAME_END_SCAN = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When the game is checking start of game action',
        lambda context: 'check_start_of_game_action' in context.matched_event,
    ),
    (
        'And the game is scanning',
        lambda context: any('scanning' in line[0] for line in context.events),
    ),
    (
        'And the scan is done',
        lambda context: any('scan_done' in line[0] for line in context.events),
    ),
    (
        'Then the game consumes the scanning event',
        lambda context: [e for e in context.events if not 'scanning' in e[0]],
    ),
]

SYSTEM_RULE_START_OF_GAME_GIVE_PRIORITY = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When the game is checking start of game action',
        lambda context: 'check_start_of_game_action' in context.matched_event,
    ),
    (
        'And the game is not scanning',
        lambda context: not any('scanning' in line[0] for line in context.events),
    ),
    (
        'And there are interactable cards',
        lambda context: any('interactable' in line[0] and line[1] for line in context.events),
    ),
    (
        'And the priority is not yet given',
        lambda context: all('give_priority' not in line[0] for line in context.events),
    ),
    (
        'Then the game gives priority to the player',
        lambda context: [*context.events, ['give_priority', context.matched_event[1]]],
    ),
]

def increment_check_start_of_game_action(context) -> List[Any]:
    new_marker = context.matched_event
    new_marker[1] += 1
    return context.events

SYSTEM_RULE_START_OF_GAME_PROCEED_NEXT = [
    (
        'When the game is checking start of game action',
        lambda context: 'check_start_of_game_action' in context.matched_event,
    ),
    (
        'And the game is not scanning',
        lambda context: not any('scanning' in line[0] for line in context.events),
    ),
    (
        'And there are no interactable cards',
        lambda context: any('interactable' in line[0] and not line[1] for line in context.events),
    ),
    (
        'Then the game consumes interactable event',
        lambda context: [e for e in context.events if not 'interactable' in e[0]],
    ),
    (
        'And the game increments check_start_of_game_action',
        increment_check_start_of_game_action,
    ),
    (
        'And the game consumes the scan_done event',
        lambda context: [e for e in context.events if 'scan_done' not in e],
    ),
]

# Create rules for the engine
CHOOSE_STARTING_PLAYER_RULES = (
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_CHOOSE_STARTING_PLAYER_DECIDER_RANDOM)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_CHOOSE_STARTING_PLAYER_ASK)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_CHOOSE_STARTING_PLAYER_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_CHOOSE_STARTING_PLAYER_PROCEED)),
)

REVEAL_COMPANION_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_REVEAL_COMPANION_KICKSTART)),
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
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_END_SCAN)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_GIVE_PRIORITY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_PROCEED_NEXT)),
]

# EVERYTHING
SYSTEM_RULES = (
    *CHOOSE_STARTING_PLAYER_RULES,
    *REVEAL_COMPANION_RULES,
    *MULLIGAN_RULES,
    *START_OF_GAME_RULES,
)
