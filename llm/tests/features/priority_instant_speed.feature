Feature: Magic: the Gathering game AI player makes decisions when receiving priority

    Background: the AI player is connected via OpneAI's API
        Given the AI player receiving priority (instant speed) is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something

    Scenario: the AI player has been given a board state
        Given the AI player receives a board state
        When the system asks the AI player for instant speed decisions
        Then the AI player responds with something
