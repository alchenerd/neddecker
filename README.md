# Ned Decker
A prototype of LLM + MTGA-esque Game Rules Engine (Whiteboard and nap explanation) [https://magic.wizards.com/en/news/mtg-arena/on-whiteboards-naps-and-living-breakthrough]

# What can it do
1. have LLM assess a starting hand of MTG
2. have LLM write card rules using gherkin format
3. have LLM convert gherkin card rules into python lambda function to apply

# What it can't do
- dynamically load and run the lambda functions on the game object
- complete a turn

# Status
This prototype will be left alone indefinitely due to time pressure.

# TODO if I could start over
- start with a text version instead of a django project
- debulk what was sent over django channels
- use cmd.Cmd instead of writing everything from scratch
- simulate a game using preconstructed decks instead of modern meta decks
- rely less on LLM when there exists a deterministic solution
- making a simple game from scratch seems easier than coding an MTG engine
