import random
from typing import List, Dict, Tuple
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib.postgres.search import TrigramSimilarity
from .models import Deck, Card, Face
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.agents import load_tools, initialize_agent, AgentType
from dotenv import load_dotenv

load_dotenv()

def ned_talks_about(name, main, side, cards, faces):
    llm = ChatOpenAI(model_name='gpt-3.5-turbo-16k', temperature=0.8, max_tokens=1024)
    whoami = f"""Assistant is Ned Decker. Ned Decker is a competitive Magic: the Gathering player. Ned Decker will be playing a deck named {name} in a modern format tournament. Ned Decker is chatting with his opponent before their first game of the match.
    """
    data = f"""[Related data]
    Ned Decker's Deck = {name}
    """
    data += "\nNed Decker's main decklist:\n"
    for card_name, quantity in main.items():
        data += f'{quantity}x {card_name}\n'
    data += "\nNed Decker's sideboard decklist:\n"
    for card_name, quantity in side.items():
        data += f'{quantity}x {card_name}\n'
    data += "\nRelated oracle text:\n"
    for card in cards:
        if not card:
            continue
        data += '\n'
        data += f'{card.name}\n'
        data += f'mana cost: {card.mana_cost}\n'
        data += f"type: {card.type_line or ''}\n"
        data += f"{card.name}'s oracle text: {card.oracle_text}\n"
        if card.mana_cost:
            data += f'mana cost: {card.mana_cost}\n'
        if card.power:
            data += f'power: {card.power}\n'
        if card.toughness:
            data += f'toughness: {card.toughness}\n'
        if card.defense:
            data += f'defense: {card.defense}\n'
        if card.loyalty:
            data += f'loyalty: {card.loyalty}\n'
        data += '\n'
    request = f"\nAssistant as Ned Decker will talk about the deck {name} that Ned decker will be using, but keep the content of the deck as top secret. Afterwards, in assistant's next reply, detailedly introduce Ned Decker's most favourite card."
    prompt = ChatPromptTemplate.from_messages([SystemMessage(content = data + whoami + request)])
    return llm.invoke(prompt.format_messages())

def index(request):
    top_5_decks = Deck.objects.order_by('-meta')[:5]
    matrix = [top_5_decks[:3],[*top_5_decks[3:5], None]]
    context = {'decks': matrix}
    return render(request, 'play/index.html', context)

def parse_decklist(decklist) -> List[Dict[str, int]]:
    lines = decklist.split('\r\n')
    maindeck, sideboard = {}, {}
    tofill = maindeck
    for line in lines:
        if line == '':
            tofill = sideboard
            continue
        parsed = line.split()
        count = int(parsed[0])
        # The replace() converts mtggoldfish to scryfall
        card = ' '.join(parsed[1:]).replace('/', ' // ')
        tofill[card] = count
    return maindeck, sideboard

def get_random_deck() -> Deck:
    total_meta = Deck.objects.aggregate(total_meta=Sum('meta'))['total_meta'] or 1.0
    weighted_meta = [deck.meta / total_meta for deck in Deck.objects.all()]
    return random.choices(Deck.objects.all(), weights=weighted_meta)[0]

def get_cards_and_faces(maindeck, sideboard) -> Tuple[List[Card], List[Face]]:
    cards, faces = [], []
    for name in maindeck | sideboard:
        card = None
        try:
            card = Card.objects.filter(name__icontains=name).first()
            if not card:
                card = Card.objects.annotate(similarity=TrigramSimilarity('name', name),).filter(similarity__gt=0.3).order_by('-similarity').first()
        except Card.DoesNotExist:
            pass
        _faces = Face.objects.filter(card=card) if card else []
        cards.append(card)
        faces.extend(_faces)
    return cards, faces

def play(request, deck_name='Custom_Deck'):
    deck_name = deck_name.replace('_', ' ')
    neds_deck = get_random_deck()
    neds_main, neds_side = parse_decklist(neds_deck.decklist)
    neds_cards, neds_faces = get_cards_and_faces(neds_main, neds_side)
    user_deck = Deck.objects.get(name=deck_name)
    user_main, user_side = parse_decklist(user_deck.decklist)
    user_cards, user_faces = get_cards_and_faces(user_main, user_side)
    gpt = None
    # uncomment if you want to be billed
    #gpt = ned_talks_about(neds_deck.name, neds_main, neds_side, neds_cards, neds_faces)
    context = {'user_deck': user_deck,
               'user_main': user_main,
               'user_side': user_side,
               'user_cards': user_cards,
               'user_faces': user_faces,
               'neds_deck': neds_deck,
               'neds_main': neds_main,
               'neds_side': neds_side,
               'neds_cards': neds_cards,
               'neds_faces': neds_faces,
               'gpt': gpt or '',}
    return render(request, 'play/play.html', context)

def chat(request, deck_name: str):
    context = {'deck_name': deck_name}
    return render(request, 'play/chat.html', context)
