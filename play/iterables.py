class Players():
    def __init__(self, players):
        assert (
            isinstance(players, list) and
            len(players) >= 2 and
            len(set(players)) == len(players) and
            all((isinstance(player, str) for player in players))
        )
        self.ring = players
        self.index = 0
    def __iter__(self):
        self.index = 0
    def __next__(self):
        who = self.ring[self.index]
        self.index = (self.index + 1) % len(self.ring)
        return who

class MtgTurnsAndPhases():
    PHASES_AND_STEPS = [
        # (name, playerGetsPriority, requirePlayerAct)
        # ('start of game phase', False, True), # This is added in initialization
        ('beginning phase', False, False),
        ('untap step', False, True),
        ('upkeep step', True, True),
        ('draw step', True, True),
        ('precombat main phase', True, True),
        ('combat phase', False, False),
        ('beginning of combat step', True, True),
        ('declare attackers step', True, True),
        ('declare blockers step', True, True),
        ('combat damage step', True, True),
        ('end of combat step', True, True),
        ('postcombat main phase', True, True),
        ('ending phase', False, False),
        ('end step', True, True),
        ('cleanup step', False, True),
    ]

    ONE_SHOT_PSEUDO_PHASES = [
        ('determine starting player', False, True),
        ('reveal companion', True, True),
        ('mulligan', True, True),
        ('take start of game actions', True, True),
    ]

    def __init__(self, players):
        assert (
            isinstance(players, list) and
            len(players) >= 2 and
            len(set(players)) == len(players) and
            all((isinstance(player, str) for player in players))
        )
        self.turn_ring = players
        self.turn_stack = []
        self.turn_ring_length = len(self.turn_ring)
        self.phase_queue = []
        self.phase_queue.extend(list(MtgTurnsAndPhases.ONE_SHOT_PSEUDO_PHASES))
        self.phase_queue.extend(list(MtgTurnsAndPhases.PHASES_AND_STEPS))
        # this is also seen at __iter__
        self.turn_count = 1
        self.turn_index = 0

    def __iter__(self):
        self.turn_count = 1
        self.turn_index = 0
        self.phase_queue = []
        self.phase_queue.extend(list(MtgTurnsAndPhases.ONE_SHOT_PSEUDO_PHASES))
        self.phase_queue.extend(list(MtgTurnsAndPhases.PHASES_AND_STEPS))
        return self

    def __next__(self):
        turn, whose, phase = None, None, None
        turn_ended = False
        if len(self.phase_queue) == 0:
            self.phase_queue.extend(MtgTurnsAndPhases.PHASES_AND_STEPS)
            turn_ended = True
            self.turn_count += 1
        phase = self.phase_queue.pop(0)
        turn = self.turn_count
        if len(self.turn_stack) > 0:
            whose = self.turn_stack.pop()
        if not whose and turn_ended:
            self.turn_index = ((self.turn_index + 1) % self.turn_ring_length)
        whose = self.turn_ring[self.turn_index]
        return turn, whose, phase

    def add_extra_turn(self, player):
        assert (isinstance(player, str) and player in turn_ring)
        self.turn_stack.append(player)

    def add_extra_phase(self, phase, after_which):
        assert (isinstance(phase, str) or isinstance(phase, int))
        assert (isinstance(after_which, str) or isinstance(after_which, int))
        if isinstance(phase, int):
            assert (phase >= 0 and phase < len(MtgTurnAndPhaseIterator.PHASES_AND_STEPS))
            phase = MtgTurnAndPhaseIterator.PHASES_AND_STEPS[phase]
        elif isinstance(phase, str):
            phase = [p for p in MtgTurnAndPhaseIterator.PHASES_AND_STEPS if p[0] == phase][-1]
        if isinstance(after_which, int):
            assert (after_which >= 0 and after_which < len(MtgTurnAndPhaseIterator.PHASES_AND_STEPS))
            after_which = MtgTurnAndPhaseIterator.PHASES_AND_STEPS[phase][0]
        for i in range(self.phase_queue):
            if self.phase_queue[i][0] == after_which:
                self.phase_queue.insert(i, phase)
                return
        raise ValueError
