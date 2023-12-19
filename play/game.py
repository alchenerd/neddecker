class Player:
    def __init__(self):
        # snapshot const
        self._mainboard = []
        self._sideboard = []
        # game variables
        self.sideboard = []
        self.library = []
        self.battlefield = []
        self.hand = []
        self.graveyard = []
        self.exile = []
        self.hitpoints = 20

class Game:
    def __init__(self):
        self.card_map = {}
        self.player1 = Player()
        self.player2 = Player()
        self.stack = []

class Match:
    def __init__(self):
        self.game = Game()
