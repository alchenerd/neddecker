Feature: AI player acts in the untap phase of an Magic: the Gathering game (prevent untap)

    Background: the AI player is connected via OpneAI's API
        Given the AI player for untap step is GPT from OpenAI

    Scenario: Say hello to the AI player
        When the system says hello to the AI player
        Then the AI player responds with something
 
    Scenario: the AI player has no card to prevent from untapping
        Given there is no card to prevent from untapping
        When the system asks the AI player for prevent untap decisions
        Then the AI player does nothing

    Scenario: the AI player has one card to prevent from untapping
        Given there is one card that doesn't untap because of oracle text
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent the card's untapping

    Scenario: the AI player has three cards to prevent from untapping
        Given there are three cards that don't untap because of oracle text
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent the three card's untapping

    Scenario: the AI player skips the untap step because of self
        Given the AI player is set to skip the untap step because of self
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent all controlled cards' untapping

    Scenario: the AI player skips the untap step because of opponent
        Given the AI player is set to skip the untap step because of opponent
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent all controlled cards' untapping

    # "may choose not to untap" will not be tested

    Scenario: the AI player has one card that was annotated as doesn't untap
        # e.g. Chill of the Grave
        Given there is one card that was annotated as doesn't untap
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent the card's untapping

    Scenario: the AI player has three cards that were annotated as doesn't untap
        Given there are three cards that were annotated as doesn't untap
        When the system asks the AI player for prevent untap decisions
        Then the AI player chooses to prevent the three card's untapping
