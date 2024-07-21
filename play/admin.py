from django.contrib import admin
from .models import Deck, Card, Face, GameRule, KeywordAbility, GherkinRule, GherkinImpl

class KeywordAbilityAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)

class GherkinRuleAdmin(admin.ModelAdmin):
    raw_id_fields = ('card',)

# Register your models here.
admin.site.register(Deck)
admin.site.register(Card)
admin.site.register(Face)
admin.site.register(GameRule)
admin.site.register(KeywordAbility, KeywordAbilityAdmin)
admin.site.register(GherkinRule, GherkinRuleAdmin)
admin.site.register(GherkinImpl)
