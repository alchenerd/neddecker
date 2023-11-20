from django.shortcuts import render
from django.http import HttpResponse
from .models import Deck, Card, Face

def index(request):
    top_5_decks = Deck.objects.order_by('date')[:5]
    context = {'top_5_decks': top_5_decks}
    return render(request, 'play/index.html', context)

def play(request):
    return HttpResponse("Hello World: Play")
