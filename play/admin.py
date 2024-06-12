from django.contrib import admin
from .models import Deck, Card, Face, GameRule

# Register your models here.
admin.site.register(Deck)
admin.site.register(Card)
admin.site.register(Face)
admin.site.register(GameRule)
