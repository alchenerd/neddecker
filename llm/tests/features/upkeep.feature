Feature: AI player acts in the upkeep phase of an Magic: the Gathering game

    Background: the AI player is connected via OpneAI's API
        Given the AI player for upkeep step is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something
