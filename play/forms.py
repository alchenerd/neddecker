from django import forms

class DecklistForm(forms.Form):
    decklist = forms.CharField(label=False, widget=forms.Textarea(attrs={'name': 'decklist-box', 'placeholder': '4 Colossal Dreadmaw\n4 Storm Crow\n...', 'rows': '23', 'cols': '50', 'class': 'decklist-box'}))

