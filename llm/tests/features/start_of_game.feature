Feature: AI player acts in the start of game phase of an Magic: the Gathering game

    Background: the AI player is connected via OpneAI's API
        Given the AI player for start of game is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something

    Scenario: the AI player has nothing to do
        Given the AI has nothing to do at the start of the game
        When the system asks the AI player for start of game decisions
        Then the AI player does nothing

    Scenario: [CR 103.2b] the AI player reveals a companion
        Given the AI player has one companion card in sideboard
        When the system asks the AI player for start of game decisions
        Then the AI Player marks the card as companion

    Scenario: the AI player reveals Chancellor of the Dross
        Given the AI player has one Chancellor of the Dross in hand
        When the system asks the AI player for start of game decisions
        Then the AI player registers a delayed trigger for Chancellor of the Dross

    Scenario: the AI player reveals three Chancellor of the Dross
        Given the AI player has three Chancellor of the Dross in hand
        When the system asks the AI player for start of game decisions
        Then the AI player registers three different delayed trigger for each of the Chancellor of the Dross

    Scenario: the AI player puts one Gemstone Caverns on the battlefield
        Given the AI player has one Gemstone Caverns in hand
        When the system asks the AI player for start of game decisions
        Then the AI player puts one Gemstone Caverns on the battlefield
        And the AI player exiles a card from hand

    Scenario: the AI player puts one Gemstone Caverns on the battlefield even if there are many Gemstone Caverns in hand
        Given the AI player has three Gemstone Caverns in hand
        When the system asks the AI player for start of game decisions
        Then the AI player puts one Gemstone Caverns on the battlefield
        And the AI player exiles a card from hand

    # In the special case of Leyline Rhinos, not putting anything on the battlefield can be a desired play.
    # We hereby consider that all leylines are better to be put on the board than staying in hand,
    # ignoring the Rhinos case.
    Scenario: the AI player puts one Leyline on the battlefield
        Given the AI player has one Leyline of the Guildpact in hand
        When the system asks the AI player for start of game decisions
        Then the AI player puts one or more Leyline of the Guildpact on the battlefield

    Scenario: the AI player puts one or more Leylines on the battlefield
        Given the AI player has three Leyline of the Guildpact in hand
        When the system asks the AI player for start of game decisions
        Then the AI player puts one or more Leyline of the Guildpact on the battlefield
