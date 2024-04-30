Feature: AI player acts in the draw phase of an Magic: the Gathering game

    Background: the AI player is connected via OpneAI's API
        Given the AI player for draw step is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something

    Scenario: the AI player has no draw replacement to make
        Given the AI player controls a Jace, Wielder of Mysteries
        When the system asks the AI player for draw replacement decisions
        Then the AI player does nothing

    Scenario: the AI player has one draw replacement to make (self-controlled permanent)
        Given the AI player controls a Thought Reflection
        When the system asks the AI player for draw replacement decisions
        Then the AI player replaces one draw with two draws

    Scenario: the AI player has one draw replacement to make (opponent-controlled permanent)
        Given the AI player's opponent controls a Possessed Portal
        When the system asks the AI player for draw replacement decisions
        Then the AI player replaces one draw with no draw

    Scenario: the AI player has one draw replacement to make (delayed trigger)
        Given the AI player's opponent controls a Urabrask, Heretic Praetor
        And Urabrask, Heretic Praetor has resolved its trigger on the AI player's upkeep
        When the system asks the AI player for draw replacement decisions
        Then the AI player replaces one draw with no draw
