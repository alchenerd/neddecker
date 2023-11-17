from django.db import models

class Deck(models.Model):
    """
    Decks scraped from mtggoldfish
    """
    name = models.CharField(max_length=127)
    meta = models.FloatField(default=0)
    url = models.URLField(max_length=255)
    decklist = models.TextField()
    date = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.name

class Card(models.Model):
    """
    Cards scraped from scryfall
    """
    cmc = models.FloatField(blank=False) # e.g. 6
    colors = models.CharField(max_length=100) # need preprocessing e.g. ["G"]
    defense = models.CharField(max_length=100) # for battles
    loyalty = models.CharField(max_length=100) # for planeswalkers
    mana_cost = models.CharField(max_length=100) # e.g. "{4}{G}{G}"
    name = models.CharField(max_length=100) # e.g. "Colossal Dreadmaw"
    oracle_text = models.CharField(max_length=500) # e.g. "Trample"
    power = models.CharField(max_length=100) # e.g. "6"
    produced_mana = models.CharField(max_length=100)# see colors
    toughness = models.CharField(max_length=100) # e.g. "6"
    type_line = models.CharField(max_length=100) # e.g. "Creature - Dinosaur"

class Face(models.Model):
    """
    Faces for multiple-faced cards
    """
    full_name = models.CharField(max_length=100) # foriegn key to Card
    cmc = models.FloatField(blank=False)
    colors = models.CharField(max_length=100)
    defense = models.CharField(max_length=100)
    loyalty = models.CharField(max_length=100)
    mana_cost = models.CharField(max_length=100)
    name = models.CharField(max_length=100) # name of this face
    oracle_text = models.TextField(max_length=500)
    power = models.CharField(max_length=100)
    toughness = models.CharField(max_length=100)
    type_line = models.CharField(max_length=100)

    
