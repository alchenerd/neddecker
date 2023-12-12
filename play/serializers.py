from .models import Deck
from rest_framework import serializers

class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ['name', 'meta', 'decklist', 'art']
