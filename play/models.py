from django.db import models
from django.core import serializers
from typing import Tuple
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
    cmc = models.FloatField(blank=False) # e.g. 6, for cascade
    colors = models.CharField(max_length=255, blank=True) # e.g. ["G"], for protection
    defense = models.CharField(max_length=255, blank=True) # for battles
    loyalty = models.CharField(max_length=255, blank=True) # for planeswalkers
    mana_cost = models.CharField(max_length=255, blank=True) # e.g. "{4}{G}{G}"
    name = models.CharField(max_length=255) # e.g. "Colossal Dreadmaw"
    oracle_text = models.CharField(max_length=1023, blank=True) # e.g. "Trample"
    power = models.CharField(max_length=255, blank=True) # e.g. "6"
    produced_mana = models.CharField(max_length=255, blank=True) # for mana sources, see colors
    toughness = models.CharField(max_length=255, blank=True) # e.g. "6"
    type_line = models.CharField(max_length=255, blank=True) # e.g. "Creature - Dinosaur"
    card_image_uri = models.URLField(max_length=255, blank=True) # for frontend rendering
    layout = models.CharField(max_length=255, blank=True) # for frontend rendering
    def __str__(self):
        fields = (
                'cmc',
                'colors',
                'name',
                'mana_cost',
                'type_line',
                'oracle_text',
                'power',
                'toughness',
                'produced_mana',
                'loyalty',
                'defense',
                'layout',
        )
        return json.dumps(json.loads(serializers.serialize('json', (self,), fields=fields))[-1]['fields'])

def get_card_by_name_as_dict(name) -> Card:
    return Card.objects.filter(name=name).order_by().values().first()

def get_card_orm_by_name(name) -> Card:
    return Card.objects.filter(name=name).order_by().first()

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
    card_image_uri = models.URLField(max_length=255, blank=True)
    def __str__(self):
        fields = (
                'cmc',
                'colors',
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

def get_faces_by_name_as_dict(name) -> Tuple[Face, Face]:
    if ' // ' not in name:
        return None, None
    f, b = name.split(' // ')
    front, back = None, None
    try:
        front = Face.objects.filter(name=f).order_by().values().first()
        back = Face.objects.filter(name=b).order_by().values().first()
    except:
        pass
    return front, back

def get_faces_orm_by_name(name) -> Tuple[Face, Face]:
    if ' // ' not in name:
        return None, None
    f, b = name.split(' // ')
    front, back = None, None
    try:
        front = Face.objects.filter(name=f).order_by().first()
        back = Face.objects.filter(name=b).order_by().first()
    except:
        pass
    return front, back

ABILITY_TYPES = {
    "spell": "spell ability",
    "activated": "activated ability",
    "triggered": "triggered ability",
    "static": "static ability",
    "mana": "mana ability",
}

class GameRule(models.Model):
    """
    Rule of a single ability printed on a card
    """
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='game_rule', verbose_name="Card this rule applies to")
    ability = models.CharField(max_length=1023, verbose_name="Text describing a single effect of the card")
    order = models.IntegerField(verbose_name="Order of execution. Lower numbers are executed first. Sort by gherkin statement order.")
    ability_type = models.CharField(max_length=255, verbose_name="Type of the ability", choices=ABILITY_TYPES)
    gherkin = models.CharField(max_length=1023, verbose_name="One-line statement in Gherkin syntax describing the card's effect. Can be a Given, When, or Then statement. And and But are allowed as well.")
    lambda_code = models.TextField(verbose_name="Python lambda function implementing the game logic based on the gherkin statement. Provided by the LLM coder. Function signature: Callable[[context: Any], bool] for Given/When statements, Callable[[context: Any], List[Any]] for Then statements.")

    class Meta:
        unique_together = (('card', 'ability', 'order'),)  # Composite key

    def __str__(self):
        return f"{self.card.name} - {self.ability}"
