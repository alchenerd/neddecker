Feature: AI player acts in the upkeep phase of an Magic: the Gathering game

    Background: the AI player is connected via OpneAI's API
        Given the AI player for upkeep step is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something

    Scenario: the AI player has no upkeep trigger to create
        Given the AI player has no permanent that has an upkeep trigger
        When the system asks the AI player for upkeep decisions
        Then the AI player does nothing

    Scenario: the AI player has one upkeep trigger to create because of permanent
        Given the AI player has one permanent that has an upkeep trigger because of permanent
        When the system asks the AI player for upkeep decisions
        Then the AI player creates one upkeep trigger

    Scenario: the AI player has one upkeep trigger to create because of delayed trigger
        Given the AI player has one permanent that has an upkeep trigger because of delayed trigger
        When the system asks the AI player for upkeep decisions
        Then the AI player creates one upkeep trigger

    Scenario: the AI player has two upkeep triggers to create
        Given the AI player has two permanents that has an upkeep trigger
        When the system asks the AI player for upkeep decisions
        Then the AI player creates two upkeep triggers
