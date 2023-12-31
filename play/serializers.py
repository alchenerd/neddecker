from .models import Deck, Card, Face
from rest_framework import serializers

class DeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ['name', 'meta', 'decklist', 'art']

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = [
                'name',
                'mana_cost',
                'type_line',
                'oracle_text',
                'power',
                'toughness',
                'produced_mana',
                'loyalty',
                'defense',
        ]

class FaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Face
        fields = [
                'name',
                'mana_cost',
                'type_line',
                'oracle_text',
                'power',
                'toughness',
                'produced_mana',
                'loyalty',
                'defense',
        ]
