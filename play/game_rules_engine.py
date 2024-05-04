from dataclasses import dataclass
from typing import List
from .game import Game

STATE_BASED_ACTIONS = {
    "life_check": "check player life totals (win/loss)",
    "library_check": "check for empty libraries (win/loss)",
    "poison_check": "check for poison counters (win/loss)",
    "creature_toughness_check": "check creature toughness (destruction)",
    "creature_damage_check": "check creature damage (destruction)",
    "deathtouch_check": "check for deathtouch damage (destruction)",
    "planeswalker_loyalty_check": "check planeswalker loyalty (destruction)",
    "legend_rule": "check for legendary permanents duplicates",
    "world_rule": "check for world permanents duplicates",
    "aura_attachment_check": "check aura attachment validity",
    "equipment_attachment_check": "check equipment attachment validity",
    "fortification_attachment_check": "check fortification attachment validity",
    "counter_removal": "remove excess +1/+1 counters",
    "limited_counter_removal": "remove excess counters based on ability",
    "saga_completion_check": "check for saga completion (sacrifice)",
    "venture_completion_check": "check for completed venture (remove marker)",
    "space_sculptor_check": "assign sector designation for creatures",
    "battle_defense_check": "check battle defense (destruction)",
    "battle_protector_check": "assign protector for battle",
    "siege_protector_check": "assign protector for siege",
    "role_timestamp_check": "remove duplicate roles based on timestamp",
}

@dataclass
class GameRulesEngine:
    self.todo: List[str] = []
    self.gherkins: Dict[str, Dict[str, str]] = {}

    def repl(self, game):
        actions = []
        while self.todo:
            actions.append(self._print(self._evaluate(self._read(game))))
        return actions

    def _read(self, game) -> List[str], Dict[str, str]:
        # load what to do
        game.whiteboard.clear()
        game.whiteboard.append(self.todo.pop(0))
        # for each card not seen by the AI, ask it to write the gherkin rules for it
        players = game.board_state.players
        battlefield_cards = [ card for card in player.battlefield for player in players ]
        hand_cards = [ card for card in game.ned.hand ]
        # load replacement gherkins
        self.gherkins
    def _evaluate(self, game):
        pass
    def _print(self, game):
        pass

    def get_turn_based_actions(self, game):
        self.todo.clear()
        assert isinstance(game, Game)
        match game.phase:
            case 'untap step':
                self.todo.append("permanents the active player controls phase in")
                self.todo.append("check day or night")
                self.todo.append("permanents the active player controls untap")
            case 'draw step':
                self.todo.append("the active player draws a card")
            case 'precombat main phase':
                self.todo.append("add a lore counter on each saga the active player controls")
            case 'declare attackers step':
                self.todo.append("the active player declares attackers")
            case 'declare blockers step':
                self.todo.append("defending player declares blockers")
                self.todo.append("active player announces damage assignment order among blocking creatures")
                self.todo.append("defending player announces damage assignment order among attacking creatures")
                self.todo.append("active player announces how attacking creatures assign combat damage")
                self.todo.append("defending player announces how blocking creatures assign combat damage")
                self.todo.append("deal combat damage")
            case 'cleanup step':
                self.todo.append("active player discards down to hand size")
                self.todo.append("remove all damage on permanents and end \"until end of turn\" or \"this turn\" effects")
        return self.repl(game)

    def get_state_based_actions(self, game):
        assert isinstance(game, Game)
        for k, v in STATE_BASED_ACTIONS.items:
            self.todo.insert(v)
        return self.repl(game)
