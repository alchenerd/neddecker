import random
from typing import List, Dict, Tuple
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from django.db.models.functions import Length
from django.contrib.postgres.search import TrigramSimilarity
from django.views.decorators.http import require_POST
from .models import Deck, Card, Face
from .models import get_card_by_name
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.agents import load_tools, initialize_agent, AgentType
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from .serializers import DeckSerializer
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
    cover_images = [deck.art for deck in top_5_decks]
    deck_matrix = [top_5_decks[:3],[*top_5_decks[3:5], None]]
    art_matrix = [cover_images[:3],[*cover_images[3:5], None]]
    decklists = {deck.name: deck.decklist for deck in top_5_decks}
    for i, rows in enumerate(deck_matrix):
        for j, deck in enumerate(rows):
            deck_matrix[i][j] = (deck, art_matrix[i][j])
    decklist_form = DecklistForm
    context = {
            'decks': deck_matrix,
            'decklists': decklists,
            'form': decklist_form,
    }
    return render(request, 'play/index.html', context)

def parse_decklist(decklist) -> List[Dict[str, int]]:
    lines = [entry.strip('\r') for entry in decklist.split('\n')]
    maindeck, sideboard = {}, {}
    tofill = maindeck
    for line in lines:
        if line == '':
            tofill = sideboard
            continue
        parsed = line.split()
        count = int(parsed[0])
        card = ' '.join(parsed[1:])
        tofill[card] = count
    return maindeck, sideboard

def get_random_deck() -> Deck:
    total_meta = Deck.objects.aggregate(total_meta=Sum('meta'))['total_meta'] or 1.0
    weighted_meta = [deck.meta / total_meta for deck in Deck.objects.all()]
    return random.choices(Deck.objects.all(), weights=weighted_meta)[0]

def get_cards_and_faces(maindeck, sideboard) -> Tuple[List[Card], List[Face], List[Card], List[Face]]:
    maindeck_count = 0
    bad_lines = []
    main_cards, main_faces, side_cards, side_faces = [], [], [], []
    for name, count in maindeck.items():
        maindeck_count += count
        try:
            card = get_card_by_name(name)
        except:
            bad_lines.append(name)
            continue
        _faces = Face.objects.filter(card=card) if card else []
        main_cards.append(card)
        main_faces.extend(_faces)
    for name in sideboard:
        try:
            card = get_card_by_name(name)
        except:
            bad_lines.append(name)
            continue
        _faces = Face.objects.filter(card=card) if card else []
        side_cards.append(card)
        side_faces.extend(_faces)

    if maindeck_count < 60:
        raise ValueError(f'Not enough cards: {maindeck_count} is less than 60.')
    if bad_lines:
        raise ValueError(', '.join(bad_lines))
    return main_cards, main_faces, side_cards, side_faces

def get_card_image_map(*args):
    card_image_map = {}
    for arg in args:
        for item in arg:
            if hasattr(item, 'card_image') and item.card_image:
                card_image_map[item.name] = item.card_image
    return card_image_map

def get_type_line_map(*args):
    type_line_map = {}
    for arg in args:
        for item in arg:
            if hasattr(item, 'type_line') and item.type_line:
                type_line_map[item.name] = item.type_line
    return type_line_map

"""
def chat(request, deck_name: str):
    context = {'deck_name': deck_name}
    return render(request, 'play/chat.html', context)
"""

class TopFiveMetaDecksViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Deck.objects.all().order_by('-meta')[:5]
    serializer_class = DeckSerializer

@api_view(['POST'])
def play(request):
    users_decklist = JSONParser().parse(request).get('decklist')
    users_main, users_side = parse_decklist(users_decklist)
    try:
        users_main_cards, users_main_faces, users_side_cards, users_side_faces = get_cards_and_faces(users_main, users_side)
    except ValueError as e:
        error_context = { 'status': 'error', 'message': str(e) }
        return JsonResponse(error_context, status=400)
    neds_deck = get_random_deck()
    neds_main, neds_side = parse_decklist(neds_deck.decklist)
    neds_main_cards, neds_main_faces, neds_side_cards, neds_side_faces = get_cards_and_faces(neds_main, neds_side)
    to_process = neds_main_cards + neds_main_faces + neds_side_cards + neds_side_faces + users_main_cards + users_main_faces + users_side_cards + users_side_faces
    card_image_map = get_card_image_map(to_process)
    context = {
            'users_main': users_main,
            'users_side': users_side,
            'neds_main': neds_main,
            'neds_side': neds_side,
            'card_image_map': card_image_map,
    }
    return JsonResponse(context)
