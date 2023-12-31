from django.db import models
from django.core import serializers
import json

class Deck(models.Model):
    """
    Decks scraped from mtggoldfish
    """
    name = models.CharField(max_length=127)
    meta = models.FloatField(default=0)
    url = models.URLField(max_length=255)
    decklist = models.TextField()
    date = models.DateField(auto_now_add=True)
    art = models.URLField(max_length=255, blank=True)
    def __str__(self):
        return serializers.serialize('json', [self,])

class Card(models.Model):
    """
    Cards scraped from scryfall
    """
    cmc = models.FloatField(blank=False) # e.g. 6
    colors = models.CharField(max_length=255, blank=True) # need preprocessing e.g. ["G"]
    defense = models.CharField(max_length=255, blank=True) # for battles
    loyalty = models.CharField(max_length=255, blank=True) # for planeswalkers
    mana_cost = models.CharField(max_length=255, blank=True) # e.g. "{4}{G}{G}"
    name = models.CharField(max_length=255) # e.g. "Colossal Dreadmaw"
    oracle_text = models.CharField(max_length=1023, blank=True) # e.g. "Trample"
    power = models.CharField(max_length=255, blank=True) # e.g. "6"
    produced_mana = models.CharField(max_length=255, blank=True)# see colors
    toughness = models.CharField(max_length=255, blank=True) # e.g. "6"
    type_line = models.CharField(max_length=255, blank=True) # e.g. "Creature - Dinosaur"
    card_image = models.URLField(max_length=255, blank=True)
    def __str__(self):
        fields = (
                'name',
                'mana_cost',
                'type_line',
                'oracle_text',
                'power',
                'toughness',
                'produced_mana',
                'loyalty',
                'defense',
        )
        return json.dumps(json.loads(serializers.serialize('json', (self,), fields=fields))[-1]['fields'])

class Face(models.Model):
    """
    Faces for multiple-faced cards
    """
    card = models.ForeignKey('Card', on_delete=models.CASCADE)
    cmc = models.FloatField(blank=False)
    colors = models.CharField(max_length=255, blank=True)
    defense = models.CharField(max_length=255, blank=True)
    loyalty = models.CharField(max_length=255, blank=True)
    mana_cost = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255) # name of this face
    oracle_text = models.TextField(max_length=1023, blank=True)
    power = models.CharField(max_length=255, blank=True)
    toughness = models.CharField(max_length=255, blank=True)
    type_line = models.CharField(max_length=255, blank=True)
    card_image = models.URLField(max_length=255, blank=True)
    def __str__(self):
        fields = (
                'name',
                'mana_cost',
                'type_line',
                'oracle_text',
                'power',
                'toughness',
                'produced_mana',
                'loyalty',
                'defense',
                )
        return json.dumps(json.loads(serializers.serialize('json', (self,), fields=fields))[-1]['fields'])
