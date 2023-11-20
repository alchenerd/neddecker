from django.contrib import admin
from .models import Deck, Card, Face

# Register your models here.
admin.site.register(Deck)
admin.site.register(Card)
admin.site.register(Face)
