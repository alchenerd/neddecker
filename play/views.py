from django.shortcuts import render
from django.http import HttpResponse
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

def play(request, deck_name='Custom Deck'):
    deck = Deck.objects.get(name=deck_name)
    reply = ask_ned_about(deck)
    return HttpResponse(f'{reply}')
