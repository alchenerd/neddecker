import random
from typing import List, Dict, Tuple
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from django.db.models.functions import Length
from django.contrib.postgres.search import TrigramSimilarity
from django.views.decorators.http import require_POST
from .models import Deck, Card, Face
from .forms import DecklistForm
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
    lines = decklist.split('\r\n')
    maindeck, sideboard = {}, {}
    tofill = maindeck
    for line in lines:
        if line == '':
            tofill = sideboard
            continue
        parsed = line.split()
        count = int(parsed[0])
        # The replace() converts mtggoldfish name to scryfall name
        card = ' '.join(parsed[1:]).replace('/', ' // ')
        tofill[card] = count
    return maindeck, sideboard

def get_random_deck() -> Deck:
    total_meta = Deck.objects.aggregate(total_meta=Sum('meta'))['total_meta'] or 1.0
    weighted_meta = [deck.meta / total_meta for deck in Deck.objects.all()]
    return random.choices(Deck.objects.all(), weights=weighted_meta)[0]

def get_card_by_name(name) -> Card:
    card = Card.objects.annotate(similarity=TrigramSimilarity('name', name),).filter(similarity__gt=0.3).order_by('-similarity', Length('card_image').desc()).first()
    return card

def get_cards_and_faces(maindeck, sideboard) -> Tuple[List[Card], List[Face], List[Card], List[Face], Dict[str, int], Dict[str, int]]:
    main_cards, main_faces, side_cards, side_faces = [], [], [], []
    dup_m, dup_s = maindeck.copy(), sideboard.copy()
    for name in maindeck:
        card = get_card_by_name(name)
        _faces = Face.objects.filter(card=card) if card else []
        if card.name not in dup_m:
            dup_m[card.name] = dup_m.get(name)
            dup_m.pop(name)
        main_cards.append(card)
        main_faces.extend(_faces)
    for name in sideboard:
        card = get_card_by_name(name)
        _faces = Face.objects.filter(card=card) if card else []
        if card.name not in dup_s:
            dup_s[card.name] = dup_s.get(name)
            dup_s.pop(name)
        side_cards.append(card)
        side_faces.extend(_faces)
    return main_cards, main_faces, side_cards, side_faces, dup_m, dup_s

def get_card_image_map(*args):
    card_image_map = {}
    for arg in args:
        for item in arg:
            if hasattr(item, 'card_image') and item.card_image:
                card_image_map[item.name] = item.card_image
    return card_image_map

@require_POST
def play(request):
    neds_deck = get_random_deck()
    neds_main, neds_side = parse_decklist(neds_deck.decklist)
    neds_main_cards, neds_main_faces, neds_side_cards, neds_side_faces, neds_main, neds_side = get_cards_and_faces(neds_main, neds_side)
    user_main, user_side = parse_decklist(request.POST.get('decklist', ''))
    user_main_cards, user_main_faces, user_side_cards, user_side_faces, user_main, user_side = get_cards_and_faces(user_main, user_side)
    card_image_map = get_card_image_map(user_main_cards, user_main_faces, user_side_cards, user_side_faces, neds_main_cards, neds_main_faces, neds_side_cards, neds_side_faces)
    #print(card_image_map)
    context = {
               'user_main': user_main,
               'user_side': user_side,
               'neds_main': neds_main,
               'neds_side': neds_side,
               'card_image_map': card_image_map,}
    return render(request, 'play/play.html', context)

def chat(request, deck_name: str):
    context = {'deck_name': deck_name}
    return render(request, 'play/chat.html', context)
