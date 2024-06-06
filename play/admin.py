from django.contrib import admin
from .models import Deck, Card, Face, GameRule

class GameRuleAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)

# Register your models here.
admin.site.register(Deck)
admin.site.register(Card)
admin.site.register(Face)
admin.site.register(GameRule, GameRuleAdmin)
