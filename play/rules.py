from dataclasses import dataclass, field
from typing import List, OrderedDict, Callable, Any, Union
from collections import OrderedDict as CollectionsOrderedDict
from deprecated import deprecated
import random
import re
from .game import Game
from .iterables import MtgTurnsAndPhases as MtgTnP

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
    # expecting matched_event = ['keep_hand', who_name, to_bottom: list[in_game_id]]
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
        ret.append(['bottom_cards', player, [card['in_game_id'] for card in player.hand]])
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
        lambda context: 'check_start_of_game_action' in context.matched_event and len(context.events) == 1,
    ),
    (
        'And the player ID has not overflowed',
        lambda context: context.matched_event[-1] < len(context.game.players),
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

SYSTEM_RULE_START_OF_GAME_GIVE_PRIORITY = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When there are interactable cards',
        lambda context: 'interactable' == context.matched_event[0] and context.matched_event[1],
    ),
    (
        'And the game is checking start of game action',
        lambda context: any('check_start_of_game_action' == e[0] for e in context.events),
    ),
    (
        'And the scan is done',
        lambda context: any('scan_done' == line[0] for line in context.events),
    ),
    (
        'And the priority is not yet given',
        lambda context: all('give_priority' != line[0] for line in context.events),
    ),
    (
        'Then the game gives priority to the player',
        lambda context: [*context.events, ['give_priority', [e for e in context.events if e[0] == 'check_start_of_game_action'][0][1], context.matched_event[1]]],
    ),
    (
        'And the game consumes the scan_done event',
        lambda context: [e for e in context.events if 'scan_done' not in e],
    ),
]

def increment_check_start_of_game_action(context) -> List[Any]:
    new_marker = [e for e in context.events if 'check_start_of_game_action' == e[0]][0]
    new_marker[1] += 1
    return context.events

SYSTEM_RULE_START_OF_GAME_PROCEED_NEXT = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When there are no interactable cards',
        lambda context: 'interactable' == context.matched_event[0] and not context.matched_event[1],
    ),
    (
        'And the game is checking start of game action',
        lambda context: any('check_start_of_game_action' == e[0] for e in context.events),
    ),
    (
        'And the game is not taking start of game actions',
        lambda context: not any('taking_start_of_game_action' == line[0] for line in context.events),
    ),
    (
        'Then the game consumes interactable event',
        lambda context: [e for e in context.events if not 'interactable' in e[0]],
    ),
    (
        'And the game consumes the scan_done event',
        lambda context: [e for e in context.events if 'scan_done' not in e],
    ),
    (
        'And the game increments check_start_of_game_action',
        increment_check_start_of_game_action,
    ),
]

SYSTEM_RULE_START_OF_GAME_TAKE_ACTION = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase',
    ),
    (
        'When the player responds to interact with a card',
        lambda context: 'interact' == context.matched_event[0],
    ),
    (
        'And the game is pending pass priority',
        lambda context: any('pending_pass_priority' == e[0] for e in context.events)
    ),
    (
        'Then consume the pending_pass_priority event',
        lambda context: [e for e in context.events if 'pending_pass_priority' != e[0]],
    ),
    (
        'And take start of game action with that card',
        lambda context: [*context.events, ['take_start_of_game_action', *context.matched_event[1:]]],
    ),
    (
        'And append taking_start_of_game_action',
        lambda context: [*context.events, ['taking_start_of_game_action']],
    ),
    (
        'And consume the interact event',
        lambda context: [e for e in context.events if 'interact' != e[0]],
    ),
]

SYSTEM_RULE_START_OF_GAME_OVERFLOW = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When the game checks for the current players for start of game action',
        lambda context: 'check_start_of_game_action' in context.matched_event and len(context.events) == 1,
    ),
    (
        'And the player index overflows',
        lambda context: context.matched_event[-1] >= len(context.game.players),
    ),
    (
        'Then the game proceeds to the next phase',
        lambda context: [['next_phase']]
    ),
]

SYSTEM_RULE_START_OF_GAME_PASS_PRIORITY = [
    (
        'Given the game is in the take start of game actions phase',
        lambda context: context.game.phase == 'take start of game actions phase'
    ),
    (
        'When a player passes priority',
        lambda context: 'pass_priority' == context.matched_event[0],
    ),
    (
        'And the game checks for the current players for start of game action',
        lambda context: any('check_start_of_game_action' == e[0] for e in context.events),
    ),
    (
        'And that player is the current target',
        lambda context: context.game.players.index(context.matched_event[1]) == [e for e in context.events if 'check_start_of_game_action' == e[0]][0][1],
    ),
    (
        'Then consume the current line',
        consume_line,
    ),
    (
        'And the game increments check_start_of_game_action',
        increment_check_start_of_game_action,
    ),
    (
        'And consume all other data',
        lambda context: [e for e in context.events if e[0] == 'check_start_of_game_action'],
    ),
]

SYSTEM_RULE_BEGINNING_PHASE_PROCEED = [
    (
        'Given the game is in the beginning phase',
        lambda context: context.game.phase == 'beginning phase',
    ),
    (
        'When the game is at the beginning of beginning phase',
        lambda context: len(context.events) == 1 and 'beginning phase' == context.matched_event[0],
    ),
    (
        'Then the game proceeds to the next phase',
        lambda context: [['next_step']]
    ),
]

SYSTEM_RULE_UNTAP_STEP_PHASING = [
    (
        'Given the game is in the untap step',
        lambda context: context.game.phase == 'untap step',
    ),
    (
        'When the game is at the beginning of the untap step',
        lambda context: len(context.events) == 1 and 'untap step' == context.matched_event[0],
    ),
    (
        'Then call handle_phasing',
        lambda context: [*context.events, ['handle_phasing']],
    ),
    (
        'And consume the current line',
        consume_line,
    ),
]

SYSTEM_RULE_UNTAP_STEP_DAY_NIGHT = [
    (
        'Given the game is in the untap step',
        lambda context: context.game.phase == 'untap step',
    ),
    (
        'When the game is done handling checking phasing',
        lambda context: len(context.events) == 1 and 'handle_phasing_done' == context.matched_event[0],
    ),
    (
        'Then call handle_day_night',
        lambda context: [*context.events, ['handle_day_night']],
    ),
    (
        'And consume the current line',
        consume_line,
    ),
]

SYSTEM_RULE_UNTAP_STEP_UNTAP = [
    (
        'Given the game is in the untap step',
        lambda context: context.game.phase == 'untap step',
    ),
    (
        'When the game is done handling day and night',
        lambda context: len(context.events) == 1 and 'handle_day_night_done' == context.matched_event[0],
    ),
    (
        'Then call handle_untap_step',
        lambda context: [*context.events, ['handle_untap_step']],
    ),
    (
        'And consume the current line',
        consume_line,
    ),
]

SYSTEM_RULE_UNTAP_STEP_PROCEED = [
    (
        'Given the game is in the untap step',
        lambda context: context.game.phase == 'untap step',
    ),
    (
        'When the game is done handling untap step',
        lambda context: len(context.events) == 1 and 'handle_untap_step_done' == context.matched_event[0],
    ),
    (
        'Then proceed to the upkeep step',
        lambda context: [['next_step']],
    ),
]

# FIXME: make generic priority giver rules
SYSTEM_RULE_UPKEEP_STEP_GIVE_PRIORITY = [
    (
        'Given the game is in the upkeep step',
        lambda context: context.game.phase == 'upkeep step'
    ),
    (
        'When the game is at the beginning of the upkeep step',
        lambda context: len(context.events) == 1 and 'upkeep step' == context.matched_event[0],
    ),
    (
        'Then the player has priority',
        lambda context: [*context.events, ['player_has_priority']],
    ),
]


def game_allows_player_to_have_priorty(context) -> bool:
    game = context.game
    return bool(game.stack) or (game.player_has_priority and all(game.phase != p[0] for p in MtgTnP.ONE_SHOT_PSEUDO_PHASES))

# before giving priority, state-based actions are checked
SYSTEM_RULE_PRIORITY_CHECK_SBA = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game is ready to give priority to players',
        lambda context: 'player_has_priority' == context.matched_event[0],
    ),
    (
        'And state-based actions are untouched',
        lambda context: not any('sba' in e[0] for e in context.events),
    ),
    (
        'Then call check_sba',
        lambda context: [*context.events, ['check_sba']],
    ),
]

def give_priority_to_appropriate_player(context) -> List[Any]:
    game = context.game
    players = game.players
    stack = game.stack
    # initialize i as the active_player
    i = [i for i, p in enumerate(players) if p.player_name == game.whose_turn][0]
    # if stack is not empty, check starts from the controller of top of stack
    if stack:
        card = stack[-1]
        who_name = card.get('annotations', {}).get('controller')
        i = [i for i, p in enumerate(players) if p.player_name == who_name][0]
    passed_players = {e[1] for e in context.events if e[0] == 'pass_priority'}
    n = len(players)
    for _ in range(n):
        if players[i] not in passed_players:
            return [*context.events, ['give_priority', i, None]]
        i = (i + 1) % n
    return [['resolve', stack[-1]]] if stack else [['next_step']]

# then if sba check is done, give priority
SYSTEM_RULE_PRIORITY_GIVE_PRIORITY = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game has done checking state-based action',
        lambda context: 'check_sba_done' == context.matched_event[0],
    ),
    (
        'And the game is not giving out priority',
        lambda context: not any('give_priority' == e[0] for e in context.events),
    ),
    (
        'And the game is not pending pass priority',
        lambda context: not any('pending_pass_priority' == e[0] for e in context.events),
    ),
    (
        'Then call give_priority with appropriate player',
        give_priority_to_appropriate_player,
    ),
]

def current_player_passed_priority(context) -> bool:
    events = context.events
    passed_events = [e for e in events if e[0] == 'pass_priority']
    if not passed_events:
        return False
    pending_event = [e for e in events if e[0] == 'pending_pass_priority'][0]
    pending_player = context.game.players[pending_event[1]]
    return any(e[1] == pending_player for e in passed_events)

# then player passes priority
SYSTEM_RULE_PRIORITY_HANDLE_PASS_PRIORITY = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game is waiting for a player to pass priority',
        lambda context: 'pending_pass_priority' == context.matched_event[0],
    ),
    (
        'And that player has passed priority',
        current_player_passed_priority,
    ),
    (
        'Then consume the pending priority event',
        consume_line,
    ),
]


def check_zero_or_less_life(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        if player.hp <= 0:
            events.append(['lose_the_game', player])
    matched_event = [e for e in events if e[0] == 'sba_check_zero_or_less_life'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_ZERO_OR_LESS_LIFE = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for zero or less life',
        lambda context: 'sba_check_zero_or_less_life' == context.matched_event[0],
    ),
    (
        'Then check for zero or less life',
        check_zero_or_less_life,
    ),
]

def check_draw_from_empty_library(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        has_drawn_from_empty_library = getattr(player, 'has_drawn_from_empty_library', False)
        if has_drawn_from_empty_library:
            events.append(['lose_the_game', player])
    matched_event = [e for e in events if e[0] == 'sba_check_draw_from_empty_library'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_DRAW_FROM_EMPTY_LIBRARY = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check draw from empty library',
        lambda context: 'sba_check_draw_from_empty_library' == context.matched_event[0],
    ),
    (
        'Then check if any player drew from an empty library',
        check_draw_from_empty_library,
    ),
]

def check_ten_or_more_poison_counters(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        poison = player.counters.get('poison', 0)
        if poison >= 10:
            events.append(['lose_the_game', player])
    matched_event = [e for e in events if e[0] == 'sba_check_ten_or_more_poison_counters'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_TEN_OR_MORE_POISON_COUNTERS = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for ten or more poison counters',
        lambda context: 'sba_check_ten_or_more_poison_counters' == context.matched_event[0],
    ),
    (
        'Then check if any player has ten or more poison counters',
        check_ten_or_more_poison_counters,
    ),
]

def check_non_battlefield_tokens(context) -> List[Any]:
    game = context.game
    stack = game.stack
    players = game.players
    zones_to_check = [
        'library',
        'hand',
        'graveyard',
        'exile',
        'command',
        'ante',
    ]
    # all tokens in non-battlefield zones ceases to exist
    stack = filter(lambda x: not x['in_game_id'].startswith('token#'), stack)
    for player in players:
        for zone in zones_to_check:
            current_zone = getattr(player, zone)
            current_zone = filter(lambda x: not x['in_game_id'].startswith('token#'), current_zone)
    # mark as done
    events = [*context.events]
    matched_event = [e for e in events if e[0] == 'sba_check_non_battlefield_tokens'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events


SYSTEM_RULE_SBA_CHECK_NON_BATTLEFIELD_TOKENS = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for non-battlefield tokens',
        lambda context: 'sba_check_non_battlefield_tokens' == context.matched_event[0],
    ),
    (
        'Then check non-battlefield tokens',
        check_non_battlefield_tokens,
    ),
]

def check_misplaced_copies(context) -> List[Any]:
    players = context.game.players
    zones_to_check = [
        'library',
        'hand',
        'graveyard',
        'exile',
        'command',
        'ante',
    ]
    for player in players:
        for zone in zones_to_check:
            current_zone = getattr(player, zone)
            current_zone = filter(lambda x: not x['in_game_id'].startswith('copy#'), current_zone)
        battlefield = filter( \
                lambda: not x['in_game_id'].startswith('copy#') and \
                any(y in x['type_line'] for y in ('instant', 'sorcery')), player.battlefield)
    # mark as done
    events = [*context.events]
    matched_event = [e for e in events if e[0] == 'sba_check_misplaced_copies'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_MISPLACED_COPIES = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for misplaced copies',
        lambda context: 'sba_check_misplaced_copies' == context.matched_event[0],
    ),
    (
        'Then check non-battlefield tokens',
        check_misplaced_copies,
    ),
]

def check_creature_zero_or_less_toughness(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'creature' in card['type_line'].lower():
                # FIXME: implement applying static effects on board state and deal with "*" toughness
                if 'toughness' in card and int(card['toughness']) <= 0:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_creature_zero_or_less_toughness'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_CREATURE_ZERO_OR_LESS_TOUGHNESS = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for creatures with zero or less toughness',
        lambda context: 'sba_check_creature_zero_or_less_toughness' == context.matched_event[0],
    ),
    (
        'Then check zero or less toughness',
        check_creature_zero_or_less_toughness,
    ),
]

def check_lethal_damage(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'creature' in card['type_line'].lower():
                toughness = card.get('toughness', 0)
                marked_damage = 0
                annotations = card.get('annotations', {})
                for key in annotations:
                    if key.endswith('damage'):
                        marked_damage += annotation[key]
                # FIXME: implement applying static effects on board state and deal with "*" toughness
                if marked_damage >= toughness:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_lethal_damage'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_LETHAL_DAMAGE = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for creatures dealt lethal damage',
        lambda context: 'sba_check_lethal_damage' == context.matched_event[0],
    ),
    (
        'Then check lethal damage',
        check_lethal_damage,
    ),
]

def check_deathtouch_damage(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'creature' in card['type_line'].lower():
                deathtouch_damage = card.get('annotations', {}).get('deathtouch_damage', 0)
                if deathtouch_damage:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_deathtouch_damage'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_DEATHTOUCH_DAMAGE = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for creatures dealt deathtouch damage',
        lambda context: 'sba_check_deathtouch_damage' == context.matched_event[0],
    ),
    (
        'Then check deathtouch damage',
        check_deathtouch_damage,
    ),
]

def check_planeswalker_loyalty(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'planeswalker' in card['type_line'].lower():
                loyalty = card.get('counters', {}).get('loyalty', 0)
                if not loyalty:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_planeswalker_loyalty'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_PLANESWALKER_LOYALTY = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for planeswalker loyalty',
        lambda context: 'sba_check_planeswalker_loyalty' == context.matched_event[0],
    ),
    (
        'Then check planeswalker loyalty',
        check_planeswalker_loyalty,
    ),
]

ASK_LEGEND_RULE_STRING = "All but one of these cards need to be sacrificed because of the Legend Rule. Which card to keep on the battlefield?"

def check_legend_rule(context) -> List[Any]:
    """Append to event ['ask_legend_rule', player, card_name] or ['done_check_legend_rule',]"""
    events = [*context.events]
    matched_event = [e for e in events if e[0] == 'sba_check_legend_rule'][0]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        seen_legendary_names = set()
        for card in battlefield:
            if 'legendary' in card['type_line'].lower():
                if card['name'] in seen_legendary_names:
                    matched_event[0] = matched_event[0].replace('sba', 'sba_ask')
                    events.append(['ask_check_legend_rule', player, ASK_LEGEND_RULE_STRING, card['name']])
                    return events
                else:
                    seen_legendary_names.add(card['name'])
    # mark as done
    matched_event[0] = matched_event[0].replace('sba_ask', 'done').replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_LEGEND_RULE = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for legend rule',
        lambda context: 'sba_check_legend_rule' == context.matched_event[0],
    ),
    (
        'Then check legend rule',
        check_legend_rule,
    ),
]

def handle_legendary_rule_question_is_answered(context) -> bool:
    events = context.events
    matched = context.matched_event
    if matched[0] != 'answer_question':
        return False
    pending = [e for e in events if e[0] == 'sba_ask_check_legend_rule']
    if len(pending) != 1:
        return False
    pending = pending[0]
    tag, who, question, answer = matched
    if question != ASK_LEGEND_RULE_STRING:
        return False
    return True

def handle_legendary_rule_answer(context) -> List[Any]:
    matched = context.matched_event
    events = [e for e in context.events if e is not matched]
    *_, player, question, answer = matched
    expr = r'\b[a-zA-Z](\d+)\#(\d+)\b'
    result = re.search(expr, answer)
    if result is None:
        return events
    in_game_id = result.group(0)
    assert isinstance(in_game_id, str)
    battlefield = player.battlefield
    chosen = [card for card in battlefield if card['in_game_id'] == in_game_id]
    name = chosen['name']
    to_sac = [card for card in player.battlefield if card['name'] == name and card is not chosen]
    for card in to_sac:
        events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    matched = [e for e in events if e[0] == 'sba_ask_check_legend_rule'][0]
    matched[0].replace('sba_ask', 'sba') # resume state-based action check
    return events

SYSTEM_RULE_SBA_CHECK_LEGEND_RULE_HANDLE_ANSWER = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When an asked player answers which legendary permanent to keep',
        handle_legendary_rule_question_is_answered,
    ),
    (
        'Then handle the answer',
        handle_legendary_rule_answer,
    ),
]

def check_aura_attachment(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'aura' in card['type_line'].lower():
                # check if it's attached to nothing or an illegal object
                annotations = card.get('annotations', [])
                attached_to = annotations.get('attaching', '')
                if not attached_to:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
                elif ['cant_attach', card, attached_to] in events:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_aura_attachment'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_AURA_ATTACHMENT = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for aura attachment',
        lambda context: 'sba_check_aura_attachment' == context.matched_event[0],
    ),
    (
        'Then check aura attachment',
        check_aura_attachment,
    ),
]

def check_equipment_or_fortification_attachment(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if any(x in card['type_line'].lower() for x in ('equipment', 'fortification')):
                # check if it's attached to nothing or an illegal object
                annotations = card.get('annotations', [])
                attached_to = annotations.get('attaching', '')
                if not attached_to:
                    continue
                if ['cant_attach', card, attached_to] in events:
                    del annotations['attaching']
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_equipment_or_fortification_attachment'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_EQUIPMENT_OR_FORTIFICATION_ATTACHMENT = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for equipment or fortification attachment',
        lambda context: 'sba_check_equipment_or_fortification_attachment' == context.matched_event[0],
    ),
    (
        'Then check equipment or fortification attachment',
        check_equipment_or_fortification_attachment,
    ),
]

def check_battle_or_creature_attachment(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if all(x not in card['type_line'].lower() for x in ('aura', 'equipment', 'fortification')):
                # check if it's attached to nothing or an illegal object
                annotations = card.get('annotations', [])
                attached_to = annotations.get('attaching', '')
                if not attached_to:
                    continue
                if ['cant_attach', card, attached_to] in events:
                    del annotations['attaching']
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_battle_or_creature_attachment'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_BATTLE_OR_CREATURE_ATTACHMENT = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for battle or creature attachment',
        lambda context: 'sba_check_battle_or_creature_attachment' == context.matched_event[0],
    ),
    (
        'Then check battle or creature attachment',
        check_battle_or_creature_attachment,
    ),
]

def check_plus_one_minus_one_counters(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            counters = card.get('counters', {})
            plus = counters.get('+1/+1', 0)
            minus = counters.get('-1/-1', 0)
            minimum = min(plus, minus)
            if not minimum:
                continue
            for key in ('+1/+1', '-1/-1'):
                counters[key] -= minimum
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_plus_one_minus_one_counters'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_PLUS_ONE_MINUS_ONE_COUNTERS = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for plus one and minus one counters',
        lambda context: 'sba_check_plus_one_minus_one_counters' == context.matched_event[0],
    ),
    (
        'Then check plus one and minus one counters',
        check_plus_one_minus_one_counters,
    ),
]

def check_saga(context) -> List[Any]:
    def get_max_chapter(oracle_text: str) -> int:
        if not oracle_text:
            return 0
        if oracle_text.lower() == oracle_text:
            raise ValueError('Please check if you have passed in roman numeral in capitalized letters')
        roman_numerals = ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII') # currently max chapter is 6
        for i, num in enumerate(roman_numerals):
            if num not in oracle_text:
                return i
        raise NotImplementedError('Too many chapter levels')

    events = [*context.events]
    players = context.game.players
    stack = context.game.stack
    sources = [card['annotations']['source'] for card in stack if card.get('annotaitons', {}).get('source', None)]
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'saga'in card['type_line'].lower() and card not in sources:
                is_face_down = card.get('annotations', {}).get('is_face_down', False)
                face = 'back' if is_face_down else 'front'
                oracle_text = card.get('oracle_text', '') or card.get('faces', {}).get(face, {}).get('oracle_text', '')
                max_chapter = get_max_chapter()
                lore_count = card.get('counters', {}).get('lore', 0)
                if lore_count >= max_chapter:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_saga'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_SAGA = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for ending sagas',
        lambda context: 'sba_check_saga' == context.matched_event[0],
    ),
    (
        'Then check saga',
        check_saga,
    ),
]

def check_dungeon(context) -> List[Any]:
    LAST_ROOMS = ('Steel Watch Foundry', "Ansur's Sanctum", 'Temple of Bhaal', "Mad Wizard's Lair", 'Cradle of the Death God', 'Throne of the Dead Tree', 'Temple of Dumathoin',)
    events = [*context.events]
    players = context.game.players
    stack = context.game.stack
    sources = [card['annotations']['source'] for card in stack if card.get('annotaitons', {}).get('source', None)]
    for player in players:
        command = player.command
        to_remove = None
        for item in command:
            if 'dungeon' in item.get('type_line').lower():
                where = item.get('annotations', {}).get('venture_marker', '').replace('’', "'")
                if where in LAST_ROOMS and where not in sources:
                    to_remove = item
                    break
        if to_remove:
            command.remove(to_remove)
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_dungeon'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_DUNGEON = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for completed dungeon',
        lambda context: 'sba_check_dungeon' == context.matched_event[0],
    ),
    (
        'Then check dungeon',
        check_dungeon,
    ),
]

def check_battle_zero_or_less_defense(context) -> List[Any]:
    events = [*context.events]
    players = context.game.players
    stack = context.game.stack
    sources = [card['annotations']['source'] for card in stack if card.get('annotaitons', {}).get('source', None)]
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'battle' in card['type_line'].lower() and card not in sources:
                defense = card.get('counters', {}).get('defense', 0)
                if not defense:
                    events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_battle_zero_or_less_defense'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_BATTLE_ZERO_OR_LESS_DEFENSE = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for battles with zero or less defense',
        lambda context: 'sba_check_battle_zero_or_less_defense' == context.matched_event[0],
    ),
    (
        'Then check battles with zero or less defense',
        check_battle_zero_or_less_defense,
    ),
]

def check_battle_designation(context) -> List[Any]:
    def has_protector(card) -> bool:
        try:
            return bool(card['annotations']['protector'])
        except:
            return False
        return False

    def get_attacked_permanents(players) -> List[Any]:
        battlefield = [card for player in players for card in player.battlefield]
        attacked = []
        for card in battlefield:
            try:
                attacking = card['annotation']['attacking']
                attacked.append(attacking)
            except:
                continue

    def get_eligible_protectors(players, card) -> List[Any]:
        ret = []
        try:
            type_line = card.get('type_line').lower
            owner_name = 'user' if 'u' in card.get('in_game_id') else 'ned'
            owner = [p for p in players if p.player_name == owner_name][0]
            opponents = [p for p in players if p is not owner]
            if 'siege' not in type_line:
                raise NotImplementedError('Battle only has Siege')
            return opponents
        except:
            return ret

    events = [*context.events]
    players = context.game.players
    attacked = get_attacked_permanents(players)
    for player in players:
        battlefield = player.battlefield
        for card in battlefield:
            if 'battle' in card['type_line'].lower():
                if has_protector(card) and card not in attacked:
                    eligible_protectors = get_eligible_protectors(players, card)
                    if not eligible_protectors:
                        events.append(['move', card, f'{player.player_name}.battlefield', f'{player.player_name}.graveyard'])
                    else:
                        opponent = eligible_protectors[-1]
                        card['annotation']['protector'] = opponent.player_name
    # mark as done
    matched_event = [e for e in events if e[0] == 'sba_check_battle_designation'][0]
    matched_event[0] = matched_event[0].replace('sba', 'done')
    return events

SYSTEM_RULE_SBA_CHECK_BATTLE_DESIGNATION = [
    (
        'Given the game is in a phase or step that gives players priority',
        game_allows_player_to_have_priorty,
    ),
    (
        'When the game needs to check for battle designation',
        lambda context: 'sba_check_battle_designation' == context.matched_event[0],
    ),
    (
        'Then check battle designation',
        check_battle_designation,
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
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_PASS_PRIORITY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_GIVE_PRIORITY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_PROCEED_NEXT)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_TAKE_ACTION)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_START_OF_GAME_OVERFLOW)),
]

BEGINNING_PHASE_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_BEGINNING_PHASE_PROCEED)),
]

UNTAP_STEP_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_UNTAP_STEP_PHASING)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_UNTAP_STEP_DAY_NIGHT)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_UNTAP_STEP_UNTAP)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_UNTAP_STEP_PROCEED)),
]

UPKEEP_STEP_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_UPKEEP_STEP_GIVE_PRIORITY)),
]

GENERAL_PRIORITY_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_PRIORITY_CHECK_SBA)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_PRIORITY_GIVE_PRIORITY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_PRIORITY_HANDLE_PASS_PRIORITY)),
]

SBA_RULES = [
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_ZERO_OR_LESS_LIFE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_DRAW_FROM_EMPTY_LIBRARY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_TEN_OR_MORE_POISON_COUNTERS)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_NON_BATTLEFIELD_TOKENS)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_MISPLACED_COPIES)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_CREATURE_ZERO_OR_LESS_TOUGHNESS)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_LETHAL_DAMAGE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_DEATHTOUCH_DAMAGE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_PLANESWALKER_LOYALTY)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_LEGEND_RULE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_LEGEND_RULE_HANDLE_ANSWER)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_AURA_ATTACHMENT)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_EQUIPMENT_OR_FORTIFICATION_ATTACHMENT)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_BATTLE_OR_CREATURE_ATTACHMENT)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_PLUS_ONE_MINUS_ONE_COUNTERS)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_SAGA)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_DUNGEON)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_BATTLE_ZERO_OR_LESS_DEFENSE)),
    Rule.from_implementations(CollectionsOrderedDict(SYSTEM_RULE_SBA_CHECK_BATTLE_DESIGNATION)),
]

# EVERYTHING
SYSTEM_RULES = (
    *CHOOSE_STARTING_PLAYER_RULES,
    *REVEAL_COMPANION_RULES,
    *MULLIGAN_RULES,
    *START_OF_GAME_RULES,
    *BEGINNING_PHASE_RULES,
    *UNTAP_STEP_RULES,
    *GENERAL_PRIORITY_RULES,
    *SBA_RULES,
    *UPKEEP_STEP_RULES,
)
