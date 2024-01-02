class Players():
    def __init__(self, players):
        assert(isinstance(players, list) and
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
        # (name, playersGetsPriority)
        ('beginning phase', False),
        ('untap step', False),
        ('upkeep step', True),
        ('draw step', True),
        ('precombat main phase', True),
        ('combat phase', False),
        ('beginning of combat step', True),
        ('declare attackers step', True),
        ('declare blockers step', True),
        ('combat damage step', True),
        ('end of combat step', True),
        ('postcombat main phase', True),
        ('ending phase', False),
        ('end step', True),
        ('cleanup step', False),
    ]

    def __init__(self, players):
        assert(isinstance(players, list) and
               len(players) >= 2 and
               len(set(players)) == len(players) and
               all((isinstance(player, str) for player in players))
        )
        self.turn_ring = players
        self.turn_stack = []
        self.turn_ring_length = len(self.turn_ring)
        self.phase_queue = list(MtgTurnsAndPhases.PHASES_AND_STEPS)
        # this is also seen at __iter__
        self.turn_count = 1
        self.turn_index = 0

    def __iter__(self):
        self.turn_count = 1
        self.turn_index = 0
        self.phase_queue = list(MtgTurnsAndPhases.PHASES_AND_STEPS)
        return self

    def __next__(self):
        turn, cycle, whose, phase = None, None, None, None
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
        cycle = turn // self.turn_ring_length + (1 if (turn % self.turn_ring_length) else 0)
        return turn, cycle, whose, phase

    def add_extra_turn(self, player):
        assert(isinstance(player, str) and player in turn_ring)
        self.turn_stack.append(player)

    def add_extra_phase(self, phase, after_which):
        assert(isinstance(phase, str) or isinstance(phase, int))
        assert(isinstance(after_which, str) or isinstance(after_which, int))
        if isinstance(phase, int):
            assert(phase >= 0 and phase < len(MtgTurnAndPhaseIterator.PHASES_AND_STEPS))
            phase = MtgTurnAndPhaseIterator.PHASES_AND_STEPS[phase]
        elif isinstance(phase, str):
            phase = [p for p in MtgTurnAndPhaseIterator.PHASES_AND_STEPS if p[0] == phase][-1]
        if isinstance(after_which, int):
            assert(after_which >= 0 and after_which < len(MtgTurnAndPhaseIterator.PHASES_AND_STEPS))
            after_which = MtgTurnAndPhaseIterator.PHASES_AND_STEPS[phase][0]
        for i in range(self.phase_queue):
            if self.phase_queue[i][0] == after_which:
                self.phase_queue.insert(i, phase)
                return
        raise ValueError
