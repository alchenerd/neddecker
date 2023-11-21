import random
from typing import List, Dict, Tuple
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from .models import Deck, Card, Face
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.agents import load_tools, initialize_agent, AgentType
from dotenv import load_dotenv

load_dotenv()

def ask_ned_about(deck):
    llm = OpenAI(temperature=0.8)
    prompt = f"""Assistant is Ned Decker; Ned Decker is a competitive Magic: the Gathering player. Ned Decker will be playing a deck named {deck.name}.

    The decklist of {deck.name}:
    {deck.decklist}

    Start chatting about {deck.name} as Ned Decker.
    """
    response = llm(prompt)
    return response

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
        try:
            card = Card.objects.filter(name__icontains=name).first()
            _faces = Face.objects.filter(card=card) if card else []
            cards.append(card)
            faces.extend(_faces)
        except Card.DoesNotExist:
            pass
    return cards, faces

def play(request, deck_name='Custom Deck'):
    neds_deck = get_random_deck()
    neds_main, neds_side = parse_decklist(neds_deck.decklist)
    neds_cards, neds_faces = get_cards_and_faces(neds_main, neds_side)
    user_deck = Deck.objects.get(name=deck_name)
    user_main, user_side = parse_decklist(user_deck.decklist)
    user_cards, user_faces = get_cards_and_faces(user_main, user_side)
    context = {'user_deck': user_deck,
               'user_main': user_main,
               'user_side': user_side,
               'user_cards': user_cards,
               'user_faces': user_faces,
               'neds_deck': neds_deck,
               'neds_main': neds_main,
               'neds_side': neds_side,
               'neds_cards': neds_cards,
               'neds_faces': neds_faces,}
    return render(request, 'play/play.html', context)
